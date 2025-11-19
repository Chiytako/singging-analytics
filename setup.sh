#!/bin/bash

# カラオケピッチアナライザー - セットアップスクリプト

echo "========================================="
echo "カラオケピッチアナライザー セットアップ"
echo "========================================="
echo ""

# Pythonバージョンチェック
echo "Pythonバージョンを確認中..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "検出されたPythonバージョン: $python_version"
echo ""

# 仮想環境の作成
echo "仮想環境を作成中..."
if [ -d "venv" ]; then
    echo "仮想環境は既に存在します。"
else
    python3 -m venv venv
    echo "✓ 仮想環境を作成しました。"
fi
echo ""

# 仮想環境の有効化
echo "仮想環境を有効化中..."
source venv/bin/activate
echo "✓ 仮想環境を有効化しました。"
echo ""

# 依存パッケージのインストール
echo "依存パッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 依存パッケージのインストールが完了しました！"
else
    echo ""
    echo "✗ パッケージのインストール中にエラーが発生しました。"
    echo "  詳細はREADME.mdのトラブルシューティングを参照してください。"
    exit 1
fi

echo ""
echo "========================================="
echo "セットアップ完了！"
echo "========================================="
echo ""
echo "実行方法:"
echo "  1. 仮想環境を有効化: source venv/bin/activate"
echo "  2. プログラムを実行:"
echo "     - コンソールモード: python main.py"
echo "     - Webモード: python web_app.py"
echo ""
echo "詳細はREADME.mdを参照してください。"
echo ""
