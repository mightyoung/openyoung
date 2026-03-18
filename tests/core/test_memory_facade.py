"""
Memory Facade 单元测试

测试统一入口 API:
1. 自动路由
2. 检索接口
3. 存储接口
4. Checkpoint 接口
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.memory.facade import (
    MemoryFacade,
    MemoryLayer,
    MemoryQuery,
    MemoryStore,
)


class TestMemoryLayer:
    """MemoryLayer 枚举测试"""

    def test_layer_values(self):
        """测试层值"""
        assert MemoryLayer.WORKING.value == "working"
        assert MemoryLayer.SEMANTIC.value == "semantic"
        assert MemoryLayer.CHECKPOINT.value == "checkpoint"


class TestMemoryFacadeAutoRoute:
    """自动路由测试"""

    @pytest.fixture
    def facade(self):
        """创建 Facade 实例"""
        return MemoryFacade()

    def test_auto_route_working_keywords(self, facade):
        """测试工作关键词路由到 Working Memory"""
        queries = [
            "current task context",
            "task status",
            "当前任务状态",
            "variable value",
        ]
        for query in queries:
            layer = facade._auto_route(query)
            assert layer == MemoryLayer.WORKING, f"Query '{query}' should route to WORKING"

    def test_auto_route_semantic_default(self, facade):
        """测试默认路由到 Semantic Memory"""
        queries = [
            "What is Python?",
            "How to implement this?",
            "知识检索",
            "best practices",
        ]
        for query in queries:
            layer = facade._auto_route(query)
            assert layer == MemoryLayer.SEMANTIC, f"Query '{query}' should route to SEMANTIC"


class TestMemoryFacadeRetrieve:
    """检索接口测试"""

    @pytest.mark.asyncio
    async def test_retrieve_working_layer(self):
        """测试从 Working Memory 检索"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        mock_context = MagicMock()
        mock_context.task_id = "test-001"
        mock_context.task_description = "Test task"
        mock_context.messages = []
        mock_context.variables = {}
        mock_working.get_current_context.return_value = mock_context
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        mock_result = MagicMock()
        mock_result.entry.content = "Test content"
        mock_result.relevance_score = 0.9
        mock_semantic.retrieve.return_value = [mock_result]
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        results = await facade.retrieve(
            query="current task",
            layer=MemoryLayer.WORKING,
        )

        assert len(results) > 0
        assert results[0]["layer"] == "working"

    @pytest.mark.asyncio
    async def test_retrieve_semantic_layer(self):
        """测试从 Semantic Memory 检索"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        mock_result = MagicMock()
        mock_result.entry.content = "Test content"
        mock_result.relevance_score = 0.9
        mock_semantic.retrieve.return_value = [mock_result]
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        results = await facade.retrieve(
            query="What is Python?",
            layer=MemoryLayer.SEMANTIC,
        )

        # 验证调用了 semantic_memory.retrieve
        mock_semantic.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_auto_route(self):
        """测试自动路由"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        mock_context = MagicMock()
        mock_context.task_id = "test-001"
        mock_context.task_description = "Test task"
        mock_context.messages = []
        mock_context.variables = {}
        mock_working.get_current_context.return_value = mock_context
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        # 工作关键词应该路由到 Working Memory
        results = await facade.retrieve(
            query="current task context",
            layer=None,  # 自动路由
        )

        assert len(results) > 0
        assert results[0]["layer"] == "working"


class TestMemoryFacadeStore:
    """存储接口测试"""

    @pytest.mark.asyncio
    async def test_store_semantic(self):
        """测试存储到 Semantic Memory"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        mock_semantic.store.return_value = "entry-001"
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        entry_id = await facade.store(
            content="Python is great",
            layer=MemoryLayer.SEMANTIC,
            category="programming",
            tags=["python"],
        )

        assert entry_id == "entry-001"
        mock_semantic.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_working(self):
        """测试存储到 Working Memory"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        entry_id = await facade.store(
            content="test value",
            layer=MemoryLayer.WORKING,
            metadata={"task_id": "test-001", "key": "test_key", "value": "test value"},
        )

        mock_working.set_variable.assert_called_once_with(
            "test-001", "test_key", "test value"
        )

    @pytest.mark.asyncio
    async def test_store_default_layer(self):
        """测试默认存储层"""
        facade = MemoryFacade()

        # Mock Working Memory
        mock_working = MagicMock()
        facade.working_memory = mock_working

        # Mock Semantic Memory
        mock_semantic = AsyncMock()
        mock_semantic.store.return_value = "entry-001"
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        entry_id = await facade.store(
            content="Some knowledge",
        )

        # 默认存储到 Semantic Memory
        assert entry_id == "entry-001"


class TestMemoryFacadeCheckpoint:
    """Checkpoint 接口测试"""

    @pytest.mark.asyncio
    async def test_save_checkpoint_delegates(self):
        """测试保存检查点委托"""
        facade = MemoryFacade()
        facade._initialized = True

        with patch("src.core.memory.facade.save_agent_state", new_callable=AsyncMock) as mock_save:
            mock_save.return_value = "checkpoint-001"

            checkpoint_id = await facade.save_checkpoint(
                agent_id="agent-001",
                state={"key": "value"},
            )

            assert checkpoint_id == "checkpoint-001"
            mock_save.assert_called_once()


class TestMemoryFacadeInitialize:
    """初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_creates_instances(self):
        """测试初始化创建实例"""
        facade = MemoryFacade()

        with patch("src.core.memory.facade.get_working_memory") as mock_get_working:
            with patch("src.core.memory.facade.get_semantic_memory", new_callable=AsyncMock) as mock_get_semantic:
                mock_get_working.return_value = MagicMock()
                mock_get_semantic.return_value = MagicMock()

                await facade.initialize()

                assert facade._initialized is True
                assert facade.working_memory is not None
                assert facade.semantic_memory is not None


class TestGlobalInstance:
    """全局实例测试"""

    def test_get_global_facade(self):
        """测试获取全局 Facade"""
        from src.core.memory.facade import get_memory_facade
        assert callable(get_memory_facade)

    def test_set_global_facade(self):
        """测试设置全局 Facade"""
        from src.core.memory.facade import set_memory_facade

        custom_facade = MemoryFacade()
        custom_facade._initialized = True

        set_memory_facade(custom_facade)

        # 验证已设置
        from src.core.memory import facade as facade_module
        assert facade_module._memory_facade_instance == custom_facade


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
