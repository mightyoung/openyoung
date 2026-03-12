"""
OpenYoung 集中配置管理

提供统一的配置访问接口，整合散落的配置定义
"""

from .loader import ConfigLoader

# 全局配置实例
_config_loader: ConfigLoader = None


def get_config_loader() -> ConfigLoader:
    """获取全局配置加载器"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_config(filename: str = "config.yaml") -> dict:
    """加载配置文件"""
    return get_config_loader().load_yaml(filename)


__all__ = [
    "ConfigLoader",
    "get_config_loader",
    "load_config",
]
