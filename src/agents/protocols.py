"""
Protocol definitions for dependency injection

This module defines abstract interfaces (Protocols) for key components,
enabling dependency injection and easier testing.

Based on Python's Protocol class (structural subtyping):
- IClient: LLM client interface
- IToolExecutor: Tool execution interface
- ICheckpointManager: Checkpoint management interface
"""

from typing import Any, Protocol, TypedDict


class ChatKwargs(TypedDict, total=False):
    """Keyword arguments for IClient.chat"""

    model: str
    temperature: float
    max_tokens: int
    system: str
    tools: list[dict[str, Any]]
    tool_choice: str


class EvaluateKwargs(TypedDict, total=False):
    """Keyword arguments for IEvaluationHub.evaluate"""

    expected: str
    threshold: float
    metadata: dict[str, Any]


class IClient(Protocol):
    """LLM Client Protocol

    Defines the interface for LLM clients.
    Implement this protocol to create mockable LLM clients.
    """

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat request to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (optional)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            **kwargs: Additional parameters (model, temperature, etc.)

        Returns:
            LLM response dict with 'content', 'usage', 'model', etc.
        """
        ...


class IToolExecutor(Protocol):
    """Tool Executor Protocol

    Defines the interface for tool execution.
    Implement this protocol to create custom tool executors.
    """

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result (can be any type)
        """
        ...

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get available tool schemas.

        Returns:
            List of tool schema definitions
        """
        ...


class ICheckpointManager(Protocol):
    """Checkpoint Manager Protocol

    Defines the interface for checkpoint management.
    Implement this protocol to create custom checkpoint managers.
    """

    async def create_checkpoint(self, file_path: str, reason: str = "edit") -> str | None:
        """Create a checkpoint.

        Args:
            file_path: File to checkpoint
            reason: Reason for checkpoint

        Returns:
            Checkpoint ID or None
        """
        ...

    async def restore_checkpoint(self, checkpoint_id: str, target_path: str | None = None) -> bool:
        """Restore from a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID
            target_path: Target path (optional)

        Returns:
            True if successful
        """
        ...


class IEvaluationHub(Protocol):
    """Evaluation Hub Protocol

    Defines the interface for evaluation.
    """

    async def evaluate(
        self, metric: str, input_data: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Evaluate input data.

        Args:
            metric: Metric name
            input_data: Input to evaluate
            **kwargs: Additional parameters (expected, threshold, metadata, etc.)

        Returns:
            Evaluation result dict with 'score', 'passed', 'details', etc.
        """
        ...


class IHarness(Protocol):
    """Test Harness Protocol

    Defines the interface for test harnesses.
    """

    def start(self) -> None:
        """Start the harness."""
        ...

    def stop(self) -> None:
        """Stop the harness."""
        ...

    def record_step(self, success: bool) -> None:
        """Record a step result.

        Args:
            success: Whether the step succeeded
        """
        ...

    def get_status(self) -> dict[str, Any]:
        """Get harness status.

        Returns:
            Status dictionary
        """
        ...
