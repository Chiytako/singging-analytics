"""
WebベースUIアプリケーション
ブラウザでリアルタイムにピッチを可視化
"""

from flask import Flask, render_template, jsonify
from flask_cors import CORS
import threading
import time
import json
from src.audio_capture import AudioCapture, SystemAudioCapture
from src.pitch_detection import PitchDetector
from src.analyzer import PitchAnalyzer, ScoreCalculator
from src.ui import PitchVisualizer


app = Flask(__name__)
CORS(app)

# グローバル変数
analyzer_instance = None
running = False
latest_data = {
    'original_pitch': None,
    'user_pitch': None,
    'evaluation': {},
    'statistics': {},
    'plot_image': None,
    'gauge_image': None
}


class WebAnalyzer:
    """Web用アナライザー"""

    def __init__(self, use_system_audio=False):
        self.sample_rate = 44100
        self.use_system_audio = use_system_audio

        # コンポーネントの初期化
        self.mic_capture = AudioCapture(sample_rate=self.sample_rate, channels=1)
        self.system_capture = None
        if use_system_audio:
            self.system_capture = SystemAudioCapture(sample_rate=self.sample_rate)

        self.pitch_detector_mic = PitchDetector(sample_rate=self.sample_rate)
        self.pitch_detector_system = None
        if use_system_audio:
            self.pitch_detector_system = PitchDetector(sample_rate=self.sample_rate)

        self.analyzer = PitchAnalyzer()
        self.visualizer = PitchVisualizer()

        self.running = False
        self.thread = None
        self.start_time = None

    def start(self):
        """分析を開始"""
        if self.running:
            return

        self.mic_capture.start()
        if self.system_capture:
            self.system_capture.start()

        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """分析を停止"""
        self.running = False
        self.mic_capture.stop()
        if self.system_capture:
            self.system_capture.stop()

    def _analysis_loop(self):
        """分析ループ"""
        global latest_data

        while self.running:
            try:
                current_time = time.time() - self.start_time

                # マイク入力からピッチを検出
                mic_data = self.mic_capture.get_audio_data()
                user_pitch = None
                if mic_data is not None:
                    user_pitch, _ = self.pitch_detector_mic.detect_pitch(mic_data)

                # システムオーディオからピッチを検出
                original_pitch = None
                if self.use_system_audio and self.system_capture:
                    system_data = self.system_capture.get_audio_data()
                    if system_data is not None:
                        original_pitch, _ = self.pitch_detector_system.detect_pitch(system_data)

                # 分析データを追加
                self.analyzer.add_pitch_data(original_pitch, user_pitch, current_time)

                # 評価を取得
                evaluation = self.analyzer.get_current_evaluation(original_pitch, user_pitch)
                statistics = self.analyzer.get_statistics()

                # 履歴を取得
                original_history, user_history, timestamp_history = \
                    self.analyzer.get_pitch_history()

                # 可視化
                plot_image = self.visualizer.create_realtime_plot(
                    original_history,
                    user_history,
                    timestamp_history,
                    evaluation
                )

                gauge_image = self.visualizer.create_gauge_plot(
                    evaluation.get('cents_diff'),
                    evaluation.get('octave_diff', 0)
                )

                # データを更新
                latest_data = {
                    'original_pitch': original_pitch,
                    'user_pitch': user_pitch,
                    'evaluation': evaluation,
                    'statistics': statistics,
                    'plot_image': plot_image,
                    'gauge_image': gauge_image,
                    'timestamp': current_time
                }

                time.sleep(0.05)

            except Exception as e:
                print(f"分析ループエラー: {e}")
                import traceback
                traceback.print_exc()

    def get_latest_data(self):
        """最新データを取得"""
        return latest_data


