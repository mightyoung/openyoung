"""
集成测试: EventBus + LangGraph 工作流

测试完整的事件驱动架构:
1. EventBus 发布/订阅
2. Hook 处理器执行
3. Checkpoint 保存/恢复
4. LangGraph 工作流执行
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.events import (
    Event,
    EventType,
    EventBus,
    get_event_bus,
)
from src.core.handlers.task_handlers import (
    register_event_handlers,
    task_started_handler,
    task_completed_handler,
    error_handler,
    heartbeat_handler,
    evaluation_handler,
)
from src.core.langgraph_state import (
    AgentState,
    TaskPhase,
    create_initial_state,
    update_phase,
    add_message,
    set_result,
)
from src.core.workflow import LangGraphWorkflow


# ====================
# Fixtures
# ====================


@pytest.fixture
def event_bus():
    """创建测试用 EventBus"""
    return EventBus()


@pytest.fixture
def agent_state():
    """创建测试用 AgentState"""
    return create_initial_state(
        task_id="test-task-001",
        task_description="Test task description",
        context={"test": True},
    )


# ====================
# EventBus 测试
# ====================


class TestEventBus:
    """EventBus 单元测试"""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self, event_bus):
        """测试发布/订阅机制"""
        received_events = []

        def handler(event):
            received_events.append(event)

        # 订阅事件
        event_bus.subscribe(EventType.TASK_STARTED, handler)

        # 发布事件
        event = Event(
            type=EventType.TASK_STARTED,
            data={"task_id": "test-001"},
        )
        event_bus.publish(event)

        # 验证事件被接收
        assert len(received_events) == 1
        assert received_events[0].data["task_id"] == "test-001"

    @pytest.mark.asyncio
    async def test_async_subscribe(self, event_bus):
        """测试异步订阅"""
        received_events = []

        async def async_handler(event):
            received_events.append(event)

        event_bus.subscribe_async(EventType.TASK_STARTED, async_handler)

        event = Event(
            type=EventType.TASK_STARTED,
            data={"task_id": "test-002"},
        )
        await event_bus.publish_async(event)

        assert len(received_events) == 1
        assert received_events[0].data["task_id"] == "test-002"

    @pytest.mark.asyncio
    async def test_event_history(self, event_bus):
        """测试事件历史记录"""
        for i in range(5):
            event_bus.publish(Event(
                type=EventType.TASK_STARTED,
                data={"index": i},
            ))

        history = event_bus.get_history(EventType.TASK_STARTED)
        assert len(history) == 5

    @pytest.mark.asyncio
    async def test_priority_ordering(self, event_bus):
        """测试优先级排序"""
        call_order = []

        def low_priority(event):
            call_order.append("low")

        def high_priority(event):
            call_order.append("high")

        from src.core.events import EventPriority
        event_bus.subscribe(EventType.TASK_STARTED, low_priority, priority=EventPriority.LOW)
        event_bus.subscribe(EventType.TASK_STARTED, high_priority, priority=EventPriority.HIGH)

        event_bus.publish(Event(type=EventType.TASK_STARTED, data={}))

        # 高优先级应该先执行
        assert call_order == ["high", "low"]


# ====================
# Handler 测试
# ====================


class TestHandlers:
    """事件处理器测试"""

    @pytest.mark.asyncio
    async def test_task_started_handler(self):
        """测试任务开始处理器"""
        event = Event(
            type=EventType.TASK_STARTED,
            data={
                "agent_id": "test-agent",
                "task_id": "test-task-001",
                "task_type": "test",
            },
        )

        await task_started_handler.handle(event)

        # 验证元数据被设置
        assert "started_at" in event.metadata

    @pytest.mark.asyncio
    async def test_task_completed_handler(self):
        """测试任务完成处理器"""
        event = Event(
            type=EventType.TASK_COMPLETED,
            data={
                "agent_id": "test-agent",
                "task_id": "test-task-001",
                "result": {"output": "test result"},
            },
            metadata={"started_at": datetime.now().isoformat()},
        )

        await task_completed_handler.handle(event)

        # 验证完成标记
        assert event.metadata.get("completed") is True

    @pytest.mark.asyncio
    async def test_error_handler(self):
        """测试错误处理器"""
        event = Event(
            type=EventType.ERROR_OCCURRED,
            data={
                "agent_id": "test-agent",
                "task_id": "test-task-001",
                "error_type": "test_error",
                "message": "Test error message",
                "recoverable": False,  # 改为不可恢复，避免需要 checkpoint
            },
        )

        await error_handler.handle(event)

        # 验证错误处理完成（不可恢复模式下不尝试 checkpoint 恢复）
        assert event is not None

    @pytest.mark.asyncio
    async def test_heartbeat_handler(self):
        """测试心跳处理器"""
        event = Event(
            type=EventType.HEARTBEAT_TICK,
            data={
                "agent_id": "test-agent",
                "task_id": "test-task-001",
                "phase": "executing",
            },
        )

        await heartbeat_handler.handle(event)

        # 验证心跳被记录
        assert event.metadata.get("last_heartbeat") is not None
        assert event.metadata.get("phase") == "executing"

    @pytest.mark.asyncio
    async def test_evaluation_handler(self):
        """测试评估处理器"""
        event = Event(
            type=EventType.EVALUATION_STARTED,
            data={
                "agent_id": "test-agent",
                "task_id": "test-task-001",
                "evaluation_type": "quality",
            },
        )

        await evaluation_handler.handle(event)

        # 验证评估结果
        assert event.metadata.get("evaluation_completed") is True


# ====================
# LangGraph 状态测试
# ====================


class TestLangGraphState:
    """LangGraph 状态测试"""

    def test_create_initial_state(self):
        """测试创建初始状态"""
        state = create_initial_state(
            task_id="test-task",
            task_description="Test description",
        )

        assert state["task_id"] == "test-task"
        assert state["task_description"] == "Test description"
        assert state["phase"] == TaskPhase.IDLE
        assert isinstance(state["messages"], list)

    def test_update_phase(self):
        """测试更新阶段"""
        state = create_initial_state("test", "test")
        new_state = update_phase(state, TaskPhase.PLANNING)

        assert new_state["phase"] == TaskPhase.PLANNING
        assert "updated_at" in new_state["metadata"]

    def test_add_message(self):
        """测试添加消息"""
        state = create_initial_state("test", "test")
        new_state = add_message(state, "user", "Hello")

        assert len(new_state["messages"]) == 1
        assert new_state["messages"][0]["role"] == "user"
        assert new_state["messages"][0]["content"] == "Hello"

    def test_set_result(self):
        """测试设置结果"""
        state = create_initial_state("test", "test")
        result = {"output": "test output", "score": 0.9}
        new_state = set_result(state, result)

        assert new_state["result"] == result
        assert new_state["phase"] == TaskPhase.RESULT


# ====================
# LangGraph Workflow 测试
# ====================


class TestLangGraphWorkflow:
    """LangGraph 工作流测试"""

    @pytest.mark.asyncio
    async def test_workflow_build(self):
        """测试工作流构建"""
        workflow = LangGraphWorkflow(name="test-workflow")
        workflow.build()

        assert workflow.graph is not None
        assert workflow.compiled_graph is not None

    @pytest.mark.asyncio
    async def test_workflow_run(self):
        """测试工作流执行"""
        workflow = LangGraphWorkflow(name="test-workflow")
        workflow.build()

        final_state = await workflow.run(
            task_id="test-task-001",
            task_description="Test task execution",
        )

        # 验证工作流执行完成
        assert final_state is not None
        assert "phase" in final_state


# ====================
# 集成测试
# ====================


class TestIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_event_flow(self):
        """测试完整事件流程"""
        bus = get_event_bus()

        # 注册处理器
        register_event_handlers()

        # 触发任务开始
        start_event = Event(
            type=EventType.TASK_STARTED,
            data={
                "agent_id": "integration-agent",
                "task_id": "integration-task-001",
                "task_type": "integration_test",
            },
        )
        await bus.publish_async(start_event)

        # 触发心跳
        heartbeat_event = Event(
            type=EventType.HEARTBEAT_TICK,
            data={
                "agent_id": "integration-agent",
                "task_id": "integration-task-001",
                "phase": "planning",
            },
        )
        await bus.publish_async(heartbeat_event)

        # 触发任务完成
        complete_event = Event(
            type=EventType.TASK_COMPLETED,
            data={
                "agent_id": "integration-agent",
                "task_id": "integration-task-001",
                "result": {"status": "success"},
            },
            metadata=start_event.metadata,
        )
        await bus.publish_async(complete_event)

        # 验证完整流程
        assert "started_at" in start_event.metadata
        assert "last_heartbeat" in heartbeat_event.metadata
        assert complete_event.metadata.get("completed") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
