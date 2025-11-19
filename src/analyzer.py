"""
分析・評価モジュール
原曲とユーザー歌唱を比較・評価する
"""

import numpy as np
from typing import Optional, Tuple, Dict
from collections import deque
from src.pitch_detection import PitchDetector


class PitchAnalyzer:
    """ピッチ分析・評価クラス"""

    def __init__(self, history_size: int = 100):
        """
        初期化

        Args:
            history_size: 履歴サイズ
        """
        self.history_size = history_size

        # ピッチ履歴
        self.original_pitch_history = deque(maxlen=history_size)
        self.user_pitch_history = deque(maxlen=history_size)
        self.timestamp_history = deque(maxlen=history_size)

        # 統計情報
        self.total_samples = 0
        self.accurate_samples = 0  # 正確なサンプル数（±50セント以内）
        self.octave_error_samples = 0  # オクターブズレサンプル数

        # 現在のオクターブズレ状態
        self.current_octave_error = 0
        self.octave_error_duration = 0  # 連続してオクターブズレが続いている時間

    def add_pitch_data(
        self,
        original_pitch: Optional[float],
        user_pitch: Optional[float],
        timestamp: float
    ):
        """
        ピッチデータを追加

        Args:
            original_pitch: 原曲のピッチ (Hz)
            user_pitch: ユーザーのピッチ (Hz)
            timestamp: タイムスタンプ
        """
        self.original_pitch_history.append(original_pitch)
        self.user_pitch_history.append(user_pitch)
        self.timestamp_history.append(timestamp)

        # 両方のピッチが検出された場合のみ統計を更新
        if original_pitch and user_pitch:
            self.total_samples += 1

            # セント差を計算
            cents_diff = abs(PitchDetector.calculate_cents_difference(
                original_pitch, user_pitch
            ))

            # オクターブ差を検出
            octave_diff = PitchDetector.detect_octave_difference(
                original_pitch, user_pitch
            )

            # 正確性を評価（±50セント以内）
            if cents_diff <= 50:
                self.accurate_samples += 1

            # オクターブズレを検出（±1オクターブ以上）
            if abs(octave_diff) >= 1:
                self.octave_error_samples += 1
                self.current_octave_error = octave_diff
                self.octave_error_duration += 1
            else:
                self.current_octave_error = 0
                self.octave_error_duration = 0

    def get_current_evaluation(
        self,
        original_pitch: Optional[float],
        user_pitch: Optional[float]
    ) -> Dict:
        """
        現在のピッチの評価を取得

        Args:
            original_pitch: 原曲のピッチ (Hz)
            user_pitch: ユーザーのピッチ (Hz)

        Returns:
            評価結果の辞書
        """
        result = {
            'cents_diff': None,
            'octave_diff': 0,
            'is_accurate': False,
            'is_octave_error': False,
            'accuracy_level': 'N/A',
            'original_note': '---',
            'user_note': '---',
        }

        if not original_pitch or not user_pitch:
            return result

        # セント差を計算
        cents_diff = PitchDetector.calculate_cents_difference(
            original_pitch, user_pitch
        )
        result['cents_diff'] = cents_diff

        # オクターブ差を検出
        octave_diff = PitchDetector.detect_octave_difference(
            original_pitch, user_pitch
        )
        result['octave_diff'] = octave_diff

        # 音名を取得
        result['original_note'] = PitchDetector.hz_to_note_name(original_pitch)
        result['user_note'] = PitchDetector.hz_to_note_name(user_pitch)

        # オクターブズレの判定
        if abs(octave_diff) >= 1:
            result['is_octave_error'] = True

        # 正確性の判定
        abs_cents_diff = abs(cents_diff)
        if abs_cents_diff <= 20:
            result['is_accurate'] = True
            result['accuracy_level'] = '完璧'
        elif abs_cents_diff <= 50:
            result['is_accurate'] = True
            result['accuracy_level'] = '良好'
        elif abs_cents_diff <= 100:
            result['accuracy_level'] = 'やや不正確'
        else:
            result['accuracy_level'] = '不正確'

        return result

    def get_statistics(self) -> Dict:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        if self.total_samples == 0:
            accuracy_rate = 0.0
            octave_error_rate = 0.0
        else:
            accuracy_rate = (self.accurate_samples / self.total_samples) * 100
            octave_error_rate = (self.octave_error_samples / self.total_samples) * 100

        return {
            'total_samples': self.total_samples,
            'accurate_samples': self.accurate_samples,
            'octave_error_samples': self.octave_error_samples,
            'accuracy_rate': accuracy_rate,
            'octave_error_rate': octave_error_rate,
            'current_octave_error': self.current_octave_error,
            'octave_error_duration': self.octave_error_duration
        }

    def should_show_octave_warning(self, threshold: int = 5) -> bool:
        """
        オクターブズレ警告を表示すべきか判定

        Args:
            threshold: 警告を出すまでの連続エラー数

        Returns:
            警告を表示すべきかどうか
        """
        return self.octave_error_duration >= threshold

    def reset_statistics(self):
        """統計情報をリセット"""
        self.total_samples = 0
        self.accurate_samples = 0
        self.octave_error_samples = 0
        self.current_octave_error = 0
        self.octave_error_duration = 0

    def clear_history(self):
        """履歴をクリア"""
        self.original_pitch_history.clear()
        self.user_pitch_history.clear()
        self.timestamp_history.clear()

    def get_pitch_history(self) -> Tuple[list, list, list]:
        """
        ピッチ履歴を取得

        Returns:
            (原曲ピッチ履歴, ユーザーピッチ履歴, タイムスタンプ履歴)
        """
        return (
            list(self.original_pitch_history),
            list(self.user_pitch_history),
            list(self.timestamp_history)
        )


class ScoreCalculator:
    """スコア計算クラス"""

    @staticmethod
    def calculate_score(
        cents_differences: list,
        max_score: int = 100
    ) -> Dict:
        """
        スコアを計算

        Args:
            cents_differences: セント差のリスト
            max_score: 最大スコア

        Returns:
            スコア情報の辞書
        """
        if not cents_differences:
            return {
                'score': 0,
                'grade': 'E',
                'average_error': 0.0,
                'median_error': 0.0
            }

        # 絶対値を取得
        abs_differences = [abs(diff) for diff in cents_differences if diff is not None]

        if not abs_differences:
            return {
                'score': 0,
                'grade': 'E',
                'average_error': 0.0,
                'median_error': 0.0
            }

        # 平均誤差と中央値
        average_error = np.mean(abs_differences)
        median_error = np.median(abs_differences)

        # スコア計算（誤差が少ないほど高スコア）
        # 0セント = 100点、100セント = 50点、200セント以上 = 0点
        score_values = []
        for diff in abs_differences:
            if diff <= 20:
                score_values.append(100)
            elif diff <= 50:
                score_values.append(90)
            elif diff <= 100:
                score_values.append(70)
            elif diff <= 150:
                score_values.append(50)
            elif diff <= 200:
                score_values.append(30)
            else:
                score_values.append(0)

        score = np.mean(score_values)

        # グレード判定
        if score >= 90:
            grade = 'S'
        elif score >= 80:
            grade = 'A'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C'
        elif score >= 50:
            grade = 'D'
        else:
            grade = 'E'

        return {
            'score': round(score, 1),
            'grade': grade,
            'average_error': round(average_error, 1),
            'median_error': round(median_error, 1)
        }
