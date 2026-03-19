"""
Resource Manager - 资源分配管理

提取 Harness 系统中的资源分配逻辑。
管理 Agent 执行过程中的计算资源、内存、并发等。
"""

from typing import Any


class ResourceManager:
    """资源分配管理器

    负责管理 Agent 执行过程中的资源分配：
    - 内存限制
    - 并发控制
    - 超时管理
    """

    def __init__(
        self,
        max_memory_mb: int = 512,
        max_concurrent_tasks: int = 4,
        default_timeout_seconds: int = 300,
    ):
        """初始化 ResourceManager

        Args:
            max_memory_mb: 最大内存限制 (MB)
            max_concurrent_tasks: 最大并发任务数
            default_timeout_seconds: 默认超时时间 (秒)
        """
        self._max_memory_mb = max_memory_mb
        self._max_concurrent_tasks = max_concurrent_tasks
        self._default_timeout_seconds = default_timeout_seconds
        self._active_tasks: dict[str, Any] = {}

    def allocate(self, task_id: str, **kwargs) -> dict[str, Any]:
        """为任务分配资源

        Args:
            task_id: 任务 ID
            **kwargs: 额外分配参数

        Returns:
            资源分配结果
        """
        if len(self._active_tasks) >= self._max_concurrent_tasks:
            return {"allocated": False, "reason": "max_concurrent_tasks_reached"}

        allocation = {
            "task_id": task_id,
            "memory_mb": kwargs.get("memory_mb", self._max_memory_mb),
            "timeout_seconds": kwargs.get("timeout_seconds", self._default_timeout_seconds),
            "allocated": True,
        }
        self._active_tasks[task_id] = allocation
        return allocation

    def release(self, task_id: str) -> None:
        """释放任务资源

        Args:
            task_id: 任务 ID
        """
        self._active_tasks.pop(task_id, None)

    def get_stats(self) -> dict[str, Any]:
        """获取资源统计

        Returns:
            资源使用统计
        """
        return {
            "active_tasks": len(self._active_tasks),
            "max_concurrent_tasks": self._max_concurrent_tasks,
            "max_memory_mb": self._max_memory_mb,
            "default_timeout_seconds": self._default_timeout_seconds,
        }
