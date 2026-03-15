"""
Security Policy Engine - 安全策略引擎

为强制沙箱执行提供安全策略支持
参考: E2B, NVIDIA AI Agent Security Best Practices
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SandboxPolicy:
    """沙箱策略配置"""

    # 强制沙箱
    force_sandbox: bool = True

    # 触发沙箱的最低风险级别
    min_risk_level: RiskLevel = RiskLevel.LOW

    # 命令白名单
    allowed_commands: set = field(default_factory=lambda: {
        "python", "python3", "pip", "pip3",
        "npm", "node", "npx",
        "git", "curl", "wget",
        "ls", "cd", "pwd", "cat", "head", "tail",
        "mkdir", "rmdir", "touch", "cp", "mv",
        "docker", "docker-compose",
    })

    # 危险模式 (阻止执行)
    blocked_patterns: list = field(default_factory=lambda: [
        r"rm\s+-rf",           # 删除根目录
        r"dd\s+if=",            # 磁盘写入
        r">\s*/dev/",          # 设备文件
        r"import\s+os.*system",  # OS命令执行
        r"subprocess.*shell\s*=\s*True",  # Shell执行
        r"eval\s*\(",          # 动态执行
        r"exec\s*\(",          # 代码执行
        r"__import__\s*\(\s*['\"]os",  # OS导入
        r"import\s+pty",       # 终端操作
        r"import\s+socket",    # 网络操作
    ])

    # 敏感路径 (只读)
    read_only_paths: set = field(default_factory=lambda: {
        "/etc/passwd",
        "/etc/shadow",
        "/root/.ssh",
        "/home/*/.ssh",
    })

    # 网络限制
    allow_network: bool = False  # 默认禁止网络
    allowed_domains: list = field(default_factory=list)  # 白名单域名
    allowed_ips: list = field(default_factory=list)  # 白名单IP
    blocked_domains: list = field(default_factory=lambda: [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ])

    # MCP服务器专用网络配置
    mcp_allowed_servers: list = field(default_factory=list)  # 允许的MCP服务器名称
    mcp_network_mode: str = "whitelist"  # whitelist, blacklist, none

    # 沙箱逃逸检测
    enable_escape_detection: bool = True  # 启用逃逸检测
    allowed_paths: list = field(default_factory=list)  # 允许的路径 (空=所有路径)
    block_path_traversal: bool = True  # 阻止路径穿越

    # 工作目录限制 (关键安全功能)
    working_directory: str = "/tmp/sandbox"  # 默认工作目录
    restrict_to_working_dir: bool = True  # 是否限制在工作目录内
    create_working_dir_if_missing: bool = True  # 是否自动创建工作目录

    # 审计日志
    enable_audit: bool = True  # 启用审计
    audit_level: str = "info"  # debug, info, warning, error

    # 速率限制
    max_calls_per_minute: int = 100
    max_execution_time_seconds: int = 300

    # 资源限制
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0


class SecurityPolicyEngine:
    """
    安全策略引擎

    负责:
    - 风险评估
    - 策略执行
    - 命令验证
    """

    def __init__(self, policy: Optional[SandboxPolicy] = None):
        self.policy = policy or SandboxPolicy()

    def assess_risk(self, code: str) -> RiskLevel:
        """
        评估代码风险级别

        Args:
            code: 要执行的代码

        Returns:
            RiskLevel: 风险级别
        """
        # 1. 检查危险模式
        for pattern in self.policy.blocked_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return RiskLevel.CRITICAL

        # 2. 检查敏感路径
        for path in self.policy.read_only_paths:
            if path in code:
                return RiskLevel.HIGH

        # 3. 检查网络操作
        network_patterns = [
            r"requests\.",
            r"urllib\.",
            r"http\.",
            r"socket\.",
            r"connect\(",
        ]
        for pattern in network_patterns:
            if re.search(pattern, code):
                return RiskLevel.MEDIUM

        # 4. 检查系统命令
        command_patterns = [
            r"subprocess\.",
            r"os\.system",
            r"os\.popen",
            r"spawn\(",
        ]
        for pattern in command_patterns:
            if re.search(pattern, code):
                return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def should_force_sandbox(self, risk_level: RiskLevel) -> bool:
        """
        判断是否强制使用沙箱

        Args:
            risk_level: 风险级别

        Returns:
            bool: 是否强制沙箱
        """
        # 强制沙箱总是返回True
        if self.policy.force_sandbox:
            return True

        # 或者风险级别超过阈值
        level_order = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }

        return level_order[risk_level] >= level_order[self.policy.min_risk_level]

    def validate_command(self, command: str) -> tuple[bool, str]:
        """
        验证命令是否允许执行

        Args:
            command: 命令字符串

        Returns:
            (是否允许, 拒绝原因)
        """
        # 提取命令
        parts = command.strip().split()
        if not parts:
            return False, "Empty command"

        # 获取主命令
        main_cmd = parts[0]

        # 检查白名单
        if main_cmd not in self.policy.allowed_commands:
            return False, f"Command '{main_cmd}' not in whitelist"

        # 检查危险参数
        dangerous_args = ["-rf", "-rf /", "--force", "sudo"]
        for arg in parts[1:]:
            if arg in dangerous_args:
                return False, f"Dangerous argument: {arg}"

        return True, ""

    def check_path_access(self, path: str) -> tuple[bool, str]:
        """
        检查路径访问权限

        Args:
            path: 文件路径

        Returns:
            (是否允许, 拒绝原因)
        """
        # 检查只读路径
        for readonly in self.policy.read_only_paths:
            if path.startswith(readonly):
                return False, f"Path '{path}' is read-only"

        return True, ""

    def get_allowed_domains(self) -> list:
        """
        获取允许访问的域名列表

        Returns:
            list: 允许的域名 (空=禁止所有)
        """
        return self.policy.allowed_domains

    def check_path_traversal(self, path: str) -> tuple[bool, str]:
        """
        检查路径穿越攻击和工作目录限制

        Args:
            path: 文件路径

        Returns:
            (是否安全, 拒绝原因)
        """
        import os
        import re

        if not self.policy.enable_escape_detection:
            return True, ""

        # 1. 规范化路径 (解析 .. 和符号链接)
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))
        except (ValueError, OSError):
            return False, f"Invalid path: {path}"

        # 2. 检查路径穿越模式
        dangerous_patterns = [
            r"\.\.",           # 双点穿越
            r"\./",            # 当前目录穿越
            r"~/",             # home目录穿越
            r"/proc",          # procfs
            r"/sys",          # sysfs
            r"/dev",          # 设备文件
            r"%2e%2e",        # URL编码穿越
            r"\.\.%2f",       # URL编码穿越
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False, f"Path traversal detected: {path}"

        # 3. 工作目录限制 (核心安全功能)
        if self.policy.restrict_to_working_dir:
            working_dir = os.path.normpath(os.path.abspath(self.policy.working_directory))

            # 确保工作目录存在
            if self.policy.create_working_dir_if_missing:
                os.makedirs(working_dir, exist_ok=True)

            # 检查路径是否在工作目录内
            if not normalized_path.startswith(working_dir):
                return False, f"Path outside working directory. Allowed: {working_dir}, Requested: {path}"

        # 4. 检查允许路径列表
        if self.policy.allowed_paths:
            allowed = False
            for allowed_path in self.policy.allowed_paths:
                if normalized_path.startswith(os.path.abspath(allowed_path)):
                    allowed = True
                    break
            if not allowed:
                return False, f"Path not in allowed list: {path}"

        return True, ""

    def check_file_access(self, path: str, operation: str = "read") -> tuple[bool, str]:
        """
        检查文件访问权限

        Args:
            path: 文件路径
            operation: 操作类型 (read, write, execute)

        Returns:
            (是否允许, 拒绝原因)
        """
        # 1. 检查路径穿越
        safe, reason = self.check_path_traversal(path)
        if not safe:
            return False, reason

        # 2. 检查只读路径
        for readonly in self.policy.read_only_paths:
            if path.startswith(readonly):
                if operation == "write":
                    return False, f"Cannot write to read-only path: {path}"
                # read 允许但记录

        return True, ""

    def check_network_request(self, url: str) -> tuple[bool, str]:
        """
        检查网络请求

        Args:
            url: 请求的URL

        Returns:
            (是否允许, 拒绝原因)
        """
        from urllib.parse import urlparse

        if not self.policy.allow_network:
            return False, "Network access is disabled"

        parsed = urlparse(url)
        hostname = parsed.hostname or ""

        # 黑名单检查
        if hostname in self.policy.blocked_domains:
            return False, f"Domain blocked: {hostname}"

        # 白名单检查 (如果配置了)
        if self.policy.allowed_domains:
            allowed = False
            for domain in self.policy.allowed_domains:
                if hostname.endswith(domain) or hostname == domain:
                    allowed = True
                    break
            if not allowed:
                return False, f"Domain not in whitelist: {hostname}"

        return True, ""

    def get_audit_log(self) -> list:
        """获取审计日志"""
        return getattr(self, "_audit_log", [])

    def log_audit(self, event_type: str, details: dict):
        """
        记录审计日志

        Args:
            event_type: 事件类型
            details: 事件详情
        """
        if not self.policy.enable_audit:
            return

        import datetime
        if not hasattr(self, "_audit_log"):
            self._audit_log = []

        self._audit_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "details": details,
        })

        # 限制日志大小
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]


def create_strict_policy() -> SandboxPolicy:
    """创建严格策略 - 最高安全级别"""
    return SandboxPolicy(
        force_sandbox=True,
        min_risk_level=RiskLevel.LOW,
    )


def create_relaxed_policy() -> SandboxPolicy:
    """创建宽松策略 - 仅阻止危险操作"""
    return SandboxPolicy(
        force_sandbox=False,
        min_risk_level=RiskLevel.HIGH,
    )
