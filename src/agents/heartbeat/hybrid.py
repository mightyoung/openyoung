"""
Hybrid Heartbeat - 混合驱动心跳

结合时间驱动和事件驱动的心跳机制。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Optional

from .event_bus import Event, EventBus, EventPriority, SystemEvents

logger = logging.getLogger(__name__)


# 心跳阶段
class HeartbeatPhase:
    """心跳阶段"""

    INFO_INTAKE = "info_intake"
    VALUE_JUDGMENT = "value_judgment"
    KNOWLEDGE_OUTPUT = "knowledge_output"
    SOCIAL_MAINTENANCE = "social_maintenance"
    SELF_REFLECTION = "self_reflection"
    SKILL_CHECK = "skill_check"
    SYSTEM_NOTIFY = "system_notify"


# 阶段处理器类型
PhaseHandler = Callable[[], Awaitable[None]]


@dataclass
class HybridHeartbeatConfig:
    """混合心跳配置"""

    # 时间驱动配置
    interval_seconds: int = 14400  # 默认4小时
    min_interval_seconds: int = 60  # 最小间隔

    # 事件驱动配置
    event_driven: bool = True
    event_threshold: int = 10  # 事件触发阈值

    # 启用控制
    enabled: bool = True
    phases_enabled: list = field(
        default_factory=lambda: [
            HeartbeatPhase.INFO_INTAKE,
            HeartbeatPhase.VALUE_JUDGMENT,
            HeartbeatPhase.SELF_REFLECTION,
        ]
    )


class HybridHeartbeat:
    """混合驱动心跳"""

    def __init__(
        self,
        config: Optional[HybridHeartbeatConfig] = None,
        event_bus: Optional[EventBus] = None,
    ):
        self.config = config or HybridHeartbeatConfig()
        self.event_bus = event_bus

        # 状态
        self._running = False
        self._timer_task: asyncio.Task = None
        self._event_count = 0
        self._last_execution = datetime.now()

        # 阶段处理器
        self._phase_handlers: dict[str, PhaseHandler] = {}

        # 事件处理器
        self._event_handler = None

    def register_phase(self, phase: str, handler: PhaseHandler):
        """注册阶段处理器"""
        self._phase_handlers[phase] = handler

    def _create_event_handler(self) -> Callable[[Event], Awaitable[None]]:
        """创建事件处理器"""

        async def handler(event: Event):
            self._event_count += 1
            logger.debug(f"Event received: {event.type}, count: {self._event_count}")

            # 检查是否触发心跳
            if self.config.event_driven and self._event_count >= self.config.event_threshold:
                self._event_count = 0
                await self.trigger()

        return handler

    async def start(self):
        """启动心跳"""
        if self._running:
            return

        self._running = True
        self._event_count = 0

        # 注册事件处理器
        if self.event_bus and self.config.event_driven:
            self._event_handler = self._create_event_handler()
            # 订阅任务相关事件
            self.event_bus.subscribe(
                SystemEvents.TASK_COMPLETED,
                self._event_handler,
                priority=EventPriority.HIGH,
            )
            self.event_bus.subscribe(
                SystemEvents.TASK_FAILED,
                self._event_handler,
                priority=EventPriority.HIGH,
            )

        # 启动定时器
        self._timer_task = asyncio.create_task(self._timer_loop())

        logger.info(f"HybridHeartbeat started, interval: {self.config.interval_seconds}s")

    async def stop(self):
        """停止心跳"""
        self._running = False

        # 取消事件订阅
        if self.event_bus and self._event_handler:
            self.event_bus.unsubscribe(SystemEvents.TASK_COMPLETED, self._event_handler)
            self.event_bus.unsubscribe(SystemEvents.TASK_FAILED, self._event_handler)

        # 取消定时器
        if self._timer_task:
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass

        logger.info("HybridHeartbeat stopped")

    async def _timer_loop(self):
        """定时器循环"""
        while self._running:
            try:
                await asyncio.sleep(self.config.interval_seconds)
                if self._running:
                    await self.trigger()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timer loop error: {e}")

    async def trigger(self):
        """触发心跳执行"""
        if not self._running:
            return

        now = datetime.now()
        elapsed = (now - self._last_execution).total_seconds()

        # 检查最小间隔
        if elapsed < self.config.min_interval_seconds:
            logger.debug(
                f"Heartbeat skipped, last executed {elapsed:.1f}s ago "
                f"(min: {self.config.min_interval_seconds}s)"
            )
            return

        logger.info("Heartbeat triggered")
        self._last_execution = now

        # 发送心跳开始事件
        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    type=SystemEvents.HEARTBEAT_TICK,
                    data={"timestamp": now.isoformat()},
                    priority=EventPriority.HIGH,
                )
            )

        # 执行各阶段
        for phase in self.config.phases_enabled:
            if phase in self._phase_handlers:
                # 发送阶段开始事件
                if self.event_bus:
                    await self.event_bus.publish(
                        Event(
                            type=SystemEvents.HEARTBEAT_PHASE,
                            data={"phase": phase},
                            priority=EventPriority.NORMAL,
                        )
                    )

                try:
                    await self._phase_handlers[phase]()
                except Exception as e:
                    logger.error(f"Phase {phase} error: {e}")

    async def run_once(self):
        """运行一次心跳（手动触发）"""
        await self.trigger()

    def get_status(self) -> dict:
        """获取状态"""
        return {
            "running": self._running,
            "event_count": self._event_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None,
            "interval_seconds": self.config.interval_seconds,
            "event_driven": self.config.event_driven,
            "event_threshold": self.config.event_threshold,
        }


# 创建默认实例
def create_hybrid_heartbeat(
    interval_seconds: int = 14400,
    event_bus: Optional[EventBus] = None,
) -> HybridHeartbeat:
    """创建混合心跳实例"""
    config = HybridHeartbeatConfig(
        interval_seconds=interval_seconds,
        event_driven=True,
        event_threshold=10,
    )
    return HybridHeartbeat(config=config, event_bus=event_bus)
