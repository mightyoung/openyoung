"""
Async Utilities - 异步工具

提供异步执行、批量处理功能
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional


@dataclass
class BatchResult:
    """批量结果"""

    total: int
    success: int
    failed: int
    results: list[Any]
    errors: list[dict]
    duration_ms: int = 0


async def batch_execute(
    items: list[Any],
    func: Callable,
    max_concurrency: int = 5,
    stop_on_error: bool = False,
) -> BatchResult:
    """批量异步执行

    Args:
        items: 要处理的项目列表
        func: 异步处理函数
        max_concurrency: 最大并发数
        stop_on_error: 遇到错误是否停止

    Returns:
        BatchResult: 批量执行结果
    """
    start_time = datetime.now()
    results = []
    errors = []

    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_semaphore(item):
        async with semaphore:
            try:
                result = await func(item)
                return {"success": True, "result": result}
            except Exception as e:
                return {"success": False, "error": str(e), "item": item}

    # 使用gather并发执行
    if stop_on_error:
        # 顺序执行，遇到错误停止
        for item in items:
            result = await process_with_semaphore(item)
            if result["success"]:
                results.append(result["result"])
            else:
                errors.append(result["error"])
                break
    else:
        # 并发执行
        batch_results = await asyncio.gather(
            *[process_with_semaphore(item) for item in items], return_exceptions=False
        )

        for result in batch_results:
            if result["success"]:
                results.append(result["result"])
            else:
                errors.append(result["error"])

    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    return BatchResult(
        total=len(items),
        success=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
        duration_ms=duration_ms,
    )


async def gather_with_limit(
    *coros,
    max_concurrent: int = 10,
) -> list[Any]:
    """限制并发数的gather

    Args:
        coros: 协程列表
        max_concurrent: 最大并发数

    Returns:
        结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def with_semaphore(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*[with_semaphore(c) for c in coros])


@asynccontextmanager
async def timeout_context(seconds: float) -> AsyncIterator[None]:
    """超时上下文管理器

    Usage:
        async with timeout_context(5.0):
            await long_operation()
    """
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        raise TimeoutError(f"Operation timed out after {seconds} seconds")


class AsyncPool:
    """异步对象池"""

    def __init__(
        self,
        factory: Callable,
        min_size: int = 1,
        max_size: int = 10,
    ):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size

        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._size = 0

    async def acquire(self) -> Any:
        """获取对象"""
        # 尝试从池中获取
        try:
            obj = self._pool.get_nowait()
            return obj
        except asyncio.QueueEmpty:
            # 池为空，创建新对象
            if self._size < self.max_size:
                self._size += 1
                return await self.factory()

            # 池满，等待释放
            obj = await self._pool.get()
            return obj

    async def release(self, obj: Any):
        """释放对象回池"""
        try:
            self._pool.put_nowait(obj)
        except asyncio.QueueFull:
            # 池满，销毁对象
            self._size -= 1
            if hasattr(obj, "close"):
                await obj.close()

    async def close(self):
        """关闭池"""
        while not self._pool.empty():
            try:
                obj = self._pool.get_nowait()
                if hasattr(obj, "close"):
                    await obj.close()
            except asyncio.QueueEmpty:
                break
        self._size = 0


class RateLimiter:
    """速率限制器"""

    def __init__(self, rate: int, per: float = 1.0):
        """初始化

        Args:
            rate: 允许的请求数
            per: 时间周期（秒）
        """
        self.rate = rate
        self.per = per
        self._tokens = rate
        self._last_update = asyncio.get_event_loop().time()

    async def acquire(self):
        """获取令牌"""
        while True:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_update

            # 补充令牌
            self._tokens = min(self.rate, self._tokens + elapsed * (self.rate / self.per))
            self._last_update = now

            if self._tokens >= 1:
                self._tokens -= 1
                return

            # 等待令牌补充
            wait_time = (1 - self._tokens) * (self.per / self.rate)
            await asyncio.sleep(wait_time)


class CircuitBreaker:
    """熔断器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """执行带熔断的调用"""
        if self._state == "open":
            # 检查是否应该进入半开状态
            if self._last_failure_time:
                now = asyncio.get_event_loop().time()
                if now - self._last_failure_time >= self.recovery_timeout:
                    self._state = "half-open"
                else:
                    raise RuntimeError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            # 成功，重置状态
            if self._state == "half-open":
                self._state = "closed"
                self._failure_count = 0

            return result

        except Exception as e:
            # 失败，增加计数
            self._failure_count += 1
            self._last_failure_time = asyncio.get_event_loop().time()

            if self._failure_count >= self.failure_threshold:
                self._state = "open"

            raise

    def get_state(self) -> dict:
        """获取状态"""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure": self._last_failure_time,
        }
