"""
DAG Scheduler - 有向无环图任务调度器

基于 Kahn's Algorithm 实现拓扑排序
支持并行层计算和失败传播

参考:
- Apache Airflow: https://airflow.apache.org
- Prefect: https://www.prefect.io
- Dagster: https://dagster.io
"""

import asyncio
import logging
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from src.core.types import Task, TaskStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class FailurePropagation(Enum):
    """失败传播策略"""

    CASCADE = "cascade"  # 所有下游任务失败
    ISOLATE = "isolate"  # 仅失败任务停止，依赖任务可继续
    RESCHEDULE = "reschedule"  # 失败任务重新排队
    FALLBACK = "fallback"  # 使用备用方案


class ErrorType(Enum):
    """错误类型分类"""

    RETRYABLE = "retryable"  # 临时错误，可重试
    NON_RETRYABLE = "non_retryable"  # 永久错误，不可重试
    TIMEOUT = "timeout"  # 超时错误
    RESOURCE = "resource"  # 资源不足


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class TaskNode:
    """DAG 中的任务节点"""

    task_id: str
    description: str
    input: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    attempt: int = 0
    max_attempts: int = 3
    timeout: float = 300.0  # 超时时间（秒）
    metadata: dict[str, Any] = field(default_factory=dict)

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.attempt < self.max_attempts

    def mark_running(self):
        """标记为运行中"""
        self.status = TaskStatus.RUNNING

    def mark_completed(self, result: Any):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.result = result

    def mark_failed(self, error: str):
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.error = error


@dataclass
class TaskResult:
    """任务执行结果"""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    attempts: int = 1


@dataclass
class DAGConfig:
    """DAG 配置"""

    failure_propagation: FailurePropagation = FailurePropagation.CASCADE
    max_parallel_tasks: int = 10
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5  # 连续失败次数阈值
    circuit_breaker_timeout: float = 60.0  # 熔断超时时间


# ============================================================================
# DAG Scheduler
# ============================================================================


