"""
Sandbox - AI Agent 安全执行沙箱

提供安全的代码执行环境，基于 asyncio subprocess 实现。
支持：
- 资源限制 (CPU/Memory/Time) via resource模块
- 网络访问控制 via 环境变量限制
- 文件系统隔离 via 临时目录和路径验证
- 命令白名单 via PATH限制
- 提示注入检测
- 敏感信息扫描

This module re-exports from:
- sandbox_config: SandboxType, SandboxConfig, SecurityCheckResult, ExecutionResult
- sandbox_instance: SandboxInstance
"""

import uuid
from typing import Optional

# Re-export config dataclasses
from .sandbox_config import (
    ExecutionResult,
    SandboxConfig,
    SandboxType,
    SecurityCheckResult,
)

# Re-export SandboxInstance
from .sandbox_instance import SandboxInstance


class AISandbox:
    """AI Subprocess 核心沙箱

    使用 asyncio subprocess 实现安全的代码执行环境。
    不同于容器沙箱，通过以下机制实现隔离：
    - 资源限制 (CPU/Memory/Time) via resource模块
    - 网络访问控制 via 环境变量限制
    - 文件系统隔离 via 临时目录和路径验证
    - 命令白名单 via PATH限制
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self._sandboxes: dict[str, SandboxInstance] = {}

    async def create(
        self,
        agent_id: str,
        config: Optional[SandboxConfig] = None,
    ) -> str:
        """创建沙箱实例"""
        sandbox_id = f"{agent_id}_{uuid.uuid4().hex[:8]}"

        # 合并配置
        sandbox_config = config or self.config

        # 创建实例
        sandbox = SandboxInstance(sandbox_id, sandbox_config)
        await sandbox.initialize()

        self._sandboxes[sandbox_id] = sandbox

        return sandbox_id

    async def execute(
        self,
        sandbox_id: str,
        code: str,
        language: str = "python",
    ) -> ExecutionResult:
        """在沙箱中执行代码"""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return ExecutionResult(
                output="",
                error=f"Sandbox not found: {sandbox_id}",
                exit_code=1,
                duration_ms=0,
            )

        if not sandbox.is_active:
            return ExecutionResult(
                output="",
                error="Sandbox is not active",
                exit_code=1,
                duration_ms=0,
            )

        return await sandbox.execute(code, language)

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
    ) -> ExecutionResult:
        """执行 shell 命令"""
        return await self.execute(sandbox_id, command, language="bash")

    async def destroy(self, sandbox_id: str) -> None:
        """销毁沙箱"""
        sandbox = self._sandboxes.pop(sandbox_id, None)
        if sandbox:
            await sandbox.cleanup()

    async def destroy_all(self) -> None:
        """销毁所有沙箱"""
        for sandbox_id in list(self._sandboxes.keys()):
            await self.destroy(sandbox_id)

    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInstance]:
        """获取沙箱实例"""
        return self._sandboxes.get(sandbox_id)

    def list_sandboxes(self) -> list[str]:
        """列出所有沙箱"""
        return list(self._sandboxes.keys())


# ========== Convenience Functions ==========


def create_sandbox(config: Optional[SandboxConfig] = None) -> AISandbox:
    """创建沙箱实例"""
    return AISandbox(config)


def create_sandbox_config(
    sandbox_type: SandboxType = SandboxType.EPHEMERAL,
    max_memory_mb: int = 512,
    max_execution_time_seconds: int = 300,
    allow_network: bool = False,
) -> SandboxConfig:
    """创建沙箱配置"""
    return SandboxConfig(
        sandbox_type=sandbox_type,
        max_memory_mb=max_memory_mb,
        max_execution_time_seconds=max_execution_time_seconds,
        allow_network=allow_network,
    )


__all__ = [
    "SandboxType",
    "SandboxConfig",
    "SecurityCheckResult",
    "ExecutionResult",
    "SandboxInstance",
    "AISandbox",
    "create_sandbox",
    "create_sandbox_config",
]
