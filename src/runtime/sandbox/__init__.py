"""
Sandbox - 沙箱执行模块

提供安全的代码执行环境
参考 E2B 设计
"""

# 安全策略
from .security_policy import (
    RiskLevel,
    SandboxPolicy,
    SecurityPolicyEngine,
    create_strict_policy,
    create_relaxed_policy,
)

# E2B 适配器
from .e2b_adapter import (
    E2BSandbox,
    E2BFallback,
    ExecutionResult,
    create_e2b_sandbox,
    E2B_AVAILABLE,
)

# 沙箱管理器
from .manager import (
    SandboxBackend,
    SandboxConfig,
    SandboxManager,
    get_sandbox_manager,
    reset_sandbox_manager,
)

# MCP 安全
from .mcp_security import (
    MCPSecurityConfig,
    MCPSecurityAdapter,
    get_mcp_security,
)

__all__ = [
    # Security Policy
    "RiskLevel",
    "SandboxPolicy",
    "SecurityPolicyEngine",
    "create_strict_policy",
    "create_relaxed_policy",
    # E2B Adapter
    "E2BSandbox",
    "E2BFallback",
    "ExecutionResult",
    "create_e2b_sandbox",
    "E2B_AVAILABLE",
    # Manager
    "SandboxBackend",
    "SandboxConfig",
    "SandboxManager",
    "get_sandbox_manager",
    "reset_sandbox_manager",
    # MCP Security
    "MCPSecurityConfig",
    "MCPSecurityAdapter",
    "get_mcp_security",
]
