"""
HarnessGraph - Executable graph with async streaming support

将 TaskCompiler 编译的 graph 包装为可执行的 async generator。
"""

import logging
from typing import Any, AsyncGenerator, Optional

from src.agents.harness.types import (
    ExecutionPhase,
    ExecutionStatus,
    PartialResult,
    StreamingExecutionResult,
)

logger = logging.getLogger(__name__)


class HarnessGraph:
    """Executable graph with async streaming support

    包装 TaskCompiler 编译的 graph， 提供 async generator 接口，
    允许调用者逐步接收执行进度。
    """

    def __init__(self, graph: dict[str, Any], config: Optional[dict[str, Any]] = None):
        """Initialize HarnessGraph.

        Args:
            graph: Compiled graph dict with nodes/edges
            config: Optional configuration dict
        """
        self._graph = graph
        self._config = config or {}
        self._engine = None  # Lazy initialization

    @property
    def graph(self) -> dict[str, Any]:
        """Get the underlying graph structure"""
        return self._graph

    @property
    def metadata(self) -> dict[str, Any]:
        """Get graph metadata"""
        return self._graph.get("metadata", {})

    async def run(self) -> AsyncGenerator[PartialResult, None]:
        """Execute graph, yielding partial results.

        Yields:
            PartialResult at each phase/step
        """
        from src.agents.harness.engine import HarnessEngine, HarnessConfig

        # Initialize engine with config
        engine_config = HarnessConfig(
            max_iterations=self._config.get("max_iterations", 10),
            enable_phases=self._config.get("enable_phases", True),
        )
        self._engine = HarnessEngine(engine_config)

        # Get task description from graph metadata
        task_description = self.metadata.get("description", "")

        # Execute with streaming
        iteration = 0
        total_phases = 3  # UNIT, INTEGRATION, E2E
        current_phase_idx = 0

        async for exec_result in self._engine.execute_streaming(task_description):
            # Calculate progress
            phase_progress = (iteration + 1) / self._config.get("max_iterations", 10)

            # Map execution phase to our phase
            phase = exec_result.phase or ExecutionPhase.UNIT

            # Determine status
            if exec_result.status == "running":
                status = ExecutionStatus.RUNNING
            elif exec_result.status == "completed":
                status = ExecutionStatus.COMPLETED
            else:
                status = ExecutionStatus.FAILED

            # Create partial result
            partial = PartialResult(
                phase=phase,
                progress=min(phase_progress, 1.0),
                iteration=exec_result.iteration,
                status=status,
                data={
                    "result": exec_result.result,
                    "evaluation": exec_result.evaluation.value if exec_result.evaluation else None,
                    "error": exec_result.error,
                    "metadata": exec_result.metadata,
                },
                partial_output=exec_result.partial_output,
                timestamp=exec_result.timestamp if hasattr(exec_result, 'timestamp') else None,
            )

            yield partial

            # Update iteration for next yield
            if exec_result.feedback_action and exec_result.feedback_action.value == "complete":
                break

            iteration += 1

        # Final result
        yield PartialResult(
            phase=ExecutionPhase.E2E,
            progress=1.0,
            iteration=iteration,
            status=ExecutionStatus.COMPLETED,
            data={"result": "completed"},
            partial_output=None,
        )
