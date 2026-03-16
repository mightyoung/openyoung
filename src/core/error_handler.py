"""
OpenYoung 全局异常处理器

提供统一的异常处理、日志记录和错误恢复机制
"""

import logging
import traceback
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, Type

from src.core.exceptions import (
    AgentError,
    ConfigError,
    DataError,
    EvaluationError,
    ExecutionError,
    NetworkError,
    OpenYoungError,
)

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """错误严重级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorContext:
    """错误上下文"""

    def __init__(
        self,
        error: Exception,
        severity: ErrorSeverity,
        context: Optional[dict[str, Any]] = None,
        recoverable: bool = False,
    ):
        self.error = error
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = None  # Set by handler


class ErrorHandler:
    """全局错误处理器

    特性:
    - 统一异常处理
    - 自动错误恢复
    - 错误日志记录
    - 错误回调机制
    """

    def __init__(self):
        self._error_callbacks: dict[Type[Exception], list[Callable]] = {}
        self._recovery_strategies: dict[Type[Exception], Callable] = {}
        self._error_log: list[ErrorContext] = []
        self._max_log_size = 1000

    def register_callback(
        self, exception_type: Type[Exception], callback: Callable[[Exception], None]
    ):
        """注册异常回调"""
        if exception_type not in self._error_callbacks:
            self._error_callbacks[exception_type] = []
        self._error_callbacks[exception_type].append(callback)

    def register_recovery(
        self, exception_type: Type[Exception], recovery_fn: Callable[[Exception], Any]
    ):
        """注册恢复策略"""
        self._recovery_strategies[exception_type] = recovery_fn

    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[dict[str, Any]] = None,
        recover: bool = True,
    ) -> Optional[Any]:
        """处理错误"""
        # 创建错误上下文
        error_ctx = ErrorContext(error, severity, context)
        error_ctx.timestamp = __import__("datetime").datetime.now()

        # 记录错误
        self._log_error(error_ctx)

        # 调用注册的回调
        self._trigger_callbacks(error)

        # 尝试恢复
        if recover:
            result = self._try_recover(error)
            if result is not None:
                return result

        # 返回错误传播
        if isinstance(error, OpenYoungError):
            raise error
        raise OpenYoungError(str(error), "HANDLED_ERROR")

    def _log_error(self, error_ctx: ErrorContext):
        """记录错误"""
        # 添加到日志
        if len(self._error_log) >= self._max_log_size:
            self._error_log.pop(0)
        self._error_log.append(error_ctx)

        # 打印日志
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(error_ctx.severity, logging.ERROR)

        logger.log(
            log_level,
            f"[{error_ctx.severity.value.upper()}] {type(error_ctx.error).__name__}: {str(error_ctx.error)}",
            extra={"context": error_ctx.context},
        )

        # 如果是严重错误，打印完整堆栈
        if error_ctx.severity == ErrorSeverity.CRITICAL:
            logger.critical(traceback.format_exc())

    def _trigger_callbacks(self, error: Exception):
        """触发注册的回调"""
        # 查找匹配的异常类型
        for exc_type, callbacks in self._error_callbacks.items():
            if isinstance(error, exc_type):
                for callback in callbacks:
                    try:
                        callback(error)
                    except Exception as e:
                        logger.error(f"Error in callback: {e}")

    def _try_recover(self, error: Exception) -> Optional[Any]:
        """尝试恢复"""
        # 查找恢复策略
        for exc_type, recovery_fn in self._recovery_strategies.items():
            if isinstance(error, exc_type):
                try:
                    logger.info(f"Attempting recovery for {exc_type.__name__}")
                    return recovery_fn(error)
                except Exception as e:
                    logger.error(f"Recovery failed: {e}")
        return None

    def get_error_history(
        self, limit: int = 100, severity: Optional[ErrorSeverity] = None
    ) -> list[ErrorContext]:
        """获取错误历史"""
        history = self._error_log[-limit:]
        if severity:
            history = [e for e in history if e.severity == severity]
        return history

    def clear_history(self):
        """清除错误历史"""
        self._error_log.clear()


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[dict[str, Any]] = None,
    recover: bool = True,
):
    """错误处理装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                return handler.handle_error(e, severity, context, recover)

        return wrapper

    return decorator


def with_error_handling(
    *exception_types: Type[Exception],
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    on_error: Optional[Callable[[Exception], Any]] = None,
):
    """特定异常处理装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                handler = get_error_handler()
                context = {"function": func.__name__, "args": str(args)}
                result = handler.handle_error(e, severity, context, recover=False)
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
        self.handler = get_error_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置恢复策略"""
        from src.core.exceptions import AgentNotFoundError

        def recover_agent_not_found(error: AgentNotFoundError):
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

        context = {"agent_name": agent_name}
        return self.handler.handle_error(error, severity, context)


class ExecutionErrorHandler:
    """执行模块错误处理器"""

    def __init__(self):
        self.handler = get_error_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置恢复策略"""
        from src.core.exceptions import ToolExecutionError

        def recover_tool_error(error: ToolExecutionError):
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
        context = {"task_id": task_id} if task_id else {}
        return self.handler.handle_error(error, ErrorSeverity.HIGH, context, recover=True)


class DAGErrorHandler:
    """DAG 调度器错误处理器"""

    def __init__(self):
        self.handler = get_error_handler()
        self._setup_recovery()

    def _setup_recovery(self):
        """设置 DAG 特定的恢复策略"""
        from src.core.exceptions import ExecutionError

        def recover_dag_failure(error: ExecutionError):
            logger.info("DAG execution failed, returning partial results")
            return {"status": "dag_partial_failure", "error": str(error)}

        self.handler.register_recovery(ExecutionError, recover_dag_failure)

    def handle_dag_error(self, error: Exception, dag_id: str) -> dict[str, Any]:
        """处理 DAG 错误"""
        context = {"dag_id": dag_id}
        return self.handler.handle_error(error, ErrorSeverity.CRITICAL, context, recover=True)


# 导出便捷函数
agent_error_handler = AgentErrorHandler()
execution_error_handler = ExecutionErrorHandler()
dag_error_handler = DAGErrorHandler()
