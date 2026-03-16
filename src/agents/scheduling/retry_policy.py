"""
Retry Policy - 重试策略模块

实现多种重试策略:
- FIXED: 固定延迟
- EXPONENTIAL: 指数退避
- LINEAR: 线性延迟
- FIBONACCI: 斐波那契延迟

参考:
- Python tenacity: https://tenacity.readthedocs.io
- Prefect retry: https://docs.prefect.io/concepts/tasks/#retrying
"""

import asyncio
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class RetryStrategy(Enum):
    """重试策略"""

    FIXED = "fixed"  # 固定延迟
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性延迟
    FIBONACCI = "fibonacci"  # 斐波那契延迟


class RetryableError(Exception):
    """可重试的错误基类"""

    def __init__(self, message: str, error_type: str = "generic"):
        super().__init__(message)
        self.error_type = error_type


@dataclass
class RetryConfig:
    """重试配置"""

    max_attempts: int = 3  # 最大尝试次数
    base_delay: float = 1.0  # 基础延迟（秒）
    max_delay: float = 60.0  # 最大延迟（秒）
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True  # 是否添加随机抖动
    jitter_factor: float = 0.5  # 抖动因子
    timeout: Optional[float] = None  # 总超时时间

    def calculate_delay(self, attempt: int) -> float:
        """计算重试延迟

        Args:
            attempt: 当前尝试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        # 根据策略计算基础延迟
        if self.strategy == RetryStrategy.FIXED:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (2**attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.FIBONACCI:
            fib = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
            delay = self.base_delay * fib[min(attempt, len(fib) - 1)]
        else:
            delay = self.base_delay * (2**attempt)

        # 限制最大延迟
        delay = min(delay, self.max_delay)

        # 添加随机抖动
        if self.jitter:
            jitter_range = delay * self.jitter_factor
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


class RetryPolicy:
    """重试策略执行器

    使用示例:
        policy = RetryPolicy(RetryConfig(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL))
        result = await policy.execute(my_async_function, arg1, arg2)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """执行函数，支持重试

        Args:
            func: 要执行的函数（同步或异步）
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 如果所有重试都失败，最后一个异常会被抛出
        """
        last_exception = None
        start_time = asyncio.get_event_loop().time()

        for attempt in range(self.config.max_attempts):
            try:
                # 检查总超时
                if self.config.timeout:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed >= self.config.timeout:
                        raise TimeoutError(f"Total timeout exceeded: {self.config.timeout}s")

                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, *args, **kwargs)

                return result

            except Exception as e:
                last_exception = e

                # 检查是否是永久错误
                if self._is_non_retryable(e):
                    raise

                # 检查是否还有重试机会
                if attempt < self.config.max_attempts - 1:
                    delay = self.config.calculate_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    break

        # 所有重试都失败
        raise last_exception

    def _is_non_retryable(self, error: Exception) -> bool:
        """判断错误是否不可重试

        Args:
            error: 异常对象

        Returns:
            是否不可重试
        """
        # 如果是 RetryableError，检查其 error_type
        if isinstance(error, RetryableError):
            return error.error_type == "permanent"

        # 基于错误消息判断
        error_msg = str(error).lower()
        non_retryable_keywords = [
            "syntax",
            "parse",
            "invalid",
            "unauthorized",
            "forbidden",
            "not found",
            "does not exist",
            "permission denied",
            "authentication",
        ]

        return any(kw in error_msg for kw in non_retryable_keywords)


# ============================================================================
# Decorator
# ============================================================================


def with_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    jitter: bool = True,
):
    """重试装饰器

    使用示例:
        @with_retry(max_attempts=3, strategy=RetryStrategy.EXPONENTIAL)
        async def my_function():
            ...
    """

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                strategy=strategy,
                base_delay=base_delay,
                jitter=jitter,
            )
            policy = RetryPolicy(config)
            return await policy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# Sync Version
# ============================================================================


class SyncRetryPolicy:
    """同步版本的重试策略"""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """同步执行函数，支持重试"""
        import time

        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e

                if self._is_non_retryable(e):
                    raise

                if attempt < self.config.max_attempts - 1:
                    delay = self.config.calculate_delay(attempt)
                    time.sleep(delay)
                else:
                    break

        raise last_exception

    def _is_non_retryable(self, error: Exception) -> bool:
        if isinstance(error, RetryableError):
            return error.error_type == "permanent"

        error_msg = str(error).lower()
        non_retryable_keywords = [
            "syntax",
            "parse",
            "invalid",
            "unauthorized",
            "forbidden",
            "not found",
            "permission denied",
        ]

        return any(kw in error_msg for kw in non_retryable_keywords)
