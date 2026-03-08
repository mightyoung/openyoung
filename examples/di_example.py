"""
Dependency Injection Examples

This module demonstrates how to use dependency injection for testing.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass, field
from typing import Any


# ========== Mock Implementations ==========


class MockLLMClient:
    """Mock LLM client for testing"""

    def __init__(self, response: str = "Mock response"):
        self.response = response
        self.call_count = 0

    async def chat(self, messages: Any, **kwargs: Any) -> Any:
        self.call_count += 1
        # Return mock response
        class MockResponse:
            content = self.response
            reasoning = None
            usage = {"input_tokens": 10, "output_tokens": 20}
            model = "mock"
            provider = "mock"

        return MockResponse()


class MockToolExecutor:
    """Mock tool executor for testing"""

    def __init__(self, result: Any = None):
        self.result = result or {"status": "success"}
        self.call_count = 0

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        self.call_count += 1
        return self.result

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        return [{"name": "mock_tool", "description": "Mock tool"}]


class MockCheckpointManager:
    """Mock checkpoint manager for testing"""

    def __init__(self):
        self.checkpoints = {}
        self.call_count = 0

    async def create_checkpoint(self, file_path: str, reason: str = "edit") -> str | None:
        self.call_count += 1
        checkpoint_id = f"mock_{self.call_count}"
        self.checkpoints[checkpoint_id] = {"file_path": file_path, "reason": reason}
        return checkpoint_id

    async def restore_checkpoint(self, checkpoint_id: str, target_path: str | None = None) -> bool:
        return checkpoint_id in self.checkpoints


class MockHarness:
    """Mock test harness for testing"""

    def __init__(self):
        self.started = False
        self.stopped = False
        self.steps = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def record_step(self, success: bool) -> None:
        self.steps.append(success)

    def get_status(self) -> dict[str, Any]:
        return {"started": self.started, "stopped": self.stopped, "steps": self.steps}


# ========== Example Usage ==========


def example_with_injected_dependencies():
    """Example: Using dependency injection with YoungAgent"""
    from src.agents import YoungAgent
    from src.core.types import AgentConfig, AgentMode

    # Create mock dependencies
    mock_llm = MockLLMClient(response="Test response")
    mock_tool_executor = MockToolExecutor(result={"status": "ok"})
    mock_checkpoint = MockCheckpointManager()
    mock_harness = MockHarness()

    # Create agent with injected dependencies
    config = AgentConfig(
        name="test_agent",
        mode=AgentMode.PRIMARY,
    )

    agent = YoungAgent(
        config,
        # Inject mock dependencies
        llm_client=mock_llm,
        tool_executor=mock_tool_executor,
        checkpoint_manager=mock_checkpoint,
        harness=mock_harness,
    )

    # Verify dependencies were injected
    assert agent._llm is mock_llm
    assert agent._tool_executor is mock_tool_executor
    assert agent._checkpoint_manager is mock_checkpoint
    assert agent._harness is mock_harness

    print("✓ Dependency injection works correctly!")
    return agent


if __name__ == "__main__":
    example_with_injected_dependencies()
