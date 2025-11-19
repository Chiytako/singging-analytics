"""
オーディオユーティリティ
音量計算、メーター表示など
"""

import numpy as np
from typing import Optional


class AudioLevelMeter:
    """オーディオレベルメータークラス"""

    def __init__(self, smoothing: float = 0.3):
        """
        初期化

        Args:
            smoothing: スムージング係数（0-1、大きいほど滑らか）
        """
        self.smoothing = smoothing
        self.current_level = 0.0
        self.peak_level = 0.0
        self.peak_hold_counter = 0
        self.peak_hold_time = 30  # フレーム数

    def calculate_rms(self, audio_data: np.ndarray) -> float:
        """
        RMS（Root Mean Square）レベルを計算

        Args:
            audio_data: オーディオデータ

        Returns:
            RMSレベル（0.0-1.0）
        """
        if audio_data is None or len(audio_data) == 0:
            return 0.0

        # RMS計算
        rms = np.sqrt(np.mean(audio_data ** 2))

        return float(rms)

    def calculate_db(self, audio_data: np.ndarray, reference: float = 1.0) -> float:
        """
        dBレベルを計算

        Args:
            audio_data: オーディオデータ
            reference: 基準レベル

        Returns:
            dBレベル
        """
        rms = self.calculate_rms(audio_data)

        if rms < 1e-10:  # ほぼ無音
            return -100.0

        db = 20 * np.log10(rms / reference)
        return float(db)

    def update(self, audio_data: Optional[np.ndarray]) -> float:
        """
        レベルメーターを更新

        Args:
            audio_data: オーディオデータ

        Returns:
            現在のレベル（0.0-1.0）
        """
        if audio_data is None or len(audio_data) == 0:
            # 減衰
            self.current_level *= (1.0 - self.smoothing)
            return self.current_level

        # 新しいレベルを計算
        new_level = self.calculate_rms(audio_data)

        # スムージング
        self.current_level = (
            self.smoothing * self.current_level +
            (1.0 - self.smoothing) * new_level
        )

        # ピークホールド
        if new_level > self.peak_level:
            self.peak_level = new_level
            self.peak_hold_counter = self.peak_hold_time
        else:
            self.peak_hold_counter -= 1
            if self.peak_hold_counter <= 0:
                self.peak_level = self.current_level

        return self.current_level

    def get_level(self) -> float:
        """現在のレベルを取得（0.0-1.0）"""
        return self.current_level

    def get_level_db(self) -> float:
        """現在のレベルをdBで取得"""
        if self.current_level < 1e-10:
            return -100.0
        return 20 * np.log10(self.current_level)

    def get_peak(self) -> float:
        """ピークレベルを取得（0.0-1.0）"""
        return self.peak_level

    def reset(self):
        """メーターをリセット"""
        self.current_level = 0.0
        self.peak_level = 0.0
        self.peak_hold_counter = 0


class VolumeMonitor:
    """音量モニタークラス"""

    def __init__(self):
        self.mic_meter = AudioLevelMeter()
        self.system_meter = AudioLevelMeter()

        # 閾値
        self.silence_threshold = 0.01  # これ以下は無音とみなす
        self.clip_threshold = 0.95    # これ以上はクリッピング

    def update(
        self,
        mic_data: Optional[np.ndarray],
        system_data: Optional[np.ndarray]
    ):
        """音量メーターを更新"""
        self.mic_meter.update(mic_data)
        self.system_meter.update(system_data)

    def get_mic_level(self) -> float:
        """マイクレベルを取得（0.0-1.0）"""
        return self.mic_meter.get_level()

    def get_system_level(self) -> float:
        """システムオーディオレベルを取得（0.0-1.0）"""
        return self.system_meter.get_level()

    def get_mic_level_db(self) -> float:
        """マイクレベルをdBで取得"""
        return self.mic_meter.get_level_db()

    def get_system_level_db(self) -> float:
        """システムオーディオレベルをdBで取得"""
        return self.system_meter.get_level_db()

    def is_mic_silent(self) -> bool:
        """マイクが無音かどうか"""
        return self.mic_meter.get_level() < self.silence_threshold

    def is_mic_clipping(self) -> bool:
        """マイクがクリッピングしているかどうか"""
        return self.mic_meter.get_peak() > self.clip_threshold

    def is_system_silent(self) -> bool:
        """システムオーディオが無音かどうか"""
        return self.system_meter.get_level() < self.silence_threshold

    def get_status(self) -> dict:
        """ステータスを取得"""
        return {
            'mic': {
                'level': self.get_mic_level(),
                'level_db': self.get_mic_level_db(),
                'peak': self.mic_meter.get_peak(),
                'is_silent': self.is_mic_silent(),
                'is_clipping': self.is_mic_clipping()
            },
            'system': {
                'level': self.get_system_level(),
                'level_db': self.get_system_level_db(),
                'peak': self.system_meter.get_peak(),
                'is_silent': self.is_system_silent(),
            }
        }

    def reset(self):
        """モニターをリセット"""
        self.mic_meter.reset()
        self.system_meter.reset()
