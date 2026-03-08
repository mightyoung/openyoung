"""DataStore 单元测试"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, '.')

from src.datacenter.store import DataStore

TEST_DIR = ".young/test_store_unit"


@pytest.fixture
def store():
    # Cleanup before
    if Path(TEST_DIR).exists():
        shutil.rmtree(TEST_DIR)
    store = DataStore(TEST_DIR)
    yield store
    # Cleanup after
    if Path(TEST_DIR).exists():
        shutil.rmtree(TEST_DIR)


def test_save_and_get_agent(store):
    """测试保存和获取 Agent"""
    store.save_agent("agent-001", {"name": "Test", "version": "1.0"})
    agent = store.get_agent("agent-001")
    assert agent is not None
    assert agent["name"] == "Test"


def test_list_agents(store):
    """测试列出 Agents"""
    store.save_agent("a1", {"name": "A1"})
    store.save_agent("a2", {"name": "A2"})
    agents = store.list_agents()
    assert len(agents) >= 2


def test_delete_agent(store):
    """测试删除 Agent"""
    store.save_agent("del-agent", {"name": "Delete"})
    result = store.delete_agent("del-agent")
    assert result is True
    assert store.get_agent("del-agent") is None


def test_save_and_get_run(store):
    """测试保存和获取 Run"""
    store.save_run("run-001", {"status": "success"})
    run = store.get_run("run-001")
    assert run is not None
    assert run["status"] == "success"


def test_list_runs(store):
    """测试列出 Runs"""
    store.save_run("r1", {"agent_id": "a1"})
    store.save_run("r2", {"agent_id": "a2"})
    runs = store.list_runs()
    assert len(runs) >= 2


def test_save_and_get_checkpoint(store):
    """测试保存和获取 Checkpoint"""
    store.save_checkpoint("cp-001", {"session_id": "s1", "state": {}})
    cp = store.get_checkpoint("cp-001")
    assert cp is not None
    assert cp["session_id"] == "s1"


def test_list_checkpoints(store):
    """测试列出 Checkpoints"""
    store.save_checkpoint("cp-s1-1", {"session_id": "s1"})
    store.save_checkpoint("cp-s1-2", {"session_id": "s1"})
    cps = store.list_checkpoints("s1")
    assert len(cps) >= 2


def test_save_and_get_workspace(store):
    """测试保存和获取 Workspace"""
    store.save_workspace("ws-001", {"agent_id": "a1", "user_id": "u1"})
    ws = store.get_workspace("ws-001")
    assert ws is not None
    assert ws["agent_id"] == "a1"


def test_transaction(store):
    """测试事务"""
    ops = [
        {"entity_type": "run", "id": "tx-1", "data": {"n": 1}},
        {"entity_type": "run", "id": "tx-2", "data": {"n": 2}},
    ]
    result = store.save_with_transaction(ops)
    assert result is True
    assert store.get_run("tx-1") is not None
    assert store.get_run("tx-2") is not None


def test_version_control(store):
    """测试版本控制"""
    store.save_version("run", "entity-1", {"v": "1.0"}, "v1")
    store.save_version("run", "entity-1", {"v": "2.0"}, "v2")

    versions = store.list_versions("run", "entity-1")
    assert len(versions) == 2
    assert versions[0]["v"] == "2.0"


def test_get_version(store):
    """测试获取特定版本"""
    vid = store.save_version("run", "e2", {"ver": 1})
    version = store.get_version(vid)
    assert version is not None
    assert version["ver"] == 1


def test_stats(store):
    """测试统计"""
    store.save_agent("s-a1", {})
    store.save_run("s-r1", {})

    stats = store.get_stats()
    assert "agent" in stats
    assert "run" in stats
    assert stats["agent"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
