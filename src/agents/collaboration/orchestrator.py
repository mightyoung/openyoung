"""
Orchestrator - 任务编排器

提供任务队列管理、Agent调度、结果聚合功能
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class QueueStrategy(Enum):
    """队列策略"""

    FIFO = "fifo"  # 先进先出
    PRIORITY = "priority"  # 优先级
    ROUND_ROBIN = "round_robin"  # 轮询


class TaskPriority(Enum):
    """任务优先级"""

    LOW = 0
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class QueuedTask:
    """队列任务"""

    id: str = field(default_factory=lambda: f"qtask_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    agent_id: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    enqueued_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: str = ""


@dataclass
class AgentState:
    """Agent状态"""

    agent_id: str
    status: str = "idle"  # idle, busy, offline
    current_task: Optional[str] = None
    capacity: int = 1  # 并发容量
    load: int = 0  # 当前负载
    last_active: datetime = field(default_factory=datetime.now)


class TaskOrchestrator:
    """任务编排器"""

    def __init__(
        self,
        strategy: QueueStrategy = QueueStrategy.FIFO,
        max_concurrent: int = 5,
    ):
        self.strategy = strategy
        self.max_concurrent = max_concurrent

        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.agents: dict[str, AgentState] = {}
        self.results: dict[str, QueuedTask] = {}

        # 任务执行器
        self._executors: dict[str, Callable] = {}

        # 锁
        self._lock = asyncio.Lock()

    def register_agent(
        self,
        agent_id: str,
        capacity: int = 1,
    ):
        """注册Agent"""
        self.agents[agent_id] = AgentState(
            agent_id=agent_id,
            capacity=capacity,
        )

    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            self.agents[agent_id].status = "offline"

    def register_executor(self, agent_id: str, executor: Callable):
        """注册任务执行器"""
        self._executors[agent_id] = executor

    async def enqueue(
        self,
        task_id: str,
        agent_id: str,
        priority: TaskPriority = TaskPriority.NORMAL,
    ):
        """入队"""
        queued_task = QueuedTask(
            task_id=task_id,
            agent_id=agent_id,
            priority=priority,
        )

        # 根据策略入队
        if self.strategy == QueueStrategy.PRIORITY:
            # 优先级队列：负值实现最大堆
            await self.task_queue.put((-priority.value, queued_task))
        else:
            await self.task_queue.put((0, queued_task))

        self.results[task_id] = queued_task

    async def start(self):
        """启动编排器"""
        # 启动worker
        workers = [asyncio.create_task(self._worker(i)) for i in range(self.max_concurrent)]
        return workers

    async def _worker(self, worker_id: int):
        """Worker协程"""
        while True:
            try:
                # 获取任务
                _, queued_task = await self.task_queue.get()

                # 检查Agent可用性
                agent = self.agents.get(queued_task.agent_id)
                if not agent or agent.status == "offline":
                    # Agent不可用，放回队列
                    await self.task_queue.put((0, queued_task))
                    await asyncio.sleep(1)
                    continue

                # 检查Agent负载
                if agent.load >= agent.capacity:
                    # Agent忙碌，放回队列
                    await self.task_queue.put((0, queued_task))
                    await asyncio.sleep(0.5)
                    continue

                # 标记Agent忙碌
                async with self._lock:
                    agent.status = "busy"
                    agent.load += 1
                    agent.current_task = queued_task.task_id

                # 记录开始时间
                queued_task.started_at = datetime.now()

                # 执行任务
                try:
                    executor = self._executors.get(queued_task.agent_id)
                    if executor:
                        result = await executor(queued_task.task_id)
                        queued_task.result = result
                    else:
                        queued_task.error = "No executor found"
                except Exception as e:
                    queued_task.error = str(e)

                # 记录完成时间
                queued_task.completed_at = datetime.now()

                # 释放Agent
                async with self._lock:
                    agent.status = "idle"
                    agent.load -= 1
                    agent.current_task = None
                    agent.last_active = datetime.now()

                self.task_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")

    async def get_result(self, task_id: str) -> Optional[Any]:
        """获取任务结果"""
        task = self.results.get(task_id)
        if task:
            return task.result
        return None

    async def get_agent_status(self, agent_id: str) -> Optional[AgentState]:
        """获取Agent状态"""
        return self.agents.get(agent_id)

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_tasks = len(self.results)
        completed = sum(1 for t in self.results.values() if t.completed_at)
        pending = total_tasks - completed

        agent_stats = {
            agent_id: {
                "status": agent.status,
                "load": agent.load,
                "capacity": agent.capacity,
            }
            for agent_id, agent in self.agents.items()
        }

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "pending": pending,
            "agents": agent_stats,
        }


class DistributedOrchestrator(TaskOrchestrator):
    """分布式编排器 - 支持跨进程/跨机器的编排"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pubsub = None  # 消息队列

    def set_pubsub(self, pubsub):
        """设置消息队列"""
        self._pubsub = pubsub

    async def broadcast_task(self, task: QueuedTask):
        """广播任务到所有Agent"""
        if self._pubsub:
            await self._pubsub.publish("tasks", task)
        else:
            await self.enqueue(task.task_id, task.agent_id, task.priority)

    async def subscribe_results(self):
        """订阅结果"""
        if self._pubsub:
            async for message in self._pubsub.subscribe("results"):
                task = QueuedTask(**message)
                self.results[task.task_id] = task
