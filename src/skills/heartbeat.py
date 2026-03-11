"""
Heartbeat - 自主驱动的"脉搏"

实现 OpenClaw 风格的心跳循环机制，提供智能体的定期自我检查和学习流程。

依赖:
- aiohttp: HTTP 客户端（用于外部信息源）
- feedparser: RSS/Atom 解析库
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from .external_sources import (
    ExternalSourcesConfig,
    ExternalSourcesFetcher,
    NewsItem,
    SourceConfig,
    SourceType,
    get_external_sources_fetcher,
)

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
    # 外部信息源配置
    external_sources: Optional[ExternalSourcesConfig] = None
    info_keywords: list[str] = field(
        default_factory=lambda: ["AI", "LLM", "machine learning", "technology", "software"]
    )  # 信息过滤关键词


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
    """

    def __init__(
        self,
        config: HeartbeatConfig | None = None,
        workspace: Path | None = None,
    ):
        self.config = config or HeartbeatConfig()
        self.workspace = workspace or Path.cwd()
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_run: datetime | None = None

        # 外部信息源获取器
        self._external_fetcher: Optional[ExternalSourcesFetcher] = None

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
    def external_fetcher(self) -> ExternalSourcesFetcher:
        """获取外部信息源获取器（延迟初始化）"""
        if self._external_fetcher is None:
            config = self.config.external_sources or ExternalSourcesConfig.default_config()
            self._external_fetcher = ExternalSourcesFetcher(config)
        return self._external_fetcher

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

        for phase in self.config.phases_enabled:
            if not self._running:
                break

            result = await self._execute_phase(phase)
            self._update_stats(phase, result.success)

            if result.success:
                logger.debug(f"Phase {phase.value} completed: {result.message}")
            else:
                logger.warning(f"Phase {phase.value} failed: {result.message}")

        self._stats["total_runs"] += 1

        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Heartbeat cycle completed in {duration:.2f}ms")

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
            """信息摄入阶段 - 扫描外部信息源"""
            try:
                # 获取外部信息源
                items = await self.external_fetcher.fetch_all(keywords=self.config.info_keywords)

                # 限制数量
                items = items[: self.config.max_info_items]

                # 更新统计
                self._stats["info_items_fetched"] = len(items)

                if items:
                    # 格式化返回
                    item_summaries = [
                        f"[{item.source}] {item.title} (score: {item.score})" for item in items[:5]
                    ]
                    return HeartbeatResult(
                        phase=HeartbeatPhase.INFO_INTAKE,
                        success=True,
                        message=f"Fetched {len(items)} items from external sources",
                        data={
                            "items_count": len(items),
                            "top_items": item_summaries,
                            "sources": list(set(item.source for item in items)),
                        },
                    )
                else:
                    return HeartbeatResult(
                        phase=HeartbeatPhase.INFO_INTAKE,
                        success=True,
                        message="No external sources configured or fetch failed",
                        data={"items_count": 0},
                    )

            except ImportError as e:
                # 缺少依赖库
                return HeartbeatResult(
                    phase=HeartbeatPhase.INFO_INTAKE,
                    success=False,
                    message=f"Missing dependencies: {e}. Install aiohttp and feedparser",
                    data={"items_count": 0, "error": str(e)},
                )
            except Exception as e:
                logger.error(f"Info intake error: {e}")
                return HeartbeatResult(
                    phase=HeartbeatPhase.INFO_INTAKE,
                    success=False,
                    message=f"Info intake failed: {e}",
                    data={"items_count": 0, "error": str(e)},
                )

        async def value_judgment():
            """价值判断阶段 - 筛选高质量内容"""
            # TODO(future): 实现内容质量评估
            # 当前返回默认结果，等待质量评估算法集成
            return HeartbeatResult(
                phase=HeartbeatPhase.VALUE_JUDGMENT,
                success=True,
                message="Value judgment: Pending implementation",
            )

        async def knowledge_output():
            """知识输出阶段 - 撰写评论/总结"""
            # TODO(future): 实现知识输出逻辑
            return HeartbeatResult(
                phase=HeartbeatPhase.KNOWLEDGE_OUTPUT,
                success=True,
                message="Knowledge output: Pending implementation",
            )

        async def social_maintenance():
            """社交维护阶段 - 检查消息/通知"""
            # TODO(future): 集成社交媒体检查
            return HeartbeatResult(
                phase=HeartbeatPhase.SOCIAL_MAINTENANCE,
                success=True,
                message="Social maintenance: No social accounts configured",
            )

        async def self_reflection():
            """自我反思阶段 - 检查技能更新"""
            # TODO(future): 实现技能更新检查
            return HeartbeatResult(
                phase=HeartbeatPhase.SELF_REFLECTION,
                success=True,
                message="Self reflection: Checking skill updates",
            )

        async def skill_check():
            """技能检查阶段 - 查看新技能"""
            # TODO(future): 实现新技能检查
            return HeartbeatResult(
                phase=HeartbeatPhase.SKILL_CHECK,
                success=True,
                message="Skill check: No new skills available",
            )

        async def system_notify():
            """系统通知阶段 - 处理待办"""
            # TODO(future): 实现系统通知处理
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
