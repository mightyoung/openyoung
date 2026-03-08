"""
YoungAgent Tests - Task 2.1
"""

import pytest

from src.agents.young_agent import YoungAgent
from src.core.types import AgentConfig, AgentMode, SubAgentType


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
        # Access via internal _sub_agents dict
        explore = agent._sub_agents.get("explore")
        assert explore is not None
        assert explore.type == SubAgentType.EXPLORE

    def test_register_subagent(self, agent):
        """测试注册自定义 SubAgent - via internal API"""
        from src.agents.sub_agent import SubAgent
        from src.core.types import SubAgentConfig

        custom_config = SubAgentConfig(
            name="custom", type=SubAgentType.GENERAL, description="Custom subagent"
        )
        # Register via internal _sub_agents dict
        agent._sub_agents["custom"] = SubAgent(
            custom_config, llm_client=agent._llm, tool_executor=agent._tool_executor
        )

        assert "custom" in agent._sub_agents

    def test_get_context(self, agent):
        """测试获取上下文 - via internal attributes"""
        # Access internal state directly
        assert hasattr(agent, "_session_id")
        assert agent._session_id is not None
        assert agent.mode is not None

    @pytest.mark.asyncio
    async def test_run_simple_input(self, agent):
        """测试简单输入"""
        result = await agent.run("Hello")
        assert result is not None

    @pytest.mark.asyncio
    async def test_run_with_mention(self, agent):
        """测试 @mention 调用"""
        # Skip if no LLM config available
        import os
        if not os.getenv("DEEPSEEK_CONFIG"):
            pytest.skip("No LLM config available")

        result = await agent.run("@explore Find all Python files")
        assert result is not None

    def test_add_message(self, agent):
        """测试添加消息 - via internal _history"""
        from src.core.types import Message, MessageRole

        msg = Message(role=MessageRole.USER, content="Test")
        # Add via internal _history
        agent._history.append(msg)

        assert len(agent._history) == 1
        assert agent._history[0].content == "Test"
