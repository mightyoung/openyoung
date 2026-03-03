"""
YoungAgent Tests - Task 2.1
"""

import pytest
from src.agents.young_agent import YoungAgent
from src.core.types import AgentConfig, AgentMode, SubAgentType, Task


class TestYoungAgent:
    """Test YoungAgent - Task 2.1"""

    @pytest.fixture
    def config(self):
        return AgentConfig(name="test-agent", mode=AgentMode.PRIMARY)

    @pytest.fixture
    def agent(self, config):
        return YoungAgent(config)

    def test_agent_initialization(self, agent):
        """测试 Agent 初始化"""
        assert agent.mode == AgentMode.PRIMARY
        assert agent._session_id is not None
        assert len(agent._history) == 0

    def test_builtin_subagents(self, agent):
        """测试内置 SubAgents"""
        assert "explore" in agent._sub_agents
        assert "general" in agent._sub_agents
        assert "builder" in agent._sub_agents
        assert "reviewer" in agent._sub_agents
        assert "eval" in agent._sub_agents

    def test_get_subagent(self, agent):
        """测试获取 SubAgent"""
        explore = agent.get_subagent("explore")
        assert explore is not None
        assert explore.type == SubAgentType.EXPLORE

    def test_register_subagent(self, agent):
        """测试注册自定义 SubAgent"""
        from src.core.types import SubAgentConfig, PermissionConfig

        custom_config = SubAgentConfig(
            name="custom", type=SubAgentType.GENERAL, description="Custom subagent"
        )
        agent.register_subagent(custom_config)

        assert "custom" in agent._sub_agents

    def test_get_context(self, agent):
        """测试获取上下文"""
        ctx = agent._get_context()
        assert "session_id" in ctx
        assert "mode" in ctx
        assert ctx["mode"] == "primary"

    @pytest.mark.asyncio
    async def test_run_simple_input(self, agent):
        """测试简单输入"""
        result = await agent.run("Hello")
        assert result is not None

    @pytest.mark.asyncio
    async def test_run_with_mention(self, agent):
        """测试 @mention 调用"""
        result = await agent.run("@explore Find all Python files")
        assert "executed" in result.lower() or "dispatched" in result.lower()

    def test_add_message(self, agent):
        """测试添加消息"""
        from src.core.types import Message, MessageRole

        msg = Message(role=MessageRole.USER, content="Test")
        agent.add_message(msg)

        assert len(agent.history) == 1
        assert agent.history[0].content == "Test"
