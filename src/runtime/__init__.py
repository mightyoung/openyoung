"""
Runtime - AI Docker 运行时模块

提供 Agent 执行沙箱，包含：
- 沙箱生命周期管理
- 资源限制
- 命令执行
- 评估集成
"""

from .audit import (
    AuditEvent,
    AuditLogger,
    get_audit_logger,
    log_execution,
)
from .pool import (
    PoolConfig,
    SandboxPool,
    create_pool,
)
from .sandbox import (
    AISandbox,
    ExecutionResult,
    SandboxConfig,
    SandboxType,
    create_sandbox,
)
# Import from old security_basic.py for backward compatibility
from .security_basic import (
    IsolationLevel,
    SecurityManager,
    SecurityPolicy as OldSecurityPolicy,
    create_security_manager,
)

# Import from new security package
from .security import (
    PromptInjector,
    SecretScanner,
    Firewall,
    SecurityConfig,
    RateLimiter,
    PolicyEngine,
    Vault,
    DangerousCodeDetector,
)
from .security_client import SecurityServiceClient, create_security_client
from .context_collector import (
    ContextCollector,
    AgentContext,
    SkillInfo,
    McpInfo,
    HookInfo,
    NetworkStatus,
    ConnectionInfo,
    SubAgentExecution,
    EvaluationResult,
    IterationRecord,
    GeneInfo,
    CapsuleInfo,
    EvolutionEventInfo,
    EvolverExecution,
    create_context_collector,
)

__all__ = [
    # Sandbox
    "AISandbox",
    "SandboxConfig",
    "SandboxType",
    "ExecutionResult",
    "create_sandbox",
    # Pool
    "SandboxPool",
    "PoolConfig",
    "create_pool",
    # Security (backward compatible)
    "SecurityManager",
    "OldSecurityPolicy",
    "IsolationLevel",
    "create_security_manager",
    # Security (new)
    "PromptInjector",
    "SecretScanner",
    "Firewall",
    "SecurityConfig",
    "RateLimiter",
    "PolicyEngine",
    "Vault",
    "DangerousCodeDetector",
    # Security Client
    "SecurityServiceClient",
    "create_security_client",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
    "log_execution",
    # Context Collector
    "ContextCollector",
    "AgentContext",
    "SkillInfo",
    "McpInfo",
    "HookInfo",
    "NetworkStatus",
    "ConnectionInfo",
    "SubAgentExecution",
    "EvaluationResult",
    "IterationRecord",
    "GeneInfo",
    "CapsuleInfo",
    "EvolutionEventInfo",
    "EvolverExecution",
    "create_context_collector",
]
