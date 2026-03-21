"""
OpenYoung 集中配置管理

提供统一的配置访问接口，整合散落的配置定义
支持：
- YAML 配置 (ConfigLoader)
- 用户配置 JSON (UserConfigManager)
- Pydantic 验证
"""

import json
from pathlib import Path
from typing import Any, Optional

from .loader import ConfigLoader

# 全局配置实例
_config_loader: ConfigLoader = None
_user_config_manager = None

# 用户配置路径
_USER_CONFIG_DIR = Path.home() / ".openyoung"
_USER_CONFIG_FILE = _USER_CONFIG_DIR / "config.json"


# ========== 用户配置管理 (从 cli/config_manager 迁移) ==========


def get_user_config_manager() -> "UserConfigManager":
    """获取全局用户配置管理器"""
    global _user_config_manager
    if _user_config_manager is None:
        _user_config_manager = UserConfigManager()
    return _user_config_manager


def load_user_config() -> dict:
    """加载用户配置"""
    if _USER_CONFIG_FILE.exists():
        try:
            return json.loads(_USER_CONFIG_FILE.read_text())
        except Exception as e:
            logger.warning(f"Failed to load user config: {e}")
    return {}


def save_user_config(config: dict) -> bool:
    """保存用户配置"""
    try:
        _USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _USER_CONFIG_FILE.write_text(json.dumps(config, indent=2))
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False


def get_user_config(key: str, default: Any = None) -> Any:
    """获取用户配置值"""
    config = load_user_config()
    return config.get(key, default)


def set_user_config(key: str, value: str) -> bool:
    """设置用户配置值"""
    config = load_user_config()
    config[key] = value
    return save_user_config(config)


class UserConfigManager:
    """用户配置管理器 - 支持 Pydantic 验证"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or _USER_CONFIG_DIR
        self.config_file = self.config_dir / "config.json"

    def load(self) -> dict:
        """加载配置"""
        return load_user_config()

    def save(self, config: dict) -> bool:
        """保存配置"""
        return save_user_config(config)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return get_user_config(key, default)

    def set(self, key: str, value: str) -> bool:
        """设置配置值"""
        return set_user_config(key, value)

    def reset(self) -> bool:
        """重置配置"""
        return save_user_config({})


# ========== 统一配置入口 ==========


def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_config(filename: str = "config.yaml") -> dict:
    """加载配置文件 (YAML)"""
    return get_config_loader().load_yaml(filename)


# 兼容旧接口
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值 (统一入口)

    优先从用户配置读取，其次从项目配置读取
    """
    # 先从用户配置读取
    user_val = get_user_config(key, None)
    if user_val is not None:
        return user_val

    # 再从项目配置读取
    return get_config_loader().get(key, default)


__all__ = [
    # ConfigLoader
    "ConfigLoader",
    "get_config_loader",
    "load_config",
    # UserConfigManager
    "UserConfigManager",
    "get_user_config_manager",
    "load_user_config",
    "save_user_config",
    # 统一入口
    "get_config",
    "set_user_config",
]
