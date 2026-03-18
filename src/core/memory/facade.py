"""
Memory Facade - 统一记忆入口

提供统一的记忆访问接口，自动路由到合适的记忆层:
- Working Memory (L0): 当前任务状态
- Semantic Memory (L2): 知识检索
- Checkpoint: 状态快照
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .working import WorkingMemory, TaskContext, get_working_memory
from .semantic import SemanticMemory, KnowledgeEntry, RetrievalResult, get_semantic_memory
from .checkpoint_integration import (
    AgentCheckpoint,
    save_agent_state,
    load_agent_state,
    restore_from_latest,
)

logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """记忆层类型"""
    WORKING = "working"  # L0: 当前任务状态
    SEMANTIC = "semantic"  # L2: 知识检索
    CHECKPOINT = "checkpoint"  # Agent 状态快照


@dataclass
class MemoryQuery:
    """记忆查询"""
    query: str
    layer: Optional[MemoryLayer] = None  # 指定层，None 表示自动
    context: Optional[dict[str, Any]] = None
    limit: int = 5


@dataclass
class MemoryStore:
    """记忆存储"""
    content: str
    layer: MemoryLayer
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class MemoryFacade:
    """Memory Facade - 统一记忆入口

    提供统一的 API 访问所有记忆层:
    - retrieve(): 查询记忆
    - store(): 存储记忆
    - checkpoint(): 保存/恢复状态
    """

    def __init__(
        self,
        working_memory: Optional[WorkingMemory] = None,
        semantic_memory: Optional[SemanticMemory] = None,
    ):
        self.working_memory = working_memory
        self.semantic_memory = semantic_memory
        self._initialized = False

    async def initialize(self) -> None:
        """初始化所有记忆层"""
        if self._initialized:
            return

        # 初始化 Working Memory
        if self.working_memory is None:
            self.working_memory = get_working_memory()

        # 初始化 Semantic Memory
        if self.semantic_memory is None:
            self.semantic_memory = await get_semantic_memory()

        self._initialized = True
        logger.info("MemoryFacade initialized with all layers")

    # ====================
    # 检索 API
    # ====================

    async def retrieve(
        self,
        query: str,
        layer: Optional[MemoryLayer] = None,
        context: Optional[dict[str, Any]] = None,
        limit: int = 5,
    ) -> list[Any]:
        """检索记忆

        Args:
            query: 查询内容
            layer: 指定记忆层，None 表示自动路由
            context: 上下文信息
            limit: 返回数量

        Returns:
            检索结果列表
        """
        await self._ensure_initialized()

        # 自动路由
        if layer is None:
            layer = self._auto_route(query)

        if layer == MemoryLayer.WORKING:
            return await self._retrieve_working(query, limit)
        elif layer == MemoryLayer.SEMANTIC:
            return await self._retrieve_semantic(query, context, limit)
        else:
            logger.warning(f"Unknown layer: {layer}, falling back to semantic")
            return await self._retrieve_semantic(query, context, limit)

    def _auto_route(self, query: str) -> MemoryLayer:
        """自动路由到合适的记忆层

        规则:
        - 任务相关关键词 → Working Memory
        - 知识/概念/问题 → Semantic Memory
        """
        query_lower = query.lower()

        # 工作记忆关键词
        working_keywords = ["task", "context", "当前", "任务", "状态", "variable", "message"]
        if any(kw in query_lower for kw in working_keywords):
            return MemoryLayer.WORKING

        # 默认走语义记忆
        return MemoryLayer.SEMANTIC

    async def _retrieve_working(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """从 Working Memory 检索"""
        if not self.working_memory:
            return []

        # 获取当前任务上下文
        current = self.working_memory.get_current_context()
        if current:
            return [{
                "layer": MemoryLayer.WORKING.value,
                "task_id": current.task_id,
                "task_description": current.task_description,
                "messages": current.messages,
                "variables": current.variables,
            }]

        return []

    async def _retrieve_semantic(
        self,
        query: str,
        context: Optional[dict[str, Any]],
        limit: int,
    ) -> list[RetrievalResult]:
        """从 Semantic Memory 检索"""
        if not self.semantic_memory:
            return []

        return await self.semantic_memory.retrieve(
            query=query,
            context=context,
            limit=limit,
        )

    # ====================
    # 存储 API
    # ====================

    async def store(
        self,
        content: str,
        layer: MemoryLayer = MemoryLayer.SEMANTIC,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """存储记忆

        Args:
            content: 记忆内容
            layer: 记忆层
            category: 分类 (Semantic Memory 用)
            tags: 标签 (Semantic Memory 用)
            metadata: 元数据

        Returns:
            存储 ID
        """
        await self._ensure_initialized()

        if layer == MemoryLayer.WORKING:
            return await self._store_working(content, metadata)
        elif layer == MemoryLayer.SEMANTIC:
            return await self._store_semantic(content, category, tags, metadata)
        else:
            raise ValueError(f"Unsupported layer for store: {layer}")

    async def _store_working(
        self,
        content: str,
        metadata: Optional[dict[str, Any]],
    ) -> str:
        """存储到 Working Memory"""
        if not self.working_memory:
            return ""

        # 解析 content 作为变量设置
        if metadata and "task_id" in metadata:
            task_id = metadata["task_id"]
            key = metadata.get("key", "content")
            value = metadata.get("value", content)
            self.working_memory.set_variable(task_id, key, value)
            return f"{task_id}:{key}"

        return ""

    async def _store_semantic(
        self,
        content: str,
        category: Optional[str],
        tags: Optional[list[str]],
        metadata: Optional[dict[str, Any]],
    ) -> str:
        """存储到 Semantic Memory"""
        if not self.semantic_memory:
            return ""

        return await self.semantic_memory.store(
            content=content,
            category=category or "general",
            tags=tags,
            metadata=metadata or {},
        )

    # ====================
    # Checkpoint API
    # ====================

    async def save_checkpoint(
        self,
        agent_id: str,
        state: dict[str, Any],
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """保存检查点

        Args:
            agent_id: Agent ID
            state: Agent 状态
            metadata: 额外元数据

        Returns:
            checkpoint_id
        """
        await self._ensure_initialized()
        return await save_agent_state(agent_id, state, metadata)

    async def load_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[dict[str, Any]]:
        """加载检查点

        Args:
            checkpoint_id: 检查点 ID

        Returns:
            Agent 状态
        """
        await self._ensure_initialized()
        return await load_agent_state(checkpoint_id)

    async def restore_latest(
        self,
        agent_id: str,
    ) -> Optional[dict[str, Any]]:
        """恢复到最新检查点

        Args:
            agent_id: Agent ID

        Returns:
            Agent 状态
        """
        await self._ensure_initialized()
        return await restore_from_latest(agent_id)

    # ====================
    # 内部方法
    # ====================

    async def _ensure_initialized(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            await self.initialize()


# ====================
# 全局实例
# ====================

_memory_facade_instance: Optional[MemoryFacade] = None


async def get_memory_facade() -> MemoryFacade:
    """获取全局 MemoryFacade 实例"""
    global _memory_facade_instance
    if _memory_facade_instance is None:
        _memory_facade_instance = MemoryFacade()
        await _memory_facade_instance.initialize()
    return _memory_facade_instance


def set_memory_facade(facade: MemoryFacade) -> None:
    """设置全局 MemoryFacade 实例"""
    global _memory_facade_instance
    _memory_facade_instance = facade
