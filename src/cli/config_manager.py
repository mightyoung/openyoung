"""
Config Manager - 配置管理模块

从 main.py 提取的配置管理功能。
支持 Pydantic 配置验证。
"""

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

# 导入配置模型
from src.cli.config_models import (
    AgentConfigModel,
    AppConfig,
    LLMConfig,
)

# 配置路径
_CONFIG_DIR = Path.home() / ".openyoung"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def load_config() -> dict:
    """加载配置"""
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}


def save_config(config: dict) -> bool:
    """保存配置"""
    try:
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _CONFIG_FILE.write_text(json.dumps(config, indent=2))
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值"""
    config = load_config()
    return config.get(key, default)


def set_config(key: str, value: str) -> bool:
    """设置配置值"""
    config = load_config()
    config[key] = value
    return save_config(config)


class ConfigManager:
    """配置管理器类 - 支持 Pydantic 验证"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or _CONFIG_DIR
        self.config_file = self.config_dir / "config.json"

    def load(self) -> dict:
        """加载配置"""
        return load_config()

    def save(self, config: dict) -> bool:
        """保存配置"""
        return save_config(config)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return get_config(key, default)

    def set(self, key: str, value: str) -> bool:
        """设置配置值"""
        return set_config(key, value)

    def reset(self) -> bool:
        """重置配置"""
        return save_config({})

    # ========== Pydantic 验证方法 ==========

    def validate_app_config(self) -> Optional[AppConfig]:
        """验证应用配置"""
        config = self.load()
        try:
            return AppConfig(**config)
        except ValidationError as e:
            print(f"Config validation error: {e}")
            return None

    def validate_agent_config(self, agent_config: dict) -> Optional[AgentConfigModel]:
        """验证 Agent 配置"""
        try:
            return AgentConfigModel(**agent_config)
        except ValidationError as e:
            print(f"Agent config validation error: {e}")
            return None

    def validate_llm_config(self, llm_config: dict) -> Optional[LLMConfig]:
        """验证 LLM 配置"""
        try:
            return LLMConfig(**llm_config)
        except ValidationError as e:
            print(f"LLM config validation error: {e}")
            return None

    def get_validated_config(self) -> AppConfig:
        """获取验证后的配置，如果无效则返回默认配置"""
        validated = self.validate_app_config()
        if validated is None:
            # 返回默认配置
            return AppConfig()
        return validated
