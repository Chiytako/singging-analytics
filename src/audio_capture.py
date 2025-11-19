"""
オーディオキャプチャモジュール
マイク入力とシステムオーディオをキャプチャする
"""

import sounddevice as sd
import numpy as np
from typing import Callable, Optional
import queue
import threading


class AudioCapture:
    """オーディオキャプチャクラス"""

    def __init__(
        self,
        sample_rate: int = 44100,
        channels: int = 1,
        blocksize: int = 2048,
        device: Optional[int] = None
    ):
        """
        初期化

        Args:
            sample_rate: サンプリングレート (Hz)
            channels: チャンネル数 (1=モノラル, 2=ステレオ)
            blocksize: バッファサイズ
            device: 使用するデバイスID (Noneの場合はデフォルト)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.blocksize = blocksize
        self.device = device
        self.stream = None
        self.audio_queue = queue.Queue()
        self.is_running = False

    def list_devices(self):
        """利用可能なオーディオデバイスをリスト表示"""
        print("\n=== 利用可能なオーディオデバイス ===")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']}")
            print(f"   入力チャンネル数: {device['max_input_channels']}")
            print(f"   出力チャンネル数: {device['max_output_channels']}")
            print(f"   サンプリングレート: {device['default_samplerate']}")
            print()
        return devices

    def _audio_callback(self, indata, frames, time, status):
        """
        オーディオストリームのコールバック関数

        Args:
            indata: 入力オーディオデータ
            frames: フレーム数
            time: タイムスタンプ
            status: ステータス
        """
        if status:
            print(f"Status: {status}")

        # モノラルに変換（ステレオの場合）
        if self.channels == 2 and len(indata.shape) > 1:
            audio_data = np.mean(indata, axis=1)
        else:
            audio_data = indata.flatten()

        # キューに追加
        self.audio_queue.put(audio_data.copy())

    def start(self):
        """オーディオキャプチャを開始"""
        if self.is_running:
            print("既にキャプチャが実行中です")
            return

        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                callback=self._audio_callback
            )
            self.stream.start()
            self.is_running = True
            print(f"オーディオキャプチャを開始しました (サンプリングレート: {self.sample_rate} Hz)")
        except Exception as e:
            print(f"オーディオキャプチャの開始に失敗しました: {e}")
            raise

    def stop(self):
        """オーディオキャプチャを停止"""
        if not self.is_running:
            return

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.is_running = False
        print("オーディオキャプチャを停止しました")

    def get_audio_data(self) -> Optional[np.ndarray]:
        """
        キューからオーディオデータを取得

        Returns:
            オーディオデータ (numpy配列)
        """
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None

    def clear_queue(self):
        """キューをクリア"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break


class SystemAudioCapture(AudioCapture):
    """
    システムオーディオキャプチャクラス

    Note: システムオーディオのキャプチャはOSによって実装が異なります
    - Windows: WASAPI ループバック
    - macOS: BlackHole等の仮想オーディオデバイスが必要
    - Linux: PulseAudio monitor デバイス
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        channels: int = 2,
        blocksize: int = 2048
    ):
        # システムオーディオ用のデバイスを自動検出
        device = self._find_system_audio_device()
        super().__init__(
            sample_rate=sample_rate,
            channels=channels,
            blocksize=blocksize,
            device=device
        )

    def _find_system_audio_device(self) -> Optional[int]:
        """
        システムオーディオデバイスを検出

        Returns:
            デバイスID (見つからない場合はNone)
        """
        devices = sd.query_devices()

        # プラットフォーム別のキーワードで検索
        keywords = [
            'stereo mix',      # Windows
            'wave out mix',    # Windows
            'loopback',        # Windows WASAPI
            'monitor',         # Linux PulseAudio
            'blackhole',       # macOS (仮想デバイス)
            'soundflower'      # macOS (仮想デバイス)
        ]

        for i, device in enumerate(devices):
            device_name = device['name'].lower()
            if any(keyword in device_name for keyword in keywords):
                if device['max_input_channels'] > 0:
                    print(f"システムオーディオデバイスを検出: {device['name']}")
                    return i

        print("警告: システムオーディオデバイスが見つかりませんでした")
        print("デフォルトの入力デバイスを使用します")
        return None
