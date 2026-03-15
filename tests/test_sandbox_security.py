"""
Security Policy Tests - 安全策略测试

验证沙箱安全功能:
1. 路径穿越检测
2. 网络访问控制
3. MCP服务器安全
4. 审计日志
"""

import unittest
import sys
sys.path.insert(0, "/Users/muyi/Downloads/dev/openyoung")


class TestPathTraversalDetection(unittest.TestCase):
    """测试路径穿越检测"""

    def setUp(self):
        from src.runtime.sandbox.security_policy import SecurityPolicyEngine, SandboxPolicy
        # 禁用工作目录限制用于基础测试
        policy = SandboxPolicy(
            restrict_to_working_dir=False,  # 基础测试禁用工作目录限制
            enable_escape_detection=True,
        )
        self.engine = SecurityPolicyEngine(policy)

    def test_block_path_traversal(self):
        """测试阻止路径穿越"""
        dangerous_paths = [
            "../../../etc/passwd",
            "./traversal/../../../etc",
            "..%2f..%2fetc%2fpasswd",
        ]
        for path in dangerous_paths:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertFalse(safe, f"Should block: {path}")

    def test_allow_safe_paths(self):
        """测试允许安全路径"""
        safe_paths = [
            "/home/user/documents/file.txt",
            "relative/path/to/file.py",
        ]
        for path in safe_paths:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertTrue(safe, f"Should allow: {path}")

    def test_block_proc_filesystem(self):
        """测试阻止 /proc 访问"""
        dangerous_paths = [
            "/proc/self",
            "/proc/1/cmdline",
            "/sys/kernel",
        ]
        for path in dangerous_paths:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertFalse(safe, f"Should block: {path}")


class TestNetworkAccessControl(unittest.TestCase):
    """测试网络访问控制"""

    def setUp(self):
        from src.runtime.sandbox.security_policy import SecurityPolicyEngine
        self.engine = SecurityPolicyEngine()
        self.engine.policy.allow_network = True
        self.engine.policy.allowed_domains = ["api.openai.com", "api.anthropic.com"]
        self.engine.policy.blocked_domains = ["localhost", "127.0.0.1"]

    def test_allow_whitelisted_domain(self):
        """测试允许白名单域名"""
        url = "https://api.openai.com/v1/models"
        safe, _ = self.engine.check_network_request(url)
        self.assertTrue(safe)

    def test_block_blacklisted_domain(self):
        """测试阻止黑名单域名"""
        url = "http://localhost:8080"
        safe, reason = self.engine.check_network_request(url)
        self.assertFalse(safe)
        self.assertIn("blocked", reason.lower())

    def test_block_unknown_domain(self):
        """测试阻止未知域名"""
        url = "https://evil.com/exfil"
        safe, reason = self.engine.check_network_request(url)
        self.assertFalse(safe)

    def test_default_deny(self):
        """测试默认拒绝网络访问"""
        engine = self.engine.__class__()
        url = "https://api.example.com"
        safe, reason = engine.check_network_request(url)
        self.assertFalse(safe)


