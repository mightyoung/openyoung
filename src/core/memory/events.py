"""
Memory Events - 记忆系统事件定义

定义记忆系统相关的事件类型，供 EventBus 使用
"""

from enum import Enum


class MemoryEventType(Enum):
    """记忆系统事件类型"""

    # Working Memory 事件
    CONTEXT_CREATED = "memory:context_created"
    CONTEXT_UPDATED = "memory:context_updated"
    CONTEXT_SWITCHED = "memory:context_switched"
    CONTEXT_DELETED = "memory:context_deleted"

    # Semantic Memory 事件
    KNOWLEDGE_STORED = "memory:knowledge_stored"
    KNOWLEDGE_RETRIEVED = "memory:knowledge_retrieved"
    KNOWLEDGE_ACCESSED = "memory:knowledge_accessed"

    # Checkpoint 事件
    CHECKPOINT_SAVED = "memory:checkpoint_saved"
    CHECKPOINT_LOADED = "memory:checkpoint_loaded"
    CHECKPOINT_RESTORED = "memory:checkpoint_restored"
    CHECKPOINT_DELETED = "memory:checkpoint_deleted"

    # 系统事件
    MEMORY_INITIALIZED = "memory:initialized"
    MEMORY_ERROR = "memory:error"


# 事件到记忆层的映射
EVENT_TO_LAYER = {
    # Working Memory
    MemoryEventType.CONTEXT_CREATED: "working",
    MemoryEventType.CONTEXT_UPDATED: "working",
    MemoryEventType.CONTEXT_SWITCHED: "working",
    MemoryEventType.CONTEXT_DELETED: "working",
    # Semantic Memory
    MemoryEventType.KNOWLEDGE_STORED: "semantic",
    MemoryEventType.KNOWLEDGE_RETRIEVED: "semantic",
    MemoryEventType.KNOWLEDGE_ACCESSED: "semantic",
    # Checkpoint
    MemoryEventType.CHECKPOINT_SAVED: "checkpoint",
    MemoryEventType.CHECKPOINT_LOADED: "checkpoint",
    MemoryEventType.CHECKPOINT_RESTORED: "checkpoint",
    MemoryEventType.CHECKPOINT_DELETED: "checkpoint",
    # System
    MemoryEventType.MEMORY_INITIALIZED: "system",
    MemoryEventType.MEMORY_ERROR: "system",
}
