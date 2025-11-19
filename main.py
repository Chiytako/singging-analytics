"""
カラオケピッチアナライザー - メインプログラム
"""

import sys
import time
import argparse
import numpy as np
from src.audio_capture import AudioCapture, SystemAudioCapture
from src.pitch_detection import PitchDetector
from src.analyzer import PitchAnalyzer, ScoreCalculator
from src.ui import ConsoleDisplay


class KaraokePitchAnalyzer:
    """カラオケピッチアナライザーメインクラス"""

    def __init__(
        self,
        sample_rate: int = 44100,
        use_system_audio: bool = False,
        mic_device: int = None,
        system_device: int = None
    ):
        """
        初期化

        Args:
            sample_rate: サンプリングレート
            use_system_audio: システムオーディオを使用するか
            mic_device: マイクデバイスID
            system_device: システムオーディオデバイスID
        """
        self.sample_rate = sample_rate
        self.use_system_audio = use_system_audio

        # コンポーネントの初期化
        self.mic_capture = AudioCapture(
            sample_rate=sample_rate,
            channels=1,
            device=mic_device
        )
        self.system_capture = None
        if use_system_audio:
            if system_device is not None:
                # 手動でデバイスIDを指定
                self.system_capture = AudioCapture(
                    sample_rate=sample_rate,
                    channels=2,
                    device=system_device
                )
            else:
                # 自動検出
                self.system_capture = SystemAudioCapture(sample_rate=sample_rate)

        self.pitch_detector_mic = PitchDetector(sample_rate=sample_rate)
        self.pitch_detector_system = None
        if use_system_audio:
            self.pitch_detector_system = PitchDetector(sample_rate=sample_rate)

        self.analyzer = PitchAnalyzer()

        print("\n" + "=" * 80)
        print("カラオケピッチアナライザー")
        print("=" * 80)

    def list_audio_devices(self):
        """オーディオデバイスをリスト表示"""
        self.mic_capture.list_devices()

    def run(self):
        """メインループを実行"""
        try:
            # オーディオキャプチャを開始
            print("\n✓ マイク入力を開始中...")
            self.mic_capture.start()

            if self.use_system_audio and self.system_capture:
                print("✓ システムオーディオキャプチャを開始中...")
                self.system_capture.start()

            print("\n準備完了！歌ってみてください。")
            print("Ctrl+C で終了します。\n")

            time.sleep(1)

            start_time = time.time()
            frame_count = 0

            # メインループ
            while True:
                current_time = time.time() - start_time

                # マイク入力からピッチを検出
                mic_data = self.mic_capture.get_audio_data()
                user_pitch = None
                user_confidence = 0.0

                if mic_data is not None:
                    user_pitch, user_confidence = self.pitch_detector_mic.detect_pitch(mic_data)

                # システムオーディオからピッチを検出（原曲）
                original_pitch = None
                original_confidence = 0.0

                if self.use_system_audio and self.system_capture:
                    system_data = self.system_capture.get_audio_data()
                    if system_data is not None:
                        original_pitch, original_confidence = \
                            self.pitch_detector_system.detect_pitch(system_data)

                # 分析データを追加
                self.analyzer.add_pitch_data(original_pitch, user_pitch, current_time)

                # 評価を取得
                evaluation = self.analyzer.get_current_evaluation(
                    original_pitch, user_pitch
                )
                statistics = self.analyzer.get_statistics()

                # 表示を更新（0.5秒ごと）
                frame_count += 1
                if frame_count % 10 == 0:
                    ConsoleDisplay.display_pitch_info(
                        original_pitch,
                        user_pitch,
                        evaluation,
                        statistics
                    )

                    # オクターブズレ警告
                    if self.analyzer.should_show_octave_warning():
                        print("\a")  # ビープ音

                # 処理速度の調整
                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n\n終了しています...")
            self._cleanup()
            self._show_final_results()

        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            self._cleanup()
            sys.exit(1)

    def _cleanup(self):
        """クリーンアップ処理"""
        print("オーディオキャプチャを停止中...")
        self.mic_capture.stop()
        if self.system_capture:
            self.system_capture.stop()

    def _show_final_results(self):
        """最終結果を表示"""
        print("\n" + "=" * 80)
        print("最終結果")
        print("=" * 80)

        statistics = self.analyzer.get_statistics()

        print(f"\n総サンプル数:     {statistics['total_samples']}")
        print(f"正確率:           {statistics['accuracy_rate']:.1f}%")
        print(f"オクターブズレ率: {statistics['octave_error_rate']:.1f}%")

        # スコアを計算
        original_history, user_history, _ = self.analyzer.get_pitch_history()

        cents_diffs = []
        for orig, user in zip(original_history, user_history):
            if orig and user:
                cents = PitchDetector.calculate_cents_difference(orig, user)
                cents_diffs.append(cents)

        if cents_diffs:
            score_info = ScoreCalculator.calculate_score(cents_diffs)
            print(f"\n総合スコア:       {score_info['score']:.1f} 点")
            print(f"グレード:         {score_info['grade']}")
            print(f"平均誤差:         {score_info['average_error']:.1f} セント")
            print(f"中央値誤差:       {score_info['median_error']:.1f} セント")

        print("\n" + "=" * 80)
        print("ありがとうございました！")
        print("=" * 80 + "\n")


