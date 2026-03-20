"""
Event Bus Client - EventBus 事件总线封装

提取自 young_agent.py 对 EventBus 的使用。
提供简化的 EventBus 客户端接口。
"""

from src.core.events import Event, EventPriority, EventType, SystemEvents, get_event_bus


class EventBusClient:
    """EventBus 客户端封装

    提供简化的 EventBus 操作接口。
    """

    def __init__(self):
        self._bus = get_event_bus()

    def publish(self, event: Event) -> None:
        """发布事件"""
        if self._bus:
            self._bus.publish(event)

    def publish_task_started(self, input_text: str, session_id: str, agent_name: str) -> None:
        """发布任务开始事件"""
        event = Event(
            type=EventType.TASK_STARTED,
            data={
                "input": input_text[:200] if input_text else "",
                "session_id": session_id,
                "agent_name": agent_name,
            },
            priority=EventPriority.NORMAL,
            source="young_agent",
        )
        self.publish(event)

    def publish_task_completed(
        self, task: str, success: bool, duration_ms: int, session_id: str, agent_name: str
    ) -> None:
        """发布任务完成事件"""
        event = Event(
            type=EventType.TASK_COMPLETED,
            data={
                "task": task,
                "success": success,
                "duration_ms": duration_ms,
                "session_id": session_id,
                "agent_name": agent_name,
            },
            priority=EventPriority.HIGH if success else EventPriority.CRITICAL,
            source="young_agent",
        )
        self.publish(event)

    def publish_error(self, task: str, error: str, session_id: str) -> None:
        """发布错误事件"""
        event = Event(
            type=SystemEvents.ERROR,
            data={
                "task": task,
                "error": error[:500] if error else "Unknown error",
                "session_id": session_id,
            },
            priority=EventPriority.CRITICAL,
            source="young_agent",
        )
        self.publish(event)
