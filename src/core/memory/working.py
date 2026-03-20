"""
Working Memory (L0) - 当前任务状态存储

功能:
- 存储当前任务的运行时状态
- 任务切换时自动保存/恢复
- 与 EventBus 集成

参考: OpenViking L0 Context Loading
"""

import asyncio
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _try_create_task(coro):
    """尝试创建异步任务 (处理无事件循环的情况)"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # 无运行中的事件循环，静默忽略
        pass


@dataclass
class TaskContext:
    """任务上下文"""

    task_id: str
    task_description: str
    phase: str = "idle"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 运行时数据
    messages: list[dict[str, Any]] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs) -> "TaskContext":
        """创建更新后的副本 (不可变模式)"""
        new_ctx = TaskContext(
            task_id=kwargs.get("task_id", self.task_id),
            task_description=kwargs.get("task_description", self.task_description),
            phase=kwargs.get("phase", self.phase),
            created_at=self.created_at,
            updated_at=datetime.now().isoformat(),
            messages=kwargs.get("messages", self.messages.copy()),
            tools_used=kwargs.get("tools_used", self.tools_used.copy()),
            variables=kwargs.get("variables", self.variables.copy()),
            metadata=kwargs.get("metadata", self.metadata.copy()),
        )
        return new_ctx


class WorkingMemory:
    """Working Memory - 当前任务状态存储 (L0)

    特点:
    - 内存存储，快速访问
    - 持久化备份到磁盘
    - 线程安全
    - 与 EventBus 集成
    """

    def __init__(
        self,
        backup_dir: Optional[Path] = None,
        max_context_size: int = 10 * 1024,  # 10KB
    ):
        self._memory: dict[str, TaskContext] = {}
        self._lock = threading.RLock()
        self._max_context_size = max_context_size
        self._current_task_id: Optional[str] = None

        # 持久化目录
        self._backup_dir = backup_dir or Path.home() / ".openyoung" / "memory"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"WorkingMemory initialized with backup_dir={self._backup_dir}")

    # ====================
    # 核心操作
    # ====================

    def create_context(self, task_id: str, task_description: str = "", **kwargs) -> TaskContext:
        """创建新的任务上下文"""
        with self._lock:
            ctx = TaskContext(task_id=task_id, task_description=task_description, **kwargs)
            self._memory[task_id] = ctx
            self._current_task_id = task_id

            # 异步持久化
            _try_create_task(self._persist_async(task_id, ctx))

            logger.debug(f"Created context for task: {task_id}")
            return ctx

    def get_context(self, task_id: Optional[str] = None) -> Optional[TaskContext]:
        """获取任务上下文"""
        with self._lock:
            task_id = task_id or self._current_task_id
            return self._memory.get(task_id)

    def update_context(self, task_id: Optional[str] = None, **kwargs) -> Optional[TaskContext]:
        """更新任务上下文 (返回新副本)"""
        with self._lock:
            task_id = task_id or self._current_task_id
            if not task_id or task_id not in self._memory:
                return None

            # 不可变更新
            updated = self._memory[task_id].update(**kwargs)
            self._memory[task_id] = updated
            self._current_task_id = task_id

            # 异步持久化
            _try_create_task(self._persist_async(task_id, updated))

            return updated

    def switch_context(self, task_id: str, create_if_missing: bool = True) -> Optional[TaskContext]:
        """切换到另一个任务上下文

        Args:
            task_id: 目标任务 ID
            create_if_missing: 如果不存在是否自动创建
        """
        with self._lock:
            # 保存当前上下文
            if self._current_task_id and self._current_task_id in self._memory:
                _try_create_task(
                    self._persist_async(self._current_task_id, self._memory[self._current_task_id])
                )

            # 切换
            self._current_task_id = task_id

            # 尝试从持久化加载
            if task_id not in self._memory:
                loaded = self._load_from_disk(task_id)
                if loaded:
                    self._memory[task_id] = loaded
                elif create_if_missing:
                    # 自动创建新上下文
                    self._memory[task_id] = TaskContext(
                        task_id=task_id,
                        task_description="",
                    )

            return self._memory.get(task_id)

    def delete_context(self, task_id: str) -> bool:
        """删除任务上下文"""
        with self._lock:
            if task_id in self._memory:
                del self._memory[task_id]
                _try_create_task(self._delete_from_disk_async(task_id))

                if self._current_task_id == task_id:
                    self._current_task_id = None

                return True
            return False

    def list_contexts(self) -> list[str]:
        """列出所有任务 ID"""
        with self._lock:
            return list(self._memory.keys())

    # ====================
    # 消息和工具
    # ====================

    def add_message(
        self,
        role: str,
        content: str,
        task_id: Optional[str] = None,
    ) -> Optional[TaskContext]:
        """添加消息"""
        return self.update_context(
            task_id=task_id,
            messages=self.get_context(task_id).messages
            + [
                {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
            ],
        )

    def add_tool_used(
        self,
        tool_name: str,
        task_id: Optional[str] = None,
    ) -> Optional[TaskContext]:
        """记录使用的工具"""
        return self.update_context(
            task_id=task_id, tools_used=self.get_context(task_id).tools_used + [tool_name]
        )

    def set_variable(
        self,
        key: str,
        value: Any,
        task_id: Optional[str] = None,
    ) -> Optional[TaskContext]:
        """设置变量"""
        variables = self.get_context(task_id).variables.copy()
        variables[key] = value
        return self.update_context(task_id=task_id, variables=variables)

    def get_variable(
        self,
        key: str,
        task_id: Optional[str] = None,
        default: Any = None,
    ) -> Any:
        """获取变量"""
        ctx = self.get_context(task_id)
        return ctx.variables.get(key, default) if ctx else default

    # ====================
    # 持久化
    # ====================

    def _get_backup_path(self, task_id: str) -> Path:
        """获取备份文件路径"""
        return self._backup_dir / f"working_{task_id}.json"

    async def _persist_async(self, task_id: str, ctx: TaskContext) -> None:
        """异步持久化到磁盘"""
        try:
            path = self._get_backup_path(task_id)
            data = {
                "task_id": ctx.task_id,
                "task_description": ctx.task_description,
                "phase": ctx.phase,
                "created_at": ctx.created_at,
                "updated_at": ctx.updated_at,
                "messages": ctx.messages,
                "tools_used": ctx.tools_used,
                "variables": ctx.variables,
                "metadata": ctx.metadata,
            }
            async with asyncio.Lock():
                with open(path, "w") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Persisted context for task: {task_id}")
        except Exception as e:
            logger.warning(f"Failed to persist context for {task_id}: {e}")

    def _load_from_disk(self, task_id: str) -> Optional[TaskContext]:
        """从磁盘加载"""
        try:
            path = self._get_backup_path(task_id)
            if not path.exists():
                return None

            with open(path) as f:
                data = json.load(f)

            return TaskContext(
                task_id=data["task_id"],
                task_description=data.get("task_description", ""),
                phase=data.get("phase", "idle"),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
                messages=data.get("messages", []),
                tools_used=data.get("tools_used", []),
                variables=data.get("variables", {}),
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            logger.warning(f"Failed to load context for {task_id}: {e}")
            return None

    async def _delete_from_disk_async(self, task_id: str) -> None:
        """异步删除磁盘备份"""
        try:
            path = self._get_backup_path(task_id)
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete context for {task_id}: {e}")

    # ====================
    # 便捷方法
    # ====================

    @property
    def current_task_id(self) -> Optional[str]:
        """当前任务 ID"""
        return self._current_task_id

    def clear(self) -> None:
        """清空所有上下文"""
        with self._lock:
            self._memory.clear()
            self._current_task_id = None


# ====================
# 全局实例
# ====================

_working_memory_instance: Optional[WorkingMemory] = None


def get_working_memory() -> WorkingMemory:
    """获取全局 WorkingMemory 实例"""
    global _working_memory_instance
    if _working_memory_instance is None:
        _working_memory_instance = WorkingMemory()
    return _working_memory_instance


def set_working_memory(memory: WorkingMemory) -> None:
    """设置全局 WorkingMemory 实例"""
    global _working_memory_instance
    _working_memory_instance = memory
