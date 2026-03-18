"""
Event Bus - 事件总线

DEPRECATED: 请使用 src.core.events
此模块已废弃，所有功能已合并到 src/core/events.py

保留此文件仅为向后兼容，新代码请直接使用:
    from src.core.events import Event, EventBus, EventPriority, SystemEvents, get_event_bus
"""

# 向后兼容导入
from src.core.events import (
    Event,
    EventBus,
    EventPriority,
    EventType,
    SystemEvents,
    event_bus,
    get_event_bus,
)

__all__ = [
    "Event",
    "EventBus",
    "EventPriority",
    "EventType",
    "SystemEvents",
    "event_bus",
    "get_event_bus",
]
