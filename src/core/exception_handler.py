"""
Exception Handler - 统一异常处理

提供:
- 异常转换: 通用 Exception → 统一异常
- 上下文增强: 添加执行上下文信息
- 异常链: 保留原始异常原因
- 可恢复性: 区分可恢复/不可恢复错误
- 错误回调: 支持多个回调处理同一异常类型
- 恢复策略: 自动错误恢复机制
- 错误历史: 记录和查询错误历史

参考 Python 最佳实践 (Raymond Hettinger)
"""

import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type


class ErrorSeverity(Enum):
    """错误严重程度"""

    LOW = "low"  # 可忽略
    MEDIUM = "medium"  # 需要注意
    HIGH = "high"  # 需要处理
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
    - 错误回调: 支持多个回调处理同一异常类型
    - 恢复策略: 自动错误恢复机制
    - 错误历史: 记录和查询错误历史
    """

    def __init__(self, logger=None):
        """初始化异常处理器

        Args:
            logger: 可选的日志器
        """
        self._handlers: dict[type, Callable] = {}
        self._error_callbacks: dict[Type[Exception], list[Callable]] = {}
        self._recovery_strategies: dict[Type[Exception], Callable] = {}
        self._error_log: list[ExceptionContext] = []
        self._max_log_size = 1000
        self._logger = logger

    def register_handler(self, exception_type: type, handler: Callable):
        """注册特定异常类型的处理器

        Args:
            exception_type: 异常类型
            handler: 处理函数
        """
        self._handlers[exception_type] = handler

    def register_callback(
        self, exception_type: Type[Exception], callback: Callable[[Exception], None]
    ):
        """注册异常回调 (支持多个回调 per 异常类型)

        Args:
            exception_type: 异常类型
            callback: 回调函数
        """
        if exception_type not in self._error_callbacks:
            self._error_callbacks[exception_type] = []
        self._error_callbacks[exception_type].append(callback)

    def register_recovery(
        self, exception_type: Type[Exception], recovery_fn: Callable[[Exception], Any]
    ):
        """注册恢复策略

        Args:
            exception_type: 异常类型
            recovery_fn: 恢复函数，返回恢复后的值
        """
        self._recovery_strategies[exception_type] = recovery_fn

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[ExceptionContext] = None,
        reraise: bool = True,
        convert: bool = True,
        recover: bool = True,
    ) -> Optional[Any]:
        """处理异常

        Args:
            exception: 原始异常
            context: 异常上下文
            reraise: 是否重新抛出
            convert: 是否转换为统一异常
            recover: 是否尝试恢复

        Returns:
            如果不重新抛出且恢复成功，返回恢复后的值
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

        # 4. 记录到错误历史
        self._error_log.append(context)
        if len(self._error_log) >= self._max_log_size:
            self._error_log.pop(0)

        # 5. 触发特定处理器
        original_type = type(exception)
        if original_type in self._handlers:
            self._handlers[original_type](converted, context)

        # 6. 触发回调
        self._trigger_callbacks(exception)

        # 7. 尝试恢复
        if recover:
            result = self._try_recover(exception)
            if result is not None:
                return result

        # 8. 重新抛出
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
        **kwargs,
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
            ctx = context or ExceptionContext(function=func.__name__, module=func.__module__)
            self.handle_exception(e, ctx, reraise=False, convert=True)
            return default

    async def safe_execute_async(
        self,
        func: Callable,
        *args,
        context: Optional[ExceptionContext] = None,
        default: Any = None,
        **kwargs,
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
            ctx = context or ExceptionContext(function=func.__name__, module=func.__module__)
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
                stack_trace=traceback.format_exc(),
            )
        return ExceptionContext()

    def _convert_exception(
        self, exception: Exception, context: ExceptionContext
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
                int(str(e).split()[0]) if str(e).split else 60,
            ),
            FileNotFoundError: lambda e: DataNotFoundError("file", str(e)),
            NotADirectoryError: lambda e: DataNotFoundError("directory", str(e)),
            IsADirectoryError: lambda e: DataValidationError(
                "path", "Expected file, got directory"
            ),
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

    def _log_exception(self, exception: Exception, context: ExceptionContext):
        """记录异常日志"""
        if self._logger:
            self._logger.error(f"[{type(exception).__name__}] {exception}", extra=context.to_dict())
        else:
            print(f"[ERROR] {type(exception).__name__}: {exception}")
            print(f"  Module: {context.module}")
            print(f"  Function: {context.function}")
            print(f"  Line: {context.line_number}")
            if context.additional_data:
                print(f"  Data: {context.additional_data}")

    def _trigger_callbacks(self, error: Exception):
        """触发注册的回调"""
        for exc_type, callbacks in self._error_callbacks.items():
            if isinstance(error, exc_type):
                for callback in callbacks:
                    try:
                        callback(error)
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Error in callback: {e}")

    def _try_recover(self, error: Exception) -> Optional[Any]:
        """尝试恢复"""
        for exc_type, recovery_fn in self._recovery_strategies.items():
            if isinstance(error, exc_type):
                try:
                    if self._logger:
                        self._logger.info(f"Attempting recovery for {exc_type.__name__}")
                    return recovery_fn(error)
                except Exception as e:
                    if self._logger:
                        self._logger.error(f"Recovery failed: {e}")
        return None

    def get_error_history(
        self, limit: int = 100, severity: Optional[ErrorSeverity] = None
    ) -> list[ExceptionContext]:
        """获取错误历史

        Args:
            limit: 返回的错误数量上限
            severity: 按严重级别过滤

        Returns:
            错误上下文列表
        """
        history = self._error_log[-limit:]
        if severity:
            # Filter by severity if specified (requires additional tracking)
            pass
        return history

    def clear_history(self):
        """清除错误历史"""
        self._error_log.clear()


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
    reraise: bool = True, convert: bool = True, default: Any = None, context: Optional[dict] = None
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
                    function=func.__name__, module=func.__module__, additional_data=context or {}
                )
                return handler.handle_exception(e, ctx, reraise=reraise, convert=convert) or default

        def sync_wrapper(*args, **kwargs):
            handler = get_exception_handler()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ctx = ExceptionContext(
                    function=func.__name__, module=func.__module__, additional_data=context or {}
                )
                return handler.handle_exception(e, ctx, reraise=reraise, convert=convert) or default

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def handle_error(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[dict[str, Any]] = None,
    recover: bool = True,
):
    """错误处理装饰器 (简化版本)

    Args:
        severity: 错误严重级别
        context: 额外的上下文数据
        recover: 是否尝试恢复
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_exception_handler()
                ctx = ExceptionContext(
                    function=func.__name__,
                    module=func.__module__,
                    additional_data=context or {},
                )
                return handler.handle_exception(
                    e, ctx, reraise=False, convert=True, recover=recover
                )

        return wrapper

    return decorator


def with_error_handling(
    *exception_types: Type[Exception],
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    on_error: Optional[Callable[[Exception], Any]] = None,
):
    """特定异常处理装饰器

    Args:
        exception_types: 要处理的异常类型
        severity: 错误严重级别
        on_error: 错误发生时的回调
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                handler = get_exception_handler()
                ctx = ExceptionContext(
                    function=func.__name__,
                    module=func.__module__,
                    additional_data={"args": str(args)},
                )
                result = handler.handle_exception(
                    e, ctx, reraise=False, convert=True, recover=False
                )
                if on_error:
                    return on_error(e)
                return result

        return wrapper

    return decorator


