"""
Sandbox Manager - 沙箱管理器

提供统一的沙箱接口，自动选择后端
支持: E2B > Docker > ERROR

安全策略:
========
ProcessSandbox 已禁用! 默认使用 E2B 或 Docker 后端。

- E2B: 提供 microVM 级别的安全隔离 (推荐)
- Docker: 提供容器级隔离 (需要 Docker 守护进程运行)
- Process: 已禁用 - 不再作为后备选项

如果 E2B 和 Docker 都不可用，将抛出 SandboxUnavailableError。

使用示例:
```python
from src.runtime.sandbox.manager import SandboxManager, SandboxConfig, SandboxBackend
from src.runtime.sandbox.security_policy import SandboxPolicy

# 默认配置 - 自动选择 E2B 或 Docker
manager = SandboxManager()

# 强制指定后端
config = SandboxConfig(backend=SandboxBackend.E2B)
manager = SandboxManager(config)

# 执行代码
result = await manager.execute("print('hello')", "python")
```
"""

import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .e2b_adapter import (
    E2B_AVAILABLE,
    E2BSandbox,
    ExecutionResult,
    create_e2b_sandbox,
)
from .security_policy import RiskLevel, SandboxPolicy, SecurityPolicyEngine

logger = logging.getLogger(__name__)


class SandboxUnavailableError(Exception):
    """Raised when no secure sandbox backend is available."""

    pass


def _check_docker_available() -> bool:
    """检查 Docker 是否可用"""
    return shutil.which("docker") is not None and _docker_daemon_running()


def _docker_daemon_running() -> bool:
    """检查 Docker 守护进程是否运行"""
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


class SandboxBackend(str, Enum):
    """沙箱后端类型"""

    E2B = "e2b"
    DOCKER = "docker"
    PROCESS = "process"  # DEPRECATED: ProcessSandbox is disabled for security


@dataclass
class SandboxConfig:
    """沙箱配置"""

    backend: SandboxBackend = SandboxBackend.E2B
    template: str = "python3"
    timeout: int = 300
    policy: SandboxPolicy = field(default_factory=SandboxPolicy)

    # 向后兼容属性 (来自原 sandbox.py)
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512
    max_execution_time_seconds: int = 300
    enable_evaluator: bool = False

    def __post_init__(self):
        """验证配置安全性"""
        if self.backend == SandboxBackend.PROCESS:
            raise ValueError(
                "PROCESS backend is disabled for security reasons. "
                "Use E2B or DOCKER backend instead."
            )


class SandboxBackendBase(ABC):
    """沙箱后端基类"""

    @abstractmethod
    async def execute(self, code: str, language: str) -> ExecutionResult:
        """执行代码"""
        pass

    @abstractmethod
    async def install(self, packages: list[str]) -> bool:
        """安装依赖"""
        pass

    @abstractmethod
    def destroy(self):
        """销毁沙箱"""
        pass


class DockerSandbox(SandboxBackendBase):
    """
    Docker 沙箱后端

    使用 Docker 容器提供隔离执行环境。
    需要 Docker 守护进程运行。
    """

    def __init__(self, config: SandboxConfig):
        self.config = config
        logger.info("Docker sandbox not yet implemented")

    async def execute(self, code: str, language: str) -> ExecutionResult:
        return ExecutionResult(
            output="",
            error="Docker sandbox not yet implemented",
            exit_code=1,
            duration_ms=0,
        )

    async def install(self, packages: list[str]) -> bool:
        return False

    def destroy(self):
        pass


