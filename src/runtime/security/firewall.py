"""
网络防火墙

基于域名白名单的网络访问控制
"""

import re
import socket
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class FirewallAction(Enum):
    """防火墙动作"""

    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"


@dataclass
class FirewallRule:
    """防火墙规则"""

    pattern: str
    action: FirewallAction
    description: str = ""

    def matches(self, domain: str) -> bool:
        """检查域名是否匹配规则"""
        # 统一转为小写比较
        pattern_lower = self.pattern.lower()
        domain_lower = domain.lower()

        # 支持通配符 *
        if "*" in self.pattern:
            regex_pattern = self.pattern.replace(".", r"\.").replace("*", ".*")
            return bool(re.match(f"^{regex_pattern}$", domain_lower, re.IGNORECASE))
        # 精确匹配或子域名匹配
        return domain_lower.endswith(pattern_lower) or domain_lower == pattern_lower


@dataclass
class FirewallConfig:
    """防火墙配置"""

    allowed_domains: list[str] = field(default_factory=list)
    blocked_domains: list[str] = field(default_factory=list)
    enable_logging: bool = True
    default_action: FirewallAction = FirewallAction.ALLOW


class Firewall:
    """网络防火墙

    基于域名白名单的网络访问控制
    """

    # 内置危险域名
    DEFAULT_BLOCKED: list[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "metadata.google.internal",  # GCP metadata
        "169.254.169.254",  # AWS/Azure/GCP metadata
    ]

    def __init__(self, config: Optional[FirewallConfig] = None):
        """初始化防火墙

        Args:
            config: 防火墙配置
        """
        self.config = config or FirewallConfig()
        self._allowed_rules: list[FirewallRule] = []
        self._blocked_rules: list[FirewallRule] = []
        self._build_rules()

    def _build_rules(self) -> None:
        """构建规则列表"""
        # 添加允许的域名规则
        for domain in self.config.allowed_domains:
            rule = FirewallRule(
                pattern=domain,
                action=FirewallAction.ALLOW,
                description=f"User allowed: {domain}",
            )
            self._allowed_rules.append(rule)

        # 添加阻止的域名规则
        for domain in self.config.blocked_domains + self.DEFAULT_BLOCKED:
            rule = FirewallRule(
                pattern=domain,
                action=FirewallAction.DENY,
                description=f"System blocked: {domain}",
            )
            self._blocked_rules.append(rule)

    def check_domain(self, domain: str) -> tuple[bool, str]:
        """检查域名是否允许访问

        Args:
            domain: 要访问的域名

        Returns:
            (allowed, reason)
        """
        # 解析域名（去除协议和路径）
        clean_domain = self._clean_domain(domain)

        # 检查是否在阻止列表
        for rule in self._blocked_rules:
            if rule.matches(clean_domain):
                if self.config.enable_logging:
                    return False, f"Domain blocked: {rule.description}"

        # 如果有白名单，检查是否在白名单中
        if self.config.allowed_domains:
            for rule in self._allowed_rules:
                if rule.matches(clean_domain):
                    return True, f"Domain allowed: {rule.description}"
            return False, "Domain not in whitelist"

        # 默认动作
        if self.config.default_action == FirewallAction.ALLOW:
            return True, "Default allow"
        return False, "Default deny"

    def _clean_domain(self, url_or_domain: str) -> str:
        """清理 URL 或域名

        Args:
            url_or_domain: URL 或域名

        Returns:
            清理后的域名
        """
        # 去除协议
        for protocol in ["https://", "http://", "ftp://"]:
            if url_or_domain.startswith(protocol):
                url_or_domain = url_or_domain[len(protocol) :]
                break

        # 去除路径和查询参数
        if "/" in url_or_domain:
            url_or_domain = url_or_domain.split("/")[0]
        if "?" in url_or_domain:
            url_or_domain = url_or_domain.split("?")[0]

        # 去除端口
        if ":" in url_or_domain:
            url_or_domain = url_or_domain.split(":")[0]

        return url_or_domain.lower()

    def resolve_domain(self, domain: str) -> Optional[str]:
        """解析域名到 IP

        Args:
            domain: 域名

        Returns:
            IP 地址或 None
        """
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return None

    def is_internal_ip(self, ip: str) -> bool:
        """检查是否为内部 IP

        Args:
            ip: IP 地址

        Returns:
            是否为内部 IP
        """
        try:
            socket.inet_aton(ip)
        except OSError:
            return False

        # 检查私有 IP 范围
        private_ranges = [
            "10.",  # 10.0.0.0/8
            "172.16.",  # 172.16.0.0/12
            "192.168.",  # 192.168.0.0/16
            "127.",  # 127.0.0.0/8
            "169.254.",  # Link-local
        ]

        return any(ip.startswith(prefix) for prefix in private_ranges)

    def can_connect(self, domain: str) -> tuple[bool, str]:
        """检查是否可以连接到域名

        Args:
            domain: 域名

        Returns:
            (allowed, reason)
        """
        # 先检查域名策略
        allowed, reason = self.check_domain(domain)
        if not allowed:
            return False, reason

        # 解析域名
        ip = self.resolve_domain(domain)
        if ip is None:
            # DNS 解析失败，默认允许但记录
            return True, f"DNS resolution failed for {domain}, allowing"

        # 检查是否为内部 IP
        if self.is_internal_ip(ip):
            return False, f"Internal IP not allowed: {ip}"

        return True, f"Allowed: {domain} -> {ip}"


# ========== Convenience Functions ==========


def is_domain_allowed(domain: str, allowed_domains: list[str]) -> bool:
    """便捷函数：检查域名是否在白名单中"""
    config = FirewallConfig(allowed_domains=allowed_domains)
    firewall = Firewall(config)
    allowed, _ = firewall.check_domain(domain)
    return allowed


def can_connect_to(domain: str, allowed_domains: list[str]) -> bool:
    """便捷函数：检查是否可以连接到域名"""
    config = FirewallConfig(allowed_domains=allowed_domains)
    firewall = Firewall(config)
    allowed, _ = firewall.can_connect(domain)
    return allowed
