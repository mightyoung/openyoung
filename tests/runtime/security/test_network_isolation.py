"""
Network Isolation Integration Tests

Tests for network isolation enforcement in the execution path.
Verifies that _check_network_access() is properly called and blocks
network commands when allow_network=False.
"""

import pytest

from src.tools.executor import ToolExecutor
from src.tools.command_validator import check_network_access


class TestNetworkIsolation:
    """网络隔离测试"""

    @pytest.fixture
    def executor_no_network(self):
        """创建禁用网络的执行器"""
        return ToolExecutor(allow_network=False)

    @pytest.fixture
    def executor_with_network(self):
        """创建允许网络的执行器"""
        return ToolExecutor(allow_network=True)

    @pytest.mark.asyncio
    async def test_block_curl_command(self, executor_no_network):
        """curl 命令应该被阻止"""
        with pytest.raises(PermissionError) as exc_info:
            await executor_no_network.execute_bash("curl https://evil.com")
        assert "Network access blocked" in str(exc_info.value)
        assert "curl" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_block_wget_command(self, executor_no_network):
        """wget 命令应该被阻止"""
        with pytest.raises(PermissionError) as exc_info:
            await executor_no_network.execute_bash("wget https://evil.com")
        assert "Network access blocked" in str(exc_info.value)
        assert "wget" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_block_netcat_command(self, executor_no_network):
        """nc 命令应该被阻止"""
        with pytest.raises(PermissionError) as exc_info:
            await executor_no_network.execute_bash("nc -l 8080")
        assert "Network access blocked" in str(exc_info.value)
        assert "nc" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_block_ssh_command(self, executor_no_network):
        """ssh 命令应该被阻止"""
        with pytest.raises(PermissionError) as exc_info:
            await executor_no_network.execute_bash("ssh user@host")
        assert "Network access blocked" in str(exc_info.value)
        assert "ssh" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_block_ftp_command(self, executor_no_network):
        """ftp 命令应该被阻止"""
        with pytest.raises(PermissionError) as exc_info:
            await executor_no_network.execute_bash("ftp server")
        assert "Network access blocked" in str(exc_info.value)
        assert "ftp" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_allow_safe_commands(self, executor_no_network):
        """安全命令应该被允许"""
        # ls 是一个安全的本地命令，不涉及网络
        result = await executor_no_network.execute_bash("ls -la")
        # 不应该包含网络阻止的消息
        assert "网络访问被阻止" not in result
        assert "Network access blocked" not in result

    @pytest.mark.asyncio
    async def test_allow_network_when_enabled(self, executor_with_network):
        """启用网络时，curl 应该被允许"""
        # 注意：这里只检查是否被阻止，不实际执行网络请求
        # 因为实际请求可能会失败，但我们关心的是没有被阻止
        result = await executor_with_network.execute_bash("curl https://example.com")
        # 应该不会被网络检查阻止
        assert "网络访问被阻止" not in result
        assert "Network access blocked" not in result


class TestCheckNetworkAccess:
    """check_network_access 函数单元测试"""

    @pytest.fixture
    def allow_network_false(self):
        return False

    def test_check_network_access_blocks_curl(self, allow_network_false):
        """check_network_access 应该阻止 curl"""
        allowed, reason = check_network_access("curl https://evil.com", allow_network=allow_network_false)
        assert allowed is False
        assert "curl" in reason

    def test_check_network_access_blocks_wget(self, allow_network_false):
        """check_network_access 应该阻止 wget"""
        allowed, reason = check_network_access("wget https://evil.com", allow_network=allow_network_false)
        assert allowed is False
        assert "wget" in reason

    def test_check_network_access_blocks_nc(self, allow_network_false):
        """check_network_access 应该阻止 nc"""
        allowed, reason = check_network_access("nc -l 8080", allow_network=allow_network_false)
        assert allowed is False
        assert "nc" in reason

    def test_check_network_access_allows_safe_commands(self, allow_network_false):
        """check_network_access 应该允许安全命令"""
        allowed, reason = check_network_access("ls -la /tmp", allow_network=allow_network_false)
        assert allowed is True

    def test_check_network_access_case_insensitive(self, allow_network_false):
        """网络模式检测应该大小写不敏感"""
        allowed, reason = check_network_access("CURL https://evil.com", allow_network=allow_network_false)
        assert allowed is False

    def test_check_network_access_in_command_args(self, allow_network_false):
        """网络检查应检测命令参数中的网络工具"""
        # 命令中包含 curl，即使它不是第一个词
        allowed, reason = check_network_access("echo 'hello' && curl https://evil.com", allow_network=allow_network_false)
        assert allowed is False


class TestNetworkIsolationWithExecutor:
    """通过 execute() 方法的网络隔离测试"""

    @pytest.fixture
    def executor(self):
        return ToolExecutor(allow_network=False)

    @pytest.mark.asyncio
    async def test_execute_blocks_network_via_bash(self, executor):
        """通过 execute() 调用 bash 工具时应该阻止网络命令"""
        result = await executor.execute(
            "bash",
            {"command": "curl https://evil.com", "description": "test"}
        )
        # ToolResult format: success=False, error contains the message
        assert result.success is False
        assert "网络访问被阻止" in result.error or "Network access blocked" in result.error

    @pytest.mark.asyncio
    async def test_execute_allows_safe_bash_commands(self, executor):
        """安全的 bash 命令应该被允许"""
        result = await executor.execute(
            "bash",
            {"command": "echo hello", "description": "test"}
        )
        # 不应该因为网络检查失败
        if not result.success:
            assert "网络访问被阻止" not in result.error
            assert "Network access blocked" not in result.error


class TestNetworkIsolationIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_execution_path_with_network_block(self):
        """完整执行路径测试：网络命令被阻止"""
        executor = ToolExecutor(allow_network=False)

        # 模拟完整执行路径
        result = await executor.execute("bash", {"command": "curl http://example.com"})

        # 验证结果
        assert result.success is False
        assert "blocked" in result.error.lower() or "阻止" in result.error

    @pytest.mark.asyncio
    async def test_full_execution_path_without_network_block(self):
        """完整执行路径测试：非网络命令正常执行"""
        executor = ToolExecutor(allow_network=False)

        # 使用一个真正安全的命令
        result = await executor.execute("bash", {"command": "pwd"})

        # 验证结果不是由于网络检查失败
        if not result.success:
            assert "网络访问被阻止" not in result.error
            assert "Network access blocked" not in result.error
