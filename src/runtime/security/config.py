"""
安全策略配置

统一的安全策略配置管理
支持白名单/黑名单/混合模式
"""

from dataclasses import dataclass, field


class DetectionMode(str):
    """检测模式"""

    BLOCKLIST = "blocklist"  # 黑名单模式：阻止匹配的
    ALLOWLIST = "allowlist"  # 白名单模式：只允许匹配的
    HYBRID = "hybrid"  # 混合模式：白名单优先


@dataclass
class SecurityConfig:
    """安全配置

    统一管理所有安全相关配置
    支持白名单/黑名单/混合模式
    """

    # 检测模式
    detection_mode: str = "blocklist"  # blocklist | allowlist | hybrid

    # 提示注入检测
    enable_prompt_detection: bool = True
    prompt_block_threshold: float = 0.8

    # 白名单/黑名单模式
    allowed_patterns: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)

    # 敏感信息检测
    enable_secret_detection: bool = True
    secret_action: str = "warn"  # warn, block, redact

    # 网络防火墙
    enable_firewall: bool = True
    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # 审计日志
    enable_audit: bool = True
    audit_level: str = "info"  # debug, info, warn, error

    # 速率限制
    enable_rate_limit: bool = False
    requests_per_minute: int = 60

    # 危险代码检测
    enable_dangerous_code_detection: bool = True

    def is_allowed(self, content: str) -> tuple[bool, str]:
        """检查内容是否允许（基于检测模式）

        Args:
            content: 待检查的内容

        Returns:
            (allowed, reason)
        """
        import re

        if self.detection_mode == "allowlist":
            # 白名单模式：只允许匹配的
            if not self.allowed_patterns:
                return True, "No allowlist configured, allowing"

            for pattern in self.allowed_patterns:
                if re.search(pattern, content):
                    return True, f"Matched allowlist pattern: {pattern}"
            return False, "Content not in allowlist"

        elif self.detection_mode == "blocklist":
            # 黑名单模式：阻止匹配的
            for pattern in self.blocked_patterns:
                if re.search(pattern, content):
                    return False, f"Matched blocklist pattern: {pattern}"
            return True, "Passed blocklist"

        else:  # hybrid
            # 混合模式：白名单优先
            if self.allowed_patterns:
                allowed = False
                for pattern in self.allowed_patterns:
                    if re.search(pattern, content):
                        allowed = True
                        break
                if not allowed:
                    return False, "Content not in allowlist (hybrid mode)"

            if self.blocked_patterns:
                for pattern in self.blocked_patterns:
                    if re.search(pattern, content):
                        return False, f"Matched blocklist pattern: {pattern}"

            return True, "Passed hybrid filter"

    @classmethod
    def from_dict(cls, config: dict) -> "SecurityConfig":
        """从字典创建配置

        Args:
            config: 配置字典

        Returns:
            SecurityConfig 实例
        """
        return cls(
            detection_mode=config.get("security.detection_mode", "blocklist"),
            enable_prompt_detection=config.get("security.prompt_detection", True),
            prompt_block_threshold=config.get("security.prompt_threshold", 0.8),
            allowed_patterns=config.get("security.allowed_patterns", []),
            blocked_patterns=config.get("security.blocked_patterns", []),
            enable_secret_detection=config.get("security.secret_detection", True),
            secret_action=config.get("security.secret_action", "warn"),
            enable_firewall=config.get("security.firewall", True),
            allowed_domains=config.get("security.allowed_domains", []),
            blocked_domains=config.get("security.blocked_domains", ["localhost", "127.0.0.1"]),
            enable_audit=config.get("security.audit", True),
            audit_level=config.get("security.audit_level", "info"),
            enable_rate_limit=config.get("security.rate_limit", False),
            requests_per_minute=config.get("security.rpm", 60),
            enable_dangerous_code_detection=config.get("security.dangerous_code", True),
        )

    @classmethod
    def from_config(cls, config: "SandboxConfig") -> "SecurityConfig":
        """从 SandboxConfig 创建配置（兼容旧接口）

        Args:
            config: SandboxConfig 实例

        Returns:
            SecurityConfig 实例
        """
        return cls(
            detection_mode=getattr(config, "detection_mode", "blocklist"),
            enable_prompt_detection=getattr(config, "enable_prompt_detection", True),
            prompt_block_threshold=getattr(config, "prompt_block_threshold", 0.8),
            allowed_patterns=getattr(config, "allowed_patterns", []),
            blocked_patterns=getattr(config, "blocked_patterns", []),
            enable_secret_detection=getattr(config, "enable_secret_detection", True),
            enable_firewall=getattr(config, "enable_firewall", True),
            allowed_domains=getattr(config, "allowed_domains", []),
            enable_audit=getattr(config, "enable_audit", True),
        )

    def to_dict(self) -> dict:
        """转换为字典

        Returns:
            配置字典
        """
        return {
            "security": {
                "detection_mode": self.detection_mode,
                "prompt_detection": self.enable_prompt_detection,
                "prompt_threshold": self.prompt_block_threshold,
                "allowed_patterns": self.allowed_patterns,
                "blocked_patterns": self.blocked_patterns,
                "secret_detection": self.enable_secret_detection,
                "secret_action": self.secret_action,
                "firewall": self.enable_firewall,
                "allowed_domains": self.allowed_domains,
                "blocked_domains": self.blocked_domains,
                "audit": self.enable_audit,
                "audit_level": self.audit_level,
                "rate_limit": self.enable_rate_limit,
                "rpm": self.requests_per_minute,
                "dangerous_code": self.enable_dangerous_code_detection,
            }
        }


# 为了向后兼容，保留原来的 SecurityPolicy 类名
@dataclass
class SecurityPolicy:
    """安全策略（向后兼容）"""

    config: SecurityConfig = field(default_factory=SecurityConfig)

    @classmethod
    def from_dict(cls, config: dict) -> "SecurityPolicy":
        """从字典创建策略"""
        return cls(config=SecurityConfig.from_dict(config))

    def get_config(self) -> SecurityConfig:
        """获取配置"""
        return self.config


# 为了向后兼容，需要导入 SandboxConfig
def _get_sandbox_config_class():
    """延迟导入 SandboxConfig 以避免循环依赖"""
    try:
        from src.runtime.sandbox import SandboxConfig

        return SandboxConfig
    except ImportError:
        return None


# ========== Convenience Functions ==========


def create_security_config(**kwargs) -> SecurityConfig:
    """便捷函数：创建安全配置"""
    return SecurityConfig(**kwargs)


def create_security_policy(**kwargs) -> SecurityPolicy:
    """便捷函数：创建安全策略"""
    config = SecurityConfig(**kwargs)
    return SecurityPolicy(config=config)
