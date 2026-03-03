"""
PackageManager - 包管理系统

轻量级方案: 使用 pip + 文件夹 + YAML
"""

# 轻量级注册中心 (推荐)
from .registry import AgentRegistry, AgentSpec

# 完整包管理器 (保留，向后兼容)
from .manager import PackageManager
from .storage import PackageStorage, PackageMetadata, LLMProviderConfig, LockManager
from .provider import ProviderManager

__all__ = [
    # 轻量级 (推荐)
    "AgentRegistry",
    "AgentSpec",
    # 完整版 (向后兼容)
    "PackageManager",
    "PackageStorage",
    "PackageMetadata",
    "LLMProviderConfig",
    "LockManager",
    "ProviderManager",
]
