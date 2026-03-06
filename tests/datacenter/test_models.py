"""数据模型单元测试"""
import pytest
import sys
sys.path.insert(0, '.')

from src.datacenter.models import (
    AgentRunData, UserData, AgentData, EvaluationData,
    IsolationLevel, RunStatus, create_unified_tables
)


def test_agent_run_data_creation():
    """测试 AgentRunData 创建"""
    run = AgentRunData(
        user_id="user-001",
        agent_id="agent-coder",
        session_id="session-001",
        status=RunStatus.SUCCESS,
        prompt_tokens=100,
        completion_tokens=50
    )
    assert run.run_id is not None
    assert run.status == RunStatus.SUCCESS
    assert run.total_tokens == 150


def test_agent_run_data_to_dict():
    """测试 AgentRunData 序列化"""
    run = AgentRunData(
        user_id="user-001",
        agent_id="agent-coder",
        status=RunStatus.FAILED,
        error="test error"
    )
    d = run.to_dict()
    assert "run_id" in d
    assert "user_id" in d
    assert d["user_id"] == "user-001"
    assert d["status"] == "failed"
    assert d["error"] == "test error"


def test_user_data():
    """测试 UserData"""
    user = UserData(
        user_id="user-001",
        preferences={"theme": "dark"},
        total_runs=10
    )
    assert user.user_id == "user-001"
    assert user.preferences["theme"] == "dark"
    assert user.total_runs == 10


def test_agent_data():
    """测试 AgentData"""
    agent = AgentData(
        agent_id="agent-001",
        name="Test Agent",
        version="1.0.0",
        quality_score=0.85,
        badges=["verified", "top-rated"]
    )
    assert agent.agent_id == "agent-001"
    assert agent.quality_score == 0.85
    assert len(agent.badges) == 2


def test_evaluation_data():
    """测试 EvaluationData"""
    eval_data = EvaluationData(
        task_id="task-001",
        agent_id="agent-001",
        completeness=0.9,
        validity=0.85,
        overall_score=0.87
    )
    assert eval_data.task_id == "task-001"
    assert eval_data.completeness == 0.9


def test_isolation_level_enum():
    """测试隔离级别枚举"""
    assert IsolationLevel.SESSION.value == "session"
    assert IsolationLevel.USER.value == "user"
    assert IsolationLevel.AGENT.value == "agent"
    assert IsolationLevel.GLOBAL.value == "global"


def test_run_status_enum():
    """测试运行状态枚举"""
    assert RunStatus.PENDING.value == "pending"
    assert RunStatus.RUNNING.value == "running"
    assert RunStatus.SUCCESS.value == "success"
    assert RunStatus.FAILED.value == "failed"
    assert RunStatus.CANCELLED.value == "cancelled"
    assert RunStatus.TIMEOUT.value == "timeout"


def test_create_unified_tables():
    """测试统一表创建"""
    create_unified_tables(".young/test_unified.db")
    from pathlib import Path
    assert Path(".young/test_unified.db").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
