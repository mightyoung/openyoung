"""
PackageManager - 包管理系统

功能模块:
- PackageManager: 核心包管理器（安装、卸载、列表）
- AgentRegistry: Agent 注册与发现
- ProviderManager: LLM Provider 管理
- MCPServerManager: MCP 服务器管理
- VersionManager: 版本管理
- HooksLoader: Hook 加载器
"""

# 包管理核心
from .hooks_loader import HookConfig, HooksLoader
from .manager import PackageManager

# MCP 服务器管理
from .mcp_manager import (
    AgentMCPLoader,
    MCPServerConfig,
    MCPServerManager,
    MCPConnectionResult,
    load_agent_with_mcps,
    load_agent_with_mcps_strict,
)

# 版本管理
from .version_manager import (
    AgentVersion,
    VersionError,
    VersionHistory,
    VersionManager,
    compare_versions,
    get_version_manager,
    parse_semver,
)

# 扩展加载
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
    # MCP 服务器管理
    "MCPServerManager",
    "MCPServerConfig",
    "MCPConnectionResult",
    "AgentMCPLoader",
    "load_agent_with_mcps",
    "load_agent_with_mcps_strict",
    # 版本管理
    "VersionManager",
    "VersionHistory",
    "VersionError",
    "AgentVersion",
    "parse_semver",
    "compare_versions",
    "get_version_manager",
    # 扩展加载
    "HooksLoader",
    "HookConfig",
]
