"""
Error Handling Utilities

提供类型安全的错误处理工具。
"""

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass
class Result(Generic[T, E]):
    """Result type for error handling - 类似 Rust 的 Result"""

    _ok: bool
    _value: T | None = None
    _error: E | None = None

    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        """创建成功 Result"""
        return cls(_ok=True, _value=value, _error=None)

    @classmethod
    def err(cls, error: E) -> "Result[T, E]":
        """创建错误 Result"""
        return cls(_ok=False, _value=None, _error=error)

    @property
    def is_ok(self) -> bool:
        return self._ok

    @property
    def is_err(self) -> bool:
        return not self._ok

    def unwrap(self) -> T:
        """获取值，失败则抛出异常"""
        if self._ok:
            return self._value
        raise RuntimeError(f"Unwrap on error: {self._error}")

    def unwrap_or(self, default: T) -> T:
        """获取值，失败返回默认值"""
        return self._value if self._ok else default

    def map(self, fn: Callable[[T], T]) -> "Result[T, E]":
        """转换成功值"""
        if self._ok:
            return Result.ok(fn(self._value))
        return self

    def map_err(self, fn: Callable[[E], E]) -> "Result[T, E]":
        """转换错误值"""
        if not self._ok:
            return Result.err(fn(self._error))
        return self


def safe_execute(
    fn: Callable[[], T], default: T | None = None, error_msg: str = ""
) -> Result[T, str]:
    """安全执行函数，返回 Result

    用法:
        result = safe_execute(lambda: risky_operation())
        if result.is_ok:
            process(result._value)
    """
    try:
        return Result.ok(fn())
    except Exception as e:
        msg = error_msg or str(e)
        return Result.err(msg)


async def safe_execute_async(fn, default=None, error_msg=""):
    """安全执行异步函数"""
    try:
        return Result.ok(await fn())
    except Exception as e:
        msg = error_msg or str(e)
        return Result.err(msg)
