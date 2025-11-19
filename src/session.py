"""
セッション管理モジュール
録音、リプレイ、データエクスポート機能
"""

import json
import csv
import wave
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import deque


class SessionRecorder:
    """セッション録音・管理クラス"""

    def __init__(self):
        self.is_recording = False
        self.session_data = {
            'start_time': None,
            'end_time': None,
            'pitch_data': [],
            'statistics': {},
            'settings': {}
        }
        self.audio_buffer = {
            'mic': deque(maxlen=44100 * 60 * 5),  # 最大5分
            'system': deque(maxlen=44100 * 60 * 5)
        }

    def start_recording(self, settings: Dict = None):
        """録音を開始"""
        self.is_recording = True
        self.session_data = {
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'pitch_data': [],
            'statistics': {},
            'settings': settings or {}
        }
        self.audio_buffer['mic'].clear()
        self.audio_buffer['system'].clear()

    def stop_recording(self):
        """録音を停止"""
        self.is_recording = False
        self.session_data['end_time'] = datetime.now().isoformat()

    def add_pitch_data(
        self,
        timestamp: float,
        original_pitch: Optional[float],
        user_pitch: Optional[float],
        cents_diff: Optional[float],
        evaluation: Dict
    ):
        """ピッチデータを追加"""
        if not self.is_recording:
            return

        self.session_data['pitch_data'].append({
            'timestamp': timestamp,
            'original_pitch': original_pitch,
            'user_pitch': user_pitch,
            'cents_diff': cents_diff,
            'original_note': evaluation.get('original_note'),
            'user_note': evaluation.get('user_note'),
            'accuracy_level': evaluation.get('accuracy_level'),
            'is_accurate': evaluation.get('is_accurate'),
            'is_octave_error': evaluation.get('is_octave_error'),
            'octave_diff': evaluation.get('octave_diff')
        })

    def add_audio_data(self, mic_data: np.ndarray = None, system_data: np.ndarray = None):
        """オーディオデータを追加"""
        if not self.is_recording:
            return

        if mic_data is not None:
            self.audio_buffer['mic'].extend(mic_data)

        if system_data is not None:
            self.audio_buffer['system'].extend(system_data)

    def set_statistics(self, statistics: Dict):
        """統計情報を設定"""
        self.session_data['statistics'] = statistics

    def save_session(self, filepath: str):
        """セッションをJSONファイルに保存"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)

        print(f"セッションを保存しました: {filepath}")

    def load_session(self, filepath: str) -> Dict:
        """セッションをJSONファイルから読み込み"""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.session_data = json.load(f)

        print(f"セッションを読み込みました: {filepath}")
        return self.session_data

    def export_to_csv(self, filepath: str):
        """ピッチデータをCSVにエクスポート"""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if not self.session_data['pitch_data']:
                print("エクスポートするデータがありません")
                return

            fieldnames = self.session_data['pitch_data'][0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(self.session_data['pitch_data'])

        print(f"CSVにエクスポートしました: {filepath}")

    def save_audio(self, filepath: str, channel: str = 'mic', sample_rate: int = 44100):
        """オーディオをWAVファイルに保存"""
        if channel not in self.audio_buffer:
            print(f"無効なチャンネル: {channel}")
            return

        if not self.audio_buffer[channel]:
            print("保存するオーディオデータがありません")
            return

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # dequeからnumpy配列に変換
        audio_data = np.array(list(self.audio_buffer[channel]), dtype=np.float32)

        # 正規化
        audio_data = np.int16(audio_data * 32767)

        # WAVファイルに書き込み
        with wave.open(str(filepath), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())

        print(f"オーディオを保存しました: {filepath}")

    def get_summary(self) -> Dict:
        """セッションのサマリーを取得"""
        if not self.session_data['pitch_data']:
            return {
                'duration': 0,
                'total_samples': 0,
                'average_cents_diff': 0,
                'accuracy_rate': 0
            }

        pitch_data = self.session_data['pitch_data']

        # 所要時間
        start_time = pitch_data[0]['timestamp']
        end_time = pitch_data[-1]['timestamp']
        duration = end_time - start_time

        # 平均セント差
        cents_diffs = [d['cents_diff'] for d in pitch_data if d['cents_diff'] is not None]
        avg_cents = np.mean(np.abs(cents_diffs)) if cents_diffs else 0

        # 正確率
        accurate_count = sum(1 for d in pitch_data if d.get('is_accurate', False))
        accuracy_rate = (accurate_count / len(pitch_data) * 100) if pitch_data else 0

        return {
            'duration': duration,
            'total_samples': len(pitch_data),
            'average_cents_diff': avg_cents,
            'accuracy_rate': accuracy_rate,
            'statistics': self.session_data.get('statistics', {})
        }


class TimingAdjuster:
    """タイミング調整クラス"""

    def __init__(self, offset_ms: int = 0):
        """
        初期化

        Args:
            offset_ms: オフセット（ミリ秒）
                       正の値: システムオーディオを遅らせる
                       負の値: マイク入力を遅らせる
        """
        self.offset_ms = offset_ms
        self.offset_samples = 0
        self.sample_rate = 44100

        self.mic_buffer = deque()
        self.system_buffer = deque()

        self.update_offset(offset_ms)

    def update_offset(self, offset_ms: int):
        """オフセットを更新"""
        self.offset_ms = offset_ms
        self.offset_samples = int(abs(offset_ms) * self.sample_rate / 1000)

        # バッファをクリア
        self.mic_buffer.clear()
        self.system_buffer.clear()

    def set_sample_rate(self, sample_rate: int):
        """サンプリングレートを設定"""
        self.sample_rate = sample_rate
        self.update_offset(self.offset_ms)

    def adjust(
        self,
        mic_data: Optional[np.ndarray],
        system_data: Optional[np.ndarray]
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        タイミング調整を適用

        Args:
            mic_data: マイクデータ
            system_data: システムオーディオデータ

        Returns:
            (調整後マイクデータ, 調整後システムデータ)
        """
        if self.offset_ms == 0:
            return mic_data, system_data

        if self.offset_ms > 0:
            # システムオーディオを遅らせる
            if system_data is not None:
                self.system_buffer.extend(system_data)

            adjusted_mic = mic_data
            adjusted_system = None

            if len(self.system_buffer) >= self.offset_samples:
                # バッファから取り出し
                output_length = len(system_data) if system_data is not None else 0
                if output_length > 0:
                    adjusted_system = np.array([
                        self.system_buffer.popleft()
                        for _ in range(min(output_length, len(self.system_buffer)))
                    ])

            return adjusted_mic, adjusted_system

        else:
            # マイク入力を遅らせる
            if mic_data is not None:
                self.mic_buffer.extend(mic_data)

            adjusted_mic = None
            adjusted_system = system_data

            if len(self.mic_buffer) >= self.offset_samples:
                # バッファから取り出し
                output_length = len(mic_data) if mic_data is not None else 0
                if output_length > 0:
                    adjusted_mic = np.array([
                        self.mic_buffer.popleft()
                        for _ in range(min(output_length, len(self.mic_buffer)))
                    ])

            return adjusted_mic, adjusted_system


class KeyChanger:
    """キー変更（ピッチシフト）クラス"""

    def __init__(self, semitone_shift: int = 0):
        """
        初期化

        Args:
            semitone_shift: 半音単位のシフト量（±12）
        """
        self.semitone_shift = semitone_shift
        self.pitch_ratio = 1.0
        self.update_shift(semitone_shift)

    def update_shift(self, semitone_shift: int):
        """シフト量を更新"""
        self.semitone_shift = max(-12, min(12, semitone_shift))
        # 半音 = 2^(1/12)
        self.pitch_ratio = 2.0 ** (self.semitone_shift / 12.0)

    def shift_pitch(self, pitch: Optional[float]) -> Optional[float]:
        """
        ピッチをシフト

        Args:
            pitch: 元のピッチ (Hz)

        Returns:
            シフトされたピッチ (Hz)
        """
        if pitch is None or pitch <= 0:
            return pitch

        return pitch * self.pitch_ratio

    def get_shift_description(self) -> str:
        """シフト量の説明を取得"""
        if self.semitone_shift == 0:
            return "キー変更なし"
        elif self.semitone_shift > 0:
            return f"+{self.semitone_shift} 半音高く"
        else:
            return f"{self.semitone_shift} 半音低く"
