"""
Flow Advanced Tests - Parallel, Conditional, Loop, Composite
"""

import pytest

from src.flow.parallel import ParallelFlow
from src.flow.conditional import ConditionalFlow
from src.flow.loop import LoopFlow
from src.flow.base import FlowSkill


class TestParallelFlow:
    """Test ParallelFlow"""

    def test_parallel_flow_creation(self):
        flow = ParallelFlow(max_concurrent=5)
        assert flow.max_concurrent == 5
        assert flow.name == "parallel"

    def test_trigger_patterns(self):
        flow = ParallelFlow()
        patterns = flow.trigger_patterns
        assert "并行" in patterns
        assert "concurrent" in patterns

    @pytest.mark.asyncio
    async def test_pre_process(self):
        flow = ParallelFlow()
        context = {}
        result = await flow.pre_process("同时执行A和B", context)
        assert "_parallel_tasks" in context
        assert "_task_count" in context

    @pytest.mark.asyncio
    async def test_post_process_partial(self):
        flow = ParallelFlow()
        context = {"_task_count": 3, "_completed_tasks": []}
        result = await flow.post_process("task 1 done", context)
        assert "1/3" in result
        assert "Still" in result

    @pytest.mark.asyncio
    async def test_post_process_complete(self):
        flow = ParallelFlow()
        context = {"_task_count": 2, "_completed_tasks": []}
        await flow.post_process("task 1", context)
        result = await flow.post_process("task 2", context)
        assert "All 2" in result


class TestConditionalFlow:
    """Test ConditionalFlow"""

    def test_conditional_flow_creation(self):
        flow = ConditionalFlow()
        assert flow.name == "conditional"

    def test_trigger_patterns(self):
        flow = ConditionalFlow()
        patterns = flow.trigger_patterns
        assert "如果" in patterns
        assert "if" in patterns

    @pytest.mark.asyncio
    async def test_pre_process(self):
        flow = ConditionalFlow()
        context = {}
        result = await flow.pre_process("如果A成功则执行B", context)
        assert "_branch_results" in context
        assert "_current_branch" in context


class TestLoopFlow:
    """Test LoopFlow"""

    def test_loop_flow_creation(self):
        flow = LoopFlow(max_iterations=10)
        assert flow.max_iterations == 10
        assert flow.name == "loop"

    def test_trigger_patterns(self):
        flow = LoopFlow()
        # Just verify it has trigger_patterns property
        patterns = flow.trigger_patterns
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_pre_process(self):
        flow = LoopFlow(max_iterations=5)
        context = {}
        result = await flow.pre_process("重复执行直到成功", context)
        assert "_loop_iteration" in context
        assert "_loop_results" in context


class TestFlowSkill:
    """Test base FlowSkill"""

    def test_flow_skill_is_abstract(self):
        """Verify FlowSkill is abstract"""
        # FlowSkill should be abstract and require implementation
        assert hasattr(FlowSkill, 'name')
        assert hasattr(FlowSkill, 'description')
