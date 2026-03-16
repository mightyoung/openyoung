"""
Core Types - Agent Module

Agent-related type definitions
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentMode(Enum):
    """Agent 模式 - 对标 OpenCode"""

    PRIMARY = "primary"  # 主 Agent，直接与用户交互
    SUBAGENT = "subagent"  # 子 Agent，被主 Agent 调用
    ALL = "all"  # 两者皆可


class PermissionAction(Enum):
    """权限动作 - 对标 OpenCode"""

    ALLOW = "allow"  # 无需批准直接执行
    ASK = "ask"  # 提示用户确认
    DENY = "deny"  # 阻止执行


class FlowSkillType(Enum):
    """Flow Skill 类型"""

    DEVELOPMENT = "development"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    GENERAL = "general"


class SubAgentType(Enum):
    """预定义 SubAgent 类型 - 对标 OpenCode"""

    EXPLORE = "explore"  # 快速探索代码库（只读）
    GENERAL = "general"  # 通用任务处理
    SEARCH = "search"  # 复杂搜索任务
    BUILDER = "builder"  # 构建和执行
    REVIEWER = "reviewer"  # 代码审查
    EVAL = "eval"  # 评估任务


@dataclass
class ExecutionConfig:
    """执行配置 - 类型安全的执行参数"""

    max_tool_calls: int = 10
    timeout_seconds: int = 300
    checkpoint_enabled: bool = True
    retry_on_error: bool = True
    max_retries: int = 3


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
