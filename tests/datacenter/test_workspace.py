"""工作空间单元测试"""
import pytest
import sys
import shutil
from pathlib import Path

sys.path.insert(0, '.')

from src.datacenter.workspace import (
    WorkspaceManager, WorkspaceQuota, WorkspaceStatus
)

TEST_ROOT = ".young/test_ws_unit"


@pytest.fixture
def wm():
    # Cleanup before
    if Path(TEST_ROOT).exists():
        shutil.rmtree(TEST_ROOT)
    wm = WorkspaceManager(TEST_ROOT)
    yield wm
    # Cleanup after
    if Path(TEST_ROOT).exists():
        shutil.rmtree(TEST_ROOT)


def test_create_workspace(wm):
    """测试创建工作空间"""
    ws = wm.create_workspace("agent-001", user_id="user-001")
    assert ws.agent_id == "agent-001"
    assert ws.user_id == "user-001"
    assert ws.root_path.exists()


def test_workspace_directory_structure(wm):
    """测试工作空间目录结构"""
    ws = wm.create_workspace("agent-002")
    assert (ws.root_path / "memory").exists()
    assert (ws.root_path / "checkpoints").exists()
    assert (ws.root_path / "traces").exists()
    assert (ws.root_path / "output").exists()
    assert (ws.root_path / "config").exists()


def test_workspace_quota(wm):
    """测试工作空间配额"""
    quota = WorkspaceQuota(max_storage_mb=100, max_checkpoints=20)
    ws = wm.create_workspace("agent-003", quota=quota)
    assert ws.quota.max_storage_mb == 100
    assert ws.quota.max_checkpoints == 20


def test_workspace_get_by_id(wm):
    """测试获取工作空间"""
    wm.create_workspace("agent-004")
    ws = wm.get_workspace("agent-004")
    assert ws is not None
    assert ws.agent_id == "agent-004"


def test_workspace_archive(wm):
    """测试工作空间归档"""
    wm.create_workspace("agent-004")
    wm.archive_workspace("agent-004")
    ws = wm.get_workspace("agent-004")
    assert ws.status == WorkspaceStatus.ARCHIVED


def test_workspace_restore(wm):
    """测试工作空间恢复"""
    wm.create_workspace("agent-005")
    wm.archive_workspace("agent-005")
    wm.restore_workspace("agent-005")
    ws = wm.get_workspace("agent-005")
    assert ws.status == WorkspaceStatus.ACTIVE


def test_workspace_suspend(wm):
    """测试工作空间暂停"""
    wm.create_workspace("agent-006")
    wm.suspend_workspace("agent-006")
    ws = wm.get_workspace("agent-006")
    assert ws.status == WorkspaceStatus.SUSPENDED


def test_workspace_copy(wm):
    """测试工作空间复制"""
    ws1 = wm.create_workspace("agent-007")
    # 添加一些文件
    (ws1.root_path / "test.txt").write_text("test")
    ws2 = wm.copy_workspace("agent-007", "agent-008")
    assert ws2.agent_id == "agent-008"
    assert ws2.root_path.exists()


def test_workspace_delete(wm):
    """测试删除工作空间"""
    wm.create_workspace("agent-009")
    result = wm.delete_workspace("agent-009")
    assert result == True
    assert wm.get_workspace("agent-009") is None


def test_workspace_list(wm):
    """测试列出工作空间"""
    wm.create_workspace("a1")
    wm.create_workspace("a2")
    workspaces = wm.list_workspaces()
    assert len(workspaces) >= 2


def test_workspace_stats(wm):
    """测试工作空间统计"""
    wm.create_workspace("a3")
    wm.create_workspace("a4")
    stats = wm.get_all_stats()
    assert stats["total_agents"] >= 2
    assert "active" in stats


def test_workspace_quota_update(wm):
    """测试更新配额"""
    wm.create_workspace("a5")
    new_quota = WorkspaceQuota(max_storage_mb=200, max_checkpoints=100)
    wm.update_quota("a5", new_quota)
    ws = wm.get_workspace("a5")
    assert ws.quota.max_storage_mb == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
