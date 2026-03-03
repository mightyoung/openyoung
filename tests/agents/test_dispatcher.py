"""
TaskDispatcher Tests - Task 2.2
"""

import pytest
from src.agents.dispatcher import TaskDispatcher, Session
from src.agents.young_agent import SubAgent
from src.core.types import (
    SubAgentConfig,
    SubAgentType,
    TaskDispatchParams,
    PermissionConfig,
)


class TestTaskDispatcher:
    """Test TaskDispatcher - Task 2.2"""

    @pytest.fixture
    def subagents(self):
        """创建测试用 SubAgents"""
        agents = {}
        for name, stype in [
            ("explore", SubAgentType.EXPLORE),
            ("builder", SubAgentType.BUILDER),
        ]:
            config = SubAgentConfig(name=name, type=stype, description=f"Test {name}")
            agents[name] = SubAgent(config)
        return agents

    @pytest.fixture
    def dispatcher(self, subagents):
        return TaskDispatcher(subagents)

    def test_dispatcher_initialization(self, dispatcher):
        """测试调度器初始化"""
        assert dispatcher.sub_agents is not None
        assert len(dispatcher._sessions) == 0

    @pytest.mark.asyncio
    async def test_get_or_create_session_new(self, dispatcher):
        """测试创建新会话"""
        session_id = await dispatcher._get_or_create_session(
            None, "parent-session", "Test task"
        )
        assert session_id is not None
        assert session_id in dispatcher._sessions

    @pytest.mark.asyncio
    async def test_get_or_create_session_existing(self, dispatcher):
        """测试恢复现有会话"""
        session_id = "existing-task-id"
        dispatcher._sessions[session_id] = Session(
            session_id=session_id, parent_id="parent", title="Existing"
        )

        result_id = await dispatcher._get_or_create_session(
            session_id, None, "Different description"
        )

        assert result_id == session_id

    def test_build_isolated_context(self, dispatcher):
        """测试构建隔离上下文"""
        params = TaskDispatchParams(
            subagent_type=SubAgentType.EXPLORE,
            task_description="Find files",
            context={"key": "value"},
        )
        parent_context = {
            "session_id": "parent-123",
            "summary": "Previous work",
            "relevant_files": ["file1.py"],
        }

        context = dispatcher._build_isolated_context(params, parent_context)

        assert context["task_description"] == "Find files"
        assert context["parent_summary"] == "Previous work"
        assert context["relevant_files"] == ["file1.py"]
        assert context["custom_context"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_subagent(self, dispatcher):
        """测试未知 SubAgent 类型"""
        params = TaskDispatchParams(
            subagent_type=SubAgentType.EVAL,
            task_description="Do something",
        )

        with pytest.raises(ValueError, match="Unknown subagent"):
            await dispatcher.dispatch(params, {})

    @pytest.mark.asyncio
    async def test_dispatch_success(self, dispatcher):
        """测试成功调度"""
        params = TaskDispatchParams(
            subagent_type=SubAgentType.EXPLORE, task_description="Find Python files"
        )

        result = await dispatcher.dispatch(params, {"session_id": "parent-123"})

        assert "task_id" in result
        assert "output" in result
        assert result["status"] == "completed"

    def test_get_session(self, dispatcher):
        """测试获取会话"""
        session = Session("test-1", None, "Test")
        dispatcher._sessions["test-1"] = session

        result = dispatcher.get_session("test-1")
        assert result is not None
        assert result.session_id == "test-1"

    def test_list_sessions(self, dispatcher):
        """测试列出会话"""
        dispatcher._sessions["s1"] = Session("s1", None, "Test 1")
        dispatcher._sessions["s2"] = Session("s2", None, "Test 2")

        sessions = dispatcher.list_sessions()
        assert len(sessions) == 2


class TestSession:
    """Test Session class"""

    def test_session_creation(self):
        """测试会话创建"""
        session = Session("s1", "parent-1", "Test task")
        assert session.session_id == "s1"
        assert session.parent_id == "parent-1"
        assert session.title == "Test task"
        assert len(session.messages) == 0

    def test_add_message(self):
        """测试添加消息"""
        session = Session("s1", None, "Test")
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there")

        assert len(session.messages) == 2
        assert session.messages[0]["role"] == "user"
