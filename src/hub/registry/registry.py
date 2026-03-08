"""
Hub Registry Module - Agent 注册中心模块

这个模块是从 package_manager.registry 重新导出的，保持向后兼容。
"""

# 从 canonical 位置重新导出
from src.package_manager.registry import AgentRegistry, AgentSpec

__all__ = [
    "AgentSpec",
    "AgentRegistry",
]
