"""Checkpoint 单元测试"""
import asyncio
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, '.')

from src.memory.checkpoint import CheckpointManager

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


@pytest.mark.asyncio
async def test_create_checkpoint(cm):
    """测试创建 checkpoint"""
    test_file = Path(TEST_CP) / "test_file.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# test content")

    cp_id = await cm.create_checkpoint(str(test_file), reason="test")
    assert cp_id is not None


@pytest.mark.asyncio
async def test_list_checkpoints(cm):
    """测试列出 checkpoints"""
    test_file = Path(TEST_CP) / "test_file.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# test content v1")

    await cm.create_checkpoint(str(test_file), reason="test v1")

    # Use different file to avoid unique constraint
    test_file2 = Path(TEST_CP) / "test_file2.py"
    test_file2.write_text("# test content v2")
    await cm.create_checkpoint(str(test_file2), reason="test v2")

    checkpoints = await cm.list_checkpoints()
    assert len(checkpoints) >= 1


@pytest.mark.asyncio
async def test_delete_checkpoint(cm):
    """测试删除 checkpoint"""
    test_file = Path(TEST_CP) / "test_file.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# test content")

    cp_id = await cm.create_checkpoint(str(test_file), reason="test to delete")

    result = await cm.delete_checkpoint(cp_id)
    assert result is True


def test_checkpoint_stats(cm):
    """测试 checkpoint 统计"""
    stats = cm.get_stats()
    assert "total_checkpoints" in stats or "total" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
