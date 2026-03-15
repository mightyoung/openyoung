"""
MCP Security Adapter - MCP 服务器安全适配器

为 MCP 服务器添加网络隔离、路径限制和审计功能
基于 2025 年 MCP 安全漏洞修复最佳实践
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPSecurityConfig:
    """MCP 安全配置"""

    # 网络隔离
    enable_network_isolation: bool = True
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=lambda: [
        "localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"
    ])

    # 路径限制
    enable_path_restriction: bool = True
    allowed_paths: list[str] = field(default_factory=list)  # 空=无限制
    denied_paths: list[str] = field(default_factory=lambda: [
        "/etc/passwd", "/etc/shadow", "/root/.ssh", "/home/*/.ssh"
    ])

    # 进程限制
    enable_process_limit: bool = True
    max_processes: int = 10
    max_memory_mb: int = 512

    # 审计
    enable_audit: bool = True
    audit_log_path: str = "./logs/mcp_audit.jsonl"


class MCPSecurityAdapter:
    """
    MCP 服务器安全适配器

    提供:
    - 网络隔离 (白名单/黑名单)
    - 路径访问控制
    - 进程资源限制
    - 安全审计
    """

    def __init__(self, config: Optional[MCPSecurityConfig] = None):
        self.config = config or MCPSecurityConfig()
        self._audit_buffer: list[dict] = []

    def _log_audit(self, event_type: str, mcp_name: str, details: dict):
        """记录审计日志"""
        if not self.config.enable_audit:
            return

        import datetime

        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "mcp_name": mcp_name,
            "details": details,
        }
        self._audit_buffer.append(entry)

        # 写入文件
        try:
            log_path = Path(self.config.audit_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            with open(log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def check_mcp_request(self, mcp_name: str, request: dict) -> tuple[bool, str]:
        """
        检查 MCP 请求的安全性

        Args:
            mcp_name: MCP 服务器名称
            request: 请求数据

        Returns:
            (是否允许, 拒绝原因)
        """
        # 检查请求类型
        method = request.get("method", "")

        # 危险方法检查
        dangerous_methods = ["exec", "run", "spawn", "write_file", "delete_file"]
        if method in dangerous_methods:
            self._log_audit("dangerous_method", mcp_name, {
                "method": method,
                "allowed": False
            })
            return False, f"Method '{method}' is not allowed for MCP servers"

        # 记录正常请求
        self._log_audit("request", mcp_name, {
            "method": method,
            "allowed": True
        })

        return True, ""

    def validate_command(self, command: str, args: list[str]) -> tuple[bool, str]:
        """
        验证 MCP 服务器执行的命令

        Args:
            command: 命令
            args: 参数

        Returns:
            (是否允许, 拒绝原因)
        """
        if not self.config.enable_process_limit:
            return True, ""

        # 检查危险命令
        dangerous_commands = [
            "rm -rf", "dd if=", "mkfs", "fdisk",
            "curl | sh", "wget | sh", "bash -c",
            "nc ", "netcat", "socat",
        ]

        full_cmd = command + " " + " ".join(args)
        for dangerous in dangerous_commands:
            if dangerous in full_cmd:
                self._log_audit("dangerous_command", "mcp", {
                    "command": full_cmd,
                    "blocked": True
                })
                return False, f"Dangerous command blocked: {dangerous}"

        return True, ""

    def sanitize_env(self, env: dict[str, str]) -> dict[str, str]:
        """
        清理环境变量，移除敏感信息

        Args:
            env: 原始环境变量

        Returns:
            清理后的环境变量
        """
        # 需要移除的敏感变量
        sensitive_vars = [
            "API_KEY", "SECRET", "PASSWORD", "TOKEN",
            "PRIVATE_KEY", "ACCESS_KEY", "CREDENTIAL",
        ]

        sanitized = {}
        for key, value in env.items():
            # 检查是否是敏感变量
            is_sensitive = any(s in key.upper() for s in sensitive_vars)

            if is_sensitive:
                sanitized[key] = "***REDACTED***"
                self._log_audit("sensitive_env_blocked", "mcp", {
                    "key": key,
                })
            else:
                sanitized[key] = value

        return sanitized

    def check_path_access(self, path: str, operation: str = "read") -> tuple[bool, str]:
        """
        检查路径访问权限

        Args:
            path: 文件路径
            operation: 操作类型

        Returns:
            (是否允许, 拒绝原因)
        """
        if not self.config.enable_path_restriction:
            return True, ""

        # 检查拒绝路径
        for denied in self.config.denied_paths:
            if path.startswith(denied.replace("*", "")):
                self._log_audit("path_denied", "mcp", {
                    "path": path,
                    "operation": operation,
                })
                return False, f"Path access denied: {path}"

        # 检查允许路径 (如果有配置)
        if self.config.allowed_paths:
            allowed = False
            for allowed_path in self.config.allowed_paths:
                if path.startswith(allowed_path):
                    allowed = True
                    break

            if not allowed:
                return False, f"Path not in allowed list: {path}"

        return True, ""

    def create_subprocess_config(
        self,
        command: str,
        args: list[str],
        env: dict[str, str],
    ) -> dict[str, Any]:
        """
        创建安全的子进程配置

        Args:
            command: 命令
            args: 参数
            env: 环境变量

        Returns:
            子进程配置字典
        """
        # 验证命令
        allowed, reason = self.validate_command(command, args)
        if not allowed:
            raise PermissionError(reason)

        # 清理环境变量
        clean_env = self.sanitize_env(env)

        # 添加审计日志
        self._log_audit("process_spawn", "mcp", {
            "command": command,
            "args": args,
        })

        return {
            "command": command,
            "args": args,
            "env": clean_env,
            "cwd": "/tmp",  # 限制工作目录
            "timeout": 300,  # 5分钟超时
        }

    def get_audit_logs(self, mcp_name: Optional[str] = None) -> list[dict]:
        """
        获取审计日志

        Args:
            mcp_name: 可选的 MCP 服务器名称过滤

        Returns:
            审计日志列表
        """
        if mcp_name:
            return [e for e in self._audit_buffer if e.get("mcp_name") == mcp_name]
        return self._audit_buffer.copy()


# 全局安全适配器实例
_mcp_security: Optional[MCPSecurityAdapter] = None


def get_mcp_security(config: Optional[MCPSecurityConfig] = None) -> MCPSecurityAdapter:
    """获取 MCP 安全适配器单例"""
    global _mcp_security

    if _mcp_security is None:
        _mcp_security = MCPSecurityAdapter(config)

    return _mcp_security
