"""
Sandbox Manager Tests - 沙箱管理器测试

测试网络隔离功能:
1. 网络访问控制
2. 命令模式检测
3. 集成测试

注意: PROCESS 后端已禁用，测试更新为使用 E2B/DOCKER 后端
"""

import asyncio
import unittest
import sys

sys.path.insert(0, "/Users/muyi/Downloads/dev/openyoung")

from src.runtime.sandbox.manager import (
    SandboxManager,
    SandboxConfig,
    SandboxBackend,
    ProcessSandbox,
    DockerSandbox,
    _check_docker_available,
)
from src.runtime.sandbox.e2b_adapter import E2B_AVAILABLE
from src.runtime.sandbox.security_policy import SandboxPolicy, RiskLevel


def run_async(coro):
    """运行异步测试的辅助函数"""
    return asyncio.run(coro)


def _sandbox_available():
    """检查是否有可用的沙箱后端"""
    if E2B_AVAILABLE:
        return True
    # Docker daemon might be running but DockerSandbox not implemented
    if _check_docker_available():
        # Check if DockerSandbox is actually implemented by trying to create one
        try:
            config = SandboxConfig(backend=SandboxBackend.DOCKER)
            ds = DockerSandbox(config)
            # If we get here, DockerSandbox exists but is it implemented?
            # DockerSandbox.execute() returns "not yet implemented" error
            # So we consider it NOT available for testing
            return False
        except Exception:
            return False
    return False


SKIP_REASON = "Requires E2B or Docker backend (PROCESS backend disabled for security)"


class TestProcessSandboxNetworkIsolation(unittest.TestCase):
    """测试 ProcessSandbox 网络隔离

    注意: 由于 PROCESS 后端已禁用，这些测试依赖于 E2B/Docker 后端
    的网络隔离能力。如果后端不可用，测试将被跳过。
    """

    def setUp(self):
        """设置测试环境"""
        self.policy = SandboxPolicy(
            allow_network=False,  # 默认禁止网络
        )
        # 检查是否有可用的沙箱后端
        if not _sandbox_available():
            self.skipTest(SKIP_REASON)
        self.config = SandboxConfig(
            backend=SandboxBackend.E2B if E2B_AVAILABLE else SandboxBackend.DOCKER,
            policy=self.policy,
            timeout=10,
        )
        self.sandbox = SandboxManager(self.config)

    def test_safe_command_allowed(self):
        """测试安全命令被允许 (无网络操作)"""
        result = run_async(
            self.sandbox.execute("echo 'hello world'", "bash")
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello world", result.output)

    def test_python_code_allowed(self):
        """测试 Python 代码被执行 (无网络操作)"""
        code = "print('hello from python')"
        result = run_async(
            self.sandbox.execute(code, "python")
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello from python", result.output)

    def test_arithmetic_python(self):
        """测试 Python 算术运算"""
        code = "x = 1 + 1; print(x)"
        result = run_async(
            self.sandbox.execute(code, "python")
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("2", result.output)


class TestSandboxManagerNetworkIsolation(unittest.TestCase):
    """测试 SandboxManager 网络隔离集成

    注意: PROCESS 后端已禁用，测试更新为使用 E2B/DOCKER 后端
    """

    def setUp(self):
        """设置测试环境"""
        self.policy = SandboxPolicy(
            allow_network=False,
            force_sandbox=True,
        )
        if not _sandbox_available():
            self.skipTest(SKIP_REASON)
        self.config = SandboxConfig(
            backend=SandboxBackend.E2B if E2B_AVAILABLE else SandboxBackend.DOCKER,
            policy=self.policy,
            timeout=10,
        )
        self.manager = SandboxManager(self.config)

    def test_manager_allows_safe_command(self):
        """测试 Manager 允许安全命令"""
        result = run_async(
            self.manager.execute("ls -la", "bash")
        )
        self.assertEqual(result.exit_code, 0)

    def test_manager_allows_safe_python(self):
        """测试 Manager 允许安全 Python 代码"""
        result = run_async(
            self.manager.execute("x = 1 + 1; print(x)", "python")
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("2", result.output)


class TestNetworkPatternsDetection(unittest.TestCase):
    """测试网络模式检测

    这些测试直接测试 ProcessSandbox._check_network_access() 方法，
    该方法仍然可用（即使 PROCESS 后端被禁用）。
    """

    def test_curl_pattern_detected(self):
        """测试 curl 模式被检测"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertFalse(sandbox._check_network_access("curl https://example.com"))

    def test_wget_pattern_detected(self):
        """测试 wget 模式被检测"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertFalse(sandbox._check_network_access("wget https://example.com"))

    def test_nc_pattern_detected(self):
        """测试 nc 模式被检测"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertFalse(sandbox._check_network_access("nc -l 8080"))

    def test_scp_pattern_detected(self):
        """测试 scp 模式被检测"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertFalse(sandbox._check_network_access("scp file.txt user@host:"))

    def test_safe_command_passes(self):
        """测试安全命令通过检查"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertTrue(sandbox._check_network_access("ls -la"))
        self.assertTrue(sandbox._check_network_access("cat file.txt"))
        self.assertTrue(sandbox._check_network_access("grep 'pattern' file"))

    def test_python_command_passes(self):
        """测试 Python 命令通过检查"""
        sandbox = ProcessSandbox(SandboxConfig())
        self.assertTrue(sandbox._check_network_access("python3 script.py"))


class TestNetworkIsolationDocumentation(unittest.TestCase):
    """文档测试 - 验证文档字符串正确性"""

    def test_sandbox_config_docstring(self):
        """测试 SandboxConfig 文档字符串"""
        doc = SandboxConfig.__doc__
        self.assertIsNotNone(doc)

    def test_process_sandbox_has_docstring(self):
        """测试 ProcessSandbox 有文档字符串"""
        doc = ProcessSandbox.__doc__
        self.assertIsNotNone(doc)

    def test_check_network_access_has_docstring(self):
        """测试 _check_network_access 有文档字符串"""
        sandbox = ProcessSandbox(SandboxConfig())
        doc = sandbox._check_network_access.__doc__
        self.assertIsNotNone(doc)
        # 检查文档字符串包含相关关键词 (支持中英文)
        self.assertTrue(
            "network" in doc.lower() or "网络" in doc,
            f"Docstring should mention network access: {doc}"
        )


if __name__ == "__main__":
    print("Running sandbox network isolation tests...")
    unittest.main(verbosity=2)
