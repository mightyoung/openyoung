"""
Command Validator - Command validation constants and functions

Provides comprehensive command validation including:
- Allowlist of permitted commands
- Pattern-based detection of dangerous commands
- Shell metacharacter filtering
- Path traversal prevention
"""

import os
import re
import shlex
from pathlib import Path

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

# Dangerous character pattern - blocks shell metacharacters
DANGEROUS_CHARS_PATTERN = re.compile(r"[;&|`$><>()\[\]{}@!#%^~*?\n\r]")

# Path traversal patterns - blocks .., ~, absolute paths, sensitive files
TRAVERSAL_PATTERN = re.compile(r"\.\./|\.\.\\|%2e%2e|/etc/passwd|/etc/shadow|~/(?:\.ssh)?")

# 网络操作命令模式
NETWORK_PATTERNS = ["curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "telnet", "ftp", "sftp"]

# 允许的 Git 子命令
GIT_ALLOWED_SUBCOMMANDS = {
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

# 允许的绝对路径
_ALLOWED_DEFAULT_PATHS = ["/tmp", "/var/tmp"]
# 支持通过环境变量添加用户自定义路径
_USER_PATH = os.getenv("ALLOWED_USER_PATH", "")
ALLOWED_ABSOLUTE_PATHS = _ALLOWED_DEFAULT_PATHS + ([_USER_PATH] if _USER_PATH else [])


def is_path_allowed(
    file_path: str,
    allowed_dirs: list[str],
    default_workspace: str = None,
) -> bool:
    """检查路径是否在允许的目录内（防止目录遍历攻击）"""
    try:
        # 解析绝对路径
        abs_path = Path(file_path).resolve()

        # 检查是否在允许的目录内
        for allowed_dir in allowed_dirs:
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


def is_safe_argument(arg: str) -> tuple[bool, str]:
    """Validate a single argument for safety"""
    if not arg:
        return True, ""

    # Check for path traversal in argument
    if ".." in arg or arg.startswith("~"):
        return False, f"Path traversal detected in argument: {arg[:50]}"

    # Block arguments that look like paths to sensitive files
    sensitive_patterns = ["/etc/passwd", "/etc/shadow", "/etc/sudoers"]
    for pattern in sensitive_patterns:
        if pattern in arg:
            return False, f"Sensitive path blocked: {pattern}"

    # Allow relative paths that don't escape workspace
    if arg.startswith("/"):
        if not any(arg.startswith(p) for p in ALLOWED_ABSOLUTE_PATHS):
            return False, f"Absolute path not in allowed list: {arg[:50]}"

    return True, ""


def validate_command(
    command: str,
    allowed_commands: set[str] = ALLOWED_COMMANDS,
    git_allowed_subcommands: set[str] = GIT_ALLOWED_SUBCOMMANDS,
) -> tuple[bool, str]:
    """验证命令是否安全（综合验证）"""
    if not command or not command.strip():
        return False, "Empty command"

    # 1. Check for dangerous shell metacharacters
    if DANGEROUS_CHARS_PATTERN.search(command):
        return False, "Dangerous shell characters detected"

    # 2. Check for path traversal patterns
    if TRAVERSAL_PATTERN.search(command):
        return False, "Path traversal pattern detected"

    # 3. Parse command properly with shlex
    try:
        parts = shlex.split(command)
    except ValueError as e:
        return False, f"Invalid shell syntax: {e}"

    if not parts:
        return False, "Empty command after parsing"

    # 4. Validate each argument separately
    for arg in parts[1:]:
        is_safe, reason = is_safe_argument(arg)
        if not is_safe:
            return False, reason

    # 5. Check base command against whitelist
    base_cmd = parts[0].split("/")[-1]
    if base_cmd not in allowed_commands:
        # 检查是否是 git 的子命令
        if parts[0] == "git" and len(parts) > 1:
            if parts[1] not in git_allowed_subcommands:
                return False, f"Git subcommand '{parts[1]}' not allowed"
        else:
            return False, f"Command '{base_cmd}' not in whitelist"

    return True, ""


def check_network_access(
    command: str,
    allow_network: bool = False,
    network_patterns: list[str] = NETWORK_PATTERNS,
) -> tuple[bool, str]:
    """检查命令是否允许网络访问

    Args:
        command: 要执行的命令
        allow_network: 是否允许网络访问
        network_patterns: 网络操作命令模式列表

    Returns:
        (allowed, reason)
    """
    if allow_network:
        return True, "Network access allowed by configuration"

    command_lower = command.lower()
    for pattern in network_patterns:
        if pattern in command_lower:
            return False, f"Network access blocked: command contains '{pattern}'"

    return True, "No network access detected"
