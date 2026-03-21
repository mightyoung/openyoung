"""
Tool Executor

网络隔离说明:
============
ToolExecutor 通过以下机制确保网络隔离:

1. 构造参数:
   - allow_network: 控制是否允许网络访问 (默认 False)

2. 网络检查 (_check_network_access):
   - 在 execute_bash 执行前检查命令是否包含网络操作
   - 检测的命令模式: curl, wget, nc, netcat, ssh, scp, rsync, telnet, ftp, sftp
   - 如果检测到网络操作且 allow_network=False, 则拒绝执行

3. 使用示例:
   ```python
   from src.tools.executor import ToolExecutor

   # 创建禁用网络的执行器
   executor = ToolExecutor(allow_network=False)

   # 执行命令 - 网络命令将被阻止
   result = await executor.execute_bash("curl https://evil.com")
   # PermissionError: Network access blocked: command contains 'curl'
   ```
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

# P0-1: Tool Contract - 2026 Best Practice
from src.tools.contract import get_tool_contract_registry

# P0-1: Tracing - 2026 Best Practice
from src.tools.tracing import SpanKind, SpanStatus, get_tracer

from .executor_methods import (
    _auto_run_tests_impl,
    _should_run_tests_impl,
    execute_bash_impl,
    execute_edit_impl,
    execute_git_impl,
    execute_glob_impl,
    execute_grep_impl,
    execute_mcp_call_impl,
    execute_mcp_list_impl,
    execute_read_impl,
    execute_web_fetch_impl,
    execute_write_impl,
)
from .executor_schemas import get_tool_schemas


@dataclass
class ToolResult:
    success: bool
    result: str
    error: str | None = None


logger = logging.getLogger(__name__)


class ToolExecutor:
    """Tool Executor with security validation and network isolation"""

    def __init__(
        self,
        workspace: str = None,
        permission_evaluator=None,
        allowed_dirs: list[str] = None,
        sandbox=None,
        allow_network: bool = False,
    ):
        # 默认使用当前工作目录或环境变量
        self.workspace = workspace or os.getcwd()
        self.permission_evaluator = permission_evaluator
        # 允许访问的目录列表
        self.allowed_dirs = allowed_dirs or [self.workspace, os.getcwd()]
        # 沙箱实例 (AI Docker)
        self._sandbox = sandbox
        self._sandbox_pool = None
        # 网络隔离配置
        self._allow_network = allow_network
        self.tools = {
            "bash": self.execute_bash,
            "write": self.execute_write,
            "edit": self.execute_edit,
            "read": self.execute_read,
            "glob": self.execute_glob,
            "grep": self.execute_grep,
            # MCP 工具
            "mcp_call": self.execute_mcp_call,
            "mcp_list": self.execute_mcp_list,
            # 增强工具
            "web_fetch": self.execute_web_fetch,
            "git": self.execute_git,
        }
        # MCP 管理器
        self._mcp_manager = None
        # P0-1: Tool Contract - 2026 Best Practice
        self._tool_contract_registry = get_tool_contract_registry()
        # P1-2: Tracing - 2026 Best Practice
        self._tracer = get_tracer("tool_executor")
        # 错误自愈配置
        self.max_retries = 3
        self.auto_fix_compile_errors = True

    def set_mcp_manager(self, mcp_manager):
        """设置 MCP 管理器"""
        self._mcp_manager = mcp_manager

    def get_tool_schemas(self) -> list:
        """Returns tool schemas - delegates to executor_schemas module."""
        return get_tool_schemas()

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        # 权限检查 - 参考 OpenCode
        if self.permission_evaluator:
            from src.core.types import PermissionAction

            action = await self.permission_evaluator.check(tool_name, arguments)

            if action == PermissionAction.DENY:
                return ToolResult(
                    success=False, result="", error=f"Permission denied: {tool_name} is not allowed"
                )

            if action == PermissionAction.ASK:
                auto_allow = os.getenv("OPENYOUNG_AUTO_ALLOW", "false").lower() == "true"

                dangerous_patterns = [
                    "rm -rf /",
                    "rm -rf ~",
                    "rm -rf /home",
                    "del /",
                    "del C:",
                    "format",
                    "shutdown",
                    "reboot",
                    "init 0",
                    "init 6",
                ]
                safe_clean_patterns = [
                    "rm -rf target",
                    "rm -rf dist",
                    "rm -rf build",
                    "rm -rf node_modules",
                    "rm -rf __pycache__",
                    "rm -rf .next",
                    "rm -rf .cache",
                ]

                args_str = str(arguments).lower()
                is_dangerous = any(p in args_str for p in dangerous_patterns)
                is_safe_clean = any(p in args_str for p in safe_clean_patterns)

                if auto_allow:
                    if is_dangerous:
                        print("  [Auto-deny] Dangerous command blocked in auto-allow mode")
                        return ToolResult(
                            success=False,
                            result="",
                            error="Permission denied: dangerous command blocked in auto-allow mode",
                        )
                    print(f"  [Auto-allowed] {tool_name} (auto-allow mode)")
                elif is_dangerous:
                    response = input(
                        "  ⚠️  This is a potentially dangerous command. Continue? [y/N]: "
                    )
                    if response.lower() not in ["y", "yes"]:
                        return ToolResult(
                            success=False, result="", error="Permission denied by user"
                        )
                elif is_safe_clean:
                    print("  [Auto-allowed] Safe clean command")
                else:
                    print("  [Auto-allowed] Non-dangerous command")

        # P0-1: Tool Contract 验证
        is_valid, contract_error = self._tool_contract_registry.validate(tool_name, arguments)
        if not is_valid:
            print(f"  [ToolContract] Validation failed: {contract_error}")
            return ToolResult(
                success=False, result="", error=f"Tool contract validation failed: {contract_error}"
            )

        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, result="", error=f"Unknown tool: {tool_name}")

        # P1-2: Tracing
        span = self._tracer.start_span(f"tool:{tool_name}", SpanKind.TOOL)
        span.set_attribute("tool_name", tool_name)
        span.set_attribute("arguments", str(arguments)[:200])

        try:
            # 错误自愈：重试机制
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    result = await tool(**arguments)

                    if self.auto_fix_compile_errors and tool_name == "bash":
                        fix_result = await self._try_auto_fix(result)
                        if fix_result:
                            result = fix_result

                    span.set_attribute("success", True)
                    span.set_attribute("attempt", attempt + 1)
                    self._tracer.end_span()
                    return ToolResult(success=True, result=result)
                except Exception as e:
                    last_error = str(e)
                    if attempt < self.max_retries - 1:
                        print(f"[Retry] Attempt {attempt + 1} failed: {e}, retrying...")
                        await asyncio.sleep(0.5 * (attempt + 1))

            span.set_attribute("success", False)
            span.set_attribute("error", last_error)
            self._tracer.end_span(SpanStatus.ERROR, last_error)
            return ToolResult(success=False, result="", error=last_error)
        except Exception as e:
            span.set_attribute("error", str(e))
            self._tracer.record_exception(e)
            raise

    async def _try_auto_fix(self, result: str) -> str | None:
        """自动修复编译错误"""
        import re

        if not result:
            return None

        rust_errors = re.findall(r"error\[E\d+\]: (.+)", result)
        if rust_errors:
            print(f"[AutoFix] Detected Rust compilation errors: {len(rust_errors)}")
            return result + "\n\n[AutoFix] Suggestion: Check error details above"

        py_errors = re.findall(r'File "(.+)", line (\d+)', result)
        if py_errors:
            print(f"[AutoFix] Detected Python errors: {len(py_errors)}")

        npm_errors = re.findall(r"error (.+?) at", result)
        if npm_errors:
            print(f"[AutoFix] Detected npm errors: {len(npm_errors)}")

        return None

    # ========== AI Docker Sandbox Support ==========

    def set_sandbox(self, sandbox) -> None:
        """设置沙箱实例"""
        self._sandbox = sandbox

    def set_sandbox_pool(self, pool) -> None:
        """设置沙箱池"""
        self._sandbox_pool = pool

    async def _execute_in_sandbox(self, command: str) -> tuple[str, int]:
        """在沙箱中执行命令"""
        if not self._sandbox and not self._sandbox_pool:
            return None, -1

        code_patterns = [
            "python",
            "python3",
            "node",
            "nodejs",
            "npm",
            "pip",
            "cargo",
            "go run",
            "ruby",
            "perl",
            "php",
        ]

        is_code_exec = any(p in command for p in code_patterns)

        if not is_code_exec:
            return None, -1

        try:
            if self._sandbox_pool:
                instance = await self._sandbox_pool.acquire(timeout=10.0)
                sandbox_id = instance.id
            elif self._sandbox:
                sandbox_id = await self._sandbox.create(f"tool_{id(command)[:8]}")
            else:
                return None, -1

            language = (
                "python" if "python" in command else "nodejs" if "node" in command else "bash"
            )

            result = await self._sandbox.execute(sandbox_id, command, language=language)

            if self._sandbox_pool and instance:
                await self._sandbox_pool.release(instance)

            return result.output + (
                f"\n[error]: {result.error}" if result.error else ""
            ), result.exit_code
        except Exception as e:
            return f"[Sandbox Error] {str(e)}", 1

    async def execute_bash(self, command: str, description: str = "") -> str:
        """Execute bash command - delegates to executor_methods."""
        return await execute_bash_impl(self, command, description)

    def _should_run_tests(self, command: str) -> bool:
        """Detect if tests should be run - delegates to executor_methods."""
        return _should_run_tests_impl(command)

    async def _auto_run_tests(self, build_command: str) -> str:
        """Auto run tests - delegates to executor_methods."""
        return await _auto_run_tests_impl(self, build_command)

    async def execute_write(self, filePath: str, content: str) -> str:
        """Write file - delegates to executor_methods."""
        return await execute_write_impl(self, filePath, content)

    async def execute_edit(self, filePath: str, old_content: str, new_content: str) -> str:
        """Edit file - delegates to executor_methods."""
        return await execute_edit_impl(self, filePath, old_content, new_content)

    async def execute_read(self, filePath: str, limit: int = None, offset: int = None) -> str:
        """Read file - delegates to executor_methods."""
        return await execute_read_impl(self, filePath, limit, offset)

    async def execute_glob(self, pattern: str) -> str:
        """Glob files - delegates to executor_methods."""
        return await execute_glob_impl(self, pattern)

    async def execute_grep(self, pattern: str, path: str = ".", include: str = None) -> str:
        """Grep search - delegates to executor_methods."""
        return await execute_grep_impl(self, pattern, path, include)

    # ========== MCP 工具 ==========

    async def execute_mcp_list(self) -> str:
        """List MCP services - delegates to executor_methods."""
        return await execute_mcp_list_impl(self)

    async def execute_mcp_call(self, server: str, method: str, params: dict = None) -> str:
        """Call MCP service - delegates to executor_methods."""
        return await execute_mcp_call_impl(self, server, method, params)

    # ========== 增强工具 ==========

    async def execute_web_fetch(self, url: str, selector: str = None) -> str:
        """Fetch web - delegates to executor_methods."""
        return await execute_web_fetch_impl(self, url, selector)

    async def execute_git(self, command: str, repo_path: str = ".") -> str:
        """Git operations - delegates to executor_methods."""
        return await execute_git_impl(self, command, repo_path)
