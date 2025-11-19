"""
シンプルなピッチ検出テスト
マイクに向かって声を出すと、検出された音程とHz数が表示されます
"""

import sys
import os
import time

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_capture import AudioCapture
from src.pitch_detection import PitchDetector


def main():
    print("=" * 60)
    print("シンプルなピッチ検出テスト")
    print("=" * 60)
    print("\nマイクに向かって声を出してください。")
    print("Ctrl+C で終了します。\n")

    # コンポーネントの初期化
    capture = AudioCapture(sample_rate=44100, channels=1)
    detector = PitchDetector(sample_rate=44100)

    try:
        # オーディオキャプチャを開始
        capture.start()
        time.sleep(1)

        print("検出中...\n")

        # メインループ
        while True:
            # オーディオデータを取得
            audio_data = capture.get_audio_data()

            if audio_data is not None:
                # ピッチを検出
                pitch, confidence = detector.detect_pitch(audio_data)

                if pitch:
                    # 音名を取得
                    note_name = PitchDetector.hz_to_note_name(pitch)
                    midi_note = PitchDetector.hz_to_midi(pitch)

                    print(f"検出: {note_name:>5} | "
                          f"{pitch:>7.2f} Hz | "
                          f"MIDI: {midi_note:>5.1f} | "
                          f"信頼度: {confidence:>4.2f}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n終了しています...")

    finally:
        capture.stop()
        print("完了！")


if __name__ == '__main__':
    main()