class DAGScheduler:
    """DAG 任务调度器

    核心功能:
    - Kahn's Algorithm 拓扑排序
    - 并行层计算
    - 失败分类
    - 重试等待时间计算
    - 失败传播
    """

    def __init__(self, config: Optional[DAGConfig] = None):
        self.config = config or DAGConfig()
        self._tasks: dict[str, TaskNode] = {}
        self._adjacency: dict[str, set[str]] = defaultdict(set)  # task -> 下游任务
        self._in_degree: dict[str, int] = defaultdict(int)  # 入度
        self._executor: Optional[Callable] = None
        self._circuit_breaker_failures: int = 0
        self._circuit_breaker_open: bool = False

    def set_executor(self, executor: Callable[[TaskNode], Any]):
        """设置任务执行器"""
        self._executor = executor

    def add_task(self, task: TaskNode) -> None:
        """添加任务到 DAG

        Args:
            task: 任务节点
        """
        if task.task_id in self._tasks:
            logger.warning(f"Task {task.task_id} already exists, skipping")
            return

        self._tasks[task.task_id] = task
        self._in_degree[task.task_id] = len(task.dependencies)

        # 构建邻接表
        for dep_id in task.dependencies:
            self._adjacency[dep_id].add(task.task_id)

        logger.info(f"Added task {task.task_id} with {len(task.dependencies)} dependencies")

    def add_task_from_task(self, task: Task) -> str:
        """从 Task 对象添加任务

        Args:
            task: Task 对象

        Returns:
            任务 ID
        """
        task_id = task.id or f"task_{uuid.uuid4().hex[:8]}"
        node = TaskNode(
            task_id=task_id,
            description=task.description,
            input=task.input,
            max_attempts=task.metadata.get("max_retries", 3),
            timeout=task.metadata.get("timeout", 300.0),
            metadata=task.metadata,
        )
        self.add_task(node)
        return task_id

    def _has_cycle(self) -> bool:
        """检测是否存在循环依赖 (DFS)"""
        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in self._tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        return False

    def topological_sort(self) -> list[str]:
        """Kahn's Algorithm 拓扑排序

        Returns:
            拓扑排序后的任务 ID 列表

        Raises:
            ValueError: 如果存在循环依赖
        """
        if self._has_cycle():
            raise ValueError("DAG contains cycle - topological sort not possible")

        # 初始化入度队列
        in_degree = self._in_degree.copy()
        queue = deque([tid for tid, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            # 减少下游任务的入度
            for neighbor in self._adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._tasks):
            raise ValueError("DAG contains cycle - topological sort incomplete")

        return result

    def get_ready_tasks(self) -> list[str]:
        """获取就绪任务（所有依赖已满足）

        Returns:
            就绪任务 ID 列表
        """
        ready = []
        for task_id, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue

            # 检查所有依赖是否完成
            deps_satisfied = all(
                self._tasks[dep_id].status == TaskStatus.COMPLETED for dep_id in task.dependencies
            )
            if deps_satisfied:
                ready.append(task_id)

        return ready

    def get_parallel_layers(self) -> list[list[str]]:
        """获取可并行执行的层次

        基于拓扑排序将任务分层，同一层内的任务可以并行执行

        Returns:
            任务层次列表，每层内的任务可以并行执行
        """
        if self._has_cycle():
            logger.error("Cannot compute parallel layers - DAG contains cycle")
            return []

        # 计算每个任务的深度（从根节点开始的最大路径长度）
        depth: dict[str, int] = {}

        # 获取拓扑排序
        try:
            topo_order = self.topological_sort()
        except ValueError:
            return []

        # 计算深度
        for task_id in topo_order:
            task = self._tasks[task_id]
            if not task.dependencies:
                depth[task_id] = 0
            else:
                depth[task_id] = max(depth[dep] for dep in task.dependencies) + 1

        # 按深度分组
        layers: dict[int, list[str]] = defaultdict(list)
        for task_id, d in depth.items():
            layers[d].append(task_id)

        # 返回层次列表
        return [layers[i] for i in sorted(layers.keys())]

    def _classify_error(self, error: Exception) -> ErrorType:
        """错误分类

        Args:
            error: 异常对象

        Returns:
            错误类型
        """
        error_msg = str(error).lower()

        # 超时错误
        if "timeout" in error_msg or "timed out" in error_msg:
            return ErrorType.TIMEOUT

        # 资源不足
        if any(kw in error_msg for kw in ["memory", "cpu", "resource", "quota", "limit"]):
            return ErrorType.RESOURCE

        # 永久错误（不可重试）
        non_retryable_keywords = [
            "syntax",
            "parse",
            "invalid",
            "unauthorized",
            "forbidden",
            "not found",
            "does not exist",
            "permission denied",
        ]
        if any(kw in error_msg for kw in non_retryable_keywords):
            return ErrorType.NON_RETRYABLE

        # 默认认为是临时错误
        return ErrorType.RETRYABLE

    def _calculate_wait_time(
        self, attempt: int, base_delay: float = 1.0, strategy: str = "exponential"
    ) -> float:
        """计算重试等待时间

        Args:
            attempt: 当前尝试次数（从 0 开始）
            base_delay: 基础延迟时间（秒）
            strategy: 策略类型 (fixed, exponential, linear, fibonacci)

        Returns:
            等待时间（秒）
        """
        if strategy == "fixed":
            return base_delay
        elif strategy == "exponential":
            return base_delay * (2**attempt)
        elif strategy == "linear":
            return base_delay * (attempt + 1)
        elif strategy == "fibonacci":
            # 斐波那契数列
            fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            return base_delay * fib[min(attempt, len(fib) - 1)]
        else:
            return base_delay * (2**attempt)  # 默认指数退避

    def _propagate_failure(self, failed_task_id: str) -> list[str]:
        """失败传播

        根据配置的失败传播策略，返回应该被标记为失败的任务

        Args:
            failed_task_id: 失败的任务 ID

        Returns:
            应该被标记为失败的任务 ID 列表
        """
        if self.config.failure_propagation == FailurePropagation.ISOLATE:
            # 仅失败任务本身
            return [failed_task_id]

        elif self.config.failure_propagation == FailurePropagation.CASCADE:
            # 使用 BFS 查找所有下游任务
            failed = [failed_task_id]
            queue = deque([failed_task_id])

            while queue:
                current = queue.popleft()
                for downstream in self._adjacency[current]:
                    if downstream not in failed:
                        failed.append(downstream)
                        queue.append(downstream)

            return failed

        elif self.config.failure_propagation == FailurePropagation.RESCHEDULE:
            # 仅失败任务，需要重新调度
            return [failed_task_id]

        elif self.config.failure_propagation == FailurePropagation.FALLBACK:
            # TODO: 实现备用方案逻辑
            return [failed_task_id]

        return [failed_task_id]

    async def execute(self, executor: Optional[Callable] = None) -> dict[str, TaskResult]:
        """执行整个 DAG

        Args:
            executor: 可选的任务执行器，如果未设置则使用 self._executor

        Returns:
            任务 ID -> 结果的映射
        """
        exec_fn = executor or self._executor
        if not exec_fn:
            raise ValueError("No executor set. Use set_executor() or pass executor to execute()")

        results: dict[str, TaskResult] = {}
        layers = self.get_parallel_layers()

        logger.info(f"Executing DAG with {len(layers)} layers")

        for layer_idx, layer in enumerate(layers):
            logger.info(f"Executing layer {layer_idx + 1}/{len(layers)} with {len(layer)} tasks")

            # 检查熔断器
            if self._circuit_breaker_open:
                logger.warning("Circuit breaker is open, aborting execution")
                break

            # 并行执行当前层
            tasks = [self._tasks[task_id] for task_id in layer]
            layer_results = await self._execute_layer(tasks, exec_fn)

            # 收集结果
            results.update(layer_results)

            # 检查是否有失败
            failed_tasks = [
                tid for tid, r in layer_results.items() if r.status == TaskStatus.FAILED
            ]

            if failed_tasks:
                logger.warning(f"Layer {layer_idx + 1} has {len(failed_tasks)} failed tasks")

                # 触发失败传播
                all_failed = set()
                for failed_id in failed_tasks:
                    propagated = self._propagate_failure(failed_id)
                    all_failed.update(propagated)

                # 标记传播的任务为失败
                for tid in all_failed:
                    if tid in self._tasks and self._tasks[tid].status == TaskStatus.PENDING:
                        self._tasks[tid].mark_failed("Propagation from failed upstream task")
                        results[tid] = TaskResult(
                            task_id=tid,
                            status=TaskStatus.FAILED,
                            error="Propagation from failed upstream task",
                        )

                # 根据失败传播策略决定是否继续
                if self.config.failure_propagation == FailurePropagation.CASCADE:
                    logger.info("CASCADE propagation - stopping execution")
                    break

        return results

    async def _execute_layer(
        self, tasks: list[TaskNode], executor: Callable[[TaskNode], Any]
    ) -> dict[str, TaskResult]:
        """执行一层任务（并行）

        Args:
            tasks: 任务列表
            executor: 执行器

        Returns:
            结果映射
        """
        results: dict[str, TaskResult] = {}

        # 创建异步任务
        async def execute_task(task: TaskNode) -> tuple[str, TaskResult]:
            import time

            start_time = time.time()
            task.mark_running()

            while task.can_retry():
                try:
                    # 执行任务（支持异步或同步）
                    if asyncio.iscoroutinefunction(executor):
                        result = await asyncio.wait_for(executor(task), timeout=task.timeout)
                    else:
                        result = await asyncio.wait_for(
                            asyncio.to_thread(executor, task), timeout=task.timeout
                        )

                    task.mark_completed(result)
                    duration = time.time() - start_time

                    # 更新熔断器（成功则重置）
                    self._circuit_breaker_failures = 0
                    self._circuit_breaker_open = False

                    return task.task_id, TaskResult(
                        task_id=task.task_id,
                        status=TaskStatus.COMPLETED,
                        result=result,
                        duration=duration,
                        attempts=task.attempt + 1,
                    )

                except asyncio.TimeoutError:
                    task.attempt += 1
                    error = f"Task timeout after {task.timeout}s"
                    logger.warning(f"Task {task.task_id} timeout (attempt {task.attempt})")

                    if task.can_retry():
                        wait_time = self._calculate_wait_time(task.attempt)
                        logger.info(f"Retrying after {wait_time}s")
                        await asyncio.sleep(wait_time)

                except Exception as e:
                    task.attempt += 1
                    error_type = self._classify_error(e)

                    logger.warning(
                        f"Task {task.task_id} failed (attempt {task.attempt}): {e} "
                        f"[{error_type.value}]"
                    )

                    if error_type == ErrorType.NON_RETRYABLE:
                        # 永久错误，不重试
                        break

                    if task.can_retry():
                        wait_time = self._calculate_wait_time(task.attempt)
                        logger.info(f"Retrying after {wait_time}s")
                        await asyncio.sleep(wait_time)

            # 所有重试都失败
            task.mark_failed(error)
            duration = time.time() - start_time

            # 更新熔断器
            self._circuit_breaker_failures += 1
            if self._circuit_breaker_failures >= self.config.circuit_breaker_threshold:
                self._circuit_breaker_open = True
                logger.error(
                    f"Circuit breaker opened after {self._circuit_breaker_failures} consecutive failures"
                )

            return task.task_id, TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=error,
                duration=duration,
                attempts=task.attempt,
            )

        # 并行执行所有任务
        coroutines = [execute_task(task) for task in tasks]
        task_results = await asyncio.gather(*coroutines, return_exceptions=True)

        # 收集结果
        for result in task_results:
            if isinstance(result, Exception):
                logger.error(f"Task execution raised exception: {result}")
            else:
                task_id, task_result = result
                results[task_id] = task_result

        return results

    def get_status(self) -> dict[str, Any]:
        """获取 DAG 状态"""
        return {
            "total_tasks": len(self._tasks),
            "pending": sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED),
            "circuit_breaker_open": self._circuit_breaker_open,
            "circuit_breaker_failures": self._circuit_breaker_failures,
        }


# ============================================================================
# Convenience Functions
# ============================================================================


def create_dag(config: Optional[DAGConfig] = None) -> DAGScheduler:
    """创建 DAG 调度器"""
    return DAGScheduler(config)


async def execute_dag(
    tasks: list[TaskNode],
    executor: Callable[[TaskNode], Any],
    config: Optional[DAGConfig] = None,
) -> dict[str, TaskResult]:
    """快速执行 DAG 的便捷函数

    Args:
        tasks: 任务列表
        executor: 执行器
        config: 配置

    Returns:
        结果映射
    """
    dag = DAGScheduler(config)
    for task in tasks:
        dag.add_task(task)
    return await dag.execute(executor)
