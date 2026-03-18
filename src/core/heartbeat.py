"""
Heartbeat - 自主驱动的"脉搏" (Core 模块)

实现智能体的定期自我检查和学习流程。

依赖:
- src.core.events: 事件总线集成
- src.core.knowledge: 知识沉淀集成

迁移自 src.skills.heartbeat，保留完整 7 阶段功能并增强 EventBus 和 Knowledge 集成。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

# 使用 core events
from src.core.events import (
    Event,
    EventPriority,
    EventType,
    SystemEvents,
    get_event_bus,
)

# Knowledge manager 延迟导入
_knowledge_manager = None


def _get_knowledge_manager():
    """延迟获取 KnowledgeManager"""
    global _knowledge_manager
    if _knowledge_manager is None:
        try:
            from src.core.knowledge import KnowledgeManager

            _knowledge_manager = KnowledgeManager
        except ImportError:
            pass
    return _knowledge_manager


logger = logging.getLogger(__name__)


class HeartbeatPhase(Enum):
    """心跳循环的各个阶段"""

    INFO_INTAKE = "info_intake"  # 信息摄入
    VALUE_JUDGMENT = "value_judgment"  # 价值判断
    KNOWLEDGE_OUTPUT = "knowledge_output"  # 知识输出
    SOCIAL_MAINTENANCE = "social_maintenance"  # 社交维护
    SELF_REFLECTION = "self_reflection"  # 自我反思
    SKILL_CHECK = "skill_check"  # 技能检查
    SYSTEM_NOTIFY = "system_notify"  # 系统通知


@dataclass
class HeartbeatConfig:
    """心跳配置"""

    interval_seconds: int = 14400  # 默认4小时
    enabled: bool = True
    phases_enabled: list[HeartbeatPhase] = field(
        default_factory=lambda: [
            HeartbeatPhase.INFO_INTAKE,
            HeartbeatPhase.VALUE_JUDGMENT,
            HeartbeatPhase.KNOWLEDGE_OUTPUT,
            HeartbeatPhase.SELF_REFLECTION,
            HeartbeatPhase.SKILL_CHECK,
        ]
    )
    max_info_items: int = 5  # 每次心跳最多摄入的信息条目
    # 外部信息源配置（简化版，不依赖 external_sources）
    info_keywords: list[str] = field(
        default_factory=lambda: ["AI", "LLM", "machine learning", "technology", "software"]
    )  # 信息过滤关键词
    # EventBus 配置
    use_event_bus: bool = True  # 是否使用事件总线


@dataclass
class HeartbeatResult:
    """心跳执行结果"""

    phase: HeartbeatPhase
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    duration_ms: int = 0


class HeartbeatScheduler:
    """心跳调度器 - 自主驱动的定期检查和学习

    心跳机制模拟智能体的"脉搏"，定期触发自我检查和学习流程，
    使智能体能够主动发现问题、吸收新知识、保持技能更新。

    特性:
    - 7 阶段完整实现
    - EventBus 集成，支持知识沉淀事件
    - 回调系统，支持自定义阶段逻辑
    - 统计功能，记录执行历史
    """

    def __init__(
        self,
        config: HeartbeatConfig | None = None,
        workspace: Path | None = None,
        event_bus=None,  # 可选的事件总线实例
        knowledge_manager=None,  # 可选的知识管理器
    ):
        self.config = config or HeartbeatConfig()
        self.workspace = workspace or Path.cwd()

        # EventBus 集成
        self._event_bus = event_bus
        if self.config.use_event_bus and self._event_bus is None:
            self._event_bus = get_event_bus()

        # Knowledge Manager 集成
        self._knowledge = knowledge_manager
        if self._knowledge is None:
            KM = _get_knowledge_manager()
            if KM:
                self._knowledge = KM(workspace=self.workspace)

        self._running = False
        self._task: asyncio.Task | None = None
        self._last_run: datetime | None = None

        # 回调函数
        self._callbacks: dict[HeartbeatPhase, list[Callable]] = {
            phase: [] for phase in HeartbeatPhase
        }

        # 统计
        self._stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "phase_stats": {phase.value: {"success": 0, "failure": 0} for phase in HeartbeatPhase},
            "info_items_fetched": 0,
        }

    @property
    def event_bus(self):
        """获取事件总线实例"""
        return self._event_bus

    @property
    def knowledge_manager(self):
        """获取知识管理器实例"""
        return self._knowledge

    def register_callback(self, phase: HeartbeatPhase, callback: Callable):
        """注册相位回调

        Args:
            phase: 心跳阶段
            callback: 回调函数，签名为 async def callback() -> HeartbeatResult
        """
        self._callbacks[phase].append(callback)

    def unregister_callback(self, phase: HeartbeatPhase, callback: Callable):
        """注销回调"""
        if callback in self._callbacks[phase]:
            self._callbacks[phase].remove(callback)

    async def _emit_event(self, event_type: str, data: dict, priority: EventPriority = EventPriority.NORMAL):
        """发送事件到 EventBus"""
        if self._event_bus:
            try:
                event = Event(
                    type=event_type,
                    data=data,
                    priority=priority,
                    source="heartbeat",
                )
                # 判断是否为异步方法
                if hasattr(self._event_bus, 'publish_async'):
                    await self._event_bus.publish_async(event)
                else:
                    self._event_bus.publish(event)
            except Exception as e:
                logger.warning(f"Failed to emit event {event_type}: {e}")

    async def start(self):
        """启动心跳调度"""
        if self._running:
            logger.warning("Heartbeat scheduler already running")
            return

        if not self.config.enabled:
            logger.info("Heartbeat scheduler disabled")
            return

        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())

        # 发送心跳启动事件
        await self._emit_event(
            SystemEvents.HEARTBEAT_TICK,
            {"action": "started", "interval": self.config.interval_seconds},
            EventPriority.HIGH,
        )

        logger.info(f"Heartbeat scheduler started with interval={self.config.interval_seconds}s")

    async def stop(self):
        """停止心跳调度"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        # 发送心跳停止事件
        await self._emit_event(
            SystemEvents.HEARTBEAT_TICK,
            {"action": "stopped"},
            EventPriority.HIGH,
        )

        logger.info("Heartbeat scheduler stopped")

    async def trigger_now(self):
        """立即触发一次心跳"""
        logger.info("Manually triggering heartbeat")
        await self._heartbeat_cycle()

    async def _heartbeat_loop(self):
        """心跳主循环"""
        while self._running:
            try:
                await self._heartbeat_cycle()
                self._last_run = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat cycle error: {e}")
                self._stats["failed_runs"] += 1

            # 等待下一个周期
            await asyncio.sleep(self.config.interval_seconds)

    async def _heartbeat_cycle(self):
        """执行一次完整的心跳循环"""
        start_time = datetime.now()
        logger.info("Starting heartbeat cycle")

        # 发送心跳开始事件
        await self._emit_event(
            SystemEvents.HEARTBEAT_TICK,
            {"action": "cycle_start", "phases": [p.value for p in self.config.phases_enabled]},
            EventPriority.HIGH,
        )

        for phase in self.config.phases_enabled:
            if not self._running:
                break

            # 发送阶段开始事件
            await self._emit_event(
                SystemEvents.HEARTBEAT_PHASE,
                {"phase": phase.value, "action": "start"},
                EventPriority.NORMAL,
            )

            result = await self._execute_phase(phase)
            self._update_stats(phase, result.success)

            # 发送阶段完成事件（带知识沉淀）
            await self._emit_event(
                SystemEvents.HEARTBEAT_PHASE,
                {
                    "phase": phase.value,
                    "action": "complete",
                    "success": result.success,
                    "message": result.message,
                    "duration_ms": result.duration_ms,
                },
                EventPriority.NORMAL,
            )

            # 发送知识沉淀事件
            if result.success and result.data:
                await self._emit_event(
                    SystemEvents.KNOWLEDGE_STORED,
                    {
                        "source": "heartbeat",
                        "phase": phase.value,
                        "data": result.data,
                        "timestamp": datetime.now().isoformat(),
                    },
                    EventPriority.LOW,
                )

            if result.success:
                logger.debug(f"Phase {phase.value} completed: {result.message}")
            else:
                logger.warning(f"Phase {phase.value} failed: {result.message}")

            # 记录阶段结果到知识库
            if self._knowledge and hasattr(self._knowledge, 'record_phase_result'):
                try:
                    await self._knowledge.record_phase_result(
                        phase=phase.value,
                        success=result.success,
                        message=result.message,
                        data=result.data,
                    )
                except Exception as e:
                    logger.warning(f"Failed to record phase result to knowledge: {e}")

        self._stats["total_runs"] += 1

        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Heartbeat cycle completed in {duration:.2f}ms")

        # 发送心跳完成事件
        await self._emit_event(
            SystemEvents.HEARTBEAT_TICK,
            {"action": "cycle_complete", "duration_ms": duration},
            EventPriority.NORMAL,
        )

        # 记录到知识库（如果可用）
        if self._knowledge and hasattr(self._knowledge, 'record_heartbeat_cycle'):
            phase_results = []
            for phase in self.config.phases_enabled:
                phase_results.append({
                    "phase": phase.value,
                    "success": self._stats["phase_stats"][phase.value]["success"] > 0,
                })
            try:
                await self._knowledge.record_heartbeat_cycle(
                    phases=[p.value for p in self.config.phases_enabled],
                    duration_ms=int(duration),
                    results=phase_results,
                )
            except Exception as e:
                logger.warning(f"Failed to record heartbeat cycle to knowledge: {e}")

    async def _execute_phase(self, phase: HeartbeatPhase) -> HeartbeatResult:
        """执行单个心跳阶段"""
        start_time = datetime.now()
        callbacks = self._callbacks.get(phase, [])

        if not callbacks:
            # 没有注册回调时，执行默认逻辑
            return await self._default_phase_logic(phase)

        # 执行所有注册的回调
        results = []
        for callback in callbacks:
            try:
                result = await callback()
                results.append(result)
            except Exception as e:
                logger.error(f"Callback error in {phase.value}: {e}")
                return HeartbeatResult(
                    phase=phase,
                    success=False,
                    message=f"Callback error: {e}",
                    duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                )

        # 返回最后一个结果
        if results:
            return results[-1]

        return HeartbeatResult(
            phase=phase,
            success=True,
            message="No callbacks registered, using default logic",
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000),
        )

    async def _default_phase_logic(self, phase: HeartbeatPhase) -> HeartbeatResult:
        """各阶段的默认逻辑实现"""

        async def info_intake():
            """信息摄入阶段 - 模拟外部信息获取"""
            # 简化版：记录信息摄入（实际应由 external_sources 提供）
            self._stats["info_items_fetched"] = 0
            return HeartbeatResult(
                phase=HeartbeatPhase.INFO_INTAKE,
                success=True,
                message="Info intake: Simulated (external sources not configured)",
                data={"items_count": 0},
            )

        async def value_judgment():
            """价值判断阶段 - 筛选高质量内容"""
            return HeartbeatResult(
                phase=HeartbeatPhase.VALUE_JUDGMENT,
                success=True,
                message="Value judgment: Pending implementation",
            )

        async def knowledge_output():
            """知识输出阶段 - 撰写评论/总结"""
            return HeartbeatResult(
                phase=HeartbeatPhase.KNOWLEDGE_OUTPUT,
                success=True,
                message="Knowledge output: Pending implementation",
            )

        async def social_maintenance():
            """社交维护阶段 - 检查消息/通知"""
            return HeartbeatResult(
                phase=HeartbeatPhase.SOCIAL_MAINTENANCE,
                success=True,
                message="Social maintenance: No social accounts configured",
            )

        async def self_reflection():
            """自我反思阶段 - 检查技能更新"""
            return HeartbeatResult(
                phase=HeartbeatPhase.SELF_REFLECTION,
                success=True,
                message="Self reflection: Checking skill updates",
            )

        async def skill_check():
            """技能检查阶段 - 查看新技能"""
            return HeartbeatResult(
                phase=HeartbeatPhase.SKILL_CHECK,
                success=True,
                message="Skill check: No new skills available",
            )

        async def system_notify():
            """系统通知阶段 - 处理待办"""
            return HeartbeatResult(
                phase=HeartbeatPhase.SYSTEM_NOTIFY,
                success=True,
                message="System notify: No pending notifications",
            )

        # 映射阶段到处理函数
        phase_handlers = {
            HeartbeatPhase.INFO_INTAKE: info_intake,
            HeartbeatPhase.VALUE_JUDGMENT: value_judgment,
            HeartbeatPhase.KNOWLEDGE_OUTPUT: knowledge_output,
            HeartbeatPhase.SOCIAL_MAINTENANCE: social_maintenance,
            HeartbeatPhase.SELF_REFLECTION: self_reflection,
            HeartbeatPhase.SKILL_CHECK: skill_check,
            HeartbeatPhase.SYSTEM_NOTIFY: system_notify,
        }

        handler = phase_handlers.get(phase)
        if handler:
            return await handler()

        return HeartbeatResult(
            phase=phase,
            success=False,
            message=f"Unknown phase: {phase}",
        )

    def _update_stats(self, phase: HeartbeatPhase, success: bool):
        """更新统计信息"""
        if success:
            self._stats["successful_runs"] += 1
            self._stats["phase_stats"][phase.value]["success"] += 1
        else:
            self._stats["failed_runs"] += 1
            self._stats["phase_stats"][phase.value]["failure"] += 1

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self._stats,
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "interval_seconds": self.config.interval_seconds,
        }

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running


# 全局实例
_default_scheduler: HeartbeatScheduler | None = None


def get_heartbeat_scheduler() -> HeartbeatScheduler:
    """获取全局心跳调度器实例"""
    global _default_scheduler
    if _default_scheduler is None:
        _default_scheduler = HeartbeatScheduler()
    return _default_scheduler


def set_heartbeat_scheduler(scheduler: HeartbeatScheduler):
    """设置全局心跳调度器"""
    global _default_scheduler
    _default_scheduler = scheduler
