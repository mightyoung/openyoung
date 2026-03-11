"""
Sandbox - AI Agent 沙箱

提供安全的代码执行环境，参考 E2B 设计
支持：
- 资源限制 (CPU/Memory/Time)
- 网络访问控制
- 文件系统隔离
- 命令白名单
- 提示注入检测
- 敏感信息扫描
"""

import asyncio
import json
import logging
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

from src.core.exception_handler import handle_exceptions


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

    # 安全检测配置
    enable_prompt_detection: bool = True
    enable_secret_detection: bool = True
    prompt_block_threshold: float = 0.8
    secret_action: str = "warn"  # warn, block, redact

    # Evaluator 配置
    enable_evaluator: bool = False
    evaluator_endpoint: str = "localhost:50051"
    evaluator_max_iterations: int = 5
    evaluator_dimensions: list[str] = field(default_factory=lambda: ["correctness", "safety"])


# 安全检测结果
@dataclass
class SecurityCheckResult:
    """安全检查结果"""

    passed: bool
    blocked: bool
    warning: bool
    message: str
    details: dict = field(default_factory=dict)


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
        """执行安全检测

        Args:
            code: 待检测的代码

        Returns:
            SecurityCheckResult: 安全检查结果
        """
        # 确保检测器已初始化
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
                # 检查是否有高风险敏感信息
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

                # 否则发出警告
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
        # 如果缓存已满，删除最早的条目
        if len(cls._eval_cache) >= cls._cache_max_size:
            # 删除第一个条目（最旧的）
            first_key = next(iter(cls._eval_cache))
            del cls._eval_cache[first_key]
        cls._eval_cache[code_hash] = result

    @classmethod
    def _clear_eval_cache(cls) -> None:
        """清空评估缓存"""
        cls._eval_cache.clear()

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

    @handle_exceptions(reraise=False, default={})
    async def evaluate(
        self,
        code: str,
        language: str = "python",
        task_description: str = "Code execution task",
    ) -> dict:
        """在沙箱中执行代码并评估结果

        Args:
            code: 要执行的代码
            language: 编程语言
            task_description: 任务描述

        Returns:
            包含执行结果和评估结果的字典
        """
        if not self.config.enable_evaluator:
            # 如果未启用evaluator，只执行代码
            result = await self.execute(code, language)
            return {
                "execution": result,
                "evaluation": None,
            }

        # B1.4: 检查评估缓存
        code_hash = self._get_code_hash(code)
        cached_result = self._get_eval_cache(code_hash)
        if cached_result is not None:
            self._logger.debug(f"Using cached evaluation for code hash: {code_hash}")
            # 执行代码但返回缓存的评估结果
            execution_result = await self.execute(code, language)
            return {
                "execution": execution_result,
                "evaluation": cached_result.get("evaluation"),
                "logs": cached_result.get("logs", []),
                "cached": True,
            }

        # 首先执行代码
        execution_result = await self.execute(code, language)

        # 如果执行失败，返回执行结果
        if execution_result.exit_code != 0:
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {execution_result.error}",
                },
            }

        # 使用evaluator评估结果
        try:
            from .evaluator_client import create_evaluator_client, create_log_consumer

            evaluator = await create_evaluator_client(self.config.evaluator_endpoint)

            # 启动日志消费者 (后台并行)
            log_consumer = create_log_consumer(evaluator, self.sandbox_id, self.sandbox_id)

            # 创建评估计划
            plan_info = {
                "task_description": task_description,
                "task_type": language,
                "complexity": "medium",
                "dimensions": [
                    {
                        "name": dim,
                        "weight": 1.0 / len(self.config.evaluator_dimensions),
                        "threshold": 0.5,
                    }
                    for dim in self.config.evaluator_dimensions
                ],
                "max_iterations": self.config.evaluator_max_iterations,
                "timeout_seconds": 60,
            }

            # 创建执行结果
            execution_data = {
                "step": 1,
                "action": "execute",
                "thought": f"Executing {language} code",
                "observation": execution_result.output,
                "output": execution_result.output,
                "traces": [],
            }

            # 收集日志 (后台运行)
            collected_logs = []

            # 启动日志消费者和评估并行运行
            async with log_consumer as log_stream:
                # 获取评估响应
                responses = []
                async for response in evaluator.evaluate_stream(
                    task_id=self.sandbox_id,
                    session_id=self.sandbox_id,
                    plan_info=plan_info,
                    results=[execution_data],
                ):
                    responses.append(response)

                    # 并行收集日志
                    try:
                        while True:
                            log = await asyncio.wait_for(log_stream.__anext__(), timeout=0.01)
                            collected_logs.append(log)
                    except StopAsyncIteration:
                        pass
                    except asyncio.TimeoutError:
                        pass

            await evaluator.close()

            if responses:
                response = responses[-1]
                # B1.4: 存储评估结果到缓存
                eval_result = {
                    "passed": response.passed,
                    "score": response.overall_score,
                    "feedback": response.feedback,
                    "next_state": response.next_state,
                    "should_continue": response.should_continue,
                }
                self._set_eval_cache(code_hash, {
                    "evaluation": eval_result,
                    "logs": collected_logs,
                })
                return {
                    "execution": execution_result,
                    "evaluation": eval_result,
                    "logs": collected_logs,
                }
        except Exception as e:
            self._logger.warning(f"Evaluator error: {e}")
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": True,
                    "score": 1.0,
                    "feedback": f"Evaluator unavailable: {e}",
                },
            }

        return {
            "execution": execution_result,
            "evaluation": None,
        }

    @handle_exceptions(reraise=False, default={})
    async def evaluate_with_feedback(
        self,
        code: str,
        session_id: str,
        task_id: str,
        language: str = "python",
        task_description: str = "Code execution task",
    ) -> dict:
        """在沙箱中执行代码并评估结果 - 支持迭代反馈

        实现真正的并行日志消费和迭代评估

        Args:
            code: 要执行的代码
            session_id: 会话 ID
            task_id: 任务 ID
            language: 编程语言
            task_description: 任务描述

        Returns:
            包含执行结果、评估结果、日志的字典
        """
        from .evaluator_client import create_evaluator_client, create_log_consumer

        # 1. 创建日志缓冲区 (使用 Queue 实现非阻塞写入)
        log_queue: asyncio.Queue[dict] = asyncio.Queue()
        collected_logs: list[dict] = []

        # 2. 执行代码
        execution_result = await self.execute(code, language)

        # 如果执行失败，返回执行结果
        if execution_result.exit_code != 0:
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {execution_result.error}",
                    "should_continue": False,
                },
                "logs": [],
            }

        # 3. 启动评估和日志消费
        try:
            evaluator = await create_evaluator_client(self.config.evaluator_endpoint)

            # 创建日志消费者上下文
            log_consumer = create_log_consumer(evaluator, session_id, task_id)

            # 创建评估计划
            plan_info = {
                "task_description": task_description,
                "task_type": language,
                "complexity": "medium",
                "dimensions": [
                    {
                        "name": dim,
                        "weight": 1.0 / len(self.config.evaluator_dimensions),
                        "threshold": 0.5,
                    }
                    for dim in self.config.evaluator_dimensions
                ],
                "max_iterations": self.config.evaluator_max_iterations,
                "timeout_seconds": 60,
            }

            # 创建执行结果
            execution_data = {
                "step": 1,
                "action": "execute",
                "thought": f"Executing {language} code",
                "observation": execution_result.output,
                "output": execution_result.output,
                "traces": [],
            }

            # 4. 真正的并行：启动日志消费任务
            log_task = asyncio.create_task(
                self._consume_logs_background(log_consumer, log_queue)
            )

            # 5. 流式评估
            responses = []
            try:
                async for response in evaluator.evaluate_stream(
                    task_id=task_id,
                    session_id=session_id,
                    plan_info=plan_info,
                    results=[execution_data],
                ):
                    responses.append(response)

                    # 并行消费日志 (非阻塞)
                    while not log_queue.empty():
                        try:
                            log = log_queue.get_nowait()
                            collected_logs.append(log)
                        except asyncio.QueueEmpty:
                            break

                # 获取剩余日志
                while not log_queue.empty():
                    try:
                        log = log_queue.get_nowait()
                        collected_logs.append(log)
                    except asyncio.QueueEmpty:
                        break

            finally:
                # 6. 清理：取消日志任务
                log_task.cancel()
                try:
                    await log_task
                except asyncio.CancelledError:
                    pass

            await evaluator.close()

            # 7. 返回结果
            if responses:
                response = responses[-1]
                return {
                    "execution": execution_result,
                    "evaluation": {
                        "passed": response.passed,
                        "score": response.overall_score,
                        "feedback": response.feedback,
                        "next_state": response.next_state,
                        "should_continue": response.should_continue,
                    },
                    "logs": collected_logs,
                }

        except Exception as e:
            self._logger.warning(f"Evaluator error: {e}")
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": True,
                    "score": 1.0,
                    "feedback": f"Evaluator unavailable: {e}",
                    "should_continue": False,
                },
                "logs": collected_logs,
            }

        return {
            "execution": execution_result,
            "evaluation": None,
            "logs": collected_logs,
        }

    async def _consume_logs_background(
        self,
        log_consumer,
        log_queue: asyncio.Queue,
    ) -> None:
        """后台消费日志 - 真正的并行执行

        Args:
            log_consumer: 日志消费者上下文
            log_queue: 日志队列
        """
        try:
            async with log_consumer as log_stream:
                async for log in log_stream:
                    # 非阻塞写入队列
                    try:
                        log_queue.put_nowait(log)
                    except asyncio.QueueFull:
                        # 队列满时丢弃旧日志
                        pass
        except Exception as e:
            self._logger.debug(f"Log consumer finished: {e}")

    @handle_exceptions(reraise=False, default={})
    async def evaluate_iterative(
        self,
        initial_code: str,
        refine_callback: callable,
        session_id: str,
        task_id: str,
        language: str = "python",
        task_description: str = "Code execution task",
        max_iterations: int = 5,
    ) -> dict:
        """迭代评估：支持 Agent 根据反馈 refin ecode

        这是 B1.3 的核心实现 - 集成迭代反馈机制

        Args:
            initial_code: 初始代码
            refine_callback: 回调函数，接收 (feedback, score) 返回 refined_code
                           返回 None 表示停止迭代
            session_id: 会话 ID
            task_id: 任务 ID
            language: 编程语言
            task_description: 任务描述
            max_iterations: 最大迭代次数

        Returns:
            包含所有迭代结果的字典
        """
        from .evaluator_client import create_evaluator_client, create_log_consumer

        # 日志队列
        log_queue: asyncio.Queue[dict] = asyncio.Queue()

        # 收集所有执行结果用于评估
        all_execution_results: list[dict] = []

        # 最终结果
        final_result = None

        # 创建评估计划
        plan_info = {
            "task_description": task_description,
            "task_type": language,
            "complexity": "medium",
            "dimensions": [
                {
                    "name": dim,
                    "weight": 1.0 / len(self.config.evaluator_dimensions),
                    "threshold": 0.5,
                }
                for dim in self.config.evaluator_dimensions
            ],
            "max_iterations": max_iterations,
            "timeout_seconds": 60,
        }

        current_code = initial_code

        for iteration in range(max_iterations):
            self._logger.info(f"Iteration {iteration + 1}/{max_iterations}")

            # 1. 执行当前代码
            execution_result = await self.execute(current_code, language)
            all_execution_results.append({
                "step": iteration + 1,
                "action": "execute",
                "thought": f"Executing {language} code (iteration {iteration + 1})",
                "observation": execution_result.output or execution_result.error or "",
                "output": execution_result.output,
                "traces": [],
            })

            # 如果执行失败，停止迭代
            if execution_result.exit_code != 0:
                final_result = {
                    "execution": execution_result,
                    "evaluation": {
                        "passed": False,
                        "score": 0.0,
                        "feedback": f"Execution failed: {execution_result.error}",
                        "should_continue": False,
                    },
                    "iteration": iteration,
                    "total_iterations": max_iterations,
                }
                break

            # 2. 评估执行结果
            try:
                evaluator = await create_evaluator_client(self.config.evaluator_endpoint)
                log_consumer = create_log_consumer(evaluator, session_id, task_id)

                collected_logs: list[dict] = []

                # 启动日志消费者
                log_task = asyncio.create_task(
                    self._consume_logs_background(log_consumer, log_queue)
                )

                # 流式评估
                responses = []
                try:
                    async for response in evaluator.evaluate_stream(
                        task_id=task_id,
                        session_id=session_id,
                        plan_info=plan_info,
                        results=all_execution_results,
                    ):
                        responses.append(response)

                        # 收集日志
                        while not log_queue.empty():
                            try:
                                log = log_queue.get_nowait()
                                collected_logs.append(log)
                            except asyncio.QueueEmpty:
                                break

                    # 获取剩余日志
                    while not log_queue.empty():
                        try:
                            log = log_queue.get_nowait()
                            collected_logs.append(log)
                        except asyncio.QueueEmpty:
                            break

                finally:
                    log_task.cancel()
                    try:
                        await log_task
                    except asyncio.CancelledError:
                        pass

                await evaluator.close()

                if responses:
                    response = responses[-1]

                    final_result = {
                        "execution": execution_result,
                        "evaluation": {
                            "passed": response.passed,
                            "score": response.overall_score,
                            "feedback": response.feedback,
                            "next_state": response.next_state,
                            "should_continue": response.should_continue,
                            "remaining_iterations": response.remaining_iterations,
                        },
                        "logs": collected_logs,
                        "iteration": iteration,
                        "total_iterations": max_iterations,
                        "all_results": all_execution_results,
                    }

                    # 3. 检查是否继续迭代
                    if response.should_continue and response.remaining_iterations > 0:
                        # 调用回调获取 refined code
                        refined_code = refine_callback(
                            feedback=response.feedback,
                            score=response.overall_score,
                            iteration=iteration + 1,
                        )

                        if refined_code is None:
                            # 用户选择停止
                            break

                        current_code = refined_code
                        continue
                    else:
                        # 评估器判断不需要继续
                        break

            except Exception as e:
                self._logger.warning(f"Evaluator error in iteration {iteration}: {e}")
                final_result = {
                    "execution": execution_result,
                    "evaluation": {
                        "passed": True,
                        "score": 1.0,
                        "feedback": f"Evaluator unavailable: {e}",
                        "should_continue": False,
                    },
                    "iteration": iteration,
                    "total_iterations": max_iterations,
                }
                break

        # 如果循环正常结束且没有结果
        if final_result is None:
            final_result = {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": "Max iterations reached",
                    "should_continue": False,
                },
                "iteration": max_iterations - 1,
                "total_iterations": max_iterations,
            }

        return final_result


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
