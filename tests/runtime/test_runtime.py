"""
Runtime module tests

Tests for sandbox and evaluator client functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSandboxConfig:
    """Test SandboxConfig"""

    def test_sandbox_config_defaults(self):
        """Test default configuration values"""
        from src.runtime.sandbox import SandboxConfig

        config = SandboxConfig()
        assert config.max_cpu_percent == 50.0
        assert config.max_memory_mb == 512
        assert config.max_execution_time_seconds == 300
        assert config.enable_evaluator is False

    def test_sandbox_config_custom(self):
        """Test custom configuration values"""
        from src.runtime.sandbox import SandboxConfig

        config = SandboxConfig(
            max_cpu_percent=80.0,
            max_memory_mb=1024,
            enable_evaluator=True,
        )
        assert config.max_cpu_percent == 80.0
        assert config.max_memory_mb == 1024
        assert config.enable_evaluator is True


class TestEvaluatorClient:
    """Test EvaluatorClient"""

    def test_evaluator_client_init(self):
        """Test evaluator client initialization"""
        from src.runtime.evaluator_client import EvaluatorClient

        client = EvaluatorClient()
        assert client is not None
        assert client._stub is None


class TestLogConsumer:
    """Test LogConsumer"""

    @pytest.mark.asyncio
    async def test_log_consumer_context(self):
        """Test log consumer context manager"""
        from src.runtime.evaluator_client import LogConsumerContext

        mock_evaluator = MagicMock()
        mock_evaluator.stream_logs = MagicMock(return_value=iter([]))

        context = LogConsumerContext(mock_evaluator, "session1", "task1")
        assert context.session_id == "session1"
        assert context.task_id == "task1"


class TestConfigLoader:
    """Test ConfigLoader"""

    def test_config_loader_init(self):
        """Test config loader initialization"""
        from src.config.loader import ConfigLoader

        loader = ConfigLoader("/tmp")
        assert str(loader.project_root) == "/tmp"

    def test_config_loader_merge(self):
        """Test config merging"""
        from src.config.loader import ConfigLoader

        loader = ConfigLoader()
        result = loader.merge_configs({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}
