"""隔离控制单元测试"""
import pytest
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '.')

from src.datacenter.isolation import IsolationManager
from src.datacenter.models import IsolationLevel

TEST_ISOLATION = ".young/test_iso_unit"


@pytest.fixture
def im():
    # Cleanup before
    if Path(TEST_ISOLATION).exists():
        shutil.rmtree(TEST_ISOLATION)
    im = IsolationManager(TEST_ISOLATION)
    yield im
    # Cleanup after
    if Path(TEST_ISOLATION).exists():
        shutil.rmtree(TEST_ISOLATION)


def test_session_isolation(im):
    """测试 Session 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.SESSION,
        session_id="session-001"
    )
    assert "sessions/session-001" in str(path)
    assert path.exists()


def test_user_isolation(im):
    """测试 User 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.USER,
        user_id="user-001"
    )
    assert "users/user-001" in str(path)
    assert path.exists()


def test_agent_isolation(im):
    """测试 Agent 级别隔离"""
    path = im.create_isolation_dirs(
        level=IsolationLevel.AGENT,
        agent_id="agent-coder"
    )
    assert "agents/agent-coder" in str(path)
    assert path.exists()


def test_global_isolation(im):
    """测试 Global 级别隔离"""
    path = im.create_isolation_dirs(level=IsolationLevel.GLOBAL)
    assert "global" in str(path)


def test_save_and_load_data(im):
    """测试隔离数据保存和加载"""
    im.save_data(
        key="context",
        data={"messages": ["hello", "world"]},
        level=IsolationLevel.SESSION,
        session_id="session-002"
    )
    data = im.load_data(
        key="context",
        level=IsolationLevel.SESSION,
        session_id="session-002"
    )
    assert data == {"messages": ["hello", "world"]}


def test_load_default_data(im):
    """测试加载默认数据"""
    data = im.load_data(
        key="nonexistent",
        level=IsolationLevel.SESSION,
        session_id="s999",
        default={"default": True}
    )
    assert data == {"default": True}


def test_query_isolation_data(im):
    """测试隔离数据查询"""
    im.save_data("key1", "value1", IsolationLevel.SESSION, session_id="s1")
    im.save_data("key2", "value2", IsolationLevel.USER, user_id="u1")
    results = im.query_data(level=IsolationLevel.SESSION)
    assert len(results) >= 1


def test_delete_isolation_data(im):
    """测试删除隔离数据"""
    im.save_data("to_delete", "data", IsolationLevel.SESSION, session_id="s_del")
    count = im.delete_data(IsolationLevel.SESSION, session_id="s_del")
    assert count >= 1


def test_isolation_path(im):
    """测试获取隔离路径"""
    path = im.get_isolation_path(
        IsolationLevel.AGENT,
        agent_id="test-agent"
    )
    assert "agents/test-agent" in str(path)


def test_stats(im):
    """测试隔离统计"""
    im.save_data("stat1", "val1", IsolationLevel.SESSION, session_id="s_stat")
    stats = im.get_stats()
    assert "total_records" in stats
    assert stats["total_records"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
