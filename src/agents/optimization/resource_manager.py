"""
Resource Manager - 资源管理

提供连接池、内存优化功能
"""

import asyncio
import gc
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ResourceStats:
    """资源统计"""

    connections_active: int = 0
    connections_total: int = 0
    memory_used_mb: float = 0
    memory_peak_mb: float = 0
    gc_count: int = 0


class ConnectionPool:
    """连接池"""

    def __init__(
        self,
        factory,
        min_size: int = 1,
        max_size: int = 10,
        max_idle_time: float = 300,
    ):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_time = max_idle_time

        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._active = 0
        self._total = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self):
        """获取连接"""
        conn = None

        try:
            # 尝试从池中获取
            conn = self._pool.get_nowait()
        except asyncio.QueueEmpty:
            # 池为空，创建新连接
            if self._total < self.max_size:
                async with self._lock:
                    if self._total < self.max_size:
                        self._total += 1
                conn = await self.factory()

            else:
                # 池满，等待
                conn = await self._pool.get()

        self._active += 1

        try:
            yield conn
        finally:
            self._active -= 1
            try:
                self._pool.put_nowait(conn)
            except asyncio.QueueFull:
                # 池满，关闭连接
                async with self._lock:
                    self._total -= 1
                if hasattr(conn, "close"):
                    await conn.close()

    async def close(self):
        """关闭连接池"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if hasattr(conn, "close"):
                    await conn.close()
            except asyncio.QueueEmpty:
                break


class ObjectPool:
    """对象池"""

    def __init__(self, factory, max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self._pool: list = []
        self._in_use: set = weakref.WeakSet()

    def acquire(self) -> Any:
        """获取对象"""
        # 从池中获取
        while self._pool:
            obj = self._pool.pop()
            if not self._is_valid(obj):
                continue
            self._in_use.add(obj)
            return obj

        # 池为空，创建新对象
        obj = self.factory()
        self._in_use.add(obj)
        return obj

    def release(self, obj: Any):
        """释放对象"""
        if obj in self._in_use:
            self._in_use.discard(obj)

            if len(self._pool) < self.max_size:
                if hasattr(obj, "reset"):
                    obj.reset()
                self._pool.append(obj)

    def _is_valid(self, obj: Any) -> bool:
        """检查对象是否有效"""
        # 可以添加自定义验证逻辑
        return True

    def clear(self):
        """清空池"""
        self._pool.clear()

    def get_stats(self) -> dict:
        """获取统计"""
        return {
            "pool_size": len(self._pool),
            "in_use": len(self._in_use),
            "max_size": self.max_size,
        }


class MemoryManager:
    """内存管理器"""

    def __init__(self, threshold_mb: float = 500):
        self.threshold_mb = threshold_mb
        self._peak_memory = 0

    def get_memory_usage(self) -> float:
        """获取内存使用量 (MB)"""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # 如果没有psutil，返回0
            return 0

    async def check_and_cleanup(self, force: bool = False):
        """检查并清理内存"""
        memory_mb = self.get_memory_usage()

        # 更新峰值
        if memory_mb > self._peak_memory:
            self._peak_memory = memory_mb

        # 如果超过阈值，强制垃圾回收
        if force or memory_mb > self.threshold_mb:
            gc.collect()
            return True

        return False

    def get_stats(self) -> dict:
        """获取内存统计"""
        current = self.get_memory_usage()

        return {
            "current_mb": current,
            "peak_mb": self._peak_memory,
            "threshold_mb": self.threshold_mb,
        }


class ResourceMonitor:
    """资源监控器"""

    def __init__(self):
        self._start_time = datetime.now()
        self._request_count = 0
        self._error_count = 0
        self._total_duration_ms = 0

    def record_request(self, duration_ms: int, success: bool = True):
        """记录请求"""
        self._request_count += 1
        self._total_duration_ms += duration_ms

        if not success:
            self._error_count += 1

    def get_stats(self) -> dict:
        """获取统计"""
        uptime = (datetime.now() - self._start_time).total_seconds()

        avg_duration = (
            self._total_duration_ms / self._request_count if self._request_count > 0 else 0
        )

        error_rate = self._error_count / self._request_count if self._request_count > 0 else 0

        return {
            "uptime_seconds": uptime,
            "requests": self._request_count,
            "errors": self._error_count,
            "error_rate": error_rate,
            "avg_duration_ms": avg_duration,
            "requests_per_second": self._request_count / uptime if uptime > 0 else 0,
        }


# 全局资源管理器
_resource_monitor = ResourceMonitor()


def get_resource_monitor() -> ResourceMonitor:
    """获取资源监控器"""
    return _resource_monitor


@asynccontextmanager
async def managed_resource(name: str):
    """资源管理上下文

    Usage:
        async with managed_resource("api_call") as timer:
            await api_call()
    """
    start = datetime.now()
    success = True

    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration_ms = int((datetime.now() - start).total_seconds() * 1000)
        _resource_monitor.record_request(duration_ms, success)
