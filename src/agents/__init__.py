"""
YoungAgent Package
"""

from .base import (
    AgentConfig,
    AgentContext,
    AgentResult,
    AgentState,
    BaseAgent,
    SimpleAgent,
)
from .dispatcher import TaskDispatcher

# Mixins - 可组合的 Agent 功能
from .mixins import (
    AgentToolsMixin,
    AgentMemoryMixin,
    AgentHooksMixin,
    AgentExceptionMixin,
)

# Protocol definitions for dependency injection
from .protocols import (
    ICheckpointManager,
    IClient,
    IEvaluationHub,
    IHarness,
    IToolExecutor,
)
from .sub_agent import SubAgent
from .young_agent import PermissionEvaluator, YoungAgent

__all__ = [
    # Base classes
    "BaseAgent",
    "SimpleAgent",
    "AgentConfig",
    "AgentContext",
    "AgentResult",
    "AgentState",
    # Mixins
    "AgentToolsMixin",
    "AgentMemoryMixin",
    "AgentHooksMixin",
    "AgentExceptionMixin",
    # Core classes
    "YoungAgent",
    "SubAgent",
    "PermissionEvaluator",
    "TaskDispatcher",
    # Protocols
    "IClient",
    "IToolExecutor",
    "ICheckpointManager",
    "IEvaluationHub",
    "IHarness",
]
