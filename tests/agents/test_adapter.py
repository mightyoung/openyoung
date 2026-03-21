"""
Agent Adapter Tests - Task #35

Tests for AgentAdapter that wraps SubAgent and converts:
- SubAgent.run(task, context) -> str
- To EvalRunner format: {transcript, outcome, metrics}
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.adapters import AgentAdapter, EvalAgent, adapt_subagent
from src.core.types import SubAgentConfig, SubAgentType, Task


class MockSubAgent:
    """Mock SubAgent for testing"""

    def __init__(self, return_value: str = "test response"):
        self.return_value = return_value
        self.run_called = False
        self.last_task = None
        self.last_context = None

    async def run(self, task: Task, context: dict) -> str:
        """Return string as real SubAgent does"""
        self.run_called = True
        self.last_task = task
        self.last_context = context
        return self.return_value


class TestAgentAdapter:
    """Test AgentAdapter class"""

    @pytest.fixture
    def mock_subagent(self):
        """Create a mock SubAgent"""
        return MockSubAgent(return_value="test response from subagent")

    @pytest.fixture
    def adapter(self, mock_subagent):
        """Create an AgentAdapter with mock SubAgent"""
        return AgentAdapter(mock_subagent)

    def test_adapter_initialization(self, adapter, mock_subagent):
        """Test adapter stores the wrapped agent"""
        assert adapter._agent is mock_subagent

    @pytest.mark.asyncio
    async def test_run_calls_subagent_run(self, adapter, mock_subagent):
        """Test that adapter.run() calls SubAgent.run()"""
        await adapter.run("test prompt")
        assert mock_subagent.run_called is True
        assert mock_subagent.last_task.input == "test prompt"

    @pytest.mark.asyncio
    async def test_run_returns_dict_format(self, adapter):
        """Test that run() returns dict with transcript, outcome, metrics"""
        result = await adapter.run("test prompt")

        assert isinstance(result, dict)
        assert "transcript" in result
        assert "outcome" in result
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_run_wraps_string_in_transcript(self, adapter):
        """Test string result is wrapped in transcript"""
        result = await adapter.run("test prompt")

        assert isinstance(result["transcript"], list)
        assert len(result["transcript"]) == 1
        assert result["transcript"][0]["role"] == "assistant"
        assert result["transcript"][0]["content"] == "test response from subagent"

    @pytest.mark.asyncio
    async def test_run_wraps_string_in_outcome(self, adapter):
        """Test string result is wrapped in outcome"""
        result = await adapter.run("test prompt")

        assert isinstance(result["outcome"], dict)
        assert "result" in result["outcome"]
        assert result["outcome"]["result"] == "test response from subagent"

    @pytest.mark.asyncio
    async def test_run_includes_metrics(self, adapter):
        """Test result includes metrics"""
        result = await adapter.run("test prompt")

        assert isinstance(result["metrics"], dict)
        assert "num_turns" in result["metrics"]
        assert result["metrics"]["num_turns"] == 1


class TestAgentAdapterWithJsonResult:
    """Test AgentAdapter with JSON string result"""

    @pytest.fixture
    def mock_subagent_with_json(self):
        """Create a mock SubAgent that returns JSON"""
        json_response = '{"transcript": [{"role": "assistant", "content": "json response"}], "outcome": {"result": "success"}, "metrics": {"score": 1.0}}'
        return MockSubAgent(return_value=json_response)

    @pytest.fixture
    def adapter(self, mock_subagent_with_json):
        return AgentAdapter(mock_subagent_with_json)

    @pytest.mark.asyncio
    async def test_parse_json_result(self, adapter):
        """Test that JSON string is parsed correctly"""
        result = await adapter.run("test prompt")

        assert isinstance(result, dict)
        assert "transcript" in result
        assert "outcome" in result
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_json_transcript_parsed(self, adapter):
        """Test JSON transcript is preserved"""
        result = await adapter.run("test prompt")

        assert len(result["transcript"]) == 1
        assert result["transcript"][0]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_json_outcome_parsed(self, adapter):
        """Test JSON outcome is preserved"""
        result = await adapter.run("test prompt")

        assert result["outcome"]["result"] == "success"

    @pytest.mark.asyncio
    async def test_json_metrics_parsed(self, adapter):
        """Test JSON metrics is preserved"""
        result = await adapter.run("test prompt")

        assert result["metrics"]["score"] == 1.0


class TestAdaptSubagent:
    """Test adapt_subagent convenience function"""

    def test_adapt_subagent_returns_adapter(self):
        """Test function returns AgentAdapter instance"""
        mock_agent = MockSubAgent()
        adapter = adapt_subagent(mock_agent)
        assert isinstance(adapter, AgentAdapter)

    @pytest.mark.asyncio
    async def test_adapted_agent_works(self):
        """Test adapted agent can run"""
        mock_agent = MockSubAgent(return_value="adapted response")
        adapter = adapt_subagent(mock_agent)

        result = await adapter.run("test")
        assert result["outcome"]["result"] == "adapted response"


class TestEvalAgentProtocol:
    """Test EvalAgent Protocol compliance"""

    @pytest.mark.asyncio
    async def test_adapter_matches_eval_agent_protocol(self):
        """Test AgentAdapter conforms to EvalAgent protocol"""
        mock_agent = MockSubAgent()
        adapter = AgentAdapter(mock_agent)

        # Protocol check: run method should exist and be callable
        assert hasattr(adapter, "run")
        assert callable(adapter.run)

        # Should return dict with expected keys
        result = await adapter.run("test")
        assert "transcript" in result
        assert "outcome" in result
        assert "metrics" in result
