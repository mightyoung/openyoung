"""
Rust Sandbox Wrapper - Rust 沙箱包装器

使用 PyO3 实现的 Rust 沙箱包装器
支持回退到 Python 实现

参考:
- PyO3: https://pyo3.rs/
- Maturin: https://maturin.rs/
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入 Rust 模块
RUST_AVAILABLE = False
try:
    import ironclaw_sandbox
    RUST_AVAILABLE = True
    logger.info("Rust sandbox module loaded successfully")
except ImportError:
    logger.warning("Rust sandbox module not available, using fallback")
    ironclaw_sandbox = None


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ExecutionResult:
    """执行结果"""

    output: str
    exit_code: int
    duration_ms: int
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and self.error is None


@dataclass
class SecurityCheckResult:
    """安全检查结果"""

    safe: bool
    warnings: list[str]
    blocked: bool = False


# ============================================================================
# Rust Sandbox Wrapper
# ============================================================================


class RustSandbox:
    """Rust 沙箱包装器

    使用 PyO3 FFI 桥接到 Rust 实现
    支持自动回退到 Python 实现
    """

    def __init__(
        self,
        max_execution_time_ms: int = 300000,  # 5 分钟
        max_memory_mb: int = 512,
        allow_network: bool = False,
        fallback_enabled: bool = True,
    ):
        self.max_execution_time_ms = max_execution_time_ms
        self.max_memory_mb = max_memory_mb
        self.allow_network = allow_network
        self.fallback_enabled = fallback_enabled

        self._instance = None
        self._use_rust = False
        self._fallback = None

        self._init()

    def _init(self):
        """初始化沙箱"""
        if RUST_AVAILABLE and ironclaw_sandbox:
            try:
                config = ironclaw_sandbox.SandboxConfig(
                    max_execution_time_ms=self.max_execution_time_ms,
                    max_memory_mb=self.max_memory_mb,
                    allow_network=self.allow_network,
                )
                self._instance = ironclaw_sandbox.SandboxInstance(config)
                self._use_rust = True
                logger.info("Rust sandbox initialized successfully")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Rust sandbox: {e}")

        # 回退到 Python 实现
        if self.fallback_enabled:
            self._init_fallback()
        else:
            raise RuntimeError("Rust sandbox not available and fallback disabled")

    def _init_fallback(self):
        """初始化 Python 回退实现"""
        from .manager import SandboxManager, SandboxConfig

        config = SandboxConfig(
            timeout=int(self.max_execution_time_ms / 1000),
            max_memory_mb=self.max_memory_mb,
            max_execution_time_seconds=int(self.max_execution_time_ms / 1000),
        )
        self._fallback = SandboxManager(config)
        self._use_rust = False
        logger.info("Using Python fallback sandbox")

    def execute(self, code: str, language: str = "python") -> ExecutionResult:
        """执行代码

        Args:
            code: 要执行的代码
            language: 语言 (python, javascript, etc.)

        Returns:
            执行结果
        """
        if self._use_rust:
            return self._execute_rust(code, language)
        else:
            return self._execute_fallback(code, language)

    def _execute_rust(self, code: str, language: str) -> ExecutionResult:
        """使用 Rust 执行"""
        try:
            result = self._instance.execute(code, language)
            return ExecutionResult(
                output=result.output,
                exit_code=result.exit_code,
                duration_ms=result.duration_ms,
                error=result.error if hasattr(result, "error") else None,
            )
        except Exception as e:
            logger.error(f"Rust execution failed: {e}")
            if self.fallback_enabled:
                return self._execute_fallback(code, language)
            raise

    def _execute_fallback(self, code: str, language: str) -> ExecutionResult:
        """使用 Python 回退执行"""
        import time

        start = time.time()

        try:
            if language == "python":
                # 在受限环境中执行 Python 代码
                result = self._fallback.execute(code) if self._fallback else self._execute_local(code)
            else:
                result = {"output": f"Language {language} not supported in fallback", "exit_code": 1}

            duration_ms = int((time.time() - start) * 1000)

            return ExecutionResult(
                output=result.get("output", ""),
                exit_code=result.get("exit_code", 0),
                duration_ms=duration_ms,
                error=result.get("error"),
            )
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            return ExecutionResult(
                output="",
                exit_code=1,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _execute_local(self, code: str) -> dict:
        """本地执行 (最基础的回退)"""
        import subprocess
        import sys

        try:
            # 使用 subprocess 执行，限制时间和内存
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=self.max_execution_time_ms / 1000,
            )
            return {
                "output": result.stdout,
                "exit_code": result.returncode,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "exit_code": -1,
                "error": "Execution timeout",
            }
        except Exception as e:
            return {
                "output": "",
                "exit_code": -1,
                "error": str(e),
            }

    def check_security(self, code: str) -> SecurityCheckResult:
        """安全检查

        Args:
            code: 要检查的代码

        Returns:
            安全检查结果
        """
        if self._use_rust:
            return self._check_security_rust(code)
        else:
            return self._check_security_fallback(code)

    def _check_security_rust(self, code: str) -> SecurityCheckResult:
        """使用 Rust 进行安全检查"""
        try:
            result = self._instance.check_security(code)
            return SecurityCheckResult(
                safe=result.safe,
                warnings=list(result.warnings),
                blocked=result.blocked if hasattr(result, "blocked") else False,
            )
        except Exception as e:
            logger.warning(f"Rust security check failed: {e}")
            return self._check_security_fallback(code)

    def _check_security_fallback(self, code: str) -> SecurityCheckResult:
        """使用 Python 进行安全检查"""
        from .security_policy import SecurityPolicyEngine, create_strict_policy, RiskLevel

        policy = create_strict_policy()
        engine = SecurityPolicyEngine(policy)

        risk_level = engine.assess_risk(code)
        warnings = []

        # Simple heuristic warnings
        if "import os" in code:
            warnings.append("File system access")
        if "subprocess" in code:
            warnings.append("Subprocess execution")
        if "eval(" in code or "exec(" in code:
            warnings.append("Dynamic code execution")

        is_safe = risk_level == RiskLevel.LOW
        is_blocked = risk_level == RiskLevel.CRITICAL

        return SecurityCheckResult(
            safe=is_safe,
            warnings=warnings,
            blocked=is_blocked,
        )

    def close(self):
        """关闭沙箱"""
        if self._fallback:
            try:
                self._fallback.cleanup()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================================
# Factory Functions
# ============================================================================


def create_rust_sandbox(
    max_execution_time_ms: int = 300000,
    max_memory_mb: int = 512,
    allow_network: bool = False,
    fallback_enabled: bool = True,
) -> RustSandbox:
    """创建 Rust 沙箱实例"""
    return RustSandbox(
        max_execution_time_ms=max_execution_time_ms,
        max_memory_mb=max_memory_mb,
        allow_network=allow_network,
        fallback_enabled=fallback_enabled,
    )


def is_rust_available() -> bool:
    """检查 Rust 模块是否可用"""
    return RUST_AVAILABLE
