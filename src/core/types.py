"""
YoungAgent Core Types - 对标 OpenCode 架构
版本: 1.0.0
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


# ============================================================================
# 2.1 Agent Mode
# ============================================================================


class AgentMode(Enum):
    """Agent 模式 - 对标 OpenCode"""

    PRIMARY = "primary"  # 主 Agent，直接与用户交互
    SUBAGENT = "subagent"  # 子 Agent，被主 Agent 调用
    ALL = "all"  # 两者皆可


# ============================================================================
# 2.2 Permission Action
# ============================================================================


class PermissionAction(Enum):
    """权限动作 - 对标 OpenCode"""

    ALLOW = "allow"  # 无需批准直接执行
    ASK = "ask"  # 提示用户确认
    DENY = "deny"  # 阻止执行


# ============================================================================
# 2.3 Agent Config
# ============================================================================


@dataclass
class PermissionRule:
    """权限规则"""

    tool_pattern: str  # 工具名模式（支持通配符）
    params_pattern: Optional[Dict[str, Any]] = None  # 参数模式
    action: PermissionAction = PermissionAction.ASK


@dataclass
class PermissionConfig:
    """权限配置"""

    _global: PermissionAction = PermissionAction.ASK
    rules: List[PermissionRule] = field(default_factory=list)
    confirm_message: str = "确认执行此操作?"


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str
    mode: AgentMode = AgentMode.PRIMARY

    # 模型配置
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    # 工具配置
    tools: List[str] = field(default_factory=list)

    # 权限配置
    permission: PermissionConfig = field(default_factory=PermissionConfig)

    # Flow Skill
    flow_skill: Optional[Any] = None

    # System Prompt
    system_prompt: str = "你是一个有帮助的AI助手。"


# ============================================================================
# 4.1 SubAgent Type
# ============================================================================


class SubAgentType(Enum):
    """预定义 SubAgent 类型 - 对标 OpenCode"""

    EXPLORE = "explore"  # 快速探索代码库（只读）
    GENERAL = "general"  # 通用任务处理
    SEARCH = "search"  # 复杂搜索任务
    BUILDER = "builder"  # 构建和执行
    REVIEWER = "reviewer"  # 代码审查
    EVAL = "eval"  # 评估任务


# ============================================================================
# 4.2 SubAgent Config
# ============================================================================


@dataclass
class SubAgentConfig:
    """SubAgent 轻量配置"""

    name: str
    type: SubAgentType
    description: str  # 必须：描述 SubAgent 用途
    model: str = "default"
    temperature: float = 0.7
    instructions: Optional[str] = None
    hidden: bool = False


# ============================================================================
# 5.1 Task Status
# ============================================================================


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# 5.2 Task
# ============================================================================


@dataclass
class Task:
    """任务"""

    id: str
    description: str
    input: str
    status: TaskStatus = TaskStatus.PENDING
    subagent_type: Optional[SubAgentType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 5.3 TaskDispatchParams
# ============================================================================


@dataclass
class TaskDispatchParams:
    """任务调度参数"""

    subagent_type: SubAgentType
    task_description: str
    context: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


# ============================================================================
# 6.1 Message Role
# ============================================================================


class MessageRole(Enum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# ============================================================================
# 6.2 Message
# ============================================================================


@dataclass
class Message:
    """消息"""

    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


# ============================================================================
# 7. Tool Definition
# ============================================================================


@dataclass
class Tool:
    """工具定义"""

    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
