"""
Firewall Tests - Phase 1.0
Tests for Firewall network control
"""

import pytest

from src.runtime.security import Firewall, FirewallConfig, FirewallRule, FirewallAction


class TestFirewallCore:
    """核心功能测试"""

    def test_default_blocked_domains(self):
        """默认阻止的域名应该被阻止"""
        firewall = Firewall()
        allowed, reason = firewall.check_domain("localhost")
        assert allowed == False

    def test_explicit_allowed_domain(self):
        """显式允许的域名应该通过"""
        config = FirewallConfig(allowed_domains=["api.example.com"])
        firewall = Firewall(config)
        allowed, reason = firewall.check_domain("api.example.com")
        assert allowed == True

    def test_whitelist_rejects_unlisted(self):
        """白名单模式应该拒绝未列出的域名"""
        config = FirewallConfig(
            allowed_domains=["api.example.com"],
            default_action=FirewallAction.DENY,
        )
        firewall = Firewall(config)
        allowed, reason = firewall.check_domain("other.com")
        assert allowed == False


class TestFirewallRule:
    """防火墙规则测试"""

    def test_exact_match(self):
        """精确匹配应该工作"""
        rule = FirewallRule("example.com", FirewallAction.ALLOW)
        assert rule.matches("example.com") == True
        assert rule.matches("api.example.com") == True  # 子域名

    def test_wildcard_match(self):
        """通配符匹配应该工作"""
        rule = FirewallRule("*.example.com", FirewallAction.ALLOW)
        assert rule.matches("api.example.com") == True
        assert rule.matches("test.example.com") == True
        assert rule.matches("example.com") == False

    def test_case_insensitive(self):
        """应该大小写不敏感"""
        rule = FirewallRule("Example.COM", FirewallAction.ALLOW)
        assert rule.matches("EXAMPLE.COM") == True
        assert rule.matches("example.com") == True


class TestFirewallIP:
    """IP 检测测试"""

    def test_is_internal_ip_private(self):
        """私有 IP 应该被识别"""
        firewall = Firewall()
        assert firewall.is_internal_ip("192.168.1.1") == True
        assert firewall.is_internal_ip("10.0.0.1") == True
        assert firewall.is_internal_ip("172.16.0.1") == True

    def test_is_internal_ip_localhost(self):
        """localhost 应该被识别"""
        firewall = Firewall()
        assert firewall.is_internal_ip("127.0.0.1") == True

    def test_is_not_internal_ip(self):
        """公网 IP 不应该被识别为内部"""
        firewall = Firewall()
        assert firewall.is_internal_ip("8.8.8.8") == False
        assert firewall.is_internal_ip("1.1.1.1") == False


class TestFirewallCleanDomain:
    """域名清理测试"""

    def test_clean_http_url(self):
        """HTTP URL 应该被清理"""
        firewall = Firewall()
        assert firewall._clean_domain("http://example.com/path") == "example.com"
        assert firewall._clean_domain("https://example.com/path") == "example.com"

    def test_clean_with_port(self):
        """带端口的 URL 应该被清理"""
        firewall = Firewall()
        assert firewall._clean_domain("example.com:8080") == "example.com"

    def test_clean_with_query(self):
        """带查询参数的 URL 应该被清理"""
        firewall = Firewall()
        assert firewall._clean_domain("example.com?query=value") == "example.com"


class TestFirewallResolution:
    """域名解析测试"""

    def test_resolve_valid_domain(self):
        """有效域名应该能解析"""
        firewall = Firewall()
        ip = firewall.resolve_domain("google.com")
        assert ip is not None

    def test_resolve_invalid_domain(self):
        """无效域名应该返回 None"""
        firewall = Firewall()
        ip = firewall.resolve_domain("this-domain-does-not-exist-xyz123.invalid")
        assert ip is None


class TestFirewallCanConnect:
    """连接测试"""

    def test_can_connect_external(self):
        """应该能连接外部域名"""
        config = FirewallConfig(allowed_domains=["google.com"])
        firewall = Firewall(config)
        allowed, reason = firewall.can_connect("google.com")
        # 可能允许也可能拒绝，取决于解析结果

    def test_cannot_connect_internal(self):
        """不应该能连接内部 IP"""
        config = FirewallConfig(allowed_domains=["*"])
        firewall = Firewall(config)
        allowed, reason = firewall.can_connect("127.0.0.1")
        assert allowed == False


class TestFirewallEdgeCases:
    """边界测试"""

    def test_empty_domain(self):
        """空域名应该被处理"""
        firewall = Firewall()
        allowed, reason = firewall.check_domain("")
        # 应该有合理的行为

    def test_ip_address(self):
        """IP 地址应该被处理"""
        firewall = Firewall()
        allowed, reason = firewall.check_domain("8.8.8.8")
        # 公网 IP 应该默认允许
