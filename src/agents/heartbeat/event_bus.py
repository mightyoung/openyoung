"""
Event Bus - 事件总线

实现发布-订阅模式的事件驱动架构。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """事件"""

    type: str
    data: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


# 事件处理器类型
EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """事件总线"""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._priority_subscribers: Dict[str, List[tuple[EventPriority, EventHandler]]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task: asyncio.Task = None

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """订阅事件"""
        if priority != EventPriority.NORMAL:
            if event_type not in self._priority_subscribers:
                self._priority_subscribers[event_type] = []
            self._priority_subscribers[event_type].append((priority, handler))
            # 按优先级排序
            self._priority_subscribers[event_type].sort(key=lambda x: x[0].value, reverse=True)
        else:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

        logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

        if event_type in self._priority_subscribers:
            self._priority_subscribers[event_type] = [
                (p, h) for p, h in self._priority_subscribers[event_type] if h != handler
            ]

    async def publish(self, event: Event):
        """发布事件"""
        await self._event_queue.put(event)
        logger.debug(f"Published event: {event.type}")

    async def publish_sync(self, event: Event):
        """同步发布事件（立即处理）"""
        await self._process_event(event)

    async def _process_event(self, event: Event):
        """处理单个事件"""
        # 先处理高优先级订阅者
        if event.type in self._priority_subscribers:
            for _, handler in self._priority_subscribers[event.type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

        # 再处理普通订阅者
        if event.type in self._subscribers:
            for handler in self._subscribers[event.type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

    async def _process_loop(self):
        """事件处理循环"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    async def start(self):
        """启动事件总线"""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus started")

    async def stop(self):
        """停止事件总线"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped")

    def is_running(self) -> bool:
        """检查是否运行中"""
        return self._running

    @property
    def queue_size(self) -> int:
        """获取队列大小"""
        return self._event_queue.qsize()


# 全局事件总线实例
_event_bus: EventBus = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# 预定义事件类型
class SystemEvents:
    """系统事件"""

    # Agent 事件
    TASK_STARTED = "task:started"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"

    # 经验事件
    EXPERIENCE_COLLECTED = "experience:collected"
    EXPERIENCE_STORED = "experience:stored"
    PATTERN_DETECTED = "pattern:detected"

    # 心跳事件
    HEARTBEAT_TICK = "heartbeat:tick"
    HEARTBEAT_PHASE = "heartbeat:phase"

    # 系统事件
    SYSTEM_START = "system:start"
    SYSTEM_STOP = "system:stop"
    ERROR = "system:error"
