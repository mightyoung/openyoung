"""
Sandbox - 沙箱执行模块

提供安全的代码执行环境
参考 E2B 设计
"""

# 安全策略
# 从 sandbox.py 导入遗留类 (保持向后兼容)
import importlib.util

# E2B 适配器
from .e2b_adapter import (
    E2B_AVAILABLE,
    E2BFallback,
    E2BSandbox,
    create_e2b_sandbox,
)
from .e2b_adapter import (
    ExecutionResult as E2BExecutionResult,
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
    MCPSecurityAdapter,
    MCPSecurityConfig,
    get_mcp_security,
)
from .security_policy import (
    RiskLevel,
    SandboxPolicy,
    SecurityPolicyEngine,
    create_relaxed_policy,
    create_strict_policy,
)

_sandbox_spec = importlib.util.spec_from_file_location(
    "_legacy_sandbox", "/Users/muyi/Downloads/dev/openyoung/src/runtime/sandbox.py"
)
_sandbox_mod = importlib.util.module_from_spec(_sandbox_spec)
try:
    _sandbox_spec.loader.exec_module(_sandbox_mod)
    SandboxType = _sandbox_mod.SandboxType
    SecurityCheckResult = _sandbox_mod.SecurityCheckResult
    ExecutionResult = _sandbox_mod.ExecutionResult
    SandboxInstance = _sandbox_mod.SandboxInstance
    AISandbox = _sandbox_mod.AISandbox
    create_sandbox = _sandbox_mod.create_sandbox
    create_sandbox_config = _sandbox_mod.create_sandbox_config
except Exception:
    # 如果导入失败，使用备用定义
    from enum import Enum

    class SandboxType(str, Enum):
        PROCESS = "process"
        DOCKER = "docker"
        E2B = "e2b"

    class SecurityCheckResult:
        pass

    class ExecutionResult:
        pass

    class SandboxInstance:
        pass

    class AISandbox:
        pass

    def create_sandbox(config=None):
        return None

    def create_sandbox_config(**kwargs):
        return None


__all__ = [
    # Legacy (from sandbox.py)
    "SandboxType",
    "SecurityCheckResult",
    "ExecutionResult",
    "SandboxInstance",
    "AISandbox",
    "create_sandbox",
    "create_sandbox_config",
    # Security Policy
    "RiskLevel",
    "SandboxPolicy",
    "SecurityPolicyEngine",
    "create_strict_policy",
    "create_relaxed_policy",
    # E2B Adapter
    "E2BSandbox",
    "E2BFallback",
    "E2BExecutionResult",
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
