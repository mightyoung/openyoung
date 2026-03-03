"""
Core Types Tests - Task 1.1 & 1.2
"""

import pytest
from src.core.types import (
    AgentMode,
    PermissionAction,
    PermissionRule,
    PermissionConfig,
    AgentConfig,
    SubAgentType,
    SubAgentConfig,
    MessageRole,
    Message,
    TaskStatus,
    Task,
    TaskDispatchParams,
)


class TestAgentMode:
    """Test AgentMode enum - Task 1.1"""

    def test_primary_mode(self):
        assert AgentMode.PRIMARY.value == "primary"

    def test_subagent_mode(self):
        assert AgentMode.SUBAGENT.value == "subagent"

    def test_all_mode(self):
        assert AgentMode.ALL.value == "all"


class TestPermissionAction:
    """Test PermissionAction enum - Task 1.1"""

    def test_allow(self):
        assert PermissionAction.ALLOW.value == "allow"

    def test_ask(self):
        assert PermissionAction.ASK.value == "ask"

    def test_deny(self):
        assert PermissionAction.DENY.value == "deny"


class TestPermissionConfig:
    """Test PermissionConfig - Task 1.1"""

    def test_default_permission(self):
        config = PermissionConfig()
        assert config._global == PermissionAction.ASK
        assert config.rules == []
        assert config.confirm_message == "确认执行此操作?"

    def test_custom_permission(self):
        rule = PermissionRule(tool_pattern="bash", action=PermissionAction.DENY)
        config = PermissionConfig(
            _global=PermissionAction.ALLOW,
            rules=[rule],
            confirm_message="Custom message?",
        )
        assert config._global == PermissionAction.ALLOW
        assert len(config.rules) == 1
        assert config.rules[0].tool_pattern == "bash"


class TestAgentConfig:
    """Test AgentConfig - Task 1.1"""

    def test_default_config(self):
        config = AgentConfig(name="test-agent")
        assert config.name == "test-agent"
        assert config.mode == AgentMode.PRIMARY
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7

    def test_custom_config(self):
        config = AgentConfig(
            name="custom-agent",
            mode=AgentMode.SUBAGENT,
            model="claude-3-opus",
            temperature=0.5,
        )
        assert config.name == "custom-agent"
        assert config.mode == AgentMode.SUBAGENT
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.5


class TestSubAgentType:
    """Test SubAgentType enum - Task 1.1"""

    def test_explore_type(self):
        assert SubAgentType.EXPLORE.value == "explore"

    def test_builder_type(self):
        assert SubAgentType.BUILDER.value == "builder"

    def test_all_types(self):
        types = [t.value for t in SubAgentType]
        assert "explore" in types
        assert "general" in types
        assert "search" in types
        assert "builder" in types
        assert "reviewer" in types
        assert "eval" in types


class TestSubAgentConfig:
    """Test SubAgentConfig - Task 1.1"""

    def test_default_subagent(self):
        config = SubAgentConfig(
            name="test-subagent", type=SubAgentType.EXPLORE, description="Test subagent"
        )
        assert config.name == "test-subagent"
        assert config.type == SubAgentType.EXPLORE
        assert config.model == "default"
        assert config.hidden is False


class TestMessage:
    """Test Message - Task 1.2"""

    def test_user_message(self):
        msg = Message(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_assistant_message(self):
        msg = Message(role=MessageRole.ASSISTANT, content="Hello!", name="assistant")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.name == "assistant"


class TestTask:
    """Test Task - Task 1.2"""

    def test_default_task(self):
        task = Task(id="task-1", description="Test task", input="Do something")
        assert task.id == "task-1"
        assert task.status == TaskStatus.PENDING
        assert task.output is None

    def test_task_status_transitions(self):
        task = Task(id="task-2", description="Test", input="test")
        task.status = TaskStatus.RUNNING
        assert task.status == TaskStatus.RUNNING
        task.status = TaskStatus.COMPLETED
        assert task.status == TaskStatus.COMPLETED


class TestTaskDispatchParams:
    """Test TaskDispatchParams - Task 1.2"""

    def test_dispatch_params(self):
        params = TaskDispatchParams(
            subagent_type=SubAgentType.BUILDER,
            task_description="Build something",
            context={"key": "value"},
        )
        assert params.subagent_type == SubAgentType.BUILDER
        assert params.task_description == "Build something"
        assert params.context["key"] == "value"
