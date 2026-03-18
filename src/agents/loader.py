"""
Agent Loader - Agent配置加载器

这个模块从 src/cli/loader.py 迁移过来，统一在 agents 模块中管理。

注意: 旧的导入路径仍然可用 (src.cli.loader.AgentLoader)
"""

# 导出 AgentLoader - 兼容旧导入
from src.cli.loader import AgentLoader

__all__ = ["AgentLoader"]
