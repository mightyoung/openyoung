"""
Runtime - AI Docker 运行时模块

提供 Agent 执行沙箱，包含：
- 沙箱生命周期管理
- 资源限制
- 命令执行
- 评估集成
"""

from .sandbox import (
    AISandbox,
    SandboxConfig,
    SandboxType,
    ExecutionResult,
    create_sandbox,
)

from .pool import (
    SandboxPool,
    PoolConfig,
    create_pool,
)

from .security import (
    SecurityManager,
    SecurityPolicy,
    IsolationLevel,
    create_security_manager,
)

from .audit import (
    AuditLogger,
    AuditEvent,
    get_audit_logger,
    log_execution,
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
    # Security
    "SecurityManager",
    "SecurityPolicy",
    "IsolationLevel",
    "create_security_manager",
    # Audit
    "AuditLogger",
    "AuditEvent",
    "get_audit_logger",
    "log_execution",
]
