"""
Knowledge - 知识沉淀模块

整合 LearningsManager（文件存储）和 VectorStore（向量存储），
为 Heartbeat 提供统一的知识沉淀能力。

功能：
- 文件持久化：LearningsManager (错误日志、最佳实践)
- 向量检索：VectorStore (语义搜索)
- 事件集成：监听 EventBus 自动记录
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 延迟导入，避免循环依赖
_LearningsManager = None
_VectorStore = None


def _get_learnings_manager():
    """延迟获取 LearningsManager"""
    global _LearningsManager
    if _LearningsManager is None:
        try:
            from src.skills.learnings import LearningsManager
            _LearningsManager = LearningsManager
        except ImportError:
            logger.warning("LearningsManager not available")
    return _LearningsManager


def _get_vector_store():
    """延迟获取 VectorStore 类"""
    global _VectorStore
    if _VectorStore is None:
        try:
            from src.core.memory.impl.vector_store import VectorStore
            _VectorStore = VectorStore  # Return class, not instance
        except ImportError:
            logger.warning("VectorStore not available")
    return _VectorStore


class KnowledgeManager:
    """知识管理器 - 统一的知识沉淀接口

    整合文件存储和向量存储：
    - 文件存储：LearningsManager → LEARNINGS.md, ERRORS.md
    - 向量存储：VectorStore → 语义搜索
    """

    def __init__(
        self,
        workspace: Optional[Path] = None,
        learnings_manager=None,
        vector_store=None,
    ):
        self.workspace = workspace or Path.cwd()

        # LearningsManager
        self._learnings = learnings_manager
        if self._learnings is None:
            LM = _get_learnings_manager()
            if LM:
                self._learnings = LM(workspace=self.workspace)

        # VectorStore
        self._vector = vector_store
        if self._vector is None:
            VS = _get_vector_store()
            if VS:
                self._vector = VS()

    @property
    def learnings(self):
        """获取 LearningsManager"""
        return self._learnings

    @property
    def vector_store(self):
        """获取 VectorStore"""
        return self._vector

    # ============ 文件存储 API ============

    async def log_learning(
        self,
        title: str,
        description: str,
        tags: list[str] = None,
        context: dict = None,
    ):
        """记录学习"""
        if self._learnings:
            entry = await self._learnings.log_learning(
                title=title,
                description=description,
                tags=tags,
                context=context,
            )
            # 同时存入向量库
            await self._index_learning(entry)
            return entry
        return None

    async def log_error(
        self,
        error: Exception,
        context: dict,
        solution: str = None,
        priority=None,
    ):
        """记录错误"""
        if self._learnings:
            entry = await self._learnings.log_error(
                error=error,
                context=context,
                solution=solution,
                priority=priority,
            )
            # 同时存入向量库
            await self._index_learning(entry)
            return entry
        return None

    async def log_correction(
        self,
        correction: str,
        original_action: str,
        context: dict = None,
    ):
        """记录纠正"""
        if self._learnings:
            entry = await self._learnings.log_correction(
                correction=correction,
                original_action=original_action,
                context=context,
            )
            await self._index_learning(entry)
            return entry
        return None

    async def log_improvement(
        self,
        title: str,
        description: str,
        context: dict = None,
    ):
        """记录改进"""
        if self._learnings:
            entry = await self._learnings.log_improvement(
                title=title,
                description=description,
                context=context,
            )
            await self._index_learning(entry)
            return entry
        return None

    # ============ 向量存储 API ============

    async def _index_learning(self, entry):
        """将学习条目存入向量库"""
        if self._vector and entry:
            try:
                content = f"{entry.title}: {entry.description}"
                self._vector.add(
                    content=content,
                    namespace="knowledge",
                    tags=[entry.type.value] + (entry.tags or []),
                    importance=0.7 if entry.priority.value == "high" else 0.5,
                )
            except Exception as e:
                logger.warning(f"Failed to index learning: {e}")

    async def search(self, query: str, limit: int = 5):
        """语义搜索知识库"""
        if self._vector:
            try:
                return self._vector.search(
                    query=query,
                    namespace="knowledge",
                    limit=limit,
                )
            except Exception as e:
                logger.warning(f"Search error: {e}")
        return []

    # ============ Heartbeat 集成 API ============

    async def record_phase_result(
        self,
        phase: str,
        success: bool,
        message: str,
        data: dict = None,
    ):
        """记录心跳阶段结果"""
        if success:
            await self.log_learning(
                title=f"Heartbeat Phase: {phase}",
                description=message,
                tags=["heartbeat", phase, "success"],
                context=data or {},
            )
        else:
            # 失败记录为错误
            from src.skills.learnings import Priority

            await self.log_error(
                error=Exception(f"Heartbeat {phase} failed: {message}"),
                context={"phase": phase, **(data or {})},
                priority=Priority.MEDIUM,
            )

    async def record_heartbeat_cycle(
        self,
        phases: list[str],
        duration_ms: int,
        results: list[dict],
    ):
        """记录完整心跳周期"""
        success_count = sum(1 for r in results if r.get("success"))
        await self.log_learning(
            title=f"Heartbeat Cycle Complete",
            description=f"Completed {success_count}/{len(phases)} phases in {duration_ms}ms",
            tags=["heartbeat", "cycle"],
            context={
                "phases": phases,
                "results": results,
                "duration_ms": duration_ms,
            },
        )


# 全局实例
_knowledge_manager: Optional[KnowledgeManager] = None


def get_knowledge_manager() -> KnowledgeManager:
    """获取全局知识管理器"""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager


def set_knowledge_manager(manager: KnowledgeManager):
    """设置全局知识管理器"""
    global _knowledge_manager
    _knowledge_manager = manager
