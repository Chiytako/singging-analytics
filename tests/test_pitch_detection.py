"""
ピッチ検出モジュールのテスト
"""

import unittest
import numpy as np
import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pitch_detection import PitchDetector


class TestPitchDetector(unittest.TestCase):
    """PitchDetectorクラスのテスト"""

    def setUp(self):
        """テストのセットアップ"""
        self.detector = PitchDetector(sample_rate=44100)

    def test_hz_to_midi_conversion(self):
        """Hz → MIDI変換のテスト"""
        # A4 = 440 Hz = MIDI 69
        midi_note = PitchDetector.hz_to_midi(440.0)
        self.assertAlmostEqual(midi_note, 69.0, places=1)

        # C4 = 261.63 Hz = MIDI 60
        midi_note = PitchDetector.hz_to_midi(261.63)
        self.assertAlmostEqual(midi_note, 60.0, places=1)

    def test_midi_to_hz_conversion(self):
        """MIDI → Hz変換のテスト"""
        # MIDI 69 = 440 Hz (A4)
        frequency = PitchDetector.midi_to_hz(69)
        self.assertAlmostEqual(frequency, 440.0, places=1)

        # MIDI 60 = 261.63 Hz (C4)
        frequency = PitchDetector.midi_to_hz(60)
        self.assertAlmostEqual(frequency, 261.63, places=1)

    def test_hz_to_note_name(self):
        """Hz → 音名変換のテスト"""
        # A4 = 440 Hz
        note_name = PitchDetector.hz_to_note_name(440.0)
        self.assertEqual(note_name, 'A4')

        # C4 = 261.63 Hz
        note_name = PitchDetector.hz_to_note_name(261.63)
        self.assertEqual(note_name, 'C4')

        # 無効な値
        note_name = PitchDetector.hz_to_note_name(0)
        self.assertEqual(note_name, '---')

    def test_calculate_cents_difference(self):
        """セント差計算のテスト"""
        # 同じ周波数 = 0セント
        cents = PitchDetector.calculate_cents_difference(440.0, 440.0)
        self.assertAlmostEqual(cents, 0.0, places=1)

        # 1オクターブ上 = 1200セント
        cents = PitchDetector.calculate_cents_difference(220.0, 440.0)
        self.assertAlmostEqual(cents, 1200.0, places=1)

        # 1オクターブ下 = -1200セント
        cents = PitchDetector.calculate_cents_difference(440.0, 220.0)
        self.assertAlmostEqual(cents, -1200.0, places=1)

    def test_detect_octave_difference(self):
        """オクターブ差検出のテスト"""
        # 同じオクターブ
        octave_diff = PitchDetector.detect_octave_difference(440.0, 440.0)
        self.assertEqual(octave_diff, 0)

        # 1オクターブ上
        octave_diff = PitchDetector.detect_octave_difference(220.0, 440.0)
        self.assertEqual(octave_diff, 1)

        # 1オクターブ下
        octave_diff = PitchDetector.detect_octave_difference(440.0, 220.0)
        self.assertEqual(octave_diff, -1)

        # 2オクターブ上
        octave_diff = PitchDetector.detect_octave_difference(220.0, 880.0)
        self.assertEqual(octave_diff, 2)

    def test_normalize_to_same_octave(self):
        """オクターブ正規化のテスト"""
        # 1オクターブ上を正規化
        normalized = PitchDetector.normalize_to_same_octave(440.0, 880.0)
        self.assertAlmostEqual(normalized, 440.0, places=1)

        # 1オクターブ下を正規化
        normalized = PitchDetector.normalize_to_same_octave(440.0, 220.0)
        self.assertAlmostEqual(normalized, 440.0, places=1)

        # 同じオクターブ
        normalized = PitchDetector.normalize_to_same_octave(440.0, 440.0)
        self.assertAlmostEqual(normalized, 440.0, places=1)


if __name__ == '__main__':
    unittest.main()
