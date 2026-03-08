"""
Memory Tests - Phase 5
"""

import os
import tempfile

import pytest

from src.memory import AutoMemory, CheckpointManager


class TestAutoMemory:
    """Test AutoMemory - Task 5.2"""

    @pytest.fixture
    def memory_system(self):
        return AutoMemory(max_memories=10, importance_threshold=0.5)

    @pytest.mark.asyncio
    async def test_add_working_memory(self, memory_system):
        """测试添加工作记忆"""
        memory = await memory_system.add_memory(
            "Current task: fix bug", layer="working"
        )
        assert memory is not None
        assert len(memory_system.working_memory) == 1

    @pytest.mark.asyncio
    async def test_add_session_memory(self, memory_system):
        """测试添加会话记忆"""
        memory = await memory_system.add_memory(
            "Important: remember to test", layer="session"
        )
        assert memory is not None
        assert len(memory_system.session_memory) == 1

    @pytest.mark.asyncio
    async def test_importance_threshold(self, memory_system):
        """测试重要性阈值过滤"""
        memory = await memory_system.add_memory("simple task", layer="session")
        assert memory is not None

    @pytest.mark.asyncio
    async def test_get_relevant_memories(self, memory_system):
        """测试获取相关记忆"""
        await memory_system.add_memory("Important error fix", layer="session")
        await memory_system.add_memory("Another task", layer="session")

        memories = await memory_system.get_relevant_memories("error", limit=2)
        assert len(memories) >= 1

    @pytest.mark.asyncio
    async def test_clear_working_memory(self, memory_system):
        """测试清除工作记忆"""
        await memory_system.add_memory("task 1", layer="working")
        await memory_system.add_memory("task 2", layer="working")

        assert len(memory_system.working_memory) == 2

        await memory_system.clear_working_memory()

        assert len(memory_system.working_memory) == 0

    @pytest.mark.asyncio
    async def test_promote_to_persistent(self, memory_system):
        """测试提升到持久层"""
        memory = await memory_system.add_memory("Remember this", layer="session")

        await memory_system.promote_to_persistent(memory.id)

        assert memory.id not in [m.id for m in memory_system.session_memory]
        assert memory.id in [m.id for m in memory_system.persistent_memory]

    def test_get_stats(self, memory_system):
        """测试获取统计"""
        stats = memory_system.get_stats()
        assert "working" in stats
        assert "session" in stats
        assert "persistent" in stats


class TestCheckpointManager:
    """Test CheckpointManager - Task 5.1"""

    @pytest.fixture
    def checkpoint_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield CheckpointManager(checkpoint_dir=tmpdir)

    @pytest.mark.asyncio
    async def test_create_checkpoint(self, checkpoint_manager):
        """测试创建检查点"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("test content")
            temp_path = f.name

        try:
            checkpoint_id = await checkpoint_manager.create_checkpoint(
                temp_path, "test"
            )
            assert checkpoint_id is not None
            assert ".txt_" in checkpoint_id
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_restore_checkpoint(self, checkpoint_manager):
        """测试恢复检查点"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("original")
            temp_path = f.name

        try:
            checkpoint_id = await checkpoint_manager.create_checkpoint(temp_path)

            with open(temp_path, "w") as f:
                f.write("modified")

            result = await checkpoint_manager.restore_checkpoint(checkpoint_id)

            assert result is True
            with open(temp_path) as f:
                assert f.read() == "original"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, checkpoint_manager):
        """测试列出检查点"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("content")
            temp_path = f.name

        try:
            await checkpoint_manager.create_checkpoint(temp_path)
            checkpoints = await checkpoint_manager.list_checkpoints()
            assert len(checkpoints) >= 1
        finally:
            os.unlink(temp_path)
