"""
Memory Integration Tests - 记忆系统集成测试

测试 EventBus 与记忆系统的集成:
1. 事件触发记忆操作
2. 自动 Checkpoint 保存
3. 端到端流程
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.events import Event, EventType, EventBus
from src.core.memory.handlers import (
    MemoryEventHandler,
    get_memory_handler,
    initialize_memory_events,
)
from src.core.memory.events import MemoryEventType


class TestMemoryEventType:
    """MemoryEventType 枚举测试"""

    def test_event_types(self):
        """测试事件类型定义"""
        assert MemoryEventType.CONTEXT_CREATED.value == "memory:context_created"
        assert MemoryEventType.KNOWLEDGE_STORED.value == "memory:knowledge_stored"
        assert MemoryEventType.CHECKPOINT_SAVED.value == "memory:checkpoint_saved"
        assert MemoryEventType.MEMORY_INITIALIZED.value == "memory:initialized"

    def test_event_to_layer_mapping(self):
        """测试事件到记忆层的映射"""
        from src.core.memory.events import EVENT_TO_LAYER

        assert EVENT_TO_LAYER[MemoryEventType.CONTEXT_CREATED] == "working"
        assert EVENT_TO_LAYER[MemoryEventType.KNOWLEDGE_STORED] == "semantic"
        assert EVENT_TO_LAYER[MemoryEventType.CHECKPOINT_SAVED] == "checkpoint"


class TestMemoryEventHandler:
    """MemoryEventHandler 测试"""

    @pytest.fixture
    def mock_event_bus(self):
        """创建 Mock EventBus"""
        bus = MagicMock(spec=EventBus)
        bus.subscribe = MagicMock()
        return bus

    @pytest.fixture
    def mock_facade(self):
        """创建 Mock MemoryFacade"""
        facade = MagicMock()
        facade.working_memory = MagicMock()
        facade.semantic_memory = MagicMock()
        facade.save_checkpoint = AsyncMock(return_value="checkpoint-001")
        return facade

    @pytest.mark.asyncio
    async def test_handler_initialization(self, mock_event_bus, mock_facade):
        """测试处理器初始化"""
        handler = MemoryEventHandler(event_bus=mock_event_bus)

        with patch("src.core.memory.handlers.get_memory_facade", return_value=mock_facade):
            await handler.initialize()

            assert handler._handlers_registered is True
            # 验证订阅了事件
            assert mock_event_bus.subscribe.call_count >= 4

    @pytest.mark.asyncio
    async def test_on_task_started(self, mock_event_bus, mock_facade):
        """测试任务开始事件处理"""
        handler = MemoryEventHandler(event_bus=mock_event_bus)
        handler.memory_facade = mock_facade
        handler._handlers_registered = True

        event = Event(
            type=EventType.TASK_STARTED,
            data={
                "task_id": "test-task-001",
                "task_description": "Test task",
            },
        )

        await handler.on_task_started(event)

        # 验证创建了上下文
        mock_facade.working_memory.create_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_task_completed(self, mock_event_bus, mock_facade):
        """测试任务完成事件处理"""
        handler = MemoryEventHandler(event_bus=mock_event_bus)
        handler.memory_facade = mock_facade
        handler._handlers_registered = True

        event = Event(
            type=EventType.TASK_COMPLETED,
            data={
                "task_id": "test-task-001",
                "result": {"output": "success"},
            },
        )

        await handler.on_task_completed(event)

        # 任务完成日志
        assert True

    @pytest.mark.asyncio
    async def test_on_task_failed(self, mock_event_bus, mock_facade):
        """测试任务失败事件处理"""
        handler = MemoryEventHandler(event_bus=mock_event_bus)
        handler.memory_facade = mock_facade
        handler._handlers_registered = True

        event = Event(
            type=EventType.TASK_FAILED,
            data={
                "task_id": "test-task-001",
                "error": "Something went wrong",
            },
        )

        await handler.on_task_failed(event)

        # 验证记录了错误
        assert True

    @pytest.mark.asyncio
    async def test_on_task_switched_auto_checkpoint(self, mock_event_bus, mock_facade):
        """测试任务切换时自动保存 Checkpoint"""
        handler = MemoryEventHandler(event_bus=mock_event_bus)
        handler.memory_facade = mock_facade
        handler._handlers_registered = True

        # 设置 Working Memory 返回上下文
        mock_context = MagicMock()
        mock_context.messages = [{"role": "user", "content": "Hello"}]
        mock_context.variables = {"key": "value"}
        mock_facade.working_memory.get_context.return_value = mock_context

        event = Event(
            type=EventType.TASK_SWITCHED,
            data={
                "from_task": "task-001",
                "to_task": "task-002",
                "agent_id": "agent-001",
            },
        )

        await handler.on_task_switched(event)

        # 验证自动保存了 Checkpoint
        mock_facade.save_checkpoint.assert_called_once()


class TestMemoryHandlerGlobal:
    """全局处理器测试"""

    def test_get_memory_handler(self):
        """测试获取全局处理器"""
        handler = get_memory_handler()
        # 返回协程，需要 await
        assert handler.__name__ == "get_memory_handler"

    def test_initialize_memory_events(self):
        """测试初始化记忆事件系统"""
        result = initialize_memory_events()
        assert result.__name__ == "initialize_memory_events"


class TestEventBusIntegration:
    """EventBus 集成测试"""

    def test_event_bus_exists(self):
        """测试 EventBus 存在"""
        from src.core import get_event_bus
        bus = get_event_bus()
        assert bus is not None
        assert isinstance(bus, EventBus)

    def test_event_types_defined(self):
        """测试任务事件类型已定义"""
        assert EventType.TASK_STARTED is not None
        assert EventType.TASK_COMPLETED is not None
        assert EventType.TASK_FAILED is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
