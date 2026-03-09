"""
Exception Handler - 统一异常处理

提供:
- 异常转换: 通用 Exception → 统一异常
- 上下文增强: 添加执行上下文信息
- 异常链: 保留原始异常原因
- 可恢复性: 区分可恢复/不可恢复错误

参考 Python 最佳实践 (Raymond Hettinger)
"""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"           # 可忽略
    MEDIUM = "medium"    # 需要注意
    HIGH = "high"        # 需要处理
    CRITICAL = "critical"  # 系统级错误


class Recoverability(Enum):
    """异常可恢复性"""
    RECOVERABLE = "recoverable"
    NON_RECOVERABLE = "non_recoverable"


@dataclass
class ExceptionContext:
    """异常上下文"""
    timestamp: datetime = field(default_factory=datetime.now)
    module: str = ""
    function: str = ""
    line_number: int = 0
    stack_trace: str = ""
    additional_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "stack_trace": self.stack_trace,
            "additional_data": self.additional_data,
        }


class ExceptionHandler:
    """统一异常处理器

    提供:
    - 异常转换: 通用 Exception → 统一异常
    - 上下文增强: 添加执行上下文信息
    - 异常链: 保留原始异常原因
    - 错误日志: 记录详细错误信息
    """

    def __init__(self, logger=None):
        """初始化异常处理器

        Args:
            logger: 可选的日志器
        """
        self._handlers: dict[type, Callable] = {}
        self._logger = logger

    def register_handler(self, exception_type: type, handler: Callable):
        """注册特定异常类型的处理器

        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        self._handlers[exception_type] = handler

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[ExceptionContext] = None,
        reraise: bool = True,
        convert: bool = True,
    ) -> Optional[Any]:
        """处理异常

        Args:
            exception: 原始异常
            context: 异常上下文
            reraise: 是否重新抛出
            convert: 是否转换为统一异常

        Returns:
            如果不重新抛出，返回转换后的异常
        """
        # 1. 增强上下文
        if context is None:
            context = self._create_context(exception)

        # 2. 转换异常
        if convert:
            converted = self._convert_exception(exception, context)
        else:
            converted = exception

        # 3. 记录日志
        self._log_exception(converted, context)

        # 4. 触发特定处理器
        original_type = type(exception)
        if original_type in self._handlers:
            self._handlers[original_type](converted, context)

        # 5. 重新抛出
        if reraise:
            if convert:
                raise converted from exception.__cause__
            else:
                raise

        return converted

    def safe_execute(
        self,
        func: Callable,
        *args,
        context: Optional[ExceptionContext] = None,
        default: Any = None,
        **kwargs
    ) -> Any:
        """安全执行函数，捕获并处理异常

        Args:
            func: 要执行的函数
            *args: 位置参数
            context: 异常上下文
            default: 异常时的默认返回值
            **kwargs: 关键字参数

        Returns:
            函数执行结果或默认值
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ctx = context or ExceptionContext(
                function=func.__name__,
                module=func.__module__
            )
            self.handle_exception(e, ctx, reraise=False, convert=True)
            return default

    async def safe_execute_async(
        self,
        func: Callable,
        *args,
        context: Optional[ExceptionContext] = None,
        default: Any = None,
        **kwargs
    ) -> Any:
        """安全执行异步函数

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            context: 异常上下文
            default: 异常时的默认返回值
            **kwargs: 关键字参数

        Returns:
            函数执行结果或默认值
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            ctx = context or ExceptionContext(
                function=func.__name__,
                module=func.__module__
            )
            self.handle_exception(e, ctx, reraise=False, convert=True)
            return default

    def _create_context(self, exception: Exception) -> ExceptionContext:
        """创建异常上下文"""
        tb = exception.__traceback__
        if tb:
            frame = tb.tb_frame
            return ExceptionContext(
                module=frame.f_code.co_filename,
                function=frame.f_code.co_name,
                line_number=tb.tb_lineno,
                stack_trace=traceback.format_exc()
            )
        return ExceptionContext()

    def _convert_exception(
        self,
        exception: Exception,
        context: ExceptionContext
    ) -> "OpenYoungError":
        """转换异常为统一异常

        Args:
            exception: 原始异常
            context: 异常上下文

        Returns:
            统一异常
        """
        # 避免循环导入
        from src.core.exceptions import (
            AgentError,
            AgentTimeoutError,
            APITimeoutError,
            ConfigValidationError,
            DataNotFoundError,
            EvaluationError,
            ExecutionError,
            NetworkError,
            OpenYoungError,
            PermissionDeniedError,
        )

        # 如果已经是统一异常，直接返回
        if isinstance(exception, OpenYoungError):
            return exception

        # 根据异常类型转换
        conversion_map: dict[type, Callable[[Exception], OpenYoungError]] = {
            PermissionError: lambda e: PermissionDeniedError(str(e)),
            TimeoutError: lambda e: AgentTimeoutError(
                context.additional_data.get("agent_name", "unknown"),
                int(str(e).split()[0]) if str(e).split else 60
            ),
            FileNotFoundError: lambda e: DataNotFoundError("file", str(e)),
            NotADirectoryError: lambda e: DataNotFoundError("directory", str(e)),
            IsADirectoryError: lambda e: DataValidationError("path", "Expected file, got directory"),
            ValueError: lambda e: ConfigValidationError("value", str(e)),
            KeyError: lambda e: DataNotFoundError("key", str(e)),
            TypeError: lambda e: ConfigValidationError("type", str(e)),
            AttributeError: lambda e: AgentError(f"Attribute error: {str(e)}"),
            ConnectionError: lambda e: NetworkError(f"Connection failed: {str(e)}"),
            OSError: lambda e: NetworkError(f"OS error: {str(e)}"),
        }

        converter = conversion_map.get(type(exception))
        if converter:
            return converter(exception)

        # 默认转换为通用 ExecutionError
        return ExecutionError(str(exception))

    def _log_exception(
        self,
        exception: Exception,
        context: ExceptionContext
    ):
        """记录异常日志"""
        if self._logger:
            self._logger.error(
                f"[{type(exception).__name__}] {exception}",
                extra=context.to_dict()
            )
        else:
            print(f"[ERROR] {type(exception).__name__}: {exception}")
            print(f"  Module: {context.module}")
            print(f"  Function: {context.function}")
            print(f"  Line: {context.line_number}")
            if context.additional_data:
                print(f"  Data: {context.additional_data}")


# 全局异常处理器实例
_default_handler: Optional[ExceptionHandler] = None


def get_exception_handler() -> ExceptionHandler:
    """获取全局异常处理器"""
    global _default_handler
    if _default_handler is None:
        _default_handler = ExceptionHandler()
    return _default_handler


def set_exception_handler(handler: ExceptionHandler):
    """设置全局异常处理器"""
    global _default_handler
    _default_handler = handler


# 便捷装饰器
def handle_exceptions(
    reraise: bool = True,
    convert: bool = True,
    default: Any = None,
    context: Optional[dict] = None
):
    """异常处理装饰器

    Args:
        reraise: 是否重新抛出
        convert: 是否转换为统一异常
        default: 异常时的默认返回值
        context: 额外的上下文数据

    Usage:
        @handle_exceptions(reraise=False, default="error")
        async def my_function():
            ...
    """
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            handler = get_exception_handler()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                ctx = ExceptionContext(
                    function=func.__name__,
                    module=func.__module__,
                    additional_data=context or {}
                )
                return handler.handle_exception(
                    e, ctx, reraise=reraise, convert=convert
                ) or default

        def sync_wrapper(*args, **kwargs):
            handler = get_exception_handler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = ExceptionContext(
                    function=func.__name__,
                    module=func.__module__,
                    additional_data=context or {}
                )
                return handler.handle_exception(
                    e, ctx, reraise=reraise, convert=convert
                ) or default

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# 向后兼容导入
from src.core.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentTimeoutError,
    APIResponseError,
    APITimeoutError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    DataError,
    DataNotFoundError,
    DataValidationError,
    EvaluationError,
    EvaluationTimeoutError,
    ExecutionError,
    NetworkError,
    OpenYoungError,
    PermissionDeniedError,
    ToolExecutionError,
)

__all__ = [
    # 核心类
    "ExceptionHandler",
    "ExceptionContext",
    "ErrorSeverity",
    "Recoverability",
    # 函数
    "get_exception_handler",
    "set_exception_handler",
    "handle_exceptions",
    # 异常类 (重新导出)
    "OpenYoungError",
    "AgentError",
    "AgentNotFoundError",
    "AgentExecutionError",
    "AgentTimeoutError",
    "ExecutionError",
    "ToolExecutionError",
    "PermissionDeniedError",
    "EvaluationError",
    "EvaluationTimeoutError",
    "ConfigError",
    "ConfigNotFoundError",
    "ConfigValidationError",
    "DataError",
    "DataNotFoundError",
    "DataValidationError",
    "NetworkError",
    "APITimeoutError",
    "APIResponseError",
]
