"""
YoungAgent Core Types - 对标 OpenCode 架构
版本: 1.0.0
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
# 2.4 Execution Config (增强类型安全)
# ============================================================================


@dataclass
class ExecutionConfig:
    """执行配置 - 类型安全的执行参数"""

    max_tool_calls: int = 10
    timeout_seconds: int = 300
    checkpoint_enabled: bool = True
    retry_on_error: bool = True
    max_retries: int = 3


# ============================================================================
# 2.5 Flow Skill Type
# 从 agent.py 导入（避免重复定义）
# ============================================================================
from src.core.types.agent import FlowSkillType, SubAgentType

# ============================================================================
# 2.3 Agent Config
# ============================================================================


@dataclass
class PermissionRule:
    """权限规则"""

    tool_pattern: str  # 工具名模式（支持通配符）
    params_pattern: dict[str, Any] | None = None  # 参数模式
    action: PermissionAction = PermissionAction.ASK


@dataclass
class PermissionConfig:
    """权限配置"""

    _global: PermissionAction = PermissionAction.ASK
    rules: list[PermissionRule] = field(default_factory=list)
    confirm_message: str = "确认执行此操作?"


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str
    mode: AgentMode = AgentMode.PRIMARY

    # 模型配置 - 支持环境变量覆盖，默认使用 deepseek（免费额度多）
    model: str = os.getenv("OPENYOUNG_MODEL", "deepseek-chat")
    temperature: float = 0.7
    max_tokens: int | None = None

    # 工具配置
    tools: list[str] = field(default_factory=list)

    # 权限配置
    permission: PermissionConfig = field(default_factory=PermissionConfig)

    # Flow Skill - 使用类型安全的 FlowSkillType
    flow_skill: FlowSkillType | None = None

    # System Prompt
    system_prompt: str = "你是一个有帮助的AI助手。"

    # Skills - 参考 Anthropic SKILL.md 格式
    skills: list[str] = field(default_factory=list)

    # Always Skills - 自动加载的技能（不需用户触发）
    always_skills: list[str] = field(default_factory=list)

    # SubAgents - 内置子代理配置
    sub_agents: list["SubAgentConfig"] = field(default_factory=list)

    # 数据目录 - 存储数据中心、评估结果等
    data_dir: str | None = None

    # 执行配置 - 使用类型安全的 ExecutionConfig
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)


# ============================================================================
# 4.1 SubAgent Type
# ============================================================================


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
    instructions: str | None = None
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
    subagent_type: SubAgentType | None = None
    custom_subagent: str | None = None  # 自定义 SubAgent 名称
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 5.3 TaskDispatchParams
# ============================================================================


@dataclass
class TaskDispatchParams:
    """任务调度参数"""

    subagent_type: SubAgentType
    task_description: str
    context: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


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
    name: str | None = None
    tool_call_id: str | None = None


# ============================================================================
# 7. Tool Definition
# ============================================================================


@dataclass
class Tool:
    """工具定义"""

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