# ====================
# 特定模块的错误处理器
# ====================


class AgentErrorHandler:
    """Agent 模块错误处理器"""

    def __init__(self):
        self.handler = get_exception_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置恢复策略"""
        from src.core.exceptions import AgentNotFoundError

        def recover_agent_not_found(error: AgentNotFoundError):
            logger = logging.getLogger(__name__)
            logger.info(f"Agent not found, returning fallback: {error.agent_name}")
            return {"status": "agent_not_found", "agent": error.agent_name}

        self.handler.register_recovery(AgentNotFoundError, recover_agent_not_found)

    def handle_agent_error(self, error: Exception, agent_name: str) -> dict[str, Any]:
        """处理 Agent 错误"""
        severity = ErrorSeverity.HIGH
        if isinstance(error, AgentNotFoundError):
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, AgentError):
            severity = ErrorSeverity.HIGH

        context = ExceptionContext(
            function="handle_agent_error",
            module=self.__class__.__module__,
            additional_data={"agent_name": agent_name},
        )
        return self.handler.handle_exception(
            error, context, reraise=False, convert=True, recover=True
        )


class ExecutionErrorHandler:
    """执行模块错误处理器"""

    def __init__(self):
        self.handler = get_exception_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置恢复策略"""
        from src.core.exceptions import ToolExecutionError

        def recover_tool_error(error: ToolExecutionError):
            logger = logging.getLogger(__name__)
            logger.warning(f"Tool failed, marking as unavailable: {error.tool_name}")
            return {
                "status": "tool_unavailable",
                "tool": error.tool_name,
                "error": error.reason,
            }

        self.handler.register_recovery(ToolExecutionError, recover_tool_error)

    def handle_execution_error(
        self, error: Exception, task_id: Optional[str] = None
    ) -> dict[str, Any]:
        """处理执行错误"""
        context = ExceptionContext(
            function="handle_execution_error",
            module=self.__class__.__module__,
            additional_data={"task_id": task_id} if task_id else {},
        )
        return self.handler.handle_exception(
            error, context, reraise=False, convert=True, recover=True
        )


class DAGErrorHandler:
    """DAG 调度器错误处理器"""

    def __init__(self):
        self.handler = get_exception_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置 DAG 特定的恢复策略"""
        from src.core.exceptions import ExecutionError

        def recover_dag_failure(error: ExecutionError):
            logger = logging.getLogger(__name__)
            logger.info("DAG execution failed, returning partial results")
            return {"status": "dag_partial_failure", "error": str(error)}

        self.handler.register_recovery(ExecutionError, recover_dag_failure)

    def handle_dag_error(self, error: Exception, dag_id: str) -> dict[str, Any]:
        """处理 DAG 错误"""
        context = ExceptionContext(
            function="handle_dag_error",
            module=self.__class__.__module__,
            additional_data={"dag_id": dag_id},
        )
        return self.handler.handle_exception(
            error, context, reraise=False, convert=True, recover=True
        )


# 全局错误处理器实例
agent_error_handler = AgentErrorHandler()
execution_error_handler = ExecutionErrorHandler()
dag_error_handler = DAGErrorHandler()


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
    "handle_error",
    "with_error_handling",
    # 特定模块错误处理器
    "AgentErrorHandler",
    "ExecutionErrorHandler",
    "DAGErrorHandler",
    "agent_error_handler",
    "execution_error_handler",
    "dag_error_handler",
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
