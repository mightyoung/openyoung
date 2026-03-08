"""
YoungAgent Core Package
"""

from .types import (
    AgentConfig,
    AgentMode,
    ExecutionConfig,
    FlowSkillType,
    Message,
    MessageRole,
    PermissionAction,
    PermissionConfig,
    PermissionRule,
    SubAgentConfig,
    SubAgentType,
    Task,
    TaskDispatchParams,
    TaskStatus,
)

from .error_handling import Result, safe_execute

# 异常处理
from .exceptions import (
    OpenYoungError,
    AgentError,
    AgentNotFoundError,
    AgentExecutionError,
    AgentTimeoutError,
    ExecutionError,
    ToolExecutionError,
    PermissionDeniedError,
    EvaluationError,
    EvaluationTimeoutError,
    ConfigError,
    ConfigNotFoundError,
    ConfigValidationError,
    DataError,
    DataNotFoundError,
    DataValidationError,
    NetworkError,
    APITimeoutError,
    APIResponseError,
)

from .exception_handler import (
    ExceptionHandler,
    ExceptionContext,
    ErrorSeverity,
    Recoverability,
    get_exception_handler,
    set_exception_handler,
    handle_exceptions,
)

__all__ = [
    "AgentMode",
    "PermissionAction",
    "PermissionRule",
    "PermissionConfig",
    "AgentConfig",
    "SubAgentType",
    "SubAgentConfig",
    "MessageRole",
    "Message",
    "TaskStatus",
    "Task",
    "TaskDispatchParams",
    # New additions
    "ExecutionConfig",
    "FlowSkillType",
    "Result",
    "safe_execute",
    # 异常类
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
    # 异常处理器
    "ExceptionHandler",
    "ExceptionContext",
    "ErrorSeverity",
    "Recoverability",
    "get_exception_handler",
    "set_exception_handler",
    "handle_exceptions",
]
