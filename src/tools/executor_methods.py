"""
Tool Execution Methods - Individual tool implementations for ToolExecutor

Contains the actual implementation of each tool's execution logic.
"""

import asyncio
import os
import shlex


async def execute_bash_impl(executor, command: str, description: str = "") -> str:
    """Execute bash command with security checks."""
    from .command_validator import check_network_access, validate_command

    # Network isolation check
    network_allowed, network_reason = check_network_access(command, executor._allow_network)
    if not network_allowed:
        raise PermissionError(f"Network access blocked: {network_reason}")

    # Security check: command validation
    is_valid, error_msg = validate_command(command)
    if not is_valid:
        return f"Error: Unsafe command - {error_msg}"

    # Try to execute in sandbox
    sandbox_output, sandbox_exit = await executor._execute_in_sandbox(command)
    if sandbox_exit != -1:
        return sandbox_output or f"[Sandbox execution completed, exit code: {sandbox_exit}]"

    # Default: direct execution
    args = shlex.split(command)
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    output = stdout.decode() if stdout else ""
    err = stderr.decode() if stderr else ""
    if err:
        output += f"\n[stderr]: {err}"

    # Auto test
    if executor._should_run_tests(command):
        test_result = await executor._auto_run_tests(command)
        output += f"\n\n[AUTO-TEST] {test_result}"

    return output or "[Command completed]"


def _should_run_tests_impl(command: str) -> bool:
    """Detect if tests should be run."""
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


async def _auto_run_tests_impl(executor, build_command: str) -> str:
    """Auto run tests."""
    cwd = os.getcwd()
    test_commands = []

    if "cargo" in build_command:
        test_commands.append(("Rust", "cargo test --quiet"))
    if "npm" in build_command:
        test_commands.append(("Node.js", "npm test"))
    if "pip" in build_command or "poetry" in build_command:
        if os.path.exists("pytest.ini") or os.path.exists("tests"):
            test_commands.append(("Python", "python -m pytest tests/ -v"))

    results = []
    for name, test_cmd in test_commands:
        test_args = shlex.split(test_cmd)
        proc = await asyncio.create_subprocess_exec(
            *test_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout, stderr = await proc.communicate()
        passed = proc.returncode == 0
        results.append(f"{name}: {'PASSED' if passed else 'FAILED'}")

    return " | ".join(results) if results else "No tests found"


async def execute_write_impl(executor, filePath: str, content: str) -> str:
    """Write file with path validation."""
    from .command_validator import is_path_allowed

    if not is_path_allowed(filePath, executor.allowed_dirs):
        return f"Error: Path not in allowed directories: {filePath}"

    dir_name = os.path.dirname(filePath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(filePath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File written: {filePath}"


async def execute_edit_impl(executor, filePath: str, old_content: str, new_content: str) -> str:
    """Edit file with path validation."""
    from .command_validator import is_path_allowed

    if not is_path_allowed(filePath, executor.allowed_dirs):
        return f"Error: Path not in allowed directories: {filePath}"

    with open(filePath, encoding="utf-8") as f:
        content = f.read()
    if old_content not in content:
        return "Error: Content not found"
    new_content_file = content.replace(old_content, new_content)
    with open(filePath, "w", encoding="utf-8") as f:
        f.write(new_content_file)
    return f"File edited: {filePath}"


async def execute_read_impl(executor, filePath: str, limit: int = None, offset: int = None) -> str:
    """Read file with path validation."""
    from .command_validator import is_path_allowed

    if not is_path_allowed(filePath, executor.allowed_dirs):
        return f"Error: Path not in allowed directories: {filePath}"

    with open(filePath, encoding="utf-8") as f:
        lines = f.readlines()
    if offset:
        lines = lines[offset - 1 :]
    if limit:
        lines = lines[:limit]
    return "".join(lines)


async def execute_glob_impl(executor, pattern: str) -> str:
    """Glob pattern matching."""
    import glob as g

    files = g.glob(pattern, recursive=True)
    return "\n".join(files) if files else "No files found"


async def execute_grep_impl(executor, pattern: str, path: str = ".", include: str = None) -> str:
    """Grep pattern search."""
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
                pass
    return "\n".join(results[:50]) if results else "No content found"


async def execute_mcp_list_impl(executor) -> str:
    """List available MCP services."""
    if not executor._mcp_manager:
        try:
            from src.package_manager.mcp_manager import MCPServerManager

            executor._mcp_manager = MCPServerManager(packages_dir="packages")
        except Exception as e:
            return f"MCP manager not available: {e}"

    servers = executor._mcp_manager.discover_mcp_servers()
    if not servers:
        return "No MCP servers found"

    result = ["Available MCP Servers:"]
    for name, config in servers.items():
        result.append(f"- {name}: {config.command} {' '.join(config.args or [])}")
    return "\n".join(result)


async def execute_mcp_call_impl(executor, server: str, method: str, params: dict = None) -> str:
    """Call MCP service."""
    if not executor._mcp_manager:
        return "MCP manager not initialized"

    result = executor._mcp_manager.check_and_start_mcp(server)
    if not result.is_connected and not result.start_success:
        return f"MCP server '{server}' is not available: {result.error}"

    return (
        f"MCP server '{server}' is connected. "
        f"Method '{method}' called with params: {params}. "
        f"[Note: Full JSON-RPC implementation pending]"
    )


async def execute_web_fetch_impl(executor, url: str, selector: str = None) -> str:
    """Fetch web content."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url, headers={"User-Agent": "Mozilla/5.0 (compatible; OpenYoung/1.0)"}
            )
            response.raise_for_status()

            content = response.text

            if selector:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(content, "html.parser")
                elements = soup.select(selector)
                if elements:
                    content = "\n".join([e.get_text(strip=True) for e in elements[:10]])

            if len(content) > 5000:
                content = content[:5000] + "\n... [truncated]"

            return content
    except Exception as e:
        return f"Failed to fetch {url}: {str(e)}"


async def execute_git_impl(executor, command: str, repo_path: str = ".") -> str:
    """Git operations."""
    import asyncio

    repo_path = os.path.abspath(repo_path)

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

    git_args = ["git"] + cmd_parts[1:]
    proc = await asyncio.create_subprocess_exec(
        *git_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=repo_path,
    )
    stdout, stderr = await proc.communicate()

    output = stdout.decode() if stdout else ""
    err = stderr.decode() if stderr else ""

    if err:
        output += f"\n[stderr]: {err}"

    return output or "[git command completed]"


__all__ = [
    "execute_bash_impl",
    "execute_write_impl",
    "execute_edit_impl",
    "execute_read_impl",
    "execute_glob_impl",
    "execute_grep_impl",
    "execute_mcp_list_impl",
    "execute_mcp_call_impl",
    "execute_web_fetch_impl",
    "execute_git_impl",
    "_should_run_tests_impl",
    "_auto_run_tests_impl",
]
