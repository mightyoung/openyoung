"""
Tests for new CLI modules, exceptions, and events
"""

import pytest
from src.cli.context import CLIContext
from src.core.exceptions import (
    OpenYoungError,
    AgentError,
    AgentNotFoundError,
    AgentExecutionError,
    ExecutionError,
    ToolExecutionError,
    ConfigError,
)
from src.core.events import Event, EventType, EventBus, on, emit


class TestCLIContext:
    """Test CLI Context"""

    def test_context_creation(self, tmp_path):
        """Test context creation"""
        ctx = CLIContext(config_dir=tmp_path / ".test")
        assert ctx.config_dir == tmp_path / ".test"
        assert ctx.verbose is False
        assert ctx.output_format == "text"

    def test_config_save_load(self, tmp_path):
        """Test config save and load"""
        ctx = CLIContext(config_dir=tmp_path)

        config = {"key": "value", "number": 42}
        assert ctx.save_config(config) is True

        loaded = ctx.load_config()
        assert loaded["key"] == "value"
        assert loaded["number"] == 42


class TestExceptions:
    """Test exception hierarchy"""

    def test_base_exception(self):
        """Test base exception"""
        err = OpenYoungError("Test error", code="TEST")
        assert err.message == "Test error"
        assert err.code == "TEST"
        assert "[TEST] Test error" in repr(err)

    def test_agent_not_found_error(self):
        """Test agent not found error"""
        err = AgentNotFoundError("my-agent")
        assert err.agent_name == "my-agent"
        assert err.code == "AGENT_NOT_FOUND"

    def test_agent_execution_error(self):
        """Test agent execution error"""
        err = AgentExecutionError("my-agent", "timeout")
        assert err.agent_name == "my-agent"
        assert err.reason == "timeout"
        assert "my-agent" in err.message
        assert "timeout" in err.message

    def test_exception_hierarchy(self):
        """Test exception inheritance"""
        assert issubclass(AgentError, OpenYoungError)
        assert issubclass(ExecutionError, OpenYoungError)
        assert issubclass(ConfigError, OpenYoungError)


class TestEventBus:
    """Test Event Bus"""

    def test_event_creation(self):
        """Test event creation"""
        event = Event(
            type=EventType.AGENT_STARTED,
            data={"agent": "test"},
        )
        assert event.type == EventType.AGENT_STARTED
        assert event.data["agent"] == "test"

    def test_event_bus_subscribe(self):
        """Test event subscription"""
        bus = EventBus()
        called = []

        def handler(event):
            called.append(event)

        bus.subscribe(EventType.AGENT_STARTED, handler)
        bus.publish(Event(type=EventType.AGENT_STARTED, data={}))

        assert len(called) == 1

    def test_event_bus_async(self):
        """Test async event handling"""
        bus = EventBus()
        results = []

        async def async_handler(event):
            results.append("async")

        bus.subscribe_async(EventType.AGENT_COMPLETED, async_handler)

        import asyncio
        asyncio.run(bus.publish_async(Event(type=EventType.AGENT_COMPLETED, data={})))

        assert len(results) == 1

    def test_decorator(self):
        """Test on() decorator"""
        # Create local event bus to test decorator
        from src.core.events import EventBus, EventType

        # Mock the global event_bus
        import src.core.events as events_module
        original_bus = events_module.event_bus
        test_bus = EventBus()
        events_module.event_bus = test_bus

        results = []

        @on(EventType.TASK_COMPLETED)
        def handler(event):
            results.append(event)

        test_bus.publish(Event(type=EventType.TASK_COMPLETED, data={}))
        assert len(results) == 1

        # Restore original
        events_module.event_bus = original_bus

    def test_event_history(self):
        """Test event history"""
        bus = EventBus()

        for i in range(5):
            bus.publish(Event(type=EventType.AGENT_STARTED, data={"i": i}))

        history = bus.get_history(EventType.AGENT_STARTED, limit=3)
        assert len(history) == 3


class TestExceptionIntegration:
    """Test exception integration with event bus"""

    def test_exception_contains_data(self):
        """Test exception can contain event data"""
        err = AgentNotFoundError("test-agent")
        event = Event(
            type=EventType.AGENT_FAILED,
            data={"error": err, "agent_name": "test-agent"},
        )
        assert event.data["error"].code == "AGENT_NOT_FOUND"
