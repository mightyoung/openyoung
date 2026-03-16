"""
Task Planner - 增强的任务规划器

提供目标分解、迭代规划、子任务生成功能
参考 AutoGPT, GPT Engineer 的任务分解模式
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    """子任务状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SubTask:
    """子任务定义"""

    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # 0-10, 10为最高
    dependencies: list[str] = field(default_factory=list)
    result: Any = None
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict = field(default_factory=dict)


@dataclass
class TaskPlan:
    """任务计划"""

    id: str = field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    original_task: str = ""
    subtasks: list[SubTask] = field(default_factory=list)
    current_index: int = 0
    completed_count: int = 0
    failed_count: int = 0
    metadata: dict = field(default_factory=dict)

    def get_pending_tasks(self) -> list[SubTask]:
        """获取待执行任务"""
        return [t for t in self.subtasks if t.status == TaskStatus.PENDING]

    def get_next_task(self) -> Optional[SubTask]:
        """获取下一个可执行任务"""
        for task in self.subtasks:
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否都满足
                deps_met = all(
                    self._get_task_status(dep_id) == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_met:
                    return task
        return None

    def _get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        for task in self.subtasks:
            if task.id == task_id:
                return task.status
        return TaskStatus.PENDING

    def mark_completed(self, task_id: str, result: Any = None):
        """标记任务完成"""
        for task in self.subtasks:
            if task.id == task_id:
                task.status = TaskStatus.COMPLETED
                task.result = result
                self.completed_count += 1

    def mark_failed(self, task_id: str, error: str):
        """标记任务失败"""
        for task in self.subtasks:
            if task.id == task_id:
                task.status = TaskStatus.FAILED
                task.error = error
                self.failed_count += 1

    @property
    def is_complete(self) -> bool:
        """计划是否完成"""
        return all(t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] for t in self.subtasks)

    @property
    def success_rate(self) -> float:
        """成功率"""
        total = len(self.subtasks)
        if total == 0:
            return 0.0
        return self.completed_count / total


class TaskPlanner:
    """增强的任务规划器"""

    def __init__(self, max_subtasks: int = 10, max_depth: int = 3):
        self.max_subtasks = max_subtasks
        self.max_depth = max_depth

    async def plan(self, task: str, context: dict = None) -> TaskPlan:
        """
        生成任务计划

        Args:
            task: 原始任务描述
            context: 额外上下文信息

        Returns:
            TaskPlan: 任务计划
        """
        plan = TaskPlan(original_task=task)

        # 使用简单规则进行任务分解
        subtasks = await self._decompose_task(task, context or {})

        # 限制子任务数量
        subtasks = subtasks[: self.max_subtasks]

        # 设置依赖关系和优先级
        for i, subtask in enumerate(subtasks):
            subtask.priority = 10 - i  # 越靠前优先级越高

        plan.subtasks = subtasks
        return plan

    async def _decompose_task(self, task: str, context: dict) -> list[SubTask]:
        """
        分解任务为子任务

        基于关键词和模式的简单分解
        生产环境可以使用 LLM 进行智能分解
        """
        subtasks = []

        # 检查关键词进行分解
        task_lower = task.lower()

        # 多步骤关键词
        step_keywords = [
            ("分析", "分析问题，理解需求"),
            ("调研", "调研相关信息"),
            ("设计", "设计解决方案"),
            ("实现", "编写代码实现"),
            ("测试", "编写测试验证"),
            ("优化", "优化和改进"),
            ("文档", "编写文档"),
            ("部署", "部署和发布"),
        ]

        for keyword, description in step_keywords:
            if keyword in task:
                subtask = SubTask(
                    description=f"{description}: {task}",
                    priority=len(subtasks),
                )
                subtasks.append(subtask)

        # 如果没有匹配到关键词，创建单一任务
        if not subtasks:
            subtasks.append(
                SubTask(
                    description=task,
                    priority=0,
                )
            )

        return subtasks

    def should_replan(self, plan: TaskPlan, failed_task: SubTask) -> bool:
        """
        判断是否需要重新规划

        Args:
            plan: 当前计划
            failed_task: 失败的任务

        Returns:
            bool: 是否需要重新规划
        """
        # 如果任务失败且可以重试
        if failed_task.retry_count < failed_task.max_retries:
            return False

        # 如果失败的任务是关键路径上的
        # 检查是否有其他任务依赖这个失败的任务
        for task in plan.subtasks:
            if failed_task.id in task.dependencies:
                return True

        return False

    def create_retry_task(self, failed_task: SubTask, feedback: str) -> SubTask:
        """
        创建重试任务

        Args:
            failed_task: 失败的任务
            feedback: 反馈信息

        Returns:
            SubTask: 新的重试任务
        """
        return SubTask(
            description=f"{failed_task.description} (重试)",
            priority=failed_task.priority,
            dependencies=failed_task.dependencies,
            metadata={
                "original_task_id": failed_task.id,
                "feedback": feedback,
                "retry_count": failed_task.retry_count + 1,
            },
        )

    def get_execution_order(self, plan: TaskPlan) -> list[str]:
        """
        获取执行顺序

        返回任务ID列表，按照依赖关系排序
        """
        order = []
        completed = set()

        max_iterations = len(plan.subtasks) * 2  # 防止无限循环

        for _ in range(max_iterations):
            next_task = plan.get_next_task()
            if next_task is None:
                break

            # 检查依赖
            can_execute = all(dep_id in completed for dep_id in next_task.dependencies)

            if can_execute:
                order.append(next_task.id)
                completed.add(next_task.id)

        return order
