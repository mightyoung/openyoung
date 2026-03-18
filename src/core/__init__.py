"""
YoungAgent Core Package
"""

# Heartbeat 模块
from .heartbeat import (
    HeartbeatConfig,
    HeartbeatPhase,
    HeartbeatResult,
    HeartbeatScheduler,
    get_heartbeat_scheduler,
    set_heartbeat_scheduler,
)

# 事件总线
from .events import (
    Event,
    EventBus,
    EventPriority,
    EventRegistry,
    EventType,
    HandlerResult,
    HandlerType,
    HookConfig,
    SystemEvents,
    event_bus,
    get_event_bus,
    get_hook_registry,
)

# Agent 检查点管理
from .agent_checkpoint import (
    AgentCheckpoint,
    AgentCheckpointManager,
    get_checkpoint_manager,
)

# 知识沉淀
from .knowledge import (
    KnowledgeManager,
    get_knowledge_manager,
    set_knowledge_manager,
)

# LangGraph 状态和工作流
from .langgraph_state import (
    AgentState,
    TaskPhase,
    create_initial_state,
    update_phase,
    add_message,
    set_result,
    set_error,
)

from .workflow import (
    LangGraphWorkflow,
    WorkflowNode,
    get_default_workflow,
    run_agent_workflow,
)

# LangGraph 工具和可观测性
from .langgraph_tools import (
    BaseTool,
    ToolResult,
    ToolResultStatus,
    ToolContract,
    ToolRegistry,
    get_tool_registry,
    register_tool,
    LangGraphToolAdapter,
)

from .langsmith import (
    LangSmithConfig,
    LangSmithClient,
    LangGraphTracer,
    TraceSpan,
    get_langsmith_client,
    get_tracer,
    configure_langsmith,
)

# 分层记忆系统
from .memory import (
    WorkingMemory,
    TaskContext,
    get_working_memory,
    set_working_memory,
    SemanticMemory,
    KnowledgeEntry,
    RetrievalResult,
    get_semantic_memory,
    set_semantic_memory,
    MemoryFacade,
    MemoryLayer,
    get_memory_facade,
    set_memory_facade,
    agent_state_to_checkpoint_state,
    checkpoint_state_to_agent_state,
    save_agent_state,
    load_agent_state,
    restore_from_latest,
    CheckpointWorkflowMixin,
)

from .error_handling import Result, safe_execute
from .exception_handler import (
    ErrorSeverity,
    ExceptionContext,
    ExceptionHandler,
    Recoverability,
    get_exception_handler,
    handle_exceptions,
    handle_error,
    with_error_handling,
    set_exception_handler,
    AgentErrorHandler,
    ExecutionErrorHandler,
    DAGErrorHandler,
    agent_error_handler,
    execution_error_handler,
    dag_error_handler,
)

# 异常处理
from .exceptions import (
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

__all__ = [
    # Heartbeat
    "HeartbeatConfig",
    "HeartbeatPhase",
    "HeartbeatResult",
    "HeartbeatScheduler",
    "get_heartbeat_scheduler",
    "set_heartbeat_scheduler",
    # EventBus
    "Event",
    "EventBus",
    "EventPriority",
    "EventType",
    "EventRegistry",
    "HookConfig",
    "HandlerType",
    "HandlerResult",
    "SystemEvents",
    "event_bus",
    "get_event_bus",
    "get_hook_registry",
    # Agent Checkpoint
    "AgentCheckpoint",
    "AgentCheckpointManager",
    "get_checkpoint_manager",
    # Knowledge
    "KnowledgeManager",
    "get_knowledge_manager",
    "set_knowledge_manager",
    # 类型
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
    "handle_error",
    "with_error_handling",
    "AgentErrorHandler",
    "ExecutionErrorHandler",
    "DAGErrorHandler",
    "agent_error_handler",
    "execution_error_handler",
    "dag_error_handler",
    # LangGraph 状态和工作流
    "AgentState",
    "TaskPhase",
    "create_initial_state",
    "update_phase",
    "add_message",
    "set_result",
    "set_error",
    "LangGraphWorkflow",
    "WorkflowNode",
    "get_default_workflow",
    "run_agent_workflow",
    # LangGraph 工具和可观测性
    "BaseTool",
    "ToolResult",
    "ToolResultStatus",
    "ToolContract",
    "ToolRegistry",
    "get_tool_registry",
    "register_tool",
    "LangGraphToolAdapter",
    # LangSmith
    "LangSmithConfig",
    "LangSmithClient",
    "LangGraphTracer",
    "TraceSpan",
    "get_langsmith_client",
    "get_tracer",
    "configure_langsmith",
    # 分层记忆系统
    "WorkingMemory",
    "TaskContext",
    "get_working_memory",
    "set_working_memory",
    "SemanticMemory",
    "KnowledgeEntry",
    "RetrievalResult",
    "get_semantic_memory",
    "set_semantic_memory",
    "MemoryFacade",
    "MemoryLayer",
    "get_memory_facade",
    "set_memory_facade",
    "agent_state_to_checkpoint_state",
    "checkpoint_state_to_agent_state",
    "save_agent_state",
    "load_agent_state",
    "restore_from_latest",
    "CheckpointWorkflowMixin",
]
