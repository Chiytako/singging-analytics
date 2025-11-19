"""
UIモジュール
リアルタイムでピッチを可視化・表示する
"""

import matplotlib
matplotlib.use('Agg')  # バックエンドを設定（GUIなし）
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.figure import Figure
from io import BytesIO
import base64
import numpy as np
from typing import Optional, List, Tuple


class PitchVisualizer:
    """ピッチ可視化クラス"""

    def __init__(self, history_size: int = 100):
        """
        初期化

        Args:
            history_size: 表示する履歴のサイズ
        """
        self.history_size = history_size
        plt.style.use('seaborn-v0_8-darkgrid')

    def create_realtime_plot(
        self,
        original_pitches: List[Optional[float]],
        user_pitches: List[Optional[float]],
        timestamps: List[float],
        current_evaluation: dict
    ) -> str:
        """
        リアルタイムピッチプロットを作成

        Args:
            original_pitches: 原曲ピッチの履歴
            user_pitches: ユーザーピッチの履歴
            timestamps: タイムスタンプの履歴
            current_evaluation: 現在の評価情報

        Returns:
            Base64エンコードされた画像データ
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor('#1e1e1e')

        # データの準備
        valid_original = [p if p else np.nan for p in original_pitches[-self.history_size:]]
        valid_user = [p if p else np.nan for p in user_pitches[-self.history_size:]]
        valid_timestamps = timestamps[-self.history_size:]

        if not valid_timestamps:
            valid_timestamps = [0]

        # 上段: ピッチの時系列プロット
        ax1.set_facecolor('#2d2d2d')
        ax1.set_title('ピッチ推移', color='white', fontsize=14, pad=10)
        ax1.set_xlabel('時間 (秒)', color='white')
        ax1.set_ylabel('周波数 (Hz)', color='white')

        # 原曲とユーザーのピッチをプロット
        ax1.plot(valid_timestamps, valid_original, 'b-', linewidth=2, label='原曲', alpha=0.8)
        ax1.plot(valid_timestamps, valid_user, 'r-', linewidth=2, label='あなた', alpha=0.8)

        ax1.legend(loc='upper right', facecolor='#3d3d3d', edgecolor='white', labelcolor='white')
        ax1.grid(True, alpha=0.3, color='gray')
        ax1.tick_params(colors='white')

        # 下段: セント差の表示
        ax2.set_facecolor('#2d2d2d')
        ax2.set_title('音程差 (セント)', color='white', fontsize=14, pad=10)
        ax2.set_xlabel('時間 (秒)', color='white')
        ax2.set_ylabel('セント差', color='white')

        # セント差を計算
        cents_diff = []
        for orig, user in zip(valid_original, valid_user):
            if orig and user and not np.isnan(orig) and not np.isnan(user):
                cents = 1200 * np.log2(user / orig)
                cents_diff.append(cents)
            else:
                cents_diff.append(np.nan)

        # セント差をプロット
        ax2.plot(valid_timestamps, cents_diff, 'g-', linewidth=2, alpha=0.8)

        # 許容範囲を表示（±50セント）
        ax2.axhline(y=50, color='yellow', linestyle='--', alpha=0.5, label='許容範囲')
        ax2.axhline(y=-50, color='yellow', linestyle='--', alpha=0.5)
        ax2.axhline(y=0, color='white', linestyle='-', alpha=0.3)

        ax2.legend(loc='upper right', facecolor='#3d3d3d', edgecolor='white', labelcolor='white')
        ax2.grid(True, alpha=0.3, color='gray')
        ax2.tick_params(colors='white')
        ax2.set_ylim(-300, 300)

        plt.tight_layout()

        # 画像をBase64エンコード
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor='#1e1e1e')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return img_base64

    def create_gauge_plot(
        self,
        cents_diff: Optional[float],
        octave_diff: int
    ) -> str:
        """
        現在のセント差をゲージ表示

        Args:
            cents_diff: セント差
            octave_diff: オクターブ差

        Returns:
            Base64エンコードされた画像データ
        """
        fig, ax = plt.subplots(figsize=(8, 3))
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#2d2d2d')

        # ゲージの範囲
        gauge_range = 200  # ±200セント

        # ゲージの描画
        ax.set_xlim(-gauge_range, gauge_range)
        ax.set_ylim(0, 2)

        # 背景領域
        # 不正確（赤）
        rect1 = patches.Rectangle((-gauge_range, 0), gauge_range - 100, 2,
                                  facecolor='#ff4444', alpha=0.3)
        rect2 = patches.Rectangle((100, 0), gauge_range - 100, 2,
                                  facecolor='#ff4444', alpha=0.3)
        # やや不正確（黄）
        rect3 = patches.Rectangle((-100, 0), 50, 2,
                                  facecolor='#ffaa00', alpha=0.3)
        rect4 = patches.Rectangle((50, 0), 50, 2,
                                  facecolor='#ffaa00', alpha=0.3)
        # 良好（緑）
        rect5 = patches.Rectangle((-50, 0), 100, 2,
                                  facecolor='#44ff44', alpha=0.3)

        ax.add_patch(rect1)
        ax.add_patch(rect2)
        ax.add_patch(rect3)
        ax.add_patch(rect4)
        ax.add_patch(rect5)

        # 中央線
        ax.axvline(x=0, color='white', linestyle='-', linewidth=2)

        # 現在位置のマーカー
        if cents_diff is not None:
            marker_x = max(-gauge_range, min(gauge_range, cents_diff))
            ax.plot(marker_x, 1, 'ro', markersize=20, markeredgecolor='white',
                   markeredgewidth=2, zorder=5)

            # セント差の数値表示
            ax.text(0, 1.5, f'{cents_diff:+.1f} セント',
                   ha='center', va='center', color='white',
                   fontsize=16, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='#3d3d3d', alpha=0.8))

        # オクターブズレ警告
        if octave_diff != 0:
            warning_text = f'⚠ {abs(octave_diff)}オクターブ{"高い" if octave_diff > 0 else "低い"}!'
            ax.text(0, 0.5, warning_text,
                   ha='center', va='center', color='#ff4444',
                   fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='#3d3d3d', alpha=0.9))

        ax.set_xticks([-200, -100, -50, 0, 50, 100, 200])
        ax.set_yticks([])
        ax.tick_params(colors='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('white')

        plt.tight_layout()

        # 画像をBase64エンコード
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor='#1e1e1e')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return img_base64


class ConsoleDisplay:
    """コンソール表示クラス"""

    @staticmethod
    def clear_screen():
        """画面をクリア（Unixのみ）"""
        print('\033[2J\033[H', end='')

    @staticmethod
    def display_pitch_info(
        original_pitch: Optional[float],
        user_pitch: Optional[float],
        evaluation: dict,
        statistics: dict
    ):
        """
        ピッチ情報をコンソールに表示

        Args:
            original_pitch: 原曲のピッチ
            user_pitch: ユーザーのピッチ
            evaluation: 評価情報
            statistics: 統計情報
        """
        ConsoleDisplay.clear_screen()

        print("=" * 80)
        print("カラオケピッチアナライザー")
        print("=" * 80)
        print()

        # 現在のピッチ情報
        print("【現在の音程】")
        print(f"  原曲:    {evaluation['original_note']:>5}  ({original_pitch:.1f} Hz)" if original_pitch else "  原曲:    ---")
        print(f"  あなた:  {evaluation['user_note']:>5}  ({user_pitch:.1f} Hz)" if user_pitch else "  あなた:  ---")
        print()

        # セント差
        if evaluation['cents_diff'] is not None:
            cents_diff = evaluation['cents_diff']
            print(f"【音程差】 {cents_diff:+.1f} セント")

            # ビジュアルバー
            bar_width = 40
            center = bar_width // 2
            offset = int((cents_diff / 200) * center)
            offset = max(-center, min(center, offset))
            bar_pos = center + offset

            bar = ['-'] * bar_width
            bar[center] = '|'
            bar[bar_pos] = '●'
            print("  " + ''.join(bar))
            print(f"  低い {'←' + ' ' * (bar_width - 6) + '→'} 高い")
            print()

        # 正確性
        print(f"【評価】 {evaluation['accuracy_level']}")
        print()

        # オクターブズレ警告
        if evaluation['is_octave_error']:
            octave_diff = evaluation['octave_diff']
            direction = "高い" if octave_diff > 0 else "低い"
            print(f"⚠⚠⚠  警告: {abs(octave_diff)}オクターブ{direction}です!  ⚠⚠⚠")
            print()

        # 統計情報
        print("【統計】")
        print(f"  総サンプル数: {statistics['total_samples']}")
        print(f"  正確率:       {statistics['accuracy_rate']:.1f}%")
        print(f"  オクターブズレ率: {statistics['octave_error_rate']:.1f}%")
        print()

        print("=" * 80)
        print("Ctrl+C で終了")
        print("=" * 80)
