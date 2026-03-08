"""
Event Bus - 事件驱动架构

参考: Django signals, Node.js EventEmitter, Redis Pub/Sub
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""

    # Agent 生命周期
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"

    # 任务生命周期
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"

    # 评估
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_COMPLETED = "evaluation_completed"

    # 执行
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"

    # 错误
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    """事件"""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "system"

    def __post_init__(self):
        if not isinstance(self.type, EventType):
            self.type = EventType(self.type)


class EventBus:
    """事件总线

    提供发布-订阅模式，解耦模块间通信
    """

    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._async_subscribers: dict[EventType, list[Callable]] = {}
        self._event_history: list[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, handler: Callable):
        """订阅事件 (同步处理)"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")

    def subscribe_async(self, event_type: EventType, handler: Callable):
        """订阅事件 (异步处理)"""
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(handler)
        logger.debug(f"Subscribed async {handler.__name__} to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    def publish(self, event: Event):
        """发布事件 (同步)"""
        # 记录历史
        self._record_event(event)

        # 同步处理
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def publish_async(self, event: Event):
        """发布事件 (异步)"""
        # 记录历史
        self._record_event(event)

        # 同步处理
        handlers = self._subscribers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

        # 异步处理
        async_handlers = self._async_subscribers.get(event.type, [])
        for handler in async_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Async event handler error: {e}")

    def _record_event(self, event: Event):
        """记录事件到历史"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

    def get_history(
        self,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """获取事件历史"""
        if event_type:
            return [e for e in self._event_history if e.type == event_type][-limit:]
        return self._event_history[-limit:]

    def clear_history(self):
        """清空历史"""
        self._event_history.clear()

    @property
    def subscriber_count(self) -> dict[EventType, int]:
        """订阅者数量"""
        result = {}
        for event_type in EventType:
            sync_count = len(self._subscribers.get(event_type, []))
            async_count = len(self._async_subscribers.get(event_type, []))
            result[event_type] = sync_count + async_count
        return result


# 全局事件总线实例
event_bus = EventBus()


# ====================
# 便捷函数
# ====================


def on(event_type: EventType):
    """装饰器: 订阅事件"""

    def decorator(func: Callable):
        event_bus.subscribe(event_type, func)
        return func

    return decorator


def on_async(event_type: EventType):
    """装饰器: 异步订阅事件"""

    def decorator(func: Callable):
        event_bus.subscribe_async(event_type, func)
        return func

    return decorator


def emit(event_type: EventType, **data):
    """便捷函数: 发布事件"""
    event = Event(type=event_type, data=data)
    event_bus.publish(event)
