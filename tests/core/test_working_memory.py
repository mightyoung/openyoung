"""
Working Memory 单元测试

测试:
1. 任务上下文创建
2. 上下文更新
3. 任务切换
4. 消息和工具记录
5. 变量存取
6. 持久化
"""

import pytest
import tempfile
import asyncio
from pathlib import Path
from src.core.memory import WorkingMemory, TaskContext, get_working_memory, set_working_memory


class TestTaskContext:
    """TaskContext 单元测试"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = TaskContext(
            task_id="test-001",
            task_description="Test task"
        )

        assert ctx.task_id == "test-001"
        assert ctx.task_description == "Test task"
        assert ctx.phase == "idle"
        assert len(ctx.messages) == 0

    def test_update_context(self):
        """测试更新上下文 (不可变)"""
        ctx = TaskContext(
            task_id="test-001",
            task_description="Test task"
        )

        # 更新
        updated = ctx.update(phase="planning")

        # 验证返回新副本
        assert updated.phase == "planning"
        assert ctx.phase == "idle"  # 原上下文不变

        # 验证其他字段保留
        assert updated.task_id == ctx.task_id


class TestWorkingMemory:
    """WorkingMemory 单元测试"""

    @pytest.fixture
    def memory(self):
        """创建测试用 WorkingMemory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield WorkingMemory(backup_dir=Path(tmpdir))

    def test_create_context(self, memory):
        """测试创建任务上下文"""
        ctx = memory.create_context(
            task_id="task-001",
            task_description="Test task"
        )

        assert ctx is not None
        assert ctx.task_id == "task-001"
        assert memory.current_task_id == "task-001"

    def test_get_context(self, memory):
        """测试获取任务上下文"""
        # 创建
        memory.create_context("task-001", "Test")

        # 获取
        ctx = memory.get_context("task-001")
        assert ctx is not None
        assert ctx.task_id == "task-001"

        # 获取不存在的
        ctx = memory.get_context("nonexistent")
        assert ctx is None

    def test_update_context(self, memory):
        """测试更新任务上下文"""
        memory.create_context("task-001", "Test")

        # 更新
        updated = memory.update_context(phase="planning")

        assert updated is not None
        assert updated.phase == "planning"

    def test_switch_context(self, memory):
        """测试任务切换"""
        # 创建两个任务
        memory.create_context("task-001", "Task 1")
        memory.update_context(phase="completed")

        # 切换
        memory.switch_context("task-002")

        assert memory.current_task_id == "task-002"

        # 创建新任务的上下文
        ctx = memory.get_context()
        assert ctx.task_id == "task-002"

    def test_add_message(self, memory):
        """测试添加消息"""
        memory.create_context("task-001", "Test")

        # 添加消息
        ctx = memory.add_message("user", "Hello")

        assert len(ctx.messages) == 1
        assert ctx.messages[0]["role"] == "user"
        assert ctx.messages[0]["content"] == "Hello"

    def test_add_tool_used(self, memory):
        """测试记录工具使用"""
        memory.create_context("task-001", "Test")

        # 记录工具
        ctx = memory.add_tool_used("search")

        assert "search" in ctx.tools_used

    def test_set_get_variable(self, memory):
        """测试变量存取"""
        memory.create_context("task-001", "Test")

        # 设置变量
        memory.set_variable("result", {"status": "ok"})

        # 获取变量
        result = memory.get_variable("result")
        assert result == {"status": "ok"}

        # 获取不存在的变量
        result = memory.get_variable("nonexistent", default="default")
        assert result == "default"

    def test_list_contexts(self, memory):
        """测试列出所有任务"""
        memory.create_context("task-001", "Task 1")
        memory.create_context("task-002", "Task 2")

        contexts = memory.list_contexts()

        assert "task-001" in contexts
        assert "task-002" in contexts

    def test_delete_context(self, memory):
        """测试删除上下文"""
        memory.create_context("task-001", "Test")

        # 删除
        result = memory.delete_context("task-001")

        assert result is True
        assert "task-001" not in memory.list_contexts()

        # 删除不存在的
        result = memory.delete_context("nonexistent")
        assert result is False


class TestGlobalInstance:
    """全局实例测试"""

    def test_get_default_instance(self):
        """测试获取默认实例"""
        memory = get_working_memory()

        assert memory is not None
        assert isinstance(memory, WorkingMemory)

    def test_set_instance(self):
        """测试设置自定义实例"""
        custom = WorkingMemory()
        set_working_memory(custom)

        assert get_working_memory() is custom


@pytest.mark.asyncio
async def test_async_persistence():
    """测试异步持久化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = WorkingMemory(backup_dir=Path(tmpdir))

        # 创建上下文
        memory.create_context("task-001", "Test task")

        # 更新以触发持久化
        memory.update_context(phase="planning")

        # 等待持久化完成
        await asyncio.sleep(0.1)

        # 验证文件存在
        backup_path = Path(tmpdir) / "working_task-001.json"
        assert backup_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
