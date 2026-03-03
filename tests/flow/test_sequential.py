"""
Flow Tests - Phase 3
"""

import pytest
from src.flow.base import FlowSkill
from src.flow.sequential import SequentialFlow


class TestSequentialFlow:
    """Test SequentialFlow - Task 3.1"""

    @pytest.fixture
    def flow(self):
        return SequentialFlow()

    @pytest.fixture
    def flow_with_steps(self):
        return SequentialFlow(
            steps=[{"task": "step1"}, {"task": "step2"}, {"task": "step3"}]
        )

    def test_name(self, flow):
        assert flow.name == "sequential"

    def test_description(self, flow):
        assert flow.description == "串行执行多个步骤"

    def test_trigger_patterns(self, flow):
        patterns = flow.trigger_patterns
        assert "依次" in patterns
        assert "逐步" in patterns

    @pytest.mark.asyncio
    async def test_pre_process_no_steps(self, flow):
        """测试无预定义步骤时的分解"""
        context = {}
        result = await flow.pre_process("task1\ntask2\ntask3", context)

        assert result == "task1\ntask2\ntask3"
        assert context["_flow_steps"] == ["task1", "task2", "task3"]
        assert context["_current_step"] == 0
        assert context["_step_count"] == 3

    @pytest.mark.asyncio
    async def test_pre_process_with_steps(self, flow_with_steps):
        """测试有预定义步骤"""
        context = {}
        result = await flow_with_steps.pre_process("do something", context)

        assert result == "do something"
        assert len(context["_flow_steps"]) == 3

    @pytest.mark.asyncio
    async def test_post_process_continue(self, flow):
        """测试还有后续步骤"""
        context = {
            "_current_step": 0,
            "_step_count": 3,
            "_flow_steps": ["step1", "step2", "step3"],
        }

        result = await flow.post_process("done", context)

        assert context["_current_step"] == 1
        assert "Step 1/3 done" in result
        assert "Next: step2" in result

    @pytest.mark.asyncio
    async def test_post_process_complete(self, flow):
        """测试全部完成"""
        context = {
            "_current_step": 2,
            "_step_count": 3,
            "_flow_steps": ["step1", "step2", "step3"],
        }

        result = await flow.post_process("all done", context)

        assert "All 3 steps completed" in result

    @pytest.mark.asyncio
    async def test_should_delegate(self, flow):
        """测试委托判断"""
        context_single = {"_flow_steps": ["single"]}
        context_multi = {"_flow_steps": ["step1", "step2"]}

        assert await flow.should_delegate("task", context_single) is False
        assert await flow.should_delegate("task", context_multi) is True

    @pytest.mark.asyncio
    async def test_get_subagent_type(self, flow):
        """测试 SubAgent 类型选择"""
        assert await flow.get_subagent_type("find files") == "search"
        assert await flow.get_subagent_type("search for code") == "search"
        assert await flow.get_subagent_type("build something") == "builder"
        assert await flow.get_subagent_type("create file") == "builder"
        assert await flow.get_subagent_type("do something") == "general"
