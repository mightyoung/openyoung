"""
YoungAgent Memory Package

分层记忆系统:
- Working Memory (L0): 当前任务状态
- Semantic Memory (L2): LLM 推理知识检索
- Checkpoint: Agent 状态快照
- Memory Facade: 统一入口
- Memory Handlers: EventBus 集成
"""

from .working import (
    WorkingMemory,
    TaskContext,
    get_working_memory,
    set_working_memory,
)

from .semantic import (
    SemanticMemory,
    KnowledgeEntry,
    RetrievalResult,
    get_semantic_memory,
    set_semantic_memory,
)

from .checkpoint_integration import (
    agent_state_to_checkpoint_state,
    checkpoint_state_to_agent_state,
    save_agent_state,
    load_agent_state,
    restore_from_latest,
    CheckpointWorkflowMixin,
)

from .facade import (
    MemoryFacade,
    MemoryLayer,
    MemoryQuery,
    MemoryStore,
    get_memory_facade,
    set_memory_facade,
)

from .events import (
    MemoryEventType,
    EVENT_TO_LAYER,
)

from .handlers import (
    MemoryEventHandler,
    get_memory_handler,
    initialize_memory_events,
)

# Legacy imports from impl (直接导入，不再通过bridge)
from .impl.vector_store import VectorStore
from .impl.checkpoint import CheckpointManager

__all__ = [
    # Working Memory
    "WorkingMemory",
    "TaskContext",
    "get_working_memory",
    "set_working_memory",
    # Semantic Memory
    "SemanticMemory",
    "KnowledgeEntry",
    "RetrievalResult",
    "get_semantic_memory",
    "set_semantic_memory",
    # Checkpoint Integration
    "agent_state_to_checkpoint_state",
    "checkpoint_state_to_agent_state",
    "save_agent_state",
    "load_agent_state",
    "restore_from_latest",
    "CheckpointWorkflowMixin",
    # Memory Facade
    "MemoryFacade",
    "MemoryLayer",
    "MemoryQuery",
    "MemoryStore",
    "get_memory_facade",
    "set_memory_facade",
    # Memory Events
    "MemoryEventType",
    "EVENT_TO_LAYER",
    # Memory Handlers
    "MemoryEventHandler",
    "get_memory_handler",
    "initialize_memory_events",
    # Legacy (从 impl 直接导入)
    "VectorStore",
    "CheckpointManager",
]
