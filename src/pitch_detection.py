"""
ピッチ検出モジュール
オーディオデータから音高を検出する
"""

import numpy as np
from typing import Optional, Tuple
import aubio


class PitchDetector:
    """ピッチ検出クラス（aubio使用）"""

    def __init__(
        self,
        sample_rate: int = 44100,
        hop_size: int = 512,
        method: str = 'yinfft',
        confidence_threshold: float = 0.8
    ):
        """
        初期化

        Args:
            sample_rate: サンプリングレート (Hz)
            hop_size: ホップサイズ
            method: 検出アルゴリズム ('yinfft', 'yin', 'mcomb', 'fcomb', 'schmitt')
                    yinfft: 高精度で高速（推奨）
            confidence_threshold: 信頼度の閾値（この値以下の検出結果は無視）
        """
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.confidence_threshold = confidence_threshold

        # aubioピッチ検出器の初期化
        self.pitch_detector = aubio.pitch(
            method,
            hop_size * 2,  # バッファサイズはホップサイズの2倍
            hop_size,
            sample_rate
        )

        # 信頼度の単位を設定
        self.pitch_detector.set_unit('Hz')
        self.pitch_detector.set_silence(-40)  # -40dB以下は無音とみなす

        # ピッチ履歴（スムージング用）
        self.pitch_history = []
        self.history_size = 5

    def detect_pitch(self, audio_data: np.ndarray) -> Tuple[Optional[float], float]:
        """
        ピッチを検出

        Args:
            audio_data: オーディオデータ (numpy配列)

        Returns:
            (周波数 (Hz), 信頼度) のタプル
            検出できない場合は (None, 0.0)
        """
        # float32に変換
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # ピッチを検出
        pitch = self.pitch_detector(audio_data)[0]
        confidence = self.pitch_detector.get_confidence()

        # 信頼度が低い場合はNone
        if confidence < self.confidence_threshold or pitch < 50.0:
            return None, confidence

        # スムージング
        smoothed_pitch = self._smooth_pitch(pitch)

        return smoothed_pitch, confidence

    def _smooth_pitch(self, pitch: float) -> float:
        """
        ピッチをスムージング（移動平均）

        Args:
            pitch: 検出されたピッチ

        Returns:
            スムージングされたピッチ
        """
        self.pitch_history.append(pitch)

        # 履歴サイズを制限
        if len(self.pitch_history) > self.history_size:
            self.pitch_history.pop(0)

        # 移動平均
        return np.mean(self.pitch_history)

    def reset_history(self):
        """ピッチ履歴をリセット"""
        self.pitch_history = []

    @staticmethod
    def hz_to_midi(frequency: float) -> float:
        """
        周波数をMIDIノート番号に変換

        Args:
            frequency: 周波数 (Hz)

        Returns:
            MIDIノート番号
        """
        if frequency <= 0:
            return 0
        return 69 + 12 * np.log2(frequency / 440.0)

    @staticmethod
    def midi_to_hz(midi_note: float) -> float:
        """
        MIDIノート番号を周波数に変換

        Args:
            midi_note: MIDIノート番号

        Returns:
            周波数 (Hz)
        """
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    @staticmethod
    def hz_to_note_name(frequency: float) -> str:
        """
        周波数を音名に変換

        Args:
            frequency: 周波数 (Hz)

        Returns:
            音名 (例: "A4", "C#5")
        """
        if frequency <= 0:
            return "---"

        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        midi_note = PitchDetector.hz_to_midi(frequency)
        note_index = int(round(midi_note)) % 12
        octave = int(round(midi_note)) // 12 - 1

        return f"{note_names[note_index]}{octave}"

    @staticmethod
    def calculate_cents_difference(freq1: float, freq2: float) -> float:
        """
        2つの周波数の差をセント単位で計算

        Args:
            freq1: 周波数1 (Hz)
            freq2: 周波数2 (Hz)

        Returns:
            セント差 (100セント = 半音)
        """
        if freq1 <= 0 or freq2 <= 0:
            return 0.0

        return 1200 * np.log2(freq2 / freq1)

    @staticmethod
    def detect_octave_difference(freq1: float, freq2: float) -> int:
        """
        2つの周波数のオクターブ差を検出

        Args:
            freq1: 基準周波数 (Hz)
            freq2: 比較周波数 (Hz)

        Returns:
            オクターブ差 (-2, -1, 0, 1, 2など)
        """
        if freq1 <= 0 or freq2 <= 0:
            return 0

        ratio = freq2 / freq1
        octaves = np.log2(ratio)

        return int(round(octaves))

    @staticmethod
    def normalize_to_same_octave(freq1: float, freq2: float) -> float:
        """
        freq2をfreq1と同じオクターブに正規化

        Args:
            freq1: 基準周波数 (Hz)
            freq2: 正規化する周波数 (Hz)

        Returns:
            正規化された周波数 (Hz)
        """
        if freq1 <= 0 or freq2 <= 0:
            return freq2

        # オクターブ差を検出
        octave_diff = PitchDetector.detect_octave_difference(freq1, freq2)

        # 同じオクターブに調整
        normalized_freq = freq2 / (2 ** octave_diff)

        return normalized_freq
