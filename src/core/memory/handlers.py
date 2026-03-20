"""
Memory Event Handlers - 记忆系统事件处理器

处理记忆相关事件:
- 任务事件触发 Working Memory 操作
- Checkpoint 自动保存
- 知识沉淀触发
"""

import logging
from typing import Any, Optional

from ..events import Event, EventBus, EventType, get_event_bus
from .events import MemoryEventType
from .facade import MemoryFacade, get_memory_facade

logger = logging.getLogger(__name__)


class MemoryEventHandler:
    """记忆事件处理器

    监听 EventBus 上的事件并执行相应的记忆操作:
    - TASK_STARTED: 创建 Working Memory 上下文
    - TASK_COMPLETED: 触发知识沉淀
    - 任务切换: 自动保存 Checkpoint
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_event_bus()
        self.memory_facade: Optional[MemoryFacade] = None
        self._handlers_registered = False

    async def initialize(self) -> None:
        """初始化并注册事件处理器"""
        if self._handlers_registered:
            return

        self.memory_facade = await get_memory_facade()

        # 注册事件监听
        await self._register_handlers()
        self._handlers_registered = True
        logger.info("MemoryEventHandler initialized and handlers registered")

    async def _register_handlers(self) -> None:
        """注册所有事件处理器"""

        # 任务事件
        self.event_bus.subscribe(EventType.TASK_STARTED, self.on_task_started)
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self.on_task_completed)
        self.event_bus.subscribe(EventType.TASK_FAILED, self.on_task_failed)
        self.event_bus.subscribe(EventType.TASK_CANCELLED, self.on_task_cancelled)

        # Checkpoint 相关
        self.event_bus.subscribe(EventType.TASK_SWITCHED, self.on_task_switched)

        logger.debug("Memory event handlers registered")

    # ====================
    # 任务事件处理
    # ====================

    async def on_task_started(self, event: Event) -> None:
        """处理任务开始事件 - 创建 Working Memory 上下文"""
        try:
            task_id = event.data.get("task_id")
            task_description = event.data.get("task_description", "")

            if task_id and self.memory_facade:
                # 使用 Working Memory 创建上下文
                working = self.memory_facade.working_memory
                if working:
                    await working.create_context(
                        task_id=task_id,
                        task_description=task_description,
                    )
                    logger.info(f"Created working context for task: {task_id}")

        except Exception as e:
            logger.error(f"Error handling TASK_STARTED: {e}")

    async def on_task_completed(self, event: Event) -> None:
        """处理任务完成事件 - 可能触发知识沉淀"""
        try:
            task_id = event.data.get("task_id")
            result = event.data.get("result")

            if task_id and self.memory_facade and result:
                # 可选: 将任务结果存储到 Semantic Memory
                # await self._store_task_result(task_id, result)
                logger.info(f"Task completed: {task_id}")

        except Exception as e:
            logger.error(f"Error handling TASK_COMPLETED: {e}")

    async def on_task_failed(self, event: Event) -> None:
        """处理任务失败事件 - 保存错误信息到 Checkpoint"""
        try:
            task_id = event.data.get("task_id")
            error = event.data.get("error")

            if task_id:
                logger.warning(f"Task failed: {task_id}, error: {error}")

        except Exception as e:
            logger.error(f"Error handling TASK_FAILED: {e}")

    async def on_task_cancelled(self, event: Event) -> None:
        """处理任务取消事件"""
        try:
            task_id = event.data.get("task_id")
            if task_id:
                logger.info(f"Task cancelled: {task_id}")

        except Exception as e:
            logger.error(f"Error handling TASK_CANCELLED: {e}")

    async def on_task_switched(self, event: Event) -> None:
        """处理任务切换事件 - 自动保存 Checkpoint"""
        try:
            from_task = event.data.get("from_task")
            to_task = event.data.get("to_task")
            agent_id = event.data.get("agent_id")

            if from_task and agent_id and self.memory_facade:
                # 获取当前任务状态
                working = self.memory_facade.working_memory
                if working:
                    context = working.get_context(from_task)
                    if context:
                        # 自动保存 Checkpoint
                        state = {
                            "task_id": from_task,
                            "messages": context.messages,
                            "variables": context.variables,
                            "metadata": {"switched_to": to_task},
                        }
                        await self.memory_facade.save_checkpoint(
                            agent_id=agent_id,
                            state=state,
                            metadata={"auto": True, "reason": "task_switch"},
                        )
                        logger.info(f"Auto-saved checkpoint for task: {from_task}")

        except Exception as e:
            logger.error(f"Error handling TASK_SWITCHED: {e}")

    # ====================
    # 内部方法
    # ====================

    async def _store_task_result(self, task_id: str, result: Any) -> None:
        """存储任务结果到 Semantic Memory"""
        if not self.memory_facade:
            return

        # 提取关键信息存储
        content = str(result)
        if len(content) > 1000:
            content = content[:1000] + "..."

        await self.memory_facade.store(
            content=content,
            layer="semantic",  # MemoryLayer.SEMANTIC
            category="task_result",
            tags=["task", task_id],
            metadata={"task_id": task_id},
        )


# ====================
# 全局处理器实例
# ====================

_memory_handler: Optional[MemoryEventHandler] = None


async def get_memory_handler() -> MemoryEventHandler:
    """获取全局 MemoryEventHandler 实例"""
    global _memory_handler
    if _memory_handler is None:
        _memory_handler = MemoryEventHandler()
        await _memory_handler.initialize()
    return _memory_handler


async def initialize_memory_events() -> None:
    """初始化记忆事件系统 - 供启动时调用"""
    await get_memory_handler()
    logger.info("Memory event system initialized")
