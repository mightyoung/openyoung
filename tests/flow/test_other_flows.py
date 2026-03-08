"""
Flow Tests - Phase 3.2
"""

import pytest

from src.flow import ConditionalFlow, LoopFlow, ParallelFlow


class TestParallelFlow:
    """Test ParallelFlow - Task 3.2"""

    @pytest.fixture
    def flow(self):
        return ParallelFlow(max_concurrent=3)

    def test_name(self, flow):
        assert flow.name == "parallel"

    def test_description(self, flow):
        assert flow.description == "并行执行多个子任务"

    @pytest.mark.asyncio
    async def test_pre_process(self, flow):
        context = {}
        result = await flow.pre_process("task1 and task2 and task3", context)

        assert result == "task1 and task2 and task3"
        assert len(context["_parallel_tasks"]) == 3

    @pytest.mark.asyncio
    async def test_post_process_incomplete(self, flow):
        context = {"_completed_tasks": [], "_task_count": 3}

        result = await flow.post_process("done1", context)

        assert "Completed 1/3" in result

    @pytest.mark.asyncio
    async def test_post_process_complete(self, flow):
        context = {"_completed_tasks": ["r1", "r2"], "_task_count": 2}

        result = await flow.post_process("r3", context)

        assert "All 2 parallel tasks completed" in result


class TestConditionalFlow:
    """Test ConditionalFlow - Task 3.2"""

    @pytest.fixture
    def flow(self):
        return ConditionalFlow(
            conditions={"error": "error_handler", "success": "success_handler"},
            default_branch="default",
        )

    def test_name(self, flow):
        assert flow.name == "conditional"

    @pytest.mark.asyncio
    async def test_pre_process_match(self, flow):
        context = {}
        result = await flow.pre_process("check for error", context)

        assert context["_current_branch"] == "error_handler"

    @pytest.mark.asyncio
    async def test_pre_process_default(self, flow):
        context = {}
        result = await flow.pre_process("do something", context)

        assert context["_current_branch"] == "default"


class TestLoopFlow:
    """Test LoopFlow - Task 3.2"""

    @pytest.fixture
    def flow(self):
        return LoopFlow(max_iterations=5)

    def test_name(self, flow):
        assert flow.name == "loop"

    @pytest.mark.asyncio
    async def test_pre_process(self, flow):
        context = {}
        result = await flow.pre_process("repeat this", context)

        assert context["_loop_iteration"] == 0
        assert context["_loop_results"] == []

    @pytest.mark.asyncio
    async def test_post_process_continue(self, flow):
        context = {"_loop_iteration": 0, "_loop_results": []}

        result = await flow.post_process("iteration 1", context)

        assert context["_loop_iteration"] == 1
        assert "Continuing loop" in result

    @pytest.mark.asyncio
    async def test_post_process_max_iterations(self, flow):
        context = {"_loop_iteration": 4, "_loop_results": []}

        result = await flow.post_process("final", context)

        assert "Max iterations" in result
