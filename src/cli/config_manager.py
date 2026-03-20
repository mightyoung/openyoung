"""
Config Manager - 配置管理模块

⚠️ DEPRECATED: 此模块已弃用
功能已迁移到 src/config/ 模块

保留仅用于向后兼容
"""

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError

# 使用统一的配置入口
from src.config import (
    UserConfigManager,
    get_user_config,
    load_user_config,
    save_user_config,
    set_user_config,
)


# 兼容函数
def load_config() -> dict:
    """加载配置 (兼容旧接口)"""
    return load_user_config()


def save_config(config: dict) -> bool:
    """保存配置 (兼容旧接口)"""
    return save_user_config(config)


def get_config(key: str, default: Any = None) -> Any:
    """获取配置值 (兼容旧接口)"""
    return get_user_config(key, default)


def set_config(key: str, value: str) -> bool:
    """设置配置值 (兼容旧接口)"""
    return set_user_config(key, value)


# 导入配置模型
from src.cli.config_models import (
    AgentConfigModel,
    AppConfig,
    LLMConfig,
)

# 保持路径兼容
_CONFIG_DIR = Path.home() / ".openyoung"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


# 保留 ConfigManager 类，但内部使用新实现


class ConfigManager(UserConfigManager):
    """配置管理器类 - 支持 Pydantic 验证"""

    def __init__(self, config_dir: Optional[Path] = None):
        super().__init__(config_dir)
        # 兼容旧接口
        self.config_dir = config_dir or _CONFIG_DIR
        self.config_file = self.config_dir / "config.json"


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