def select_device_interactive():
    """インタラクティブにデバイスを選択"""
    import sounddevice as sd

    devices = sd.query_devices()

    print("\n" + "=" * 80)
    print("利用可能なオーディオデバイス")
    print("=" * 80)

    input_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(i)
            print(f"[{i}] {device['name']}")
            print(f"    入力チャンネル数: {device['max_input_channels']}")
            print(f"    サンプリングレート: {device['default_samplerate']} Hz")
            print()

    while True:
        try:
            choice = input("デバイスIDを入力してください (キャンセル: Enter): ").strip()
            if not choice:
                return None
            device_id = int(choice)
            if device_id in input_devices:
                return device_id
            else:
                print("無効なデバイスIDです。入力可能なデバイスから選択してください。")
        except ValueError:
            print("数値を入力してください。")
        except KeyboardInterrupt:
            print("\nキャンセルしました。")
            return None


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='カラオケピッチアナライザー - 歌唱の音程精度をリアルタイム評価'
    )
    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='利用可能なオーディオデバイスをリスト表示'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='インタラクティブモードでデバイスを選択'
    )
    parser.add_argument(
        '--mic-device',
        type=int,
        default=None,
        help='マイクデバイスID (--list-devicesで確認可能)'
    )
    parser.add_argument(
        '--system-device',
        type=int,
        default=None,
        help='システムオーディオデバイスID (--list-devicesで確認可能)'
    )
    parser.add_argument(
        '--system-audio',
        action='store_true',
        help='システムオーディオ（原曲）もキャプチャする'
    )
    parser.add_argument(
        '--sample-rate',
        type=int,
        default=44100,
        help='サンプリングレート (デフォルト: 44100)'
    )

    args = parser.parse_args()

    # デバイスリスト表示モード
    if args.list_devices:
        capture = AudioCapture()
        capture.list_devices()
        return

    # インタラクティブモード
    mic_device = args.mic_device
    system_device = args.system_device

    if args.interactive:
        print("\n【マイクデバイスの選択】")
        mic_device = select_device_interactive()

        if args.system_audio:
            print("\n【システムオーディオデバイスの選択】")
            system_device = select_device_interactive()

    # メインプログラムを実行
    analyzer = KaraokePitchAnalyzer(
        sample_rate=args.sample_rate,
        use_system_audio=args.system_audio,
        mic_device=mic_device,
        system_device=system_device
    )
    analyzer.run()


if __name__ == '__main__':
    main()
