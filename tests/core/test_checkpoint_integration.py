"""
Checkpoint Integration 单元测试

测试:
1. AgentState <-> Checkpoint 相互转换
2. 状态序列化/反序列化
3. LangGraph State 兼容性
"""

import pytest
from src.core.memory import (
    agent_state_to_checkpoint_state,
    checkpoint_state_to_agent_state,
)
from src.core.langgraph_state import (
    AgentState,
    TaskPhase,
    create_initial_state,
)


class TestAgentStateConversion:
    """AgentState <-> Checkpoint 转换测试"""

    def test_agent_state_to_checkpoint(self):
        """测试 AgentState -> Checkpoint 格式"""
        state = create_initial_state(
            task_id="test-001",
            task_description="Test task",
            context={"key": "value"},
        )
        state["phase"] = TaskPhase.PLANNING
        state["messages"] = [{"role": "user", "content": "Hello"}]

        # 转换
        checkpoint_state = agent_state_to_checkpoint_state(state)

        assert checkpoint_state["task_id"] == "test-001"
        assert checkpoint_state["phase"] == "planning"
        assert checkpoint_state["messages"] == [{"role": "user", "content": "Hello"}]
        assert checkpoint_state["context"] == {"key": "value"}

    def test_checkpoint_to_agent_state(self):
        """测试 Checkpoint 格式 -> AgentState"""
        checkpoint_state = {
            "task_id": "test-001",
            "task_description": "Test task",
            "phase": "planning",
            "messages": [{"role": "user", "content": "Hello"}],
            "context": {"key": "value"},
            "checkpoint_ref": None,
            "metadata": {},
            "result": None,
            "evaluation_score": None,
            "evaluation_feedback": None,
            "error": None,
            "error_trace": None,
        }

        # 转换
        state = checkpoint_state_to_agent_state(checkpoint_state)

        assert state["task_id"] == "test-001"
        assert state["phase"] == TaskPhase.PLANNING
        assert state["messages"] == [{"role": "user", "content": "Hello"}]
        assert state["context"] == {"key": "value"}

    def test_roundtrip(self):
        """测试往返转换"""
        # 创建原始状态
        original = create_initial_state(
            task_id="roundtrip-test",
            task_description="Roundtrip test",
        )
        original["phase"] = TaskPhase.EXECUTING
        original["messages"] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        original["result"] = {"status": "completed", "output": "Done"}

        # 转换为 Checkpoint
        checkpoint_state = agent_state_to_checkpoint_state(original)

        # 转换回 AgentState
        restored = checkpoint_state_to_agent_state(checkpoint_state)

        # 验证
        assert restored["task_id"] == original["task_id"]
        assert restored["task_description"] == original["task_description"]
        assert restored["phase"] == original["phase"]
        assert restored["messages"] == original["messages"]
        assert restored["result"] == original["result"]

    def test_partial_state(self):
        """测试部分状态转换"""
        # 最小状态
        minimal_state = AgentState(
            messages=[],
            context={},
            phase=TaskPhase.IDLE,
            checkpoint_ref=None,
            metadata={},
        )

        # 转换
        checkpoint_state = agent_state_to_checkpoint_state(minimal_state)
        restored = checkpoint_state_to_agent_state(checkpoint_state)

        assert restored["phase"] == TaskPhase.IDLE
        assert restored["messages"] == []

    def test_error_state_conversion(self):
        """测试错误状态转换"""
        state = create_initial_state("test", "Test")
        state["phase"] = TaskPhase.FAILED
        state["error"] = "Something went wrong"
        state["error_trace"] = "Traceback..."

        # 转换
        checkpoint_state = agent_state_to_checkpoint_state(state)
        restored = checkpoint_state_to_agent_state(checkpoint_state)

        assert restored["phase"] == TaskPhase.FAILED
        assert restored["error"] == "Something went wrong"
        assert restored["error_trace"] == "Traceback..."

    def test_evaluation_state_conversion(self):
        """测试评估状态转换"""
        state = create_initial_state("test", "Test")
        state["evaluation_score"] = 0.85
        state["evaluation_feedback"] = "Good job!"

        # 转换
        checkpoint_state = agent_state_to_checkpoint_state(state)
        restored = checkpoint_state_to_agent_state(checkpoint_state)

        assert restored["evaluation_score"] == 0.85
        assert restored["evaluation_feedback"] == "Good job!"


class TestPhaseConversion:
    """阶段转换测试"""

    def test_string_phase_to_enum(self):
        """测试字符串阶段转换为枚举"""
        checkpoint_state = {
            "task_id": "test",
            "phase": "executing",
            "messages": [],
            "context": {},
            "checkpoint_ref": None,
            "metadata": {},
            "task_description": "",
            "result": None,
            "evaluation_score": None,
            "evaluation_feedback": None,
            "error": None,
            "error_trace": None,
        }

        state = checkpoint_state_to_agent_state(checkpoint_state)
        assert state["phase"] == TaskPhase.EXECUTING

    def test_invalid_phase(self):
        """测试无效阶段"""
        checkpoint_state = {
            "task_id": "test",
            "phase": "invalid_phase",
            "messages": [],
            "context": {},
            "checkpoint_ref": None,
            "metadata": {},
            "task_description": "",
            "result": None,
            "evaluation_score": None,
            "evaluation_feedback": None,
            "error": None,
            "error_trace": None,
        }

        state = checkpoint_state_to_agent_state(checkpoint_state)
        # 无效阶段应回退到 IDLE
        assert state["phase"] == TaskPhase.IDLE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