class ProcessSandbox(SandboxBackendBase):
    """
    进程沙箱后端 (已禁用!)

    WARNING: ProcessSandbox 使用 subprocess.run() 执行代码，不提供真正的进程隔离。
    此后端已禁用，不再作为后备选项。

    如需真正的沙箱隔离，请使用 E2B 或 Docker 后端。
    """

    # 网络操作命令模式
    _NETWORK_PATTERNS = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "telnet", "ftp", "sftp"]

    def __init__(self, config: SandboxConfig):
        self.config = config

    def _check_network_access(self, command: str) -> bool:
        """
        检查命令是否允许网络访问

        Args:
            command: 要执行的命令

        Returns:
            bool: 是否允许网络访问
        """
        # 如果配置允许网络，则直接通过
        if getattr(self.config.policy, 'allow_network', False):
            return True

        # 检查命令是否包含网络操作模式
        for pattern in self._NETWORK_PATTERNS:
            if pattern in command:
                return False

        return True

    async def execute(self, code: str, language: str) -> ExecutionResult:
        """使用本地进程执行 (演示用)"""
        import subprocess
        import time

        start_time = time.time()

        # 构建命令用于网络检查
        if language.lower() in ("python", "py"):
            cmd_str = f"python3 -c {code}"
        else:
            cmd_str = f"bash -c {code}"

        # 检查网络访问权限
        if not self._check_network_access(cmd_str):
            return ExecutionResult(
                output="",
                error="Network access blocked: command attempts to access network",
                exit_code=1,
                duration_ms=0,
            )

        try:
            if language.lower() in ("python", "py"):
                result = subprocess.run(
                    ["python3", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout,
                )
            else:
                result = subprocess.run(
                    ["bash", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout,
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                output="",
                error="Execution timeout",
                exit_code=1,
                duration_ms=self.config.timeout * 1000,
            )
        except Exception as e:
            return ExecutionResult(
                output="",
                error=str(e),
                exit_code=1,
                duration_ms=0,
            )

    async def install(self, packages: list[str]) -> bool:
        """安装依赖"""
        import subprocess

        try:
            subprocess.run(
                ["pip", "install"] + packages,
                capture_output=True,
                timeout=120,
            )
            return True
        except Exception as e:
            logger.error(f"Package install failed: {e}")
            return False

    def destroy(self):
        pass


class SandboxManager:
    """
    沙箱管理器工厂

    自动选择最佳后端:
    1. E2B (推荐)
    2. Docker

    注意: ProcessSandbox 已禁用，不再作为后备选项。
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._backend: Optional[SandboxBackendBase] = None
        self._security_engine = SecurityPolicyEngine(self.config.policy)

    def _create_backend(self) -> SandboxBackendBase:
        """创建后端实例 (E2B > Docker > Error)"""
        if self.config.backend == SandboxBackend.E2B:
            if E2B_AVAILABLE:
                logger.info("Using E2B backend")
                return create_e2b_sandbox(
                    template=self.config.template,
                    timeout=self.config.timeout,
                    fallback=False,  # 不使用后备实现
                )
            else:
                # E2B 不可用，尝试 Docker
                logger.info("E2B not available, trying Docker")
                return self._create_docker_backend()

        elif self.config.backend == SandboxBackend.DOCKER:
            return self._create_docker_backend()

        else:
            # PROCESS 后端已在 SandboxConfig.__post_init__ 中被禁用
            # 此处不会执行到
            raise SandboxUnavailableError(
                "Process backend is disabled. Use E2B or Docker instead."
            )

    def _create_docker_backend(self) -> SandboxBackendBase:
        """创建 Docker 后端或抛出错误"""
        if _check_docker_available():
            logger.info("Using Docker backend")
            return DockerSandbox(self.config)
        else:
            raise SandboxUnavailableError(
                "No secure sandbox backend available. "
                f"E2B available: {E2B_AVAILABLE}, "
                f"Docker available: {_check_docker_available()}. "
                "Please install E2B SDK or start Docker daemon."
            )

    async def execute(
        self,
        code: str,
        language: str = "python",
        force_sandbox: bool = True,
    ) -> ExecutionResult:
        """
        执行代码 (带安全检查)

        Args:
            code: 代码
            language: 语言
            force_sandbox: 是否强制沙箱

        Returns:
            ExecutionResult: 执行结果
        """
        # 1. 安全风险评估
        risk_level = self._security_engine.assess_risk(code)

        # 2. 检查是否需要沙箱
        if force_sandbox or self._security_engine.should_force_sandbox(risk_level):
            logger.info(f"Executing in sandbox (risk: {risk_level.value})")

            if self._backend is None:
                self._backend = self._create_backend()

            return await self._backend.execute(code, language)

        else:
            logger.info(f"Executing locally (risk: {risk_level.value})")
            # 本地执行 (需要实现)
            return await self._execute_local(code, language)

    async def _execute_local(
        self,
        code: str,
        language: str,
    ) -> ExecutionResult:
        """本地执行 (非沙箱) - 禁用中"""
        raise SandboxUnavailableError(
            "Local execution is disabled for security reasons. "
            "Use a secure sandbox backend (E2B or Docker) instead."
        )

    async def install(self, packages: list[str]) -> bool:
        """安装依赖"""
        if self._backend is None:
            self._backend = self._create_backend()

        return await self._backend.install(packages)

    def destroy(self):
        """销毁沙箱"""
        if self._backend:
            self._backend.destroy()
            self._backend = None


# 全局管理器实例
_manager: Optional[SandboxManager] = None


def get_sandbox_manager(config: Optional[SandboxConfig] = None) -> SandboxManager:
    """获取沙箱管理器单例"""
    global _manager

    if _manager is None:
        _manager = SandboxManager(config)

    return _manager


def reset_sandbox_manager():
    """重置沙箱管理器"""
    global _manager

    if _manager:
        _manager.destroy()
        _manager = None
