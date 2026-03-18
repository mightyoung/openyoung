"""
Heartbeat Enhancement - 心跳增强模块

DEPRECATED: 请使用 src.core.heartbeat 和 src.core.events

此模块已废弃，功能已合并到 core 模块。
保留此文件仅为向后兼容。
"""

# Event Bus - 从 core 导入
from src.core.events import Event, EventBus, EventPriority, SystemEvents, get_event_bus

# Heartbeat - 从 core 导入
from src.core.heartbeat import (
    HeartbeatConfig,
    HeartbeatPhase,
    HeartbeatResult,
    HeartbeatScheduler,
    get_heartbeat_scheduler,
)

__all__ = [
    # Event Bus (from core)
    "EventBus",
    "Event",
    "SystemEvents",
    "EventPriority",
    "get_event_bus",
    # Heartbeat (from core)
    "HeartbeatScheduler",
    "HeartbeatConfig",
    "HeartbeatPhase",
    "HeartbeatResult",
    "get_heartbeat_scheduler",
    # 向后兼容别名
    "HybridHeartbeat",
    "HybridHeartbeatConfig",
    "create_hybrid_heartbeat",
]

# 向后兼容别名
HybridHeartbeat = HeartbeatScheduler


class HybridHeartbeatConfig(HeartbeatConfig):
    """向后兼容别名"""

    pass


def create_hybrid_heartbeat(interval_seconds: int = 14400, event_bus=None):
    """创建混合心跳实例（向后兼容）"""
    config = HeartbeatConfig(interval_seconds=interval_seconds)
    return HeartbeatScheduler(config=config, event_bus=event_bus)
