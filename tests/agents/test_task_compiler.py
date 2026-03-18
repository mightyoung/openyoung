"""
Tests for TaskCompiler - Task → Harness Graph Compilation

Tests the TaskCompiler class that converts Task objects into HarnessGraph format.
"""

import pytest
from unittest.mock import MagicMock


class MockTask:
    """Mock Task object for testing"""

    def __init__(self, task_id: str = "test-id", description: str = "Test task description"):
        self.id = task_id
        self.description = description


class TestTaskCompiler:
    """Test TaskCompiler class"""

    def test_initialization(self):
        """Test TaskCompiler initialization"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()

        assert compiler._graph_template is not None
        assert "nodes" in compiler._graph_template
        assert "edges" in compiler._graph_template
        assert "metadata" in compiler._graph_template
        assert compiler._graph_template["nodes"] == []
        assert compiler._graph_template["edges"] == []

    def test_compile_task_with_description(self):
        """Test compiling a task with description"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        task = MockTask(task_id="task-123", description="Build a REST API")

        graph = compiler.compile(task)

        assert graph is not None
        assert graph.metadata["task_id"] == "task-123"
        assert graph.metadata["description"] == "Build a REST API"

    def test_compile_task_nodes(self):
        """Test that compiled task has root node"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        task = MockTask(description="Test task")

        graph = compiler.compile(task)

        assert len(graph.graph["nodes"]) == 1
        assert graph.graph["nodes"][0]["id"] == "root"
        assert graph.graph["nodes"][0]["type"] == "task"

    def test_compile_task_node_label(self):
        """Test that node label is truncated to 100 chars"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        long_description = "A" * 200
        task = MockTask(description=long_description)

        graph = compiler.compile(task)

        label = graph.graph["nodes"][0]["label"]
        assert len(label) == 100
        assert label == "A" * 100

    def test_compile_with_timestamp(self):
        """Test compile with custom timestamp"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        task = MockTask()

        graph = compiler.compile(task, timestamp="2024-01-01T00:00:00")

        assert graph.metadata["compiled_at"] == "2024-01-01T00:00:00"

    def test_compile_task_without_id(self):
        """Test compiling task without id attribute"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()

        class TaskWithoutId:
            description = "Task without ID"

        graph = compiler.compile(TaskWithoutId())

        assert graph.metadata["task_id"] is None

    def test_compile_task_without_description(self):
        """Test compiling task without description attribute falls back to str(task)"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()

        class TaskWithoutDesc:
            id = "task-456"

        task_instance = TaskWithoutDesc()
        task_str = str(task_instance)
        graph = compiler.compile(task_instance)

        # Falls back to str(task) since no description attribute
        assert graph.metadata["description"] == task_str

    def test_add_node(self):
        """Test adding a node to graph"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        result = compiler.add_node(graph, "node-1", "tool", "My Tool")

        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "node-1"
        assert result["nodes"][0]["type"] == "tool"
        assert result["nodes"][0]["label"] == "My Tool"

    def test_add_node_returns_modified_graph(self):
        """Test add_node returns the same graph object"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        result = compiler.add_node(graph, "node-1", "task", "Label")

        assert result is graph

    def test_add_edge(self):
        """Test adding an edge to graph"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        result = compiler.add_edge(graph, "node-1", "node-2", "next")

        assert len(result["edges"]) == 1
        assert result["edges"][0]["from"] == "node-1"
        assert result["edges"][0]["to"] == "node-2"
        assert result["edges"][0]["type"] == "next"

    def test_add_edge_default_type(self):
        """Test adding edge with default type"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        result = compiler.add_edge(graph, "node-1", "node-2")

        assert result["edges"][0]["type"] == "next"

    def test_add_edge_custom_type(self):
        """Test adding edge with custom type"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        result = compiler.add_edge(graph, "node-1", "node-2", "dependency")

        assert result["edges"][0]["type"] == "dependency"

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        compiler.add_node(graph, "node-1", "task", "Task 1")
        compiler.add_node(graph, "node-2", "tool", "Tool 1")
        compiler.add_node(graph, "node-3", "condition", "Condition 1")

        assert len(graph["nodes"]) == 3
        assert graph["nodes"][0]["id"] == "node-1"
        assert graph["nodes"][1]["id"] == "node-2"
        assert graph["nodes"][2]["id"] == "node-3"

    def test_add_multiple_edges(self):
        """Test adding multiple edges"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        graph = {"nodes": [], "edges": []}

        compiler.add_edge(graph, "node-1", "node-2", "next")
        compiler.add_edge(graph, "node-2", "node-3", "dependency")

        assert len(graph["edges"]) == 2
        assert graph["edges"][0]["from"] == "node-1"
        assert graph["edges"][1]["from"] == "node-2"


class TestTaskCompilerIntegration:
    """Integration tests for TaskCompiler"""

    def test_compile_and_extend_graph(self):
        """Test compiling a task and extending the graph"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()
        task = MockTask(description="Complex multi-step task")

        graph = compiler.compile(task)

        # Add more nodes
        compiler.add_node(graph.graph, "step-1", "task", "Step 1")
        compiler.add_node(graph.graph, "step-2", "task", "Step 2")
        compiler.add_node(graph.graph, "step-3", "tool", "Build tool")

        # Add edges
        compiler.add_edge(graph.graph, "root", "step-1", "dependency")
        compiler.add_edge(graph.graph, "step-1", "step-2", "next")
        compiler.add_edge(graph.graph, "step-2", "step-3", "next")

        assert len(graph.graph["nodes"]) == 4  # root + 3 steps
        assert len(graph.graph["edges"]) == 3

    def test_compile_empty_task(self):
        """Test compiling task with minimal attributes"""
        from src.agents.harness.task_compiler import TaskCompiler

        compiler = TaskCompiler()

        class EmptyTask:
            pass

        graph = compiler.compile(EmptyTask())

        assert graph is not None
        # Empty task has no description, so no root node is added
        assert len(graph.graph["nodes"]) == 0