class TestMCPSecurityAdapter(unittest.TestCase):
    """测试 MCP 安全适配器"""

    def setUp(self):
        from src.runtime.sandbox.mcp_security import MCPSecurityAdapter, MCPSecurityConfig
        self.config = MCPSecurityConfig()
        self.adapter = MCPSecurityAdapter(self.config)

    def test_block_dangerous_commands(self):
        """测试阻止危险命令"""
        dangerous = [
            ("rm", ["-rf", "/"]),
            ("dd", ["if=/dev/zero", "of=/dev/sda"]),
            ("mkfs", ["/dev/sda"]),
        ]
        for cmd, args in dangerous:
            allowed, reason = self.adapter.validate_command(cmd, args)
            self.assertFalse(allowed, f"Should block: {cmd} {args}")

    def test_allow_safe_commands(self):
        """测试允许安全命令"""
        safe = [
            ("pip", ["install", "requests"]),
            ("npm", ["install"]),
            ("git", ["clone"]),
        ]
        for cmd, args in safe:
            allowed, reason = self.adapter.validate_command(cmd, args)
            self.assertTrue(allowed, f"Should allow: {cmd} {args}")

    def test_sanitize_env(self):
        """测试环境变量清理"""
        env = {
            "PATH": "/usr/bin",
            "API_KEY": "sk-1234567890",
            "PASSWORD": "secret",
            "HOME": "/home/user",
        }
        clean = self.adapter.sanitize_env(env)

        self.assertEqual(clean["PATH"], "/usr/bin")
        self.assertEqual(clean["HOME"], "/home/user")
        self.assertEqual(clean["API_KEY"], "***REDACTED***")
        self.assertEqual(clean["PASSWORD"], "***REDACTED***")

    def test_check_path_access(self):
        """测试路径访问控制"""
        # 测试拒绝路径
        allowed, reason = self.adapter.check_path_access("/etc/passwd", "read")
        self.assertFalse(allowed)

        # 测试允许路径
        allowed, reason = self.adapter.check_path_access("/tmp/file.txt", "write")
        self.assertTrue(allowed)


class TestAuditLogging(unittest.TestCase):
    """测试审计日志"""

    def test_audit_log(self):
        """测试审计日志记录"""
        from src.runtime.sandbox.security_policy import SecurityPolicyEngine

        engine = SecurityPolicyEngine()
        engine.policy.enable_audit = True

        # 记录审计日志
        engine.log_audit("test_event", {"detail": "test data"})

        logs = engine.get_audit_log()
        self.assertGreater(len(logs), 0)
        self.assertEqual(logs[-1]["event_type"], "test_event")


class TestWorkingDirectoryRestriction(unittest.TestCase):
    """测试工作目录限制"""

    def setUp(self):
        from src.runtime.sandbox.security_policy import SecurityPolicyEngine, SandboxPolicy

        # 创建带工作目录限制的策略
        policy = SandboxPolicy(
            working_directory="/tmp/test_sandbox",
            restrict_to_working_dir=True,
            create_working_dir_if_missing=False,
        )
        self.engine = SecurityPolicyEngine(policy)

    def test_allow_paths_in_working_dir(self):
        """测试允许工作目录内的路径"""
        allowed = [
            "/tmp/test_sandbox/file.txt",
            "/tmp/test_sandbox/subdir/code.py",
        ]
        for path in allowed:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertTrue(safe, f"Should allow: {path}")

    def test_block_paths_outside_working_dir(self):
        """测试阻止工作目录外的路径"""
        blocked = [
            "/etc/passwd",
            "/home/user/file.txt",
            "/var/log/syslog",
        ]
        for path in blocked:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertFalse(safe, f"Should block: {path}")

    def test_block_path_traversal_from_working_dir(self):
        """测试阻止从工作目录开始的路径穿越"""
        blocked = [
            "/tmp/test_sandbox/../../../etc/passwd",
            "/tmp/test_sandbox/../root",
        ]
        for path in blocked:
            safe, reason = self.engine.check_path_traversal(path)
            self.assertFalse(safe, f"Should block: {path}")

    def test_custom_working_directory(self):
        """测试自定义工作目录"""
        from src.runtime.sandbox.security_policy import SandboxPolicy, SecurityPolicyEngine

        # 使用临时目录作为工作目录
        import tempfile

        temp_dir = tempfile.mkdtemp(prefix="sandbox_test_")

        # 测试不同的工作目录
        policy = SandboxPolicy(
            working_directory=temp_dir,
            restrict_to_working_dir=True,
            create_working_dir_if_missing=True,
        )
        engine = SecurityPolicyEngine(policy)

        # 允许的路径 (在工作目录内)
        safe, _ = engine.check_path_traversal(f"{temp_dir}/file.txt")
        self.assertTrue(safe)

        # 阻止的路径
        safe, _ = engine.check_path_traversal("/etc/passwd")
        self.assertFalse(safe)


if __name__ == "__main__":
    print("Running security tests...")
    unittest.main(verbosity=2)
