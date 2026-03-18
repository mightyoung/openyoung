"""
Tests for HarnessGraph streaming interface

Tests for:
- HarnessGraph.run() async generator
- PartialResult output
- Graph metadata
- Integration with HarnessEngine
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.harness.graph import HarnessGraph
from src.agents.harness.types import (
    ExecutionPhase,
    ExecutionStatus,
    PartialResult,
    StreamingExecutionResult,
    EvaluationResult,
    FeedbackAction,
)


class TestHarnessGraph:
    """Test HarnessGraph class"""

    @pytest.fixture
    def sample_graph(self):
        """Create sample graph structure"""
        return {
            "nodes": ["start", "unit", "integration", "e2e", "end"],
            "edges": [
                ("start", "unit"),
                ("unit", "integration"),
                ("integration", "e2e"),
                ("e2e", "end"),
            ],
            "metadata": {
                "description": "Test task for graph execution",
                "version": "1.0",
            },
        }

    @pytest.fixture
    def harness_graph(self, sample_graph):
        """Create HarnessGraph instance"""
        config = {
            "max_iterations": 3,
            "enable_phases": True,
        }
        return HarnessGraph(sample_graph, config)

    def test_harness_graph_initialization(self, harness_graph, sample_graph):
        """Test HarnessGraph initializes correctly"""
        assert harness_graph.graph == sample_graph
        assert harness_graph.metadata["description"] == "Test task for graph execution"
        assert harness_graph._engine is None

    def test_harness_graph_graph_property(self, harness_graph, sample_graph):
        """Test graph property returns underlying graph"""
        assert harness_graph.graph == sample_graph

    def test_harness_graph_metadata_property(self, harness_graph):
        """Test metadata property returns graph metadata"""
        assert harness_graph.metadata["description"] == "Test task for graph execution"
        assert harness_graph.metadata["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_harness_graph_run_is_async_generator(self, harness_graph):
        """Test that run() returns an async generator"""
        result = harness_graph.run()
        assert asyncio.iscoroutine(result) or hasattr(result, '__aiter__')
        # Consume the generator to avoid warnings
        if hasattr(result, '__anext__'):
            try:
                await result.__anext__()
            except StopAsyncIteration:
                pass

    @pytest.mark.asyncio
    async def test_harness_graph_run_yields_partial_results(self, sample_graph):
        """Test that run() yields PartialResult objects"""
        config = {"max_iterations": 3, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.RUNNING,
                partial_output="Starting unit phase...",
            ),
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.COMPLETE,
                result={"status": "success"},
                partial_output="Completed unit phase",
            ),
        ]

        # Create mock engine
        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        # Patch HarnessEngine class to return our mock engine
        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            results = []
            async for partial in harness_graph.run():
                results.append(partial)
                assert isinstance(partial, PartialResult)
                assert partial.phase in ExecutionPhase
                assert partial.progress >= 0.0

    @pytest.mark.asyncio
    async def test_harness_graph_maps_execution_status(self, sample_graph):
        """Test that execution status is mapped correctly"""
        config = {"max_iterations": 3, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.COMPLETE,
                result={"status": "success"},
                partial_output="Completed unit phase",
            ),
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            async for partial in harness_graph.run():
                assert partial.status in ExecutionStatus

    @pytest.mark.asyncio
    async def test_harness_graph_partial_result_to_dict(self, sample_graph):
        """Test PartialResult.to_dict() method"""
        config = {"max_iterations": 3, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.COMPLETE,
                result={"status": "success"},
                partial_output="Completed unit phase",
            ),
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            async for partial in harness_graph.run():
                result_dict = partial.to_dict()
                assert isinstance(result_dict, dict)
                assert "phase" in result_dict
                assert "progress" in result_dict
                assert "iteration" in result_dict
                assert "status" in result_dict
                assert "data" in result_dict

    @pytest.mark.asyncio
    async def test_harness_graph_progress_calculation(self, sample_graph):
        """Test that progress is calculated correctly"""
        config = {"max_iterations": 3, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.COMPLETE,
                result={"status": "success"},
                partial_output="Completed unit phase",
            ),
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            async for partial in harness_graph.run():
                assert partial.progress >= 0.0
                assert partial.progress <= 1.0

    @pytest.mark.asyncio
    async def test_harness_graph_multiple_iterations(self):
        """Test graph execution with multiple iterations"""
        graph = {
            "nodes": ["start", "unit", "end"],
            "edges": [("start", "unit"), ("unit", "end")],
            "metadata": {"description": "Multi-iteration test"},
        }
        config = {"max_iterations": 5, "enable_phases": True}
        harness_graph = HarnessGraph(graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=i,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.RETRY if i < 2 else FeedbackAction.COMPLETE,
                result={"iteration": i},
                partial_output=f"Completed iteration {i}",
            )
            for i in range(3)
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            results = []
            async for partial in harness_graph.run():
                results.append(partial)

            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_harness_graph_error_in_execution(self, sample_graph):
        """Test graph handles errors in execution"""
        config = {"max_iterations": 1, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.FAILED,
                error="Test error",
                partial_output="Error occurred",
            ),
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            results = []
            async for partial in harness_graph.run():
                results.append(partial)

            # Should still yield results even on error
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_harness_graph_final_result(self, sample_graph):
        """Test that final result is yielded"""
        config = {"max_iterations": 1, "enable_phases": True}
        harness_graph = HarnessGraph(sample_graph, config)

        mock_streaming_results = [
            StreamingExecutionResult(
                phase=ExecutionPhase.UNIT,
                iteration=0,
                status=ExecutionStatus.COMPLETED,
                evaluation=EvaluationResult.PASS,
                feedback_action=FeedbackAction.COMPLETE,
                result={"status": "success"},
                partial_output="Completed",
            ),
        ]

        mock_engine = MagicMock()
        mock_engine.execute_streaming = MagicMock(return_value=async_gen(mock_streaming_results))

        with patch('src.agents.harness.engine.HarnessEngine', return_value=mock_engine):
            results = []
            async for partial in harness_graph.run():
                results.append(partial)

            # Last result should be final
            final_result = results[-1]
            assert final_result.progress == 1.0


class TestHarnessGraphEdgeCases:
    """Test HarnessGraph edge cases"""

    def test_harness_graph_empty_metadata(self):
        """Test graph with empty metadata"""
        graph = {
            "nodes": ["start", "end"],
            "edges": [("start", "end")],
            "metadata": {},
        }
        harness_graph = HarnessGraph(graph)

        assert harness_graph.metadata == {}

    def test_harness_graph_no_metadata_key(self):
        """Test graph without metadata key"""
        graph = {
            "nodes": ["start", "end"],
            "edges": [("start", "end")],
        }
        harness_graph = HarnessGraph(graph)

        assert harness_graph.metadata == {}

    def test_harness_graph_custom_config(self):
        """Test graph with custom configuration"""
        graph = {
            "nodes": ["start", "end"],
            "edges": [("start", "end")],
            "metadata": {"description": "test"},
        }
        config = {
            "max_iterations": 20,
            "enable_phases": False,
            "custom_key": "custom_value",
        }
        harness_graph = HarnessGraph(graph, config)

        assert harness_graph.graph["metadata"]["description"] == "test"


# Helper to create async generator
def async_gen(items):
    """Create async generator from list of items"""
    async def generator():
        for item in items:
            yield item
    return generator()
