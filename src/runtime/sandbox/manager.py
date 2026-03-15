"""
Sandbox Manager - 沙箱管理器

提供统一的沙箱接口，自动选择后端
支持: E2B > Docker > Process
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .security_policy import SandboxPolicy, SecurityPolicyEngine, RiskLevel
from .e2b_adapter import (
    E2BSandbox,
    create_e2b_sandbox,
    ExecutionResult,
    E2B_AVAILABLE,
)

logger = logging.getLogger(__name__)


class SandboxBackend(str, Enum):
    """沙箱后端类型"""
    E2B = "e2b"
    DOCKER = "docker"
    PROCESS = "process"


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
    """Docker 沙箱后端 (未来实现)"""

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
    """进程沙箱后端 (使用现有sandbox.py)"""

    def __init__(self, config: SandboxConfig):
        self.config = config

    async def execute(self, code: str, language: str) -> ExecutionResult:
        """使用本地进程执行 (演示用)"""
        import subprocess
        import time

        start_time = time.time()

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
    3. Process (后备)
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._backend: Optional[SandboxBackendBase] = None
        self._security_engine = SecurityPolicyEngine(self.config.policy)

    def _create_backend(self) -> SandboxBackendBase:
        """创建后端实例"""
        if self.config.backend == SandboxBackend.E2B:
            if E2B_AVAILABLE:
                logger.info("Using E2B backend")
                return create_e2b_sandbox(
                    template=self.config.template,
                    timeout=self.config.timeout,
                )
            else:
                logger.warning("E2B not available, falling back to Process")
                return ProcessSandbox(self.config)

        elif self.config.backend == SandboxBackend.DOCKER:
            return DockerSandbox(self.config)

        else:
            return ProcessSandbox(self.config)

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
        """本地执行 (非沙箱)"""
        # 简化实现 - 使用ProcessSandbox
        if self._backend is None:
            self._backend = ProcessSandbox(self.config)

        return await self._backend.execute(code, language)

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
