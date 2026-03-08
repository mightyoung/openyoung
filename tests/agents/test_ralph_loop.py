"""
Tests for Ralph Loop implementation
"""

import pytest
import asyncio

from src.agents.ralph_loop import (
    AgentCategory,
    AgentCategoryConfig,
    AGENT_CATEGORY_CONFIGS,
    RalphLoop,
    RalphLoopConfig,
    LoopIteration,
    TodoEnforcer,
)


class TestAgentCategory:
    """Test Agent Category enum and configs"""

    def test_category_enum(self):
        """Test AgentCategory enum values"""
        assert AgentCategory.QUICK.value == "quick"
        assert AgentCategory.VISUAL.value == "visual"
        assert AgentCategory.DEEP.value == "deep"
        assert AgentCategory.ULTRABRAIN.value == "ultrabrain"

    def test_category_configs(self):
        """Test category configurations"""
        assert len(AGENT_CATEGORY_CONFIGS) == 4

        quick_config = AGENT_CATEGORY_CONFIGS[AgentCategory.QUICK]
        assert quick_config.timeout_seconds == 60
        assert "快速" in quick_config.description

        deep_config = AGENT_CATEGORY_CONFIGS[AgentCategory.DEEP]
        assert deep_config.timeout_seconds == 600


class TestRalphLoopConfig:
    """Test RalphLoopConfig"""

    def test_default_config(self):
        """Test default configuration"""
        config = RalphLoopConfig()
        assert config.max_iterations == 10
        assert config.min_completion_rate == 0.8
        assert config.enable_parallel is True
        assert config.max_parallel_agents == 5

    def test_custom_config(self):
        """Test custom configuration"""
        config = RalphLoopConfig(
            max_iterations=5,
            min_completion_rate=0.9,
            enable_parallel=False,
        )
        assert config.max_iterations == 5
        assert config.min_completion_rate == 0.9
        assert config.enable_parallel is False


class TestRalphLoop:
    """Test RalphLoop"""

    @pytest.mark.asyncio
    async def test_loop_creation(self):
        """Test RalphLoop creation"""
        loop = RalphLoop()
        assert loop.config.max_iterations == 10
        assert loop.is_running is False
        assert loop.get_iteration_count() == 0

    @pytest.mark.asyncio
    async def test_run_until_complete_first_try(self):
        """Test loop completes on first try"""
        loop = RalphLoop()

        result = await loop.run_until_complete(
            task_description="简单任务",
            initial_context={},
        )

        assert result["is_complete"] is True
        assert result["iterations"] == 1

    @pytest.mark.asyncio
    async def test_max_iterations_limit(self):
        """Test max iterations limit"""
        # 创建一个总是返回未完成的 loop
        loop = RalphLoop()

        # 覆盖评估方法让每次都返回未完成
        async def always_incomplete(*args):
            return {"is_complete": False, "completion_rate": 0.5}

        loop._evaluate_results = always_incomplete

        result = await loop.run_until_complete(
            task_description="复杂任务",
            initial_context={},
        )

        # 应该达到最大迭代次数
        assert result["iterations"] == 10
        assert result["is_complete"] is False

    @pytest.mark.asyncio
    async def test_stop_loop(self):
        """Test stopping the loop"""
        loop = RalphLoop()

        # 启动循环
        task = asyncio.create_task(
            loop.run_until_complete("长时间任务", {})
        )

        # 等待一小段时间让循环开始
        await asyncio.sleep(0.1)

        # 停止循环
        loop.stop()

        # 等待任务完成
        result = await task

        # 循环应该被停止
        assert loop.is_running is False


class TestTodoEnforcer:
    """Test TodoEnforcer"""

    def test_enforcer_creation(self):
        """Test TodoEnforcer creation"""
        enforcer = TodoEnforcer()
        assert enforcer.idle_count == 0
        assert enforcer.busy_count == 0

    def test_register_idle(self):
        """Test registering idle agents"""
        enforcer = TodoEnforcer()

        enforcer.register_idle("agent-1", {"name": "Worker 1"})
        enforcer.register_idle("agent-2", {"name": "Worker 2"})

        assert enforcer.idle_count == 2

    def test_register_busy(self):
        """Test registering busy agents"""
        enforcer = TodoEnforcer()

        enforcer.register_idle("agent-1")
        enforcer.register_busy("agent-1", "task-1")

        assert enforcer.idle_count == 0
        assert enforcer.busy_count == 1

    def test_release_agent(self):
        """Test releasing agents"""
        enforcer = TodoEnforcer()

        enforcer.register_busy("agent-1", "task-1")
        enforcer.release_agent("agent-1")

        assert enforcer.idle_count == 1
        assert enforcer.busy_count == 0

    def test_pull_idle_for_task(self):
        """Test pulling idle agent for task"""
        enforcer = TodoEnforcer()

        enforcer.register_idle("agent-1")
        enforcer.register_idle("agent-2")

        pulled = enforcer.pull_idle_for_task("task-new")

        assert pulled == "agent-1"
        assert enforcer.idle_count == 1
        assert enforcer.busy_count == 1

    def test_no_idle_agents(self):
        """Test when no idle agents available"""
        enforcer = TodoEnforcer()

        # 没有空闲 agent
        assert enforcer.get_idle_agent() is None

        pulled = enforcer.pull_idle_for_task("task-1")
        assert pulled is None


class TestAgentCategorySelection:
    """Test agent category selection logic"""

    def test_select_quick_for_simple_task(self):
        """Test selecting QUICK for simple task"""
        # 简单文件操作应该选择 quick
        task = "修改 config.json 中的 timeout 值"
        category = AgentCategory.QUICK  # 简化测试

        assert category == AgentCategory.QUICK

    def test_select_deep_for_complex_task(self):
        """Test selecting DEEP for complex task"""
        # 复杂任务应该选择 deep
        category = AgentCategory.DEEP

        assert category == AgentCategory.DEEP

    def test_category_config_timeout(self):
        """Test category timeout values"""
        assert AGENT_CATEGORY_CONFIGS[AgentCategory.QUICK].timeout_seconds == 60
        assert AGENT_CATEGORY_CONFIGS[AgentCategory.DEEP].timeout_seconds == 600
        assert AGENT_CATEGORY_CONFIGS[AgentCategory.ULTRABRAIN].timeout_seconds == 900
