"""
Sandbox Instance - Individual sandbox execution instance
"""

import asyncio
import logging
import resource
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional

from src.core.exception_handler import handle_exceptions

from .sandbox_config import (
    ExecutionResult,
    SandboxConfig,
    SandboxType,
    SecurityCheckResult,
)
from .sandbox_evaluator import SandboxEvaluator


class SandboxInstance(SandboxEvaluator):
    """沙箱实例"""

    # 类级别的评估缓存（所有实例共享）
    _eval_cache: dict[str, dict] = {}
    _cache_max_size: int = 100

    def __init__(self, sandbox_id: str, config: SandboxConfig):
        self.id = sandbox_id
        self.config = config
        self.created_at = datetime.now()
        self.working_dir: Optional[Path] = None
        self.is_active = True
        self._process: Optional[asyncio.subprocess.Process] = None

        # 安全检测器（延迟初始化）
        self._prompt_detector = None
        self._secret_scanner = None
        self._firewall = None
        self._logger = logging.getLogger(f"sandbox.{sandbox_id}")

    def _init_security_detectors(self) -> None:
        """初始化安全检测器"""
        if self._prompt_detector is None:
            try:
                from src.runtime.security import (
                    Firewall,
                    FirewallConfig,
                    PromptInjector,
                    SecretScanner,
                )

                self._prompt_detector = PromptInjector(
                    block_threshold=self.config.prompt_block_threshold
                )
                self._secret_scanner = SecretScanner(redact=True)
                self._firewall = Firewall(
                    FirewallConfig(allowed_domains=self.config.allowed_domains)
                )
            except ImportError as e:
                self._logger.warning(f"Security detectors not available: {e}")

    async def initialize(self) -> None:
        """初始化沙箱"""
        # 创建工作目录
        self.working_dir = Path(tempfile.mkdtemp(prefix=f"openyoung_{self.id}_"))

        # 设置环境变量
        if self.config.environment:
            import os

            os.environ.update(self.config.environment)

        # 初始化安全检测器
        self._init_security_detectors()

    async def execute(
        self,
        code: str,
        language: str = "python",
    ) -> ExecutionResult:
        """在沙箱中执行代码"""
        if not self.working_dir:
            await self.initialize()

        # 安全检测
        security_result = await self._check_security(code)
        if security_result.blocked:
            return ExecutionResult(
                output="",
                error=security_result.message,
                exit_code=1,
                duration_ms=0,
                metadata={"security_check": security_result.details},
            )

        if security_result.warning:
            self._logger.warning(f"Security warning: {security_result.message}")

        start_time = time.time()

        # 收集安全检测元数据
        security_metadata = {"security_check": security_result.details}
        if security_result.warning:
            security_metadata["security_warning"] = security_result.message

        try:
            if language == "python":
                result = await self._execute_python(code, start_time)
            elif language == "nodejs":
                result = await self._execute_nodejs(code, start_time)
            elif language == "bash":
                result = await self._execute_bash(code, start_time)
            else:
                return ExecutionResult(
                    output="",
                    error=f"Unsupported language: {language}",
                    exit_code=1,
                    duration_ms=int((time.time() - start_time) * 1000),
                )

            # 合并安全元数据
            if security_result.warning:
                result.metadata.update(security_metadata)
            return result
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

    async def _check_security(self, code: str) -> SecurityCheckResult:
        """执行安全检测"""
        self._init_security_detectors()

        # 提示注入检测
        if self.config.enable_prompt_detection and self._prompt_detector:
            prompt_result = self._prompt_detector.detect(code)
            if prompt_result.is_malicious:
                return SecurityCheckResult(
                    passed=False,
                    blocked=True,
                    warning=False,
                    message=f"Blocked: prompt injection detected ({', '.join(prompt_result.matched_patterns)})",
                    details={
                        "type": "prompt_injection",
                        "confidence": prompt_result.confidence,
                        "patterns": prompt_result.matched_patterns,
                    },
                )

        # 敏感信息检测
        if self.config.enable_secret_detection and self._secret_scanner:
            secret_result = self._secret_scanner.scan(code)
            if secret_result.has_secrets:
                if self._secret_scanner.is_high_risk(secret_result):
                    if self.config.secret_action == "block":
                        return SecurityCheckResult(
                            passed=False,
                            blocked=True,
                            warning=False,
                            message=f"Blocked: high-risk secrets detected ({len(secret_result.secrets_found)} found)",
                            details={
                                "type": "high_risk_secrets",
                                "secrets": [s.type.value for s in secret_result.secrets_found],
                            },
                        )

                return SecurityCheckResult(
                    passed=True,
                    blocked=False,
                    warning=True,
                    message=f"Warning: secrets detected ({len(secret_result.secrets_found)} found)",
                    details={
                        "type": "secrets_detected",
                        "secrets": [s.type.value for s in secret_result.secrets_found],
                    },
                )

        return SecurityCheckResult(
            passed=True,
            blocked=False,
            warning=False,
            message="Security check passed",
            details={},
        )

    async def _execute_python(self, code: str, start_time: float) -> ExecutionResult:
        """执行 Python 代码"""
        code_file = self.working_dir / "script.py"
        code_file.write_text(code)

        cmd = ["python3", str(code_file)]
        return await self._run_command(cmd, start_time)

    async def _execute_nodejs(self, code: str, start_time: float) -> ExecutionResult:
        """执行 Node.js 代码"""
        code_file = self.working_dir / "script.js"
        code_file.write_text(code)

        cmd = ["node", str(code_file)]
        return await self._run_command(cmd, start_time)

    async def _execute_bash(self, code: str, start_time: float) -> ExecutionResult:
        """执行 Bash 命令"""
        cmd = ["bash", "-c", code]
        return await self._run_command(cmd, start_time)

    async def _run_command(self, cmd: list[str], start_time: float) -> ExecutionResult:
        """运行命令"""
        try:
            if not self._check_network_access(" ".join(cmd)):
                return ExecutionResult(
                    output="",
                    error="Network access blocked: command attempts to access network",
                    exit_code=1,
                    duration_ms=0,
                    metadata={"security": "network_blocked"},
                )

            self._apply_resource_limits()

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
            max_memory_bytes = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))

            max_cpu_seconds = self.config.max_execution_time_seconds
            resource.setrlimit(resource.RLIMIT_CPU, (max_cpu_seconds, max_cpu_seconds))

            resource.setrlimit(resource.RLIMIT_NPROC, (50, 50))

            resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))

        except Exception as e:
            logging.debug(f"Failed to set resource limits: {e}")

    def _get_restricted_env(self) -> dict:
        """获取受限的环境变量"""
        env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": str(self.working_dir) if self.working_dir else "/tmp",
            "TMPDIR": str(self.working_dir) if self.working_dir else "/tmp",
            "LANG": "en_US.UTF-8",
        }

        env.update(self.config.environment)

        if not self.config.allow_network:
            for key in list(env.keys()):
                if key.startswith("HTTP") or key.startswith("HTTPS"):
                    del env[key]

        return env

    def _check_network_access(self, command: str) -> bool:
        """检查网络访问"""
        if self.config.allow_network:
            return True

        network_patterns = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync"]
        for pattern in network_patterns:
            if pattern in command:
                return False

        return True

    @classmethod
    def _get_code_hash(cls, code: str) -> str:
        """生成代码哈希用于缓存"""
        import hashlib

        return hashlib.sha256(code.encode()).hexdigest()[:16]

    @classmethod
    def _get_eval_cache(cls, code_hash: str) -> Optional[dict]:
        """获取缓存的评估结果"""
        return cls._eval_cache.get(code_hash)

    @classmethod
    def _set_eval_cache(cls, code_hash: str, result: dict) -> None:
        """设置评估结果缓存"""
        if len(cls._eval_cache) >= cls._cache_max_size:
            first_key = next(iter(cls._eval_cache))
            del cls._eval_cache[first_key]
        cls._eval_cache[code_hash] = result

    @classmethod
    def _clear_eval_cache(cls) -> None:
        """清空评估缓存"""
        cls._eval_cache.clear()

    def _validate_file_access(self, path: str) -> bool:
        """验证文件访问权限"""
        if not self.config.allowed_paths:
            temp_dirs = ["/tmp", tempfile.gettempdir()]
            return any(path.startswith(d) for d in temp_dirs)

        for allowed in self.config.allowed_paths:
            if path.startswith(allowed):
                return True

        return False

    async def execute_command(self, command: str) -> ExecutionResult:
        """执行 shell 命令"""
        return await self.execute(command, language="bash")

    async def cleanup(self) -> None:
        """清理沙箱"""
        self.is_active = False

        if self.working_dir and self.working_dir.exists():
            try:
                shutil.rmtree(self.working_dir)
            except Exception as e:
                logging.debug(f"Failed to cleanup sandbox directory: {e}")
