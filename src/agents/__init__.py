"""
YoungAgent Package
"""

# Agent adapters for EvalRunner compatibility
from .adapters import AgentAdapter, EvalAgent, adapt_subagent
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
    AgentExceptionMixin,
    AgentHooksMixin,
    AgentMemoryMixin,
    AgentToolsMixin,
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
    # Agent adapters
    "AgentAdapter",
    "EvalAgent",
    "adapt_subagent",
]
