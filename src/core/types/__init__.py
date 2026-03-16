"""
Core Types - Unified Type Definitions

This package provides centralized type definitions for the OpenYoung project.

Modules:
- agent: Agent-related types (AgentConfig, AgentMode, PermissionConfig, etc.)
- task: Task-related types (Task, TaskStatus, TaskDispatchParams)
- common: Common types (Message, MessageRole, Tool)
- evaluation: Evaluation types (MetricType, EvaluationDimension, etc.)

Usage:
    from src.core.types import AgentConfig, Task, MessageRole
    from src.core.types.agent import AgentMode, PermissionAction
    from src.core.types.task import TaskStatus
    from src.core.types.common import Message, Tool

Backward Compatibility:
    The old import path from src.core.types still works:
    from src.core.types import AgentConfig, Task, MessageRole
"""

# Agent types
from .agent import (
    AgentConfig,
    AgentMode,
    ExecutionConfig,
    FlowSkillType,
    PermissionAction,
    PermissionConfig,
    PermissionRule,
    SubAgentConfig,
    SubAgentType,
)

# Common types
from .common import (
    Message,
    MessageRole,
    Tool,
)

# Evaluation types (re-exports from metrics)
from .evaluation import (
    EvaluationDimension,
    MetricDefinition,
    MetricType,
)

# Task types
from .task import (
    Task,
    TaskDispatchParams,
    TaskStatus,
)

__all__ = [
    # Agent types
    "AgentConfig",
    "AgentMode",
    "ExecutionConfig",
    "FlowSkillType",
    "PermissionAction",
    "PermissionConfig",
    "PermissionRule",
    "SubAgentConfig",
    "SubAgentType",
    # Task types
    "Task",
    "TaskDispatchParams",
    "TaskStatus",
    # Common types
    "Message",
    "MessageRole",
    "Tool",
    # Evaluation types
    "EvaluationDimension",
    "MetricDefinition",
    "MetricType",
]
