# 🎤 カラオケピッチアナライザー

PC上で再生中の音楽とマイク入力をリアルタイム分析し、歌唱の音程精度を評価する軽量ソフトウェアです。

## ✨ 主な機能

- **リアルタイムピッチ検出**: マイク入力から歌声の音高を高精度で検出
- **音程精度評価**: 原曲との音程差をセント単位で計算・表示
- **オクターブズレ検出**: 1オクターブ高い/低い歌唱を自動検出して警告
- **リアルタイム可視化**: ピッチの時系列グラフ、セント差ゲージ表示
- **スコアリング**: 歌唱精度に基づいた総合スコア・グレード評価
- **2つのUIモード**: コンソールモード & Webブラウザモード

## 📋 必要要件

- Python 3.7以上
- マイク（歌唱入力用）
- スピーカー/ヘッドホン（原曲再生用）
- システムオーディオキャプチャ機能（オプション）

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/karaoke-pitch-analyzer.git
cd karaoke-pitch-analyzer
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. プログラムの実行

#### コンソールモード（基本）

```bash
python main.py
```

マイクに向かって歌うと、リアルタイムで音程が分析されます。

#### Webモード（ビジュアル）

```bash
python web_app.py
```

ブラウザで `http://localhost:5000` を開くと、グラフィカルなインターフェースが表示されます。

## 📖 詳細な使用方法

### コンソールモード

基本的な使い方:

```bash
# マイク入力のみを分析（デフォルト）
python main.py

# システムオーディオ（原曲）も同時にキャプチャ
python main.py --system-audio

# 利用可能なオーディオデバイスをリスト表示
python main.py --list-devices

# インタラクティブモードでデバイスを選択
python main.py --interactive

# 特定のデバイスIDを指定
python main.py --mic-device 1 --system-audio --system-device 5
```

#### オプション引数

- `--system-audio`: システムオーディオ（PC内部音声）もキャプチャして原曲と比較
- `--list-devices`: 利用可能なオーディオデバイス一覧を表示
- `--interactive` / `-i`: インタラクティブモードでデバイスを選択
- `--mic-device ID`: マイクデバイスIDを指定（`--list-devices`で確認可能）
- `--system-device ID`: システムオーディオデバイスIDを指定
- `--sample-rate RATE`: サンプリングレートを指定（デフォルト: 44100 Hz）

#### デバイス選択の方法

**1. デバイス一覧を確認**
```bash
python main.py --list-devices
```

出力例:
```
=== 利用可能なオーディオデバイス ===
0: マイク配列 (Realtek High Definition Audio)
   入力チャンネル数: 2
   出力チャンネル数: 0
   サンプリングレート: 44100.0

1: ステレオミキサー (Realtek High Definition Audio)
   入力チャンネル数: 2
   出力チャンネル数: 0
   サンプリングレート: 44100.0
```

**2. デバイスIDを指定して実行**
```bash
# マイクはデバイス0、システムオーディオはデバイス1を使用
python main.py --mic-device 0 --system-audio --system-device 1
```

**3. インタラクティブモードで選択**
```bash
python main.py --interactive --system-audio
```

インタラクティブモードでは、起動時にデバイス一覧から選択できます。

#### 表示される情報

```
================================================================================
カラオケピッチアナライザー
================================================================================

【現在の音程】
  原曲:    A4    (440.0 Hz)
  あなた:  A4    (442.0 Hz)

【音程差】 +4.5 セント
  ────────────────|●──────────────────
  低い ←                        → 高い

【評価】 完璧

【統計】
  総サンプル数: 1523
  正確率:       87.3%
  オクターブズレ率: 2.1%

================================================================================
Ctrl+C で終了
================================================================================
```

### Webモード

```bash
# 基本起動
python web_app.py

# システムオーディオも使用
python web_app.py --system-audio

# デバイスIDを指定
python web_app.py --mic-device 0 --system-audio --system-device 1

# ポート番号を変更
python web_app.py --port 8080
```

#### Webモードのオプション

- `--system-audio`: システムオーディオもキャプチャ
- `--mic-device ID`: マイクデバイスIDを指定
- `--system-device ID`: システムオーディオデバイスIDを指定
- `--port PORT`: ポート番号（デフォルト: 5000）

ブラウザで以下のURLにアクセス:
- http://localhost:5000 （デフォルト）
- http://localhost:8080 （ポート変更時）

#### Web画面の機能

- **リアルタイムピッチグラフ**: 原曲とあなたのピッチを時系列で表示
- **セント差ゲージ**: 現在の音程のズレを視覚的に表示
- **統計情報**: 正確率、評価レベルなどをリアルタイム更新
- **オクターブズレ警告**: 検出時に赤い警告バナーを表示

## 🎯 評価基準

### 音程精度

