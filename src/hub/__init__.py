"""
Hub - Agent 生命周期管理模块

按功能领域组织的子模块：
- discover: Agent 发现与检索
- evaluate: Agent 评估
- badge: Badge 徽章系统
- intent: 意图分析
- registry: Agent 注册中心
- mcp: MCP 工具集成
- hooks: Hooks 扩展
- storage: 存储抽象 (待完善)
- import: 导入功能
- version: 版本管理
- io: 输入输出
- compare: Agent 比较
- subagent: 子 Agent
- template: 模板
- dependency: 依赖管理
- provider: 提供商

保持向后兼容：通过 package_manager 模块导出。
"""

# 发现与检索
try:
    from .discover import AgentRetriever
except ImportError:
    AgentRetriever = None

# 评估
try:
    from .evaluate import AgentEvaluator
except ImportError:
    AgentEvaluator = None

# Badge 系统
try:
    from .badge import BadgeSystem
except ImportError:
    BadgeSystem = None

# 意图分析
try:
    from .intent import IntentAnalyzer
except ImportError:
    IntentAnalyzer = None

# 注册中心
try:
    from .registry import AgentRegistry, AgentSpec
except ImportError:
    AgentRegistry = None
    AgentSpec = None

# MCP 集成
try:
    from .mcp import (
        MCPLoader,
        MCPServerConfig,
        MCPServerManager,
    )
except ImportError:
    MCPServerManager = None
    MCPServerConfig = None
    MCPLoader = None

# Hooks
try:
    from .hooks import HooksLoader
except ImportError:
    HooksLoader = None

# 存储 (需要从 package_manager 迁移)
try:
    from .storage import Storage
except ImportError:
    Storage = None

# 导入
try:
    from .import_ import ImportManager
except ImportError:
    ImportManager = None

# 版本管理
try:
    from .version import VersionManager
except ImportError:
    VersionManager = None

# IO
try:
    from .io import AgentExporter, AgentImporter, AgentIO
except ImportError:
    AgentIO = None
    AgentExporter = None
    AgentImporter = None

# 比较
try:
    from .compare import AgentComparer
except ImportError:
    AgentComparer = None

# 子 Agent
try:
    from .subagent import SubAgentRegistry
except ImportError:
    SubAgentRegistry = None

# 模板
try:
    from .template import TemplateRegistry
except ImportError:
    TemplateRegistry = None

# 依赖
try:
    from .dependency import DependencyInstaller, DependencyResolver
except ImportError:
    DependencyResolver = None
    DependencyInstaller = None

# 提供商
try:
    from .provider import Provider
except ImportError:
    Provider = None

# 版本
__version__ = "0.1.0"

__all__ = [
    # 发现
    "AgentRetriever",
    # 评估
    "AgentEvaluator",
    # Badge
    "BadgeSystem",
    # 意图
    "IntentAnalyzer",
    # 注册
    "AgentRegistry",
    "AgentSpec",
    # MCP
    "MCPServerManager",
    "MCPServerConfig",
    "MCPLoader",
    # Hooks
    "HooksLoader",
    # 存储
    "Storage",
    # 导入
    "ImportManager",
    # 版本
    "VersionManager",
    # IO
    "AgentIO",
    "AgentExporter",
    "AgentImporter",
    # 比较
    "AgentComparer",
    # 子 Agent
    "SubAgentRegistry",
    # 模板
    "TemplateRegistry",
    # 依赖
    "DependencyResolver",
    "DependencyInstaller",
    # 提供商
    "Provider",
]
