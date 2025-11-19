@echo off
chcp 65001 >nul
echo =========================================
echo カラオケピッチアナライザー セットアップ
echo =========================================
echo.

REM Pythonバージョンチェック
echo Pythonバージョンを確認中...
python --version
if errorlevel 1 (
    echo エラー: Pythonが見つかりません。
    echo Python 3.7以上をインストールしてください。
    pause
    exit /b 1
)
echo.

REM 仮想環境の作成
echo 仮想環境を作成中...
if exist venv\ (
    echo 仮想環境は既に存在します。
) else (
    python -m venv venv
    echo ✓ 仮想環境を作成しました。
)
echo.

REM 仮想環境の有効化
echo 仮想環境を有効化中...
call venv\Scripts\activate.bat
echo ✓ 仮想環境を有効化しました。
echo.

REM 依存パッケージのインストール
echo 依存パッケージをインストール中...
python -m pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ✗ パッケージのインストール中にエラーが発生しました。
    echo   詳細はREADME.mdのトラブルシューティングを参照してください。
    pause
    exit /b 1
)

echo.
echo ✓ 依存パッケージのインストールが完了しました！
echo.
echo =========================================
echo セットアップ完了！
echo =========================================
echo.
echo 実行方法:
echo   1. 仮想環境を有効化: venv\Scripts\activate
echo   2. プログラムを実行:
echo      - コンソールモード: python main.py
echo      - Webモード: python web_app.py
echo.
echo 詳細はREADME.mdを参照してください。
echo.
pause