| セント差 | 評価 |
|---------|------|
| ±20セント以内 | 完璧 ⭐⭐⭐ |
| ±50セント以内 | 良好 ⭐⭐ |
| ±100セント以内 | やや不正確 ⭐ |
| それ以上 | 不正確 |

※ 100セント = 半音

### グレード

| スコア | グレード |
|--------|---------|
| 90点以上 | S |
| 80-89点 | A |
| 70-79点 | B |
| 60-69点 | C |
| 50-59点 | D |
| 50点未満 | E |

## ⚙️ システムオーディオのキャプチャ設定

### Windows

1. **ステレオミキサーを有効化**
   - サウンド設定 → 録音デバイス
   - 右クリック → 「無効なデバイスの表示」
   - 「ステレオミキサー」を有効化

2. **または、仮想オーディオデバイスを使用**
   - [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) をインストール

### macOS

1. **仮想オーディオデバイスのインストール**
   - [BlackHole](https://github.com/ExistentialAudio/BlackHole) をインストール

```bash
brew install blackhole-2ch
```

2. **Audio MIDI設定で集約デバイスを作成**
   - アプリケーション → ユーティリティ → Audio MIDI設定
   - 「+」→ 「機能集約デバイスを作成」
   - BlackHoleと内蔵マイクを選択

### Linux

PulseAudioを使用している場合、monitorデバイスが自動的に利用可能です:

```bash
# 利用可能なデバイスを確認
python main.py --list-devices
```

## 🗂️ プロジェクト構成

```
karaoke-pitch-analyzer/
├── README.md                 # このファイル
├── requirements.txt          # 依存パッケージ
├── main.py                   # コンソールモードのエントリーポイント
├── web_app.py               # Webモードのエントリーポイント
├── src/
│   ├── audio_capture.py     # オーディオキャプチャ
│   ├── pitch_detection.py   # ピッチ検出（aubio使用）
│   ├── analyzer.py          # 比較・評価ロジック
│   └── ui.py               # UI/可視化
└── tests/                   # テスト（今後追加予定）
```

## 🔧 トラブルシューティング

### マイクが認識されない

```bash
# 利用可能なデバイスを確認
python main.py --list-devices
```

デバイス一覧が表示されるので、マイクのデバイスIDを確認してください。

### システムオーディオがキャプチャできない

1. 上記の「システムオーディオのキャプチャ設定」を確認
2. デバイスリストに「stereo mix」「loopback」「monitor」等が表示されるか確認
3. 表示されない場合は、仮想オーディオデバイスのインストールが必要

### aubioのインストールに失敗する

#### Windows
```bash
pip install wheel
pip install aubio --only-binary :all:
```

#### macOS
```bash
brew install aubio
pip install aubio
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install libaubio-dev libaubio5
pip install aubio
```

### matplotlibの警告が出る

GUI環境がない場合、以下のエラーが出ることがあります:
```
UserWarning: Matplotlib is currently using agg, which is a non-GUI backend
```

これは正常な動作です。プログラムは問題なく動作します。

## 💡 使用例

### 1. マイクの音程チェック

```bash
python main.py
```

マイクに向かって「ラー」（A4 = 440 Hz）と歌ってみましょう。
画面に現在の音程とHz数が表示されます。

### 2. YouTubeで歌ってみる

1. システムオーディオキャプチャを設定
2. プログラムを起動:
   ```bash
   python main.py --system-audio
   ```
3. YouTubeでカラオケ動画を再生
4. 歌う！

### 3. Webモードでビジュアル確認

```bash
python web_app.py --system-audio
```

ブラウザで `http://localhost:5000` を開き、カラオケを楽しみながらリアルタイムでグラフを確認できます。

## 📊 技術詳細

### ピッチ検出アルゴリズム

- **YIN/YIN-FFT**: 高精度な基本周波数検出アルゴリズム
- **ライブラリ**: aubio（軽量で高速）
- **サンプリングレート**: 44100 Hz（CD品質）
- **ホップサイズ**: 512サンプル

### 音程差の計算

セント（cent）単位で計算:

```
cents = 1200 × log₂(f₂ / f₁)
```

- 1200セント = 1オクターブ
- 100セント = 半音
- ±50セント = 許容範囲

### オクターブズレ検出

```
octave_diff = round(log₂(f₂ / f₁))
```

`|octave_diff| >= 1` の場合、警告を表示

## 🤝 コントリビューション

バグ報告、機能リクエスト、プルリクエストを歓迎します！

## 📄 ライセンス

MIT License

## 🙏 謝辞

- [aubio](https://aubio.org/) - 高精度なピッチ検出ライブラリ
- [sounddevice](https://python-sounddevice.readthedocs.io/) - オーディオI/O
- [matplotlib](https://matplotlib.org/) - データ可視化

## 📧 お問い合わせ

質問や提案がある場合は、GitHubのIssuesでお知らせください。

---

**楽しいカラオケライフを！** 🎵
