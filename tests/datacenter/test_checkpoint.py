"""Checkpoint 单元测试"""
import pytest
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '.')

from src.datacenter.datacenter import CheckpointManager

TEST_CP = ".young/test_cp_unit"


@pytest.fixture
def cm():
    # Cleanup before
    if Path(TEST_CP).exists():
        shutil.rmtree(TEST_CP)
    if Path(f"{TEST_CP}.db").exists():
        Path(f"{TEST_CP}.db").unlink()
    cm = CheckpointManager(TEST_CP, f"{TEST_CP}.db")
    yield cm
    # Cleanup after
    if Path(TEST_CP).exists():
        shutil.rmtree(TEST_CP)
    if Path(f"{TEST_CP}.db").exists():
        Path(f"{TEST_CP}.db").unlink()


def test_save_checkpoint(cm):
    """测试保存 checkpoint"""
    cp_id = cm.save_checkpoint(
        session_id="session-001",
        data={"state": "running", "progress": 50},
        agent_id="agent-001"
    )
    assert cp_id is not None
    assert "session-001" in cp_id


def test_load_checkpoint(cm):
    """测试加载 checkpoint"""
    cp_id = cm.save_checkpoint("s1", {"data": "test"}, "a1")
    cp = cm.load_checkpoint(cp_id)
    assert cp is not None
    assert cp.data["data"] == "test"


def test_get_latest_checkpoint(cm):
    """测试获取最新 checkpoint"""
    cm.save_checkpoint("s2", {"step": 1}, "a1")
    cm.save_checkpoint("s2", {"step": 2}, "a1")
    latest = cm.get_latest("s2")
    assert latest.data["step"] == 2


def test_get_session_checkpoints(cm):
    """测试获取会话的所有 checkpoints"""
    cm.save_checkpoint("s3", {"v": 1}, "a1")
    cm.save_checkpoint("s3", {"v": 2}, "a1")
    cps = cm.get_session_checkpoints("s3")
    assert len(cps) == 2


def test_delete_session_checkpoints(cm):
    """测试删除会话的 checkpoints"""
    cm.save_checkpoint("s4", {"del": True}, "a1")
    count = cm.delete_session_checkpoints("s4")
    assert count >= 1
    assert cm.get_latest("s4") is None


def test_checkpoint_with_metadata(cm):
    """测试带元数据的 checkpoint"""
    cp_id = cm.save_checkpoint(
        "s5",
        {"state": "done"},
        "a1",
        metadata={"version": "1.0", "tags": ["test"]}
    )
    cp = cm.load_checkpoint(cp_id)
    assert cp.agent_id == "a1"
    assert cp.metadata["version"] == "1.0"


def test_checkpoint_stats(cm):
    """测试 checkpoint 统计"""
    cm.save_checkpoint("s6", {"stat": True}, "agent-x")
    stats = cm.get_stats()
    assert "total" in stats
    assert stats["total"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
