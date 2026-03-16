"""
Collaboration Module - Agent协作模块

提供:
- MultiAgentCrew: 多Agent团队
- TaskOrchestrator: 任务编排器
- TeamMemory: 团队共享记忆
"""

from .crew import (
    AgentRole,
    AgentSpec,
    BaseAgent,
    CrewResult,
    MultiAgentCrew,
    ProcessType,
    TaskDefinition,
    TaskResult,
    create_crew,
)
from .orchestrator import (
    AgentState,
    DistributedOrchestrator,
    QueuedTask,
    QueueStrategy,
    TaskOrchestrator,
    TaskPriority,
)
from .team_memory import (
    ConflictResolver,
    MemoryEntry,
    SharedContext,
    TeamMemory,
)

__all__ = [
    # Crew
    "MultiAgentCrew",
    "BaseAgent",
    "AgentSpec",
    "AgentRole",
    "TaskDefinition",
    "TaskResult",
    "CrewResult",
    "ProcessType",
    "create_crew",
    # Orchestrator
    "TaskOrchestrator",
    "DistributedOrchestrator",
    "AgentState",
    "QueuedTask",
    "QueueStrategy",
    "TaskPriority",
    # Team Memory
    "TeamMemory",
    "SharedContext",
    "ConflictResolver",
    "MemoryEntry",
]
