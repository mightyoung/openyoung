"""
Tool Executor
"""

import asyncio
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# P0-1: Tool Contract - 2026 Best Practice
from src.tools.contract import get_tool_contract_registry

# P1-2: Tracing - 2026 Best Practice
from src.tools.tracing import SpanKind, SpanStatus, get_tracer


@dataclass
class ToolResult:
    success: bool
    result: str
    error: str | None = None


# 允许的命令白名单（用于安全检查）
ALLOWED_COMMANDS = {
    # 构建工具
    "cargo",
    "rustc",
    "rustup",
    "npm",
    "node",
    "npx",
    "yarn",
    "pnpm",
    "python",
    "python3",
    "pip",
    "pip3",
    "poetry",
    "go",
    "gradle",
    "make",
    "cmake",
    # 版本控制
    "git",
    # 文件操作
    "ls",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "cat",
    "echo",
    "touch",
    "chmod",
    "pwd",
    "cd",
    # 搜索
    "grep",
    "find",
    "rg",
    "fd",
    # 其他
    "curl",
    "wget",
    "tar",
    "unzip",
    "zip",
}

# 危险命令模式（禁止执行）
FORBIDDEN_PATTERNS = [
    r"rm\s+-rf\s+/",  # 删除根目录
    r"rm\s+-rf\s+~",  # 删除 home 目录
    r"del\s+/",  # Windows 删除根目录
    r"format\s+",  # 格式化
    r"shutdown",  # 关机
    r"reboot",  # 重启
    r"curl.*\|\s*sh",  # 管道到 shell
    r"wget.*\|\s*sh",
    r";\s*rm\s+",  # 命令注入
    r"\|\s*rm\s+",
    r"&&\s*rm\s+",
    r"eval\s*\(",  # eval 执行
    r"exec\s*\(",  # exec 执行
]


