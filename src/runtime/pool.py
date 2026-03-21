"""
Sandbox Pool - 沙箱实例池

提供沙箱实例的复用与自动扩缩容，参考 Modal 设计
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .sandbox import AISandbox, SandboxConfig, SandboxInstance

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """资源池配置"""

    min_instances: int = 2
    max_instances: int = 10
    idle_timeout_seconds: int = 300
    scale_up_threshold: float = 0.7
    scale_down_threshold: float = 0.3

    # 自动扩缩容配置
    auto_scale_enabled: bool = True
    scale_check_interval_seconds: int = 30
    warm_up_enabled: bool = True
    warm_up_target: int = 3  # 预热到3个可用实例

    # 状态持久化
    persist_state: bool = False
    state_file: str = ".young/sandbox_pool_state.json"

    # 沙箱配置
    sandbox_config: SandboxConfig = field(default_factory=SandboxConfig)


@dataclass
class PoolStats:
    """池统计信息"""

    total_instances: int = 0
    active_instances: int = 0
    available_instances: int = 0
    utilization: float = 0.0
    created_count: int = 0
    destroyed_count: int = 0


class SandboxPool:
    """沙箱实例池"""

    def __init__(
        self,
        config: Optional[PoolConfig] = None,
        sandbox: Optional[AISandbox] = None,
    ):
        self.config = config or PoolConfig()
        self.sandbox = sandbox or AISandbox(self.config.sandbox_config)

        self._available: asyncio.Queue = asyncio.Queue()
        self._active: dict[str, SandboxInstance] = {}
        self._lock = asyncio.Lock()

        # 统计
        self._created_count = 0
        self._destroyed_count = 0

        # 自动扩缩容任务
        self._scale_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> None:
        """初始化池，创建最小实例数"""
        logger.info(f"Initializing sandbox pool with {self.config.min_instances} instances")

        # 尝试恢复状态
        if self.config.persist_state:
            await self._load_state()

        for i in range(self.config.min_instances):
            sandbox_id = await self.sandbox.create(
                agent_id=f"pool_{i}",
                config=self.config.sandbox_config,
            )
            instance = self.sandbox.get_sandbox(sandbox_id)
            if instance:
                await self._available.put(instance)
                self._created_count += 1

        logger.info(f"Sandbox pool initialized with {self._available.qsize()} available instances")

        # 启动自动扩缩容
        if self.config.auto_scale_enabled:
            await self.start_auto_scaling()

    async def start_auto_scaling(self) -> None:
        """启动自动扩缩容"""
        if self._running:
            logger.warning("Auto-scaling already running")
            return

        self._running = True
        self._scale_task = asyncio.create_task(self._auto_scale_loop())
        logger.info("Auto-scaling started")

    async def stop_auto_scaling(self) -> None:
        """停止自动扩缩容"""
        self._running = False
        if self._scale_task:
            self._scale_task.cancel()
            try:
                await self._scale_task
            except asyncio.CancelledError:
                pass  # Task was cancelled as expected
        logger.info("Auto-scaling stopped")

    async def _auto_scale_loop(self) -> None:
        """自动扩缩容循环"""
        while self._running:
            try:
                # 检查并执行扩缩容
                await self.scale_check()

                # 预热实例
                if self.config.warm_up_enabled:
                    await self._warm_up_instances()

                # 保存状态
                if self.config.persist_state:
                    await self._save_state()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scale error: {e}")

            await asyncio.sleep(self.config.scale_check_interval_seconds)

    async def _warm_up_instances(self) -> None:
        """预热实例 - 保持足够的预热实例"""
        available = self._available.qsize()
        active = len(self._active)

        # 如果可用实例少于预热目标，创建新实例
        if (
            available < self.config.warm_up_target
            and (available + active) < self.config.max_instances
        ):
            needed = self.config.warm_up_target - available
            needed = min(needed, 2)  # 每次最多预热2个

            for i in range(needed):
                sandbox_id = await self.sandbox.create(
                    agent_id=f"pool_warm_{uuid.uuid4().hex[:8]}",
                    config=self.config.sandbox_config,
                )
                instance = self.sandbox.get_sandbox(sandbox_id)
                if instance:
                    await self._available.put(instance)
                    self._created_count += 1
                    logger.info(f"Warm-up: created sandbox {instance.id}")

    async def _save_state(self) -> None:
        """保存池状态"""
        import json
        from pathlib import Path

        try:
            state = {
                "created_count": self._created_count,
                "destroyed_count": self._destroyed_count,
                "config": {
                    "min_instances": self.config.min_instances,
                    "max_instances": self.config.max_instances,
                },
                "timestamp": datetime.now().isoformat(),
            }

            state_file = Path(self.config.state_file)
            state_file.parent.mkdir(parents=True, exist_ok=True)
            state_file.write_text(json.dumps(state, indent=2))

            logger.debug(f"Pool state saved to {state_file}")
        except Exception as e:
            logger.error(f"Failed to save pool state: {e}")

    async def _load_state(self) -> None:
        """加载池状态"""
        import json
        from pathlib import Path

        try:
            state_file = Path(self.config.state_file)
            if not state_file.exists():
                logger.info("No saved pool state found")
                return

            state = json.loads(state_file.read_text())
            self._created_count = state.get("created_count", 0)
            self._destroyed_count = state.get("destroyed_count", 0)

            logger.info(
                f"Pool state loaded: created={self._created_count}, destroyed={self._destroyed_count}"
            )
        except Exception as e:
            logger.error(f"Failed to load pool state: {e}")

    async def acquire(self, timeout: float = 30.0) -> SandboxInstance:
        """获取沙箱实例"""
        # 尝试从池中获取
        try:
            instance = self._available.get_nowait()
            self._active[instance.id] = instance
            logger.debug(f"Acquired sandbox from pool: {instance.id}")
            return instance
        except asyncio.QueueEmpty:
            # 池为空，检查是否可以创建新实例
            if len(self._active) < self.config.max_instances:
                sandbox_id = await self.sandbox.create(
                    agent_id=f"pool_{uuid.uuid4().hex[:8]}",
                    config=self.config.sandbox_config,
                )
                instance = self.sandbox.get_sandbox(sandbox_id)
                if instance:
                    self._active[instance.id] = instance
                    self._created_count += 1
                    logger.info(f"Created new sandbox: {instance.id}")
                    return instance

            # 等待可用实例
            logger.warning("Pool exhausted, waiting for available sandbox")
            instance = await asyncio.wait_for(
                self._available.get(),
                timeout=timeout,
            )
            self._active[instance.id] = instance
            return instance

    async def release(self, instance: SandboxInstance) -> None:
        """释放沙箱实例回池"""
        async with self._lock:
            if instance.id in self._active:
                del self._active[instance.id]

                # 检查是否需要缩容
                utilization = len(self._active) / self.config.max_instances

                if (
                    utilization < self.config.scale_down_threshold
                    and self._available.qsize() > self.config.min_instances
                ):
                    # 缩容：销毁实例
                    await self.sandbox.destroy(instance.id)
                    self._destroyed_count += 1
                    logger.info(f"Scaled down: destroyed sandbox {instance.id}")
                else:
                    # 回收到池
                    await self._available.put(instance)
                    logger.debug(f"Released sandbox to pool: {instance.id}")

    async def destroy(self, sandbox_id: str) -> None:
        """销毁指定沙箱"""
        if sandbox_id in self._active:
            del self._active[sandbox_id]

        await self.sandbox.destroy(sandbox_id)
        self._destroyed_count += 1

    async def shutdown(self) -> None:
        """关闭池，销毁所有实例"""
        logger.info("Shutting down sandbox pool")

        # 停止自动扩缩容
        await self.stop_auto_scaling()

        # 保存状态
        if self.config.persist_state:
            await self._save_state()

        # 等待活跃实例完成
        await asyncio.sleep(1)

        # 销毁所有实例
        for sandbox_id in list(self._active.keys()):
            await self.sandbox.destroy(sandbox_id)

        # 清空池
        while not self._available.empty():
            try:
                self._available.get_nowait()
            except asyncio.QueueEmpty:
                break

        self._active.clear()
        logger.info(
            f"Sandbox pool shut down. Created: {self._created_count}, Destroyed: {self._destroyed_count}"
        )

    def get_stats(self) -> PoolStats:
        """获取池统计信息"""
        total = self._available.qsize() + len(self._active)
        utilization = (
            len(self._active) / self.config.max_instances if self.config.max_instances > 0 else 0
        )

        return PoolStats(
            total_instances=total,
            active_instances=len(self._active),
            available_instances=self._available.qsize(),
            utilization=utilization,
            created_count=self._created_count,
            destroyed_count=self._destroyed_count,
        )

    async def scale_check(self) -> None:
        """检查并执行扩缩容"""
        utilization = (
            len(self._active) / self.config.max_instances if self.config.max_instances > 0 else 0
        )

        # 扩容
        if utilization > self.config.scale_up_threshold:
            needed = min(
                2,  # 每次最多扩容2个
                self.config.max_instances - len(self._active) - self._available.qsize(),
            )
            for i in range(needed):
                sandbox_id = await self.sandbox.create(
                    agent_id=f"pool_scale_{uuid.uuid4().hex[:8]}",
                    config=self.config.sandbox_config,
                )
                instance = self.sandbox.get_sandbox(sandbox_id)
                if instance:
                    await self._available.put(instance)
                    self._created_count += 1
                    logger.info(f"Scaled up: created sandbox {instance.id}")


# ========== Convenience Functions ==========


def create_pool(
    min_instances: int = 2,
    max_instances: int = 10,
    sandbox_config: Optional[SandboxConfig] = None,
) -> SandboxPool:
    """创建沙箱池"""
    pool_config = PoolConfig(
        min_instances=min_instances,
        max_instances=max_instances,
        sandbox_config=sandbox_config or SandboxConfig(),
    )
    return SandboxPool(config=pool_config)
