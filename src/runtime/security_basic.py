"""
Security - 沙箱安全管理

提供沙箱安全策略与验证
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IsolationLevel(str, Enum):
    """隔离级别"""

    PROCESS = "process"  # 进程隔离
    CONTAINER = "container"  # 容器隔离
    VM = "vm"  # VM隔离 (E2B方式)


@dataclass
class SecurityPolicy:
    """安全策略"""

    isolation: IsolationLevel = IsolationLevel.PROCESS

    # 资源限制
    max_cpu_percent: float = 100.0
    max_memory_mb: int = 1024
    max_disk_mb: int = 5120

    # 访问控制
    allow_network: bool = True
    allow_file_write: bool = True
    allowed_commands: list[str] = field(default_factory=list)

    # 审计
    log_all_calls: bool = True
    record_screenshots: bool = False


class SecurityManager:
    """安全管理器"""

    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()

        # 危险模式
        self._dangerous_patterns = [
            # 系统调用
            r"import\s+os;?\s*os\.system",
            r"import\s+subprocess",
            r"subprocess\.call",
            r"subprocess\.run",
            r"subprocess\.Popen",
            r"os\.popen",
            r"os\.spawn",
            # 代码执行
            r"eval\s*\(",
            r"exec\s*\(",
            r"exec\s+",
            # 导入
            r"__import__\s*\(",
            r"importlib\.import_module",
            # 文件操作
            r"open\s*\([^)]*['\"]w['\"]",  # 写入模式
            r"with\s+open\s*\([^)]*['\"]w['\"]",
            # 网络
            r"socket\.socket",
            r"urllib\.request",
            r"requests\.post",
            r"requests\.get",
            r"http\.client",
            # 系统
            r"os\.chmod",
            r"os\.chown",
            r"os\.remove",
            r"shutil\.rmtree",
        ]

    def validate_code(self, code: str) -> tuple[bool, str]:
        """验证代码安全性

        Returns:
            (is_safe, reason)
        """
        # 检查危险模式
        for pattern in self._dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        # 检查文件路径遍历
        if "../" in code or "..\\" in code:
            return False, "Path traversal detected"

        # 检查硬编码的敏感路径
        sensitive_paths = ["/etc/passwd", "/etc/shadow", "~/.ssh", "~/.aws"]
        for path in sensitive_paths:
            if path in code:
                return False, f"Sensitive path detected: {path}"

        return True, ""

    def validate_command(self, command: str) -> tuple[bool, str]:
        """验证命令安全性

        Returns:
            (is_safe, reason)
        """
        # 白名单检查
        if self.policy.allowed_commands:
            if command not in self.policy.allowed_commands:
                return False, f"Command not in whitelist: {command}"

        # 危险命令检查
        dangerous_commands = [
            "rm -rf",
            "dd if=",
            "mkfs",
            ":(){:|:&};:",  # Fork bomb
            "chmod 777",
            "chown",
        ]

        for cmd in dangerous_commands:
            if cmd in command:
                return False, f"Dangerous command detected: {cmd}"

        return True, ""

    def validate_file_path(self, path: str) -> tuple[bool, str]:
        """验证文件路径安全性

        Returns:
            (is_safe, reason)
        """
        # 路径遍历检查
        if "../" in path or "..\\" in path:
            return False, "Path traversal detected"

        # 检查是否在允许路径内
        if self.policy.allowed_paths:
            allowed = False
            for allowed_path in self.policy.allowed_paths:
                if path.startswith(allowed_path):
                    allowed = True
                    break

            if not allowed:
                return False, f"Path not in allowed list: {path}"

        return True, ""

    def should_allow_network(self) -> bool:
        """检查是否允许网络访问"""
        return self.policy.allow_network

    def should_allow_file_write(self) -> bool:
        """检查是否允许文件写入"""
        return self.policy.allow_file_write

    def get_max_memory_mb(self) -> int:
        """获取最大内存限制"""
        return self.policy.max_memory_mb

    def get_max_execution_time(self) -> int:
        """获取最大执行时间"""
        return self.policy.max_cpu_percent


# ========== Convenience Functions ==========


def create_security_manager(
    isolation: IsolationLevel = IsolationLevel.PROCESS,
    allow_network: bool = True,
    allow_file_write: bool = True,
    max_memory_mb: int = 1024,
) -> SecurityManager:
    """创建安全管理器"""
    policy = SecurityPolicy(
        isolation=isolation,
        allow_network=allow_network,
        allow_file_write=allow_file_write,
        max_memory_mb=max_memory_mb,
    )
    return SecurityManager(policy)
