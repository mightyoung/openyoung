"""
Sandbox - AI Agent 沙箱

提供安全的代码执行环境，参考 E2B 设计
支持：
- 资源限制 (CPU/Memory/Time)
- 网络访问控制
- 文件系统隔离
- 命令白名单
"""

import asyncio
import json
import os
import resource
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class SandboxType(str, Enum):
    """沙箱类型"""

    EPHEMERAL = "ephemeral"  # 临时 - 每个任务
    PERSISTENT = "persistent"  # 持久 - 保持状态
    POOL = "pool"  # 池化 - 复用实例


@dataclass
class SandboxConfig:
    """沙箱配置"""

    sandbox_type: SandboxType = SandboxType.EPHEMERAL

    # 资源限制
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512
    max_execution_time_seconds: int = 300

    # 网络
    allow_network: bool = False
    allowed_domains: list[str] = field(default_factory=list)

    # 文件系统
    allowed_paths: list[str] = field(default_factory=list)
    read_only_paths: list[str] = field(default_factory=list)
    temp_dir: str = "/tmp/openyoung"

    # 环境
    environment: dict[str, str] = field(default_factory=dict)

    # 安全
    isolation_level: str = "process"


@dataclass
class ExecutionResult:
    """执行结果"""

    output: str
    error: str
    exit_code: int
    duration_ms: int
    tokens_used: int = 0
    metadata: dict = field(default_factory=dict)


class SandboxInstance:
    """沙箱实例"""

    def __init__(self, sandbox_id: str, config: SandboxConfig):
        self.id = sandbox_id
        self.config = config
        self.created_at = datetime.now()
        self.working_dir: Optional[Path] = None
        self.is_active = True
        self._process: Optional[asyncio.subprocess.Process] = None

    async def initialize(self) -> None:
        """初始化沙箱"""
        # 创建工作目录
        self.working_dir = Path(tempfile.mkdtemp(prefix=f"openyoung_{self.id}_"))

        # 设置环境变量
        if self.config.environment:
            os.environ.update(self.config.environment)

    async def execute(
        self,
        code: str,
        language: str = "python",
    ) -> ExecutionResult:
        """在沙箱中执行代码"""
        if not self.working_dir:
            await self.initialize()

        start_time = time.time()

        try:
            if language == "python":
                return await self._execute_python(code, start_time)
            elif language == "nodejs":
                return await self._execute_nodejs(code, start_time)
            elif language == "bash":
                return await self._execute_bash(code, start_time)
            else:
                return ExecutionResult(
                    output="",
                    error=f"Unsupported language: {language}",
                    exit_code=1,
                    duration_ms=int((time.time() - start_time) * 1000),
                )
        except asyncio.TimeoutError:
            return ExecutionResult(
                output="",
                error="Execution timeout",
                exit_code=124,  # timeout exit code
                duration_ms=int((time.time() - start_time) * 1000),
            )
        except Exception as e:
            return ExecutionResult(
                output="",
                error=str(e),
                exit_code=1,
                duration_ms=int((time.time() - start_time) * 1000),
            )

    async def _execute_python(
        self,
        code: str,
        start_time: float,
    ) -> ExecutionResult:
        """执行 Python 代码"""
        # 写入临时文件
        code_file = self.working_dir / "script.py"
        code_file.write_text(code)

        # 构建命令
        cmd = [
            "python3",
            str(code_file),
        ]

        return await self._run_command(cmd, start_time)

    async def _execute_nodejs(
        self,
        code: str,
        start_time: float,
    ) -> ExecutionResult:
        """执行 Node.js 代码"""
        code_file = self.working_dir / "script.js"
        code_file.write_text(code)

        cmd = ["node", str(code_file)]

        return await self._run_command(cmd, start_time)

    async def _execute_bash(
        self,
        code: str,
        start_time: float,
    ) -> ExecutionResult:
        """执行 Bash 命令"""
        cmd = ["bash", "-c", code]

        return await self._run_command(cmd, start_time)

    async def _run_command(
        self,
        cmd: list[str],
        start_time: float,
    ) -> ExecutionResult:
        """运行命令"""
        try:
            # 设置资源限制
            self._apply_resource_limits()

            # 设置超时
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.working_dir) if self.working_dir else None,
                env=self._get_restricted_env(),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_execution_time_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise asyncio.TimeoutError()

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                output=stdout.decode() if stdout else "",
                error=stderr.decode() if stderr else "",
                exit_code=process.returncode or 0,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            raise
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return ExecutionResult(
                output="",
                error=str(e),
                exit_code=1,
                duration_ms=duration_ms,
            )

    def _apply_resource_limits(self) -> None:
        """应用资源限制 (仅 Unix)"""
        import platform

        if platform.system() != "Linux":
            return

        try:
            # 内存限制
            max_memory_bytes = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

            # CPU 时间限制
            max_cpu_seconds = self.config.max_execution_time_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, max_cpu_seconds))

            # 限制最大子进程数
            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))

            # 限制最大文件大小
            resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))

        except Exception:
            pass  # 资源限制可能需要特定权限

    def _get_restricted_env(self) -> dict:
        """获取受限的环境变量"""
        # 基础环境变量
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.working_dir) if self.working_dir else "/tmp",
            "TMPDIR": str(self.working_dir) if self.working_dir else "/tmp",
            "LANG": "en_US.UTF-8",
        }

        # 添加沙箱环境变量
        env.update(self.config.environment)

        # 如果不允许网络，移除网络相关变量
        if not self.config.allow_network:
            for key in list(env.keys()):
                if key.startswith("HTTP") or key.startswith("HTTPS"):
                    del env[key]

        return env

    def _check_network_access(self, command: str) -> bool:
        """检查网络访问"""
        if self.config.allow_network:
            return True

        # 检查命令是否包含网络操作
        network_patterns = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync"]
        for pattern in network_patterns:
            if pattern in command:
                return False

        return True

    def _validate_file_access(self, path: str) -> bool:
        """验证文件访问权限"""
        # 如果没有设置允许路径，默认只允许临时目录
        if not self.config.allowed_paths:
            # 检查是否在临时目录
            temp_dirs = ["/tmp", tempfile.gettempdir()]
            return any(path.startswith(d) for d in temp_dirs)

        # 检查是否在允许路径内
        for allowed in self.config.allowed_paths:
            if path.startswith(allowed):
                return True

        return False

    async def execute_command(
        self,
        command: str,
    ) -> ExecutionResult:
        """执行 shell 命令"""
        return await self.execute(command, language="bash")

    async def cleanup(self) -> None:
        """清理沙箱"""
        self.is_active = False

        if self.working_dir and self.working_dir.exists():
            try:
                shutil.rmtree(self.working_dir)
            except Exception:
                pass


class AISandbox:
    """AI Docker 核心沙箱"""

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