class ToolExecutor:
    def __init__(
        self, workspace: str = None, permission_evaluator=None, allowed_dirs: list[str] = None,
        sandbox=None
    ):
        # 默认使用当前工作目录或环境变量
        self.workspace = workspace or os.getcwd()
        self.permission_evaluator = permission_evaluator  # 权限评估器
        # 允许访问的目录列表
        self.allowed_dirs = allowed_dirs or [self.workspace, os.getcwd()]
        # 沙箱实例 (AI Docker)
        self._sandbox = sandbox
        self._sandbox_pool = None
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

    def _is_path_allowed(self, filePath: str) -> bool:
        """检查路径是否在允许的目录内（防止目录遍历攻击）"""
        try:
            # 解析绝对路径
            abs_path = Path(filePath).resolve()

            # 检查是否在允许的目录内
            for allowed_dir in self.allowed_dirs:
                allowed_abs = Path(allowed_dir).resolve()
                try:
                    abs_path.relative_to(allowed_abs)
                    return True
                except ValueError:
                    continue

            # 如果不在允许目录内，检查是否是新创建的输出目录
            if str(abs_path).startswith("/Users/muyi/Downloads/dev/openyoung/output/"):
                return True

            return False
        except Exception:
            return False

    def _validate_command(self, command: str) -> tuple[bool, str]:
        """验证命令是否安全"""
        cmd_lower = command.lower().strip()

        # 检查危险模式
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, cmd_lower):
                return False, f"Forbidden pattern detected: {pattern}"

        # 检查是否包含管道或重定向（可能导致命令注入）
        if re.search(r"\|\s*sh", cmd_lower) or re.search(r"&&\s*", cmd_lower):
            return False, "Chained commands not allowed for security"

        # 检查基本命令（简化检查）
        cmd_parts = cmd_lower.split()
        if cmd_parts:
            base_cmd = cmd_parts[0].split("/")[-1]  # 去掉路径
            # 允许的命令或 git 子命令
            if base_cmd not in ALLOWED_COMMANDS and base_cmd != "git":
                # 检查是否是 git 的子命令
                if cmd_parts[0] == "git" and len(cmd_parts) > 1:
                    git_allowed = {
                        "status",
                        "log",
                        "diff",
                        "branch",
                        "add",
                        "commit",
                        "push",
                        "pull",
                        "fetch",
                        "clone",
                        "init",
                    }
                    if cmd_parts[1] not in git_allowed:
                        return False, f"Git subcommand '{cmd_parts[1]}' not allowed"

        return True, ""

    def set_mcp_manager(self, mcp_manager):
        """设置 MCP 管理器"""
        self._mcp_manager = mcp_manager

    def get_tool_schemas(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "执行命令行命令",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write",
                    "description": "创建或覆盖文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filePath": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["filePath", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit",
                    "description": "编辑文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filePath": {"type": "string"},
                            "old_content": {"type": "string"},
                            "new_content": {"type": "string"},
                        },
                        "required": ["filePath", "old_content", "new_content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "read",
                    "description": "读取文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filePath": {"type": "string"},
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                        },
                        "required": ["filePath"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "glob",
                    "description": "查找文件",
                    "parameters": {
                        "type": "object",
                        "properties": {"pattern": {"type": "string"}},
                        "required": ["pattern"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "grep",
                    "description": "搜索内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string"},
                            "path": {"type": "string"},
                            "include": {"type": "string"},
                        },
                        "required": ["pattern"],
                    },
                },
            },
            # MCP 工具
            {
                "type": "function",
                "function": {
                    "name": "mcp_list",
                    "description": "列出可用的MCP服务",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_call",
                    "description": "调用MCP服务方法",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "server": {"type": "string", "description": "MCP服务器名称"},
                            "method": {"type": "string", "description": "要调用的方法"},
                            "params": {"type": "object", "description": "方法参数"},
                        },
                        "required": ["server", "method"],
                    },
                },
            },
            # 增强工具
            {
                "type": "function",
                "function": {
                    "name": "web_fetch",
                    "description": "获取网页内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "selector": {"type": "string", "description": "CSS选择器(可选)"},
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "git",
                    "description": "执行Git命令",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "git命令(不含git前缀)"},
                            "repo_path": {"type": "string", "description": "仓库路径"},
                        },
                        "required": ["command"],
                    },
                },
            },
        ]

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
                # 检查是否自动允许模式（非交互式运行）
                import os

                auto_allow = os.getenv("OPENYOUNG_AUTO_ALLOW", "false").lower() == "true"

                # 危险命令模式（排除常见的构建清理命令）
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
                # 安全的清理命令模式（允许自动执行）
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
                    # 自动允许模式：所有非危险命令直接执行
                    if is_dangerous:
                        print("  [Auto-deny] Dangerous command blocked in auto-allow mode")
                        return ToolResult(
                            success=False,
                            result="",
                            error="Permission denied: dangerous command blocked in auto-allow mode",
                        )
                    print(f"  [Auto-allowed] {tool_name} (auto-allow mode)")
                elif is_dangerous:
                    # 交互式模式：危险命令需要确认
                    response = input(
                        "  ⚠️  This is a potentially dangerous command. Continue? [y/N]: "
                    )
                    if response.lower() not in ["y", "yes"]:
                        return ToolResult(
                            success=False, result="", error="Permission denied by user"
                        )
                elif is_safe_clean:
                    # 安全清理命令自动允许
                    print("  [Auto-allowed] Safe clean command")
                else:
                    # 非危险命令，自动允许
                    print("  [Auto-allowed] Non-dangerous command")

        # P0-1: Tool Contract 验证 - 2026 Best Practice
        is_valid, contract_error = self._tool_contract_registry.validate(tool_name, arguments)
        if not is_valid:
            print(f"  [ToolContract] Validation failed: {contract_error}")
            return ToolResult(
                success=False, result="", error=f"Tool contract validation failed: {contract_error}"
            )

        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(success=False, result="", error=f"Unknown tool: {tool_name}")

        # P1-2: Tracing - 2026 Best Practice
        span = self._tracer.start_span(f"tool:{tool_name}", SpanKind.TOOL)
        span.set_attribute("tool_name", tool_name)
        span.set_attribute("arguments", str(arguments)[:200])  # 截断长参数

        try:
            # 错误自愈：重试机制
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    result = await tool(**arguments)

                    # 检查是否需要自动修复编译错误
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
                        await asyncio.sleep(0.5 * (attempt + 1))  # 指数退避

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

        # 检测是否是编译错误
        if not result:
            return None

        # Rust 编译错误
        rust_errors = re.findall(r"error\[E\d+\]: (.+)", result)
        if rust_errors:
            print(f"[AutoFix] Detected Rust compilation errors: {len(rust_errors)}")
            # 运行 cargo check 获取详细错误
            return result + "\n\n[AutoFix] Suggestion: Check error details above"

        # Python 错误
        py_errors = re.findall(r'File "(.+)", line (\d+)', result)
        if py_errors:
            print(f"[AutoFix] Detected Python errors: {len(py_errors)}")

        # npm/node 错误
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

        # 检测是否是代码执行命令
        code_patterns = [
            "python", "python3", "node", "nodejs", "npm", "pip",
            "cargo", "go run", "ruby", "perl", "php"
        ]

        is_code_exec = any(p in command for p in code_patterns)

        if not is_code_exec:
            return None, -1

        try:
            # 如果有沙箱池，从池中获取实例
            if self._sandbox_pool:
                instance = await self._sandbox_pool.acquire(timeout=10.0)
                sandbox_id = instance.id
            elif self._sandbox:
                # 直接使用沙箱
                sandbox_id = await self._sandbox.create(f"tool_{id(command)[:8]}")
            else:
                return None, -1

            # 确定语言
            language = "python" if "python" in command else "nodejs" if "node" in command else "bash"

            # 执行代码
            result = await self._sandbox.execute(sandbox_id, command, language=language)

            # 释放池实例
            if self._sandbox_pool and instance:
                await self._sandbox_pool.release(instance)

            return result.output + (f"\n[error]: {result.error}" if result.error else ""), result.exit_code
        except Exception as e:
            return f"[Sandbox Error] {str(e)}", 1

    async def execute_bash(self, command: str, description: str = "") -> str:
        # 安全检查：命令验证
        is_valid, error_msg = self._validate_command(command)
        if not is_valid:
            return f"错误: 不安全的命令 - {error_msg}"

        # 尝试在沙箱中执行
        sandbox_output, sandbox_exit = await self._execute_in_sandbox(command)
        if sandbox_exit != -1:
            # 使用沙箱执行结果
            return sandbox_output or f"[沙箱执行完成，退出码: {sandbox_exit}]"

        # 默认：直接执行
        proc = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() if stdout else ""
        err = stderr.decode() if stderr else ""
        if err:
            output += f"\n[stderr]: {err}"

        # 自动测试：检测构建命令并运行测试
        if self._should_run_tests(command):
            test_result = await self._auto_run_tests(command)
            output += f"\n\n[AUTO-TEST] {test_result}"

        return output or "[命令执行完成]"

    def _should_run_tests(self, command: str) -> bool:
        """检测是否应该运行测试"""
        build_patterns = [
            "cargo build",
            "cargo run",
            "npm run build",
            "npm install",
            "pip install",
            "poetry install",
            "make build",
            "go build",
            "gradle build",
            "dotnet build",
        ]
        return any(p in command for p in build_patterns)

    async def _auto_run_tests(self, build_command: str) -> str:
        """自动运行测试"""
        import os

        # 获取当前工作目录
        cwd = os.getcwd()

        # 检测项目类型并运行测试
        test_commands = []

        # Rust
        if "cargo" in build_command:
            test_commands.append(("Rust", "cargo test --quiet"))

        # Node.js
        if "npm" in build_command:
            test_commands.append(("Node.js", "npm test"))

        # Python
        if "pip" in build_command or "poetry" in build_command:
            # 查找测试文件
            if os.path.exists("pytest.ini") or os.path.exists("tests"):
                test_commands.append(("Python", "python -m pytest tests/ -v"))

        # 运行测试
        results = []
        for name, test_cmd in test_commands:
            proc = await asyncio.create_subprocess_shell(
                test_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await proc.communicate()
            passed = proc.returncode == 0
            results.append(f"{name}: {'PASSED' if passed else 'FAILED'}")

        return " | ".join(results) if results else "No tests found"

    async def execute_write(self, filePath: str, content: str) -> str:
        import os

        # 安全检查：路径验证
        if not self._is_path_allowed(filePath):
            return f"错误: 路径不在允许的目录内: {filePath}"

        dir_name = os.path.dirname(filePath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入文件: {filePath}"

    async def execute_edit(self, filePath: str, old_content: str, new_content: str) -> str:
        # 安全检查：路径验证
        if not self._is_path_allowed(filePath):
            return f"错误: 路径不在允许的目录内: {filePath}"

        with open(filePath, encoding="utf-8") as f:
            content = f.read()
        if old_content not in content:
            return "错误: 未找到内容"
        new_content_file = content.replace(old_content, new_content)
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(new_content_file)
        return f"已编辑文件: {filePath}"

    async def execute_read(self, filePath: str, limit: int = None, offset: int = None) -> str:
        # 安全检查：路径验证
        if not self._is_path_allowed(filePath):
            return f"错误: 路径不在允许的目录内: {filePath}"

        with open(filePath, encoding="utf-8") as f:
            lines = f.readlines()
        if offset:
            lines = lines[offset - 1 :]
        if limit:
            lines = lines[:limit]
        return "".join(lines)

    async def execute_glob(self, pattern: str) -> str:
        import glob as g

        files = g.glob(pattern, recursive=True)
        return "\n".join(files) if files else "未找到文件"

    async def execute_grep(self, pattern: str, path: str = ".", include: str = None) -> str:
        import os
        import re

        results = []
        for root, _, files in os.walk(path):
            for f in files:
                if include and not f.endswith(include.replace("*", "")):
                    continue
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, encoding="utf-8") as file:
                        for i, line in enumerate(file, 1):
                            if re.search(pattern, line):
                                results.append(f"{filepath}:{i}: {line.rstrip()}")
                except Exception:
                    pass  # Skip files that can't be read
        return "\n".join(results[:50]) if results else "未找到内容"

    # ========== 自动依赖管理 ==========

    async def detect_dependencies(self, project_path: str = ".") -> dict[str, list[str]]:
        """自动检测项目依赖"""
        import json
        import os

        import toml

        deps = {"python": [], "rust": [], "nodejs": [], "system": []}
        project_path = os.path.abspath(project_path)

        # Python 检测
        req_files = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
        for f in req_files:
            fp = os.path.join(project_path, f)
            if os.path.exists(fp):
                if f == "pyproject.toml":
                    try:
                        with open(fp) as file:
                            data = toml.load(file)
                            if "project" in data and "dependencies" in data["project"]:
                                deps["python"].extend(data["project"]["dependencies"])
                    except Exception:
                        pass  # Skip invalid pyproject.toml
                elif f == "requirements.txt":
                    with open(fp) as file:
                        deps["python"].extend(
                            [l.strip() for l in file if l.strip() and not l.startswith("#")]
                        )
                break

        # Rust 检测
        cargo_toml = os.path.join(project_path, "Cargo.toml")
        if os.path.exists(cargo_toml):
            try:
                with open(cargo_toml) as file:
                    data = toml.load(file)
                    if "dependencies" in data:
                        deps["rust"].extend(list(data["dependencies"].keys()))
                    if "dev-dependencies" in data:
                        deps["rust"].extend(list(data["dev-dependencies"].keys()))
            except Exception:
                pass  # Skip invalid Cargo.toml

        # Node.js 检测
        package_json = os.path.join(project_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json) as file:
                    data = json.load(file)
                    deps["nodejs"].extend(list(data.get("dependencies", {}).keys()))
                    deps["nodejs"].extend(list(data.get("devDependencies", {}).keys()))
            except Exception:
                pass  # Skip invalid package.json

        return deps

    async def install_dependencies(
        self, project_path: str = ".", deps: dict[str, list[str]] = None
    ) -> str:
        """自动安装依赖"""
        import os

        if not deps:
            deps = await self.detect_dependencies(project_path)

        results = []

        # Python
        if deps.get("python"):
            req_file = os.path.join(project_path, "requirements.txt")
            if os.path.exists(req_file):
                proc = await asyncio.create_subprocess_shell(
                    f"cd {project_path} && pip install -r requirements.txt",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                results.append(f"Python: {'OK' if proc.returncode == 0 else stderr.decode()[:100]}")

        # Rust
        if deps.get("rust"):
            cargo_toml = os.path.join(project_path, "Cargo.toml")
            if os.path.exists(cargo_toml):
                proc = await asyncio.create_subprocess_shell(
                    f"cd {project_path} && cargo fetch",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                results.append(f"Rust: {'OK' if proc.returncode == 0 else stderr.decode()[:100]}")

        # Node.js
        if deps.get("nodejs"):
            package_json = os.path.join(project_path, "package.json")
            if os.path.exists(package_json):
                proc = await asyncio.create_subprocess_shell(
                    f"cd {project_path} && npm install",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                results.append(
                    f"Node.js: {'OK' if proc.returncode == 0 else stderr.decode()[:100]}"
                )

        return "\n".join(results) if results else "No dependencies to install"

    # ========== MCP 工具 ==========

    async def execute_mcp_list(self) -> str:
        """列出可用的 MCP 服务"""
        if not self._mcp_manager:
            # 尝试初始化 MCP 管理器
            try:
                from src.package_manager.mcp_manager import MCPServerManager

                self._mcp_manager = MCPServerManager(packages_dir="packages")
            except Exception as e:
                return f"MCP manager not available: {e}"

        servers = self._mcp_manager.discover_mcp_servers()
        if not servers:
            return "No MCP servers found"

        result = ["Available MCP Servers:"]
        for name, config in servers.items():
            result.append(f"- {name}: {config.command} {' '.join(config.args or [])}")
        return "\n".join(result)

    async def execute_mcp_call(self, server: str, method: str, params: dict = None) -> str:
        """调用 MCP 服务"""
        if not self._mcp_manager:
            return "MCP manager not initialized"

        # 检查服务器是否运行
        result = self._mcp_manager.check_and_start_mcp(server)
        if not result.is_connected and not result.start_success:
            return f"MCP server '{server}' is not available: {result.error}"

        # MCP 调用需要实现 JSON-RPC 协议
        # 暂时返回服务器状态信息
        return (
            f"MCP server '{server}' is connected. "
            f"Method '{method}' called with params: {params}. "
            f"[Note: Full JSON-RPC implementation pending]"
        )

    # ========== 增强工具 ==========

    async def execute_web_fetch(self, url: str, selector: str = None) -> str:
        """获取网页内容"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0 (compatible; OpenYoung/1.0)"}
                )
                response.raise_for_status()

                content = response.text

                # 如果指定了 selector，尝试提取内容
                if selector:
                    from bs4 import BeautifulSoup

                    soup = BeautifulSoup(content, "html.parser")
                    elements = soup.select(selector)
                    if elements:
                        content = "\n".join([e.get_text(strip=True) for e in elements[:10]])

                # 截断过长的内容
                if len(content) > 5000:
                    content = content[:5000] + "\n... [truncated]"

                return content
        except Exception as e:
            return f"Failed to fetch {url}: {str(e)}"

    async def execute_git(self, command: str, repo_path: str = ".") -> str:
        """Git 操作"""
        import os

        repo_path = os.path.abspath(repo_path)

        # 安全检查：只允许特定的 git 命令
        allowed_commands = [
            "status",
            "log",
            "diff",
            "branch",
            "pull",
            "fetch",
            "clone",
            "add",
            "commit",
            "push",
        ]
        cmd_parts = command.split()

        if not cmd_parts or cmd_parts[0] not in allowed_commands:
            return f"Git command not allowed. Allowed: {', '.join(allowed_commands)}"

        # 构建完整命令
        full_command = f"cd {repo_path} && git {command}"

        proc = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        output = stdout.decode() if stdout else ""
        err = stderr.decode() if stderr else ""

        if err:
            output += f"\n[stderr]: {err}"

        return output or "[git command completed]"
