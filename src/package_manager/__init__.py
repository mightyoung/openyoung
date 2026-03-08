"""
PackageManager - 包管理系统

功能模块:
- PackageManager: 核心包管理器（安装、卸载、列表）
- AgentRegistry: Agent 注册与发现
- ProviderManager: LLM Provider 管理
- DependencyResolver: 依赖解析
- DependencyInstaller: 依赖自动安装
- MCPLoader: MCP 服务器加载
- HooksLoader: Hook 加载器
"""

# 包管理核心
from .agent_io import AgentExporter, AgentImporter
from .dependency_installer import (
    DependencyInstaller,
    InstallResult,
    install_agent_dependencies,
)

# 依赖管理
from .dependency_resolver import (
    AgentDependency,
    DependencyInfo,
    DependencyResolver,
    resolve_agent_dependencies,
)
from .hooks_loader import HookConfig, HooksLoader
from .manager import PackageManager

# 扩展加载
from .mcp_loader import MCPLoader
from .provider import ProviderManager

# Agent 注册
from .registry import AgentRegistry, AgentSpec
from .storage import LLMProviderConfig, LockManager, PackageMetadata, PackageStorage

__all__ = [
    # 核心
    "PackageManager",
    "PackageStorage",
    "PackageMetadata",
    "LLMProviderConfig",
    "LockManager",
    "ProviderManager",
    # Agent 注册
    "AgentRegistry",
    "AgentSpec",
    "AgentExporter",
    "AgentImporter",
    # 扩展加载
    "MCPLoader",
    "HooksLoader",
    "HookConfig",
    # 依赖管理
    "DependencyResolver",
    "DependencyInfo",
    "AgentDependency",
    "resolve_agent_dependencies",
    "DependencyInstaller",
    "InstallResult",
    "install_agent_dependencies",
]