@app.route('/')
def index():
    """メインページ"""
    html = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>カラオケピッチアナライザー</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #ffffff;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 30px;
            border-bottom: 2px solid #444;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #4a9eff;
        }

        .subtitle {
            font-size: 1.2em;
            color: #aaa;
        }

        .status {
            background: #2d2d2d;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }

        .status-item {
            background: #3d3d3d;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }

        .status-label {
            font-size: 0.9em;
            color: #aaa;
            margin-bottom: 5px;
        }

        .status-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #4a9eff;
        }

        .warning {
            background: #ff4444;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .charts {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .chart-container {
            background: #2d2d2d;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }

        .chart-container img {
            width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .controls {
            text-align: center;
            margin-top: 30px;
        }

        button {
            background: #4a9eff;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1em;
            border-radius: 8px;
            cursor: pointer;
            margin: 0 10px;
            transition: background 0.3s;
        }

        button:hover {
            background: #3a7edf;
        }

        button:disabled {
            background: #555;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎤 カラオケピッチアナライザー</h1>
            <p class="subtitle">リアルタイム音程評価システム</p>
        </header>

        <div id="octave-warning" class="warning" style="display: none;">
            ⚠️ オクターブズレを検出しました！
        </div>

        <div class="status">
            <h2>現在の状態</h2>
            <div class="status-grid">
                <div class="status-item">
                    <div class="status-label">原曲</div>
                    <div class="status-value" id="original-note">---</div>
                </div>
                <div class="status-item">
                    <div class="status-label">あなた</div>
                    <div class="status-value" id="user-note">---</div>
                </div>
                <div class="status-item">
                    <div class="status-label">評価</div>
                    <div class="status-value" id="accuracy-level">---</div>
                </div>
                <div class="status-item">
                    <div class="status-label">正確率</div>
                    <div class="status-value" id="accuracy-rate">0%</div>
                </div>
            </div>
        </div>

        <div class="charts">
            <div class="chart-container">
                <img id="gauge-chart" src="" alt="ゲージチャート">
            </div>
            <div class="chart-container">
                <img id="pitch-chart" src="" alt="ピッチチャート">
            </div>
        </div>

        <div class="controls">
            <button onclick="location.reload()">リセット</button>
        </div>
    </div>

    <script>
        // データを定期的に更新
        function updateData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    // ステータス更新
                    document.getElementById('original-note').textContent =
                        data.evaluation.original_note || '---';
                    document.getElementById('user-note').textContent =
                        data.evaluation.user_note || '---';
                    document.getElementById('accuracy-level').textContent =
                        data.evaluation.accuracy_level || '---';
                    document.getElementById('accuracy-rate').textContent =
                        data.statistics.accuracy_rate.toFixed(1) + '%';

                    // オクターブズレ警告
                    const warning = document.getElementById('octave-warning');
                    if (data.evaluation.is_octave_error) {
                        warning.style.display = 'block';
                    } else {
                        warning.style.display = 'none';
                    }

                    // チャート更新
                    if (data.gauge_image) {
                        document.getElementById('gauge-chart').src =
                            'data:image/png;base64,' + data.gauge_image;
                    }
                    if (data.plot_image) {
                        document.getElementById('pitch-chart').src =
                            'data:image/png;base64,' + data.plot_image;
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        // 500msごとに更新
        setInterval(updateData, 500);
        updateData();
    </script>
</body>
</html>
    """
    return html


@app.route('/api/data')
def get_data():
    """最新データをJSON形式で返す"""
    global analyzer_instance
    if analyzer_instance:
        return jsonify(analyzer_instance.get_latest_data())
    return jsonify(latest_data)


@app.route('/api/start')
def start_analysis():
    """分析を開始"""
    global analyzer_instance, running
    if not running:
        analyzer_instance.start()
        running = True
    return jsonify({'status': 'started'})


@app.route('/api/stop')
def stop_analysis():
    """分析を停止"""
    global analyzer_instance, running
    if running:
        analyzer_instance.stop()
        running = False
    return jsonify({'status': 'stopped'})


def run_web_app(use_system_audio=False, port=5000):
    """Webアプリを起動"""
    global analyzer_instance

    print("\n" + "=" * 80)
    print("カラオケピッチアナライザー - Webモード")
    print("=" * 80)
    print(f"\nブラウザで http://localhost:{port} にアクセスしてください")
    print("Ctrl+C で終了します\n")

    analyzer_instance = WebAnalyzer(use_system_audio=use_system_audio)
    analyzer_instance.start()

    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n終了しています...")
        analyzer_instance.stop()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='カラオケピッチアナライザー - Webモード')
    parser.add_argument('--system-audio', action='store_true',
                       help='システムオーディオもキャプチャする')
    parser.add_argument('--port', type=int, default=5000,
                       help='ポート番号 (デフォルト: 5000)')

    args = parser.parse_args()

    run_web_app(use_system_audio=args.system_audio, port=args.port)
