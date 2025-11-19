"""
GUIベースのカラオケピッチアナライザー
tkinterを使用したデスクトップアプリケーション
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from src.audio_capture import AudioCapture, SystemAudioCapture
from src.pitch_detection import PitchDetector
from src.analyzer import PitchAnalyzer
from src.config import Config
from src.session import SessionRecorder, TimingAdjuster, KeyChanger
from src.audio_utils import VolumeMonitor


class SettingsWindow:
    """設定ウィンドウ"""

    def __init__(self, parent, config: Config, on_save_callback=None):
        self.window = tk.Toplevel(parent)
        self.window.title("設定")
        self.window.geometry("600x500")
        self.config = config
        self.on_save_callback = on_save_callback

        self._create_widgets()

    def _create_widgets(self):
        """ウィジェットを作成"""
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # オーディオ設定タブ
        audio_frame = ttk.Frame(notebook)
        notebook.add(audio_frame, text='オーディオ')
        self._create_audio_settings(audio_frame)

        # 表示設定タブ
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text='表示')
        self._create_display_settings(display_frame)

        # 分析設定タブ
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text='分析')
        self._create_analysis_settings(analysis_frame)

        # 高度な設定タブ
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text='高度な設定')
        self._create_advanced_settings(advanced_frame)

        # ボタン
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(button_frame, text='保存', command=self._save_settings).pack(side='right', padx=5)
        ttk.Button(button_frame, text='キャンセル', command=self.window.destroy).pack(side='right', padx=5)
        ttk.Button(button_frame, text='デフォルトに戻す', command=self._reset_to_default).pack(side='left', padx=5)

    def _create_audio_settings(self, parent):
        """オーディオ設定を作成"""
        # システムオーディオ使用
        self.use_system_audio_var = tk.BooleanVar(
            value=self.config.get('audio', 'use_system_audio', False)
        )
        ttk.Checkbutton(
            parent,
            text='システムオーディオを使用（原曲との比較）',
            variable=self.use_system_audio_var
        ).pack(anchor='w', padx=10, pady=10)

        # デバイス選択
        ttk.Label(parent, text='マイクデバイス:').pack(anchor='w', padx=10, pady=(10, 0))

        self.mic_device_var = tk.StringVar()
        mic_combo = ttk.Combobox(parent, textvariable=self.mic_device_var, state='readonly')
        mic_combo.pack(fill='x', padx=10, pady=5)

        # デバイスリストを取得
        import sounddevice as sd
        devices = sd.query_devices()
        self.input_devices = []
        device_names = ['自動検出']

        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                self.input_devices.append(i)
                device_names.append(f"[{i}] {device['name']}")

        mic_combo['values'] = device_names

        # 現在の設定を反映
        current_mic = self.config.get('audio', 'mic_device')
        if current_mic is None:
            mic_combo.current(0)
        else:
            try:
                idx = self.input_devices.index(current_mic) + 1
                mic_combo.current(idx)
            except ValueError:
                mic_combo.current(0)

        ttk.Label(parent, text='システムオーディオデバイス:').pack(anchor='w', padx=10, pady=(10, 0))

        self.system_device_var = tk.StringVar()
        system_combo = ttk.Combobox(parent, textvariable=self.system_device_var, state='readonly')
        system_combo.pack(fill='x', padx=10, pady=5)
        system_combo['values'] = device_names

        # 現在の設定を反映
        current_system = self.config.get('audio', 'system_device')
        if current_system is None:
            system_combo.current(0)
        else:
            try:
                idx = self.input_devices.index(current_system) + 1
                system_combo.current(idx)
            except ValueError:
                system_combo.current(0)

        # サンプリングレート
        ttk.Label(parent, text='サンプリングレート (Hz):').pack(anchor='w', padx=10, pady=(10, 0))

        self.sample_rate_var = tk.StringVar(
            value=str(self.config.get('audio', 'sample_rate', 44100))
        )
        sample_rate_combo = ttk.Combobox(
            parent,
            textvariable=self.sample_rate_var,
            values=['22050', '44100', '48000'],
            state='readonly'
        )
        sample_rate_combo.pack(fill='x', padx=10, pady=5)

    def _create_display_settings(self, parent):
        """表示設定を作成"""
        # 表示モード
        ttk.Label(parent, text='表示モード:').pack(anchor='w', padx=10, pady=(10, 0))

        self.display_mode_var = tk.StringVar(
            value=self.config.get('display', 'mode', 'detailed')
        )

        modes = [
            ('シンプル', 'simple'),
            ('詳細', 'detailed'),
            ('プロフェッショナル', 'professional')
        ]

        for text, value in modes:
            ttk.Radiobutton(
                parent,
                text=text,
                variable=self.display_mode_var,
                value=value
            ).pack(anchor='w', padx=30, pady=2)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # テーマ
        ttk.Label(parent, text='テーマ:').pack(anchor='w', padx=10, pady=(10, 0))

        self.theme_var = tk.StringVar(
            value=self.config.get('display', 'theme', 'dark')
        )

        themes = [('ダーク', 'dark'), ('ライト', 'light')]

        for text, value in themes:
            ttk.Radiobutton(
                parent,
                text=text,
                variable=self.theme_var,
                value=value
            ).pack(anchor='w', padx=30, pady=2)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # 表示要素
        ttk.Label(parent, text='表示要素:').pack(anchor='w', padx=10, pady=(10, 0))

        self.show_pitch_graph_var = tk.BooleanVar(
            value=self.config.get('display', 'show_pitch_graph', True)
        )
        ttk.Checkbutton(
            parent,
            text='ピッチグラフを表示',
            variable=self.show_pitch_graph_var
        ).pack(anchor='w', padx=30, pady=2)

        self.show_cents_gauge_var = tk.BooleanVar(
            value=self.config.get('display', 'show_cents_gauge', True)
        )
        ttk.Checkbutton(
            parent,
            text='セント差ゲージを表示',
            variable=self.show_cents_gauge_var
        ).pack(anchor='w', padx=30, pady=2)

        self.show_statistics_var = tk.BooleanVar(
            value=self.config.get('display', 'show_statistics', True)
        )
        ttk.Checkbutton(
            parent,
            text='統計情報を表示',
            variable=self.show_statistics_var
        ).pack(anchor='w', padx=30, pady=2)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # 更新間隔
        ttk.Label(parent, text='更新間隔 (ミリ秒):').pack(anchor='w', padx=10, pady=(10, 0))

        self.update_interval_var = tk.IntVar(
            value=self.config.get('display', 'update_interval', 100)
        )

        interval_scale = ttk.Scale(
            parent,
            from_=50,
            to=500,
            variable=self.update_interval_var,
            orient='horizontal'
        )
        interval_scale.pack(fill='x', padx=30, pady=5)

        interval_label = ttk.Label(parent, text='100 ms')
        interval_label.pack(anchor='w', padx=30)

        def update_interval_label(val):
            interval_label.config(text=f'{int(float(val))} ms')

        interval_scale.config(command=update_interval_label)

    def _create_analysis_settings(self, parent):
        """分析設定を作成"""
        # 信頼度閾値
        ttk.Label(parent, text='ピッチ検出信頼度閾値:').pack(anchor='w', padx=10, pady=(10, 0))

        self.confidence_threshold_var = tk.DoubleVar(
            value=self.config.get('analysis', 'confidence_threshold', 0.8)
        )

        conf_scale = ttk.Scale(
            parent,
            from_=0.1,
            to=1.0,
            variable=self.confidence_threshold_var,
            orient='horizontal'
        )
        conf_scale.pack(fill='x', padx=30, pady=5)

        conf_label = ttk.Label(parent, text='0.8')
        conf_label.pack(anchor='w', padx=30)

        def update_conf_label(val):
            conf_label.config(text=f'{float(val):.2f}')

        conf_scale.config(command=update_conf_label)

        ttk.Label(
            parent,
            text='※ 低い値: より多くのピッチを検出（ノイズも増加）\n　高い値: より確実なピッチのみ検出',
            foreground='gray'
        ).pack(anchor='w', padx=30, pady=5)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # 履歴サイズ
        ttk.Label(parent, text='履歴サイズ:').pack(anchor='w', padx=10, pady=(10, 0))

        self.history_size_var = tk.IntVar(
            value=self.config.get('analysis', 'history_size', 100)
        )

        history_scale = ttk.Scale(
            parent,
            from_=50,
            to=500,
            variable=self.history_size_var,
            orient='horizontal'
        )
        history_scale.pack(fill='x', padx=30, pady=5)

        history_label = ttk.Label(parent, text='100')
        history_label.pack(anchor='w', padx=30)

        def update_history_label(val):
            history_label.config(text=f'{int(float(val))}')

        history_scale.config(command=update_history_label)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # オクターブ警告閾値
        ttk.Label(parent, text='オクターブズレ警告閾値:').pack(anchor='w', padx=10, pady=(10, 0))

        self.octave_warning_var = tk.IntVar(
            value=self.config.get('analysis', 'octave_warning_threshold', 5)
        )

        octave_scale = ttk.Scale(
            parent,
            from_=1,
            to=20,
            variable=self.octave_warning_var,
            orient='horizontal'
        )
        octave_scale.pack(fill='x', padx=30, pady=5)

        octave_label = ttk.Label(parent, text='5')
        octave_label.pack(anchor='w', padx=30)

        def update_octave_label(val):
            octave_label.config(text=f'{int(float(val))}')

        octave_scale.config(command=update_octave_label)

        ttk.Label(
            parent,
            text='※ この回数連続でオクターブズレが続くと警告を表示',
            foreground='gray'
        ).pack(anchor='w', padx=30, pady=5)

    def _create_advanced_settings(self, parent):
        """高度な設定を作成"""
        # タイミング調整
        ttk.Label(parent, text='タイミング調整 (ミリ秒):').pack(anchor='w', padx=10, pady=(10, 0))
        ttk.Label(
            parent,
            text='システムオーディオとマイク入力の同期オフセット',
            foreground='gray',
            font=('Arial', 9)
        ).pack(anchor='w', padx=10)

        self.timing_offset_var = tk.IntVar(
            value=self.config.get('audio', 'timing_offset_ms', 0)
        )

        timing_frame = ttk.Frame(parent)
        timing_frame.pack(fill='x', padx=30, pady=5)

        timing_scale = ttk.Scale(
            timing_frame,
            from_=-1000,
            to=1000,
            variable=self.timing_offset_var,
            orient='horizontal'
        )
        timing_scale.pack(side='left', fill='x', expand=True)

        timing_label = ttk.Label(timing_frame, text='0 ms', width=10)
        timing_label.pack(side='right', padx=5)

        def update_timing_label(val):
            ms = int(float(val))
            timing_label.config(text=f'{ms:+d} ms')

        timing_scale.config(command=update_timing_label)

        ttk.Label(
            parent,
            text='正の値: システムオーディオを遅らせる / 負の値: マイクを遅らせる',
            foreground='gray',
            font=('Arial', 8)
        ).pack(anchor='w', padx=30)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # キー変更
        ttk.Label(parent, text='キー変更 (半音):').pack(anchor='w', padx=10, pady=(10, 0))
        ttk.Label(
            parent,
            text='原曲のピッチを半音単位で変更（カラオケのキーコン機能）',
            foreground='gray',
            font=('Arial', 9)
        ).pack(anchor='w', padx=10)

        self.key_shift_var = tk.IntVar(
            value=self.config.get('features', 'key_shift_semitones', 0)
        )

        key_frame = ttk.Frame(parent)
        key_frame.pack(fill='x', padx=30, pady=5)

        key_scale = ttk.Scale(
            key_frame,
            from_=-12,
            to=12,
            variable=self.key_shift_var,
            orient='horizontal'
        )
        key_scale.pack(side='left', fill='x', expand=True)

        key_label = ttk.Label(key_frame, text='0 (変更なし)', width=15)
        key_label.pack(side='right', padx=5)

        def update_key_label(val):
            semitones = int(float(val))
            if semitones == 0:
                key_label.config(text='0 (変更なし)')
            elif semitones > 0:
                key_label.config(text=f'+{semitones} 半音高く')
            else:
                key_label.config(text=f'{semitones} 半音低く')

        key_scale.config(command=update_key_label)

        ttk.Separator(parent, orient='horizontal').pack(fill='x', padx=10, pady=10)

        # 録音設定
        ttk.Label(parent, text='録音設定:').pack(anchor='w', padx=10, pady=(10, 0))

        self.enable_recording_var = tk.BooleanVar(
            value=self.config.get('features', 'enable_recording', True)
        )
        ttk.Checkbutton(
            parent,
            text='セッション録音を有効化',
            variable=self.enable_recording_var
        ).pack(anchor='w', padx=30, pady=2)

        self.auto_save_var = tk.BooleanVar(
            value=self.config.get('features', 'auto_save_session', False)
        )
        ttk.Checkbutton(
            parent,
            text='セッション終了時に自動保存',
            variable=self.auto_save_var
        ).pack(anchor='w', padx=30, pady=2)

        ttk.Label(parent, text='保存先ディレクトリ:').pack(anchor='w', padx=30, pady=(10, 0))

        self.session_dir_var = tk.StringVar(
            value=self.config.get('features', 'session_save_dir', str(Path.home() / 'karaoke_sessions'))
        )

        dir_frame = ttk.Frame(parent)
        dir_frame.pack(fill='x', padx=30, pady=5)

        ttk.Entry(dir_frame, textvariable=self.session_dir_var).pack(side='left', fill='x', expand=True)
        ttk.Button(dir_frame, text='参照...', command=self._browse_session_dir).pack(side='right', padx=5)

    def _browse_session_dir(self):
        """保存先ディレクトリを選択"""
        from tkinter import filedialog
        directory = filedialog.askdirectory(initialdir=self.session_dir_var.get())
        if directory:
            self.session_dir_var.set(directory)

    def _save_settings(self):
        """設定を保存"""
        # オーディオ設定
        self.config.set('audio', 'use_system_audio', self.use_system_audio_var.get())
        self.config.set('audio', 'sample_rate', int(self.sample_rate_var.get()))

        # マイクデバイス
        mic_idx = self.mic_device_var.get()
        if mic_idx.startswith('['):
            device_id = int(mic_idx.split(']')[0][1:])
            self.config.set('audio', 'mic_device', device_id)
        else:
            self.config.set('audio', 'mic_device', None)

        # システムデバイス
        system_idx = self.system_device_var.get()
        if system_idx.startswith('['):
            device_id = int(system_idx.split(']')[0][1:])
            self.config.set('audio', 'system_device', device_id)
        else:
            self.config.set('audio', 'system_device', None)

        # 表示設定
        self.config.set('display', 'mode', self.display_mode_var.get())
        self.config.set('display', 'theme', self.theme_var.get())
        self.config.set('display', 'show_pitch_graph', self.show_pitch_graph_var.get())
        self.config.set('display', 'show_cents_gauge', self.show_cents_gauge_var.get())
        self.config.set('display', 'show_statistics', self.show_statistics_var.get())
        self.config.set('display', 'update_interval', self.update_interval_var.get())

        # 分析設定
        self.config.set('analysis', 'confidence_threshold', self.confidence_threshold_var.get())
        self.config.set('analysis', 'history_size', self.history_size_var.get())
        self.config.set('analysis', 'octave_warning_threshold', self.octave_warning_var.get())

        # 高度な設定
        self.config.set('audio', 'timing_offset_ms', self.timing_offset_var.get())
        self.config.set('features', 'key_shift_semitones', self.key_shift_var.get())
        self.config.set('features', 'enable_recording', self.enable_recording_var.get())
        self.config.set('features', 'auto_save_session', self.auto_save_var.get())
        self.config.set('features', 'session_save_dir', self.session_dir_var.get())

        # 保存
        self.config.save()

        messagebox.showinfo('設定', '設定を保存しました')

        if self.on_save_callback:
            self.on_save_callback()

        self.window.destroy()

    def _reset_to_default(self):
        """デフォルトに戻す"""
        if messagebox.askyesno('確認', '設定をデフォルトに戻しますか？'):
            self.config.reset_to_default()
            messagebox.showinfo('設定', '設定をデフォルトに戻しました')
            self.window.destroy()


class KaraokePitchAnalyzerGUI:
    """GUIメインアプリケーション"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("カラオケピッチアナライザー")
        self.root.geometry("1000x700")

        # 設定を読み込み
        self.config = Config()

        # コンポーネント
        self.mic_capture = None
        self.system_capture = None
        self.pitch_detector_mic = None
        self.pitch_detector_system = None
        self.analyzer = None

        # 状態
        self.is_running = False
        self.analysis_thread = None

        # UI作成
        self._create_menu()
        self._create_widgets()
        self._apply_theme()

        # ウィンドウ閉じる時のハンドラ
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='ファイル', menu=file_menu)
        file_menu.add_command(label='設定', command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label='終了', command=self._on_closing)

        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='表示', menu=view_menu)
        view_menu.add_command(label='シンプルモード', command=lambda: self._change_display_mode('simple'))
        view_menu.add_command(label='詳細モード', command=lambda: self._change_display_mode('detailed'))
        view_menu.add_command(label='プロフェッショナルモード', command=lambda: self._change_display_mode('professional'))

        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='ヘルプ', menu=help_menu)
        help_menu.add_command(label='使い方', command=self._show_help)
        help_menu.add_command(label='バージョン情報', command=self._show_about)

    def _create_widgets(self):
        """ウィジェットを作成"""
        # コントロールパネル
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=10)

        self.start_button = ttk.Button(
            control_frame,
            text='開始',
            command=self._start_analysis
        )
        self.start_button.pack(side='left', padx=5)

        self.stop_button = ttk.Button(
            control_frame,
            text='停止',
            command=self._stop_analysis,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=5)

        ttk.Button(
            control_frame,
            text='設定',
            command=self._open_settings
        ).pack(side='left', padx=5)

        # ステータス表示
        self.status_label = ttk.Label(control_frame, text='停止中', foreground='gray')
        self.status_label.pack(side='right', padx=10)

        # メインコンテンツエリア
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 表示モードに応じてウィジェットを作成
        self._create_display_widgets()

    def _create_display_widgets(self):
        """表示モードに応じてウィジェットを作成"""
        # 既存のウィジェットをクリア
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        display_mode = self.config.get('display', 'mode', 'detailed')

        if display_mode == 'simple':
            self._create_simple_display()
        elif display_mode == 'detailed':
            self._create_detailed_display()
        elif display_mode == 'professional':
            self._create_professional_display()

    def _create_simple_display(self):
        """シンプル表示を作成"""
        # 大きなピッチ表示
        pitch_frame = ttk.LabelFrame(self.content_frame, text='現在の音程', padding=20)
        pitch_frame.pack(fill='both', expand=True)

        self.user_pitch_label = ttk.Label(
            pitch_frame,
            text='---',
            font=('Arial', 72, 'bold')
        )
        self.user_pitch_label.pack(pady=20)

        self.cents_diff_label = ttk.Label(
            pitch_frame,
            text='0 セント',
            font=('Arial', 36)
        )
        self.cents_diff_label.pack(pady=10)

        self.accuracy_label = ttk.Label(
            pitch_frame,
            text='',
            font=('Arial', 24)
        )
        self.accuracy_label.pack(pady=10)

    def _create_detailed_display(self):
        """詳細表示を作成"""
        # 上部: ピッチ情報
        info_frame = ttk.Frame(self.content_frame)
        info_frame.pack(fill='x', pady=5)

        # 原曲
        original_frame = ttk.LabelFrame(info_frame, text='原曲', padding=10)
        original_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.original_pitch_label = ttk.Label(
            original_frame,
            text='---',
            font=('Arial', 36, 'bold')
        )
        self.original_pitch_label.pack()

        # あなた
        user_frame = ttk.LabelFrame(info_frame, text='あなた', padding=10)
        user_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.user_pitch_label = ttk.Label(
            user_frame,
            text='---',
            font=('Arial', 36, 'bold')
        )
        self.user_pitch_label.pack()

        # 評価
        eval_frame = ttk.LabelFrame(info_frame, text='評価', padding=10)
        eval_frame.pack(side='left', fill='both', expand=True, padx=5)

        self.accuracy_label = ttk.Label(
            eval_frame,
            text='---',
            font=('Arial', 24)
        )
        self.accuracy_label.pack()

        # セント差表示
        cents_frame = ttk.LabelFrame(self.content_frame, text='音程差', padding=10)
        cents_frame.pack(fill='x', pady=5)

        self.cents_diff_label = ttk.Label(
            cents_frame,
            text='0 セント',
            font=('Arial', 28)
        )
        self.cents_diff_label.pack()

        # グラフエリア
        if self.config.get('display', 'show_pitch_graph', True):
            graph_frame = ttk.LabelFrame(self.content_frame, text='ピッチ推移', padding=10)
            graph_frame.pack(fill='both', expand=True, pady=5)

            self.figure = Figure(figsize=(8, 3), dpi=100)
            self.ax = self.figure.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
            self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # 統計情報
        if self.config.get('display', 'show_statistics', True):
            stats_frame = ttk.LabelFrame(self.content_frame, text='統計', padding=10)
            stats_frame.pack(fill='x', pady=5)

            self.stats_label = ttk.Label(stats_frame, text='統計情報はここに表示されます')
            self.stats_label.pack()

    def _create_professional_display(self):
        """プロフェッショナル表示を作成"""
        # 左右2列レイアウト
        left_frame = ttk.Frame(self.content_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=5)

        right_frame = ttk.Frame(self.content_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5)

        # 左側: グラフとゲージ
        graph_frame = ttk.LabelFrame(left_frame, text='リアルタイム分析', padding=10)
        graph_frame.pack(fill='both', expand=True, pady=5)

        self.figure = Figure(figsize=(6, 5), dpi=100)

        # ピッチグラフ
        self.ax1 = self.figure.add_subplot(211)
        self.ax1.set_title('ピッチ推移')
        self.ax1.set_ylabel('周波数 (Hz)')

        # セント差グラフ
        self.ax2 = self.figure.add_subplot(212)
        self.ax2.set_title('音程差')
        self.ax2.set_ylabel('セント')
        self.ax2.set_xlabel('時間')

        self.canvas = FigureCanvasTkAgg(self.figure, graph_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # 右側: 情報パネル
        # 現在のピッチ
        pitch_frame = ttk.LabelFrame(right_frame, text='現在の音程', padding=10)
        pitch_frame.pack(fill='x', pady=5)

        ttk.Label(pitch_frame, text='原曲:').grid(row=0, column=0, sticky='w', padx=5)
        self.original_pitch_label = ttk.Label(pitch_frame, text='---', font=('Arial', 18, 'bold'))
        self.original_pitch_label.grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(pitch_frame, text='あなた:').grid(row=1, column=0, sticky='w', padx=5)
        self.user_pitch_label = ttk.Label(pitch_frame, text='---', font=('Arial', 18, 'bold'))
        self.user_pitch_label.grid(row=1, column=1, sticky='w', padx=5)

        ttk.Label(pitch_frame, text='差分:').grid(row=2, column=0, sticky='w', padx=5)
        self.cents_diff_label = ttk.Label(pitch_frame, text='0 セント', font=('Arial', 16))
        self.cents_diff_label.grid(row=2, column=1, sticky='w', padx=5)

        # 評価
        eval_frame = ttk.LabelFrame(right_frame, text='評価', padding=10)
        eval_frame.pack(fill='x', pady=5)

        self.accuracy_label = ttk.Label(eval_frame, text='---', font=('Arial', 20))
        self.accuracy_label.pack()

        # 統計情報
        stats_frame = ttk.LabelFrame(right_frame, text='統計情報', padding=10)
        stats_frame.pack(fill='both', expand=True, pady=5)

        self.stats_text = tk.Text(stats_frame, height=10, width=30)
        self.stats_text.pack(fill='both', expand=True)

        # 警告表示
        self.warning_label = ttk.Label(
            right_frame,
            text='',
            font=('Arial', 14, 'bold'),
            foreground='red'
        )
        self.warning_label.pack(fill='x', pady=5)

    def _apply_theme(self):
        """テーマを適用"""
        theme = self.config.get('display', 'theme', 'dark')

        if theme == 'dark':
            # ダークテーマ（tkinterのデフォルトスタイルを使用）
            style = ttk.Style()
            style.theme_use('default')
        else:
            # ライトテーマ
            style = ttk.Style()
            style.theme_use('clam')

    def _start_analysis(self):
        """分析を開始"""
        if self.is_running:
            return

        try:
            # 設定から値を取得
            sample_rate = self.config.get('audio', 'sample_rate', 44100)
            mic_device = self.config.get('audio', 'mic_device')
            system_device = self.config.get('audio', 'system_device')
            use_system_audio = self.config.get('audio', 'use_system_audio', False)
            confidence_threshold = self.config.get('analysis', 'confidence_threshold', 0.8)
            history_size = self.config.get('analysis', 'history_size', 100)

            # オーディオキャプチャを初期化
            self.mic_capture = AudioCapture(
                sample_rate=sample_rate,
                channels=1,
                device=mic_device
            )

            if use_system_audio:
                if system_device is not None:
                    self.system_capture = AudioCapture(
                        sample_rate=sample_rate,
                        channels=2,
                        device=system_device
                    )
                else:
                    self.system_capture = SystemAudioCapture(sample_rate=sample_rate)

            # ピッチ検出器を初期化
            self.pitch_detector_mic = PitchDetector(
                sample_rate=sample_rate,
                confidence_threshold=confidence_threshold
            )

            if use_system_audio:
                self.pitch_detector_system = PitchDetector(
                    sample_rate=sample_rate,
                    confidence_threshold=confidence_threshold
                )

            # アナライザーを初期化
            self.analyzer = PitchAnalyzer(history_size=history_size)

            # キャプチャを開始
            self.mic_capture.start()
            if self.system_capture:
                self.system_capture.start()

            # 状態を更新
            self.is_running = True
            self.start_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.status_label.config(text='分析中', foreground='green')

            # 分析スレッドを開始
            self.analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()

            # UI更新を開始
            self._update_display()

        except Exception as e:
            messagebox.showerror('エラー', f'分析の開始に失敗しました:\n{e}')
            self._stop_analysis()

    def _stop_analysis(self):
        """分析を停止"""
        self.is_running = False

        if self.mic_capture:
            self.mic_capture.stop()
        if self.system_capture:
            self.system_capture.stop()

        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.status_label.config(text='停止中', foreground='gray')

    def _analysis_loop(self):
        """分析ループ（バックグラウンドスレッド）"""
        start_time = time.time()

        while self.is_running:
            try:
                current_time = time.time() - start_time

                # マイク入力からピッチを検出
                user_pitch = None
                mic_data = self.mic_capture.get_audio_data()
                if mic_data is not None:
                    user_pitch, _ = self.pitch_detector_mic.detect_pitch(mic_data)

                # システムオーディオからピッチを検出
                original_pitch = None
                if self.system_capture and self.pitch_detector_system:
                    system_data = self.system_capture.get_audio_data()
                    if system_data is not None:
                        original_pitch, _ = self.pitch_detector_system.detect_pitch(system_data)

                # 分析データを追加
                self.analyzer.add_pitch_data(original_pitch, user_pitch, current_time)

                time.sleep(0.05)

            except Exception as e:
                print(f"分析ループエラー: {e}")

    def _update_display(self):
        """表示を更新"""
        if not self.is_running:
            return

        try:
            if self.analyzer:
                # 最新のピッチを取得
                original_history, user_history, timestamp_history = \
                    self.analyzer.get_pitch_history()

                original_pitch = original_history[-1] if original_history else None
                user_pitch = user_history[-1] if user_history else None

                # 評価を取得
                evaluation = self.analyzer.get_current_evaluation(original_pitch, user_pitch)
                statistics = self.analyzer.get_statistics()

                # 表示を更新
                display_mode = self.config.get('display', 'mode', 'detailed')

                if display_mode == 'simple':
                    self._update_simple_display(evaluation, statistics)
                elif display_mode == 'detailed':
                    self._update_detailed_display(evaluation, statistics, original_history, user_history, timestamp_history)
                elif display_mode == 'professional':
                    self._update_professional_display(evaluation, statistics, original_history, user_history, timestamp_history)

        except Exception as e:
            print(f"表示更新エラー: {e}")

        # 次の更新をスケジュール
        update_interval = self.config.get('display', 'update_interval', 100)
        self.root.after(update_interval, self._update_display)

    def _update_simple_display(self, evaluation, statistics):
        """シンプル表示を更新"""
        user_note = evaluation.get('user_note', '---')
        self.user_pitch_label.config(text=user_note)

        cents_diff = evaluation.get('cents_diff', 0)
        if cents_diff is not None:
            self.cents_diff_label.config(text=f'{cents_diff:+.1f} セント')
        else:
            self.cents_diff_label.config(text='--- セント')

        accuracy = evaluation.get('accuracy_level', '')
        self.accuracy_label.config(text=accuracy)

        # 色を変更
        if accuracy == '完璧':
            self.accuracy_label.config(foreground='green')
        elif accuracy == '良好':
            self.accuracy_label.config(foreground='blue')
        elif accuracy == 'やや不正確':
            self.accuracy_label.config(foreground='orange')
        else:
            self.accuracy_label.config(foreground='red')

    def _update_detailed_display(self, evaluation, statistics, original_history, user_history, timestamp_history):
        """詳細表示を更新"""
        # ピッチ表示
        self.original_pitch_label.config(text=evaluation.get('original_note', '---'))
        self.user_pitch_label.config(text=evaluation.get('user_note', '---'))

        cents_diff = evaluation.get('cents_diff', 0)
        if cents_diff is not None:
            self.cents_diff_label.config(text=f'{cents_diff:+.1f} セント')
        else:
            self.cents_diff_label.config(text='--- セント')

        accuracy = evaluation.get('accuracy_level', '---')
        self.accuracy_label.config(text=accuracy)

        # グラフ更新
        if hasattr(self, 'ax') and hasattr(self, 'canvas'):
            self.ax.clear()

            if original_history and user_history and timestamp_history:
                # Noneを除外
                valid_original = [p if p else np.nan for p in original_history]
                valid_user = [p if p else np.nan for p in user_history]

                self.ax.plot(timestamp_history, valid_original, 'b-', label='原曲', linewidth=2)
                self.ax.plot(timestamp_history, valid_user, 'r-', label='あなた', linewidth=2)
                self.ax.set_xlabel('時間 (秒)')
                self.ax.set_ylabel('周波数 (Hz)')
                self.ax.legend()
                self.ax.grid(True, alpha=0.3)

            self.canvas.draw()

        # 統計情報
        if hasattr(self, 'stats_label'):
            stats_text = (
                f"総サンプル数: {statistics['total_samples']}  "
                f"正確率: {statistics['accuracy_rate']:.1f}%  "
                f"オクターブズレ率: {statistics['octave_error_rate']:.1f}%"
            )
            self.stats_label.config(text=stats_text)

    def _update_professional_display(self, evaluation, statistics, original_history, user_history, timestamp_history):
        """プロフェッショナル表示を更新"""
        # ピッチ表示
        self.original_pitch_label.config(text=evaluation.get('original_note', '---'))
        self.user_pitch_label.config(text=evaluation.get('user_note', '---'))

        cents_diff = evaluation.get('cents_diff', 0)
        if cents_diff is not None:
            self.cents_diff_label.config(text=f'{cents_diff:+.1f} セント')
        else:
            self.cents_diff_label.config(text='--- セント')

        accuracy = evaluation.get('accuracy_level', '---')
        self.accuracy_label.config(text=accuracy)

        # 2つのグラフを更新
        if hasattr(self, 'ax1') and hasattr(self, 'ax2'):
            self.ax1.clear()
            self.ax2.clear()

            if original_history and user_history and timestamp_history:
                # ピッチグラフ
                valid_original = [p if p else np.nan for p in original_history]
                valid_user = [p if p else np.nan for p in user_history]

                self.ax1.plot(timestamp_history, valid_original, 'b-', label='原曲', linewidth=2)
                self.ax1.plot(timestamp_history, valid_user, 'r-', label='あなた', linewidth=2)
                self.ax1.set_ylabel('周波数 (Hz)')
                self.ax1.legend(loc='upper right')
                self.ax1.grid(True, alpha=0.3)

                # セント差グラフ
                cents_diffs = []
                for orig, user in zip(valid_original, valid_user):
                    if not np.isnan(orig) and not np.isnan(user):
                        cents = 1200 * np.log2(user / orig)
                        cents_diffs.append(cents)
                    else:
                        cents_diffs.append(np.nan)

                self.ax2.plot(timestamp_history, cents_diffs, 'g-', linewidth=2)
                self.ax2.axhline(y=0, color='white', linestyle='-', alpha=0.5)
                self.ax2.axhline(y=50, color='yellow', linestyle='--', alpha=0.5)
                self.ax2.axhline(y=-50, color='yellow', linestyle='--', alpha=0.5)
                self.ax2.set_ylabel('セント')
                self.ax2.set_xlabel('時間 (秒)')
                self.ax2.set_ylim(-300, 300)
                self.ax2.grid(True, alpha=0.3)

            self.canvas.draw()

        # 統計情報テキスト
        if hasattr(self, 'stats_text'):
            self.stats_text.delete('1.0', tk.END)
            stats_info = f"""総サンプル数: {statistics['total_samples']}
正確サンプル数: {statistics['accurate_samples']}
正確率: {statistics['accuracy_rate']:.1f}%
オクターブズレ: {statistics['octave_error_samples']}
オクターブズレ率: {statistics['octave_error_rate']:.1f}%
"""
            self.stats_text.insert('1.0', stats_info)

        # オクターブズレ警告
        if hasattr(self, 'warning_label'):
            octave_warning_threshold = self.config.get('analysis', 'octave_warning_threshold', 5)
            if statistics['octave_error_duration'] >= octave_warning_threshold:
                octave_diff = statistics['current_octave_error']
                direction = '高い' if octave_diff > 0 else '低い'
                self.warning_label.config(
                    text=f'⚠ {abs(octave_diff)}オクターブ{direction}です！'
                )
            else:
                self.warning_label.config(text='')

    def _change_display_mode(self, mode):
        """表示モードを変更"""
        self.config.set('display', 'mode', mode)
        self._create_display_widgets()

    def _open_settings(self):
        """設定ウィンドウを開く"""
        SettingsWindow(self.root, self.config, on_save_callback=self._on_settings_saved)

    def _on_settings_saved(self):
        """設定が保存された時のコールback"""
        # 表示モードが変更された可能性があるので再作成
        self._create_display_widgets()
        self._apply_theme()

    def _show_help(self):
        """ヘルプを表示"""
        help_text = """
カラオケピッチアナライザー - 使い方

1. メニューから「設定」を開いてオーディオデバイスを選択
2. 「開始」ボタンをクリックして分析を開始
3. マイクに向かって歌うと、リアルタイムで音程が分析されます

表示モード:
- シンプル: 現在の音程のみを大きく表示
- 詳細: ピッチグラフと統計情報を表示
- プロフェッショナル: 2つのグラフと詳細な統計を表示

評価基準:
- 完璧: ±20セント以内
- 良好: ±50セント以内
- やや不正確: ±100セント以内
- 不正確: それ以上
        """
        messagebox.showinfo('使い方', help_text)

    def _show_about(self):
        """バージョン情報を表示"""
        about_text = """
カラオケピッチアナライザー
Version 1.0.0

リアルタイムで歌唱の音程精度を評価するソフトウェア

© 2024
        """
        messagebox.showinfo('バージョン情報', about_text)

    def _on_closing(self):
        """ウィンドウを閉じる時の処理"""
        if self.is_running:
            self._stop_analysis()
        self.root.destroy()

    def run(self):
        """アプリケーションを実行"""
        self.root.mainloop()


def main():
    """メイン関数"""
    app = KaraokePitchAnalyzerGUI()
    app.run()


if __name__ == '__main__':
    main()
