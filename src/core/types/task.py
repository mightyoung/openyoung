"""
Core Types - Task Module

Task-related type definitions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .agent import SubAgentType


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


@dataclass
class TaskDispatchParams:
    """任务调度参数"""

    subagent_type: SubAgentType
    task_description: str
    context: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None
