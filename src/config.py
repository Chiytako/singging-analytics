"""
設定管理モジュール
ユーザー設定の保存・読み込みを管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """設定管理クラス"""

    DEFAULT_CONFIG = {
        'audio': {
            'sample_rate': 44100,
            'mic_device': None,
            'system_device': None,
            'use_system_audio': False,
        },
        'display': {
            'mode': 'detailed',  # 'simple', 'detailed', 'professional'
            'theme': 'dark',  # 'dark', 'light'
            'show_pitch_graph': True,
            'show_cents_gauge': True,
            'show_statistics': True,
            'update_interval': 100,  # ms
        },
        'analysis': {
            'confidence_threshold': 0.8,
            'history_size': 100,
            'octave_warning_threshold': 5,
        }
    }

    def __init__(self, config_file: Optional[str] = None):
        """
        初期化

        Args:
            config_file: 設定ファイルのパス（Noneの場合はデフォルトパス）
        """
        if config_file is None:
            # ホームディレクトリに設定ファイルを保存
            config_dir = Path.home() / '.karaoke_pitch_analyzer'
            config_dir.mkdir(exist_ok=True)
            self.config_file = config_dir / 'config.json'
        else:
            self.config_file = Path(config_file)

        self.config = self.DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """設定ファイルを読み込む"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # デフォルト設定とマージ
                    self._merge_config(self.config, loaded_config)
                print(f"設定を読み込みました: {self.config_file}")
            except Exception as e:
                print(f"設定ファイルの読み込みに失敗しました: {e}")
                print("デフォルト設定を使用します")

    def save(self):
        """設定ファイルに保存"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"設定を保存しました: {self.config_file}")
        except Exception as e:
            print(f"設定ファイルの保存に失敗しました: {e}")

    def _merge_config(self, default: Dict, loaded: Dict):
        """設定をマージ（ネストされた辞書に対応）"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        設定値を取得

        Args:
            section: セクション名（例: 'audio', 'display'）
            key: キー名
            default: デフォルト値

        Returns:
            設定値
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default

    def set(self, section: str, key: str, value: Any):
        """
        設定値を設定

        Args:
            section: セクション名
            key: キー名
            value: 値
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def get_section(self, section: str) -> Dict:
        """
        セクション全体を取得

        Args:
            section: セクション名

        Returns:
            セクションの辞書
        """
        return self.config.get(section, {})

    def update_section(self, section: str, updates: Dict):
        """
        セクションを更新

        Args:
            section: セクション名
            updates: 更新する値の辞書
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section].update(updates)

    def reset_to_default(self):
        """設定をデフォルトにリセット"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
