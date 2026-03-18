"""
Event Bus - 事件驱动架构

参考: Django signals, Node.js EventEmitter, Redis Pub/Sub
参考: Claude Code Hooks 系统

功能:
- 发布-订阅模式
- 同步/异步处理
- 事件优先级队列
- Hook 注册表系统
- 知识沉淀相关事件
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class EventType(Enum):
    """事件类型"""

    # Agent 生命周期
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_PAUSED = "agent_paused"
    AGENT_RESUMED = "agent_resumed"

    # 任务生命周期
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_SWITCHED = "task_switched"

    # 评估
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_COMPLETED = "evaluation_completed"

    # 执行
    TOOL_EXECUTED = "tool_executed"
    TOOL_FAILED = "tool_failed"

    # 错误
    ERROR_OCCURRED = "error_occurred"

    # 心跳 (Heartbeat)
    HEARTBEAT_TICK = "heartbeat_tick"
    HEARTBEAT_PHASE = "heartbeat_phase"

    # 知识沉淀 (Knowledge & Learning)
    KNOWLEDGE_STORED = "knowledge_stored"
    EXPERIENCE_COLLECTED = "experience_collected"
    PATTERN_DETECTED = "pattern_detected"
    LEARNING_LOGGED = "learning_logged"
    ERROR_LOGGED = "error_logged"

    # Streaming 进度
    TASK_PROGRESS = "task_progress"


# 事件处理器类型
EventHandler = Callable[["Event"], Awaitable[None] | None]


# ====================
# Hook 注册表系统 (参考 Claude Code Hooks)
# ====================


class HandlerType(Enum):
    """处理器类型"""

    COMMAND = "command"  # Shell 命令
    PROMPT = "prompt"  # LLM 提示处理
    AGENT = "agent"  # Agent 处理


@dataclass
class HookConfig:
    """Hook 配置 - 类似 Claude Code settings.json"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: EventType = EventType.TASK_STARTED
    name: str = ""
    handler: str = ""  # handler 名称或命令
    handler_type: HandlerType = HandlerType.AGENT
    blocking: bool = False  # 是否阻塞执行
    enabled: bool = True
    priority: EventPriority = EventPriority.NORMAL
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HandlerResult:
    """处理器执行结果"""

    hook_id: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: float = 0


class EventRegistry:
    """事件注册表 - 管理所有事件处理器 (Hook)

    类似 Claude Code 的 hooks 系统:
    - 支持 command, prompt, agent 三种 handler 类型
    - 支持阻塞/非阻塞执行
    - 完整的执行结果记录
    """

    def __init__(self):
        self._hooks: dict[EventType, list[HookConfig]] = {}
        self._handlers: dict[str, Callable] = {}  # name -> handler function

    def register_hook(self, config: HookConfig) -> None:
        """注册 Hook"""
        if config.event not in self._hooks:
            self._hooks[config.event] = []

        # 避免重复注册
        existing = [h for h in self._hooks[config.event] if h.id == config.id]
        for e in existing:
            self._hooks[config.event].remove(e)

        self._hooks[config.event].append(config)
        # 按优先级排序
        self._hooks[config.event].sort(key=lambda x: x.priority.value, reverse=True)
        logger.info(f"Registered hook: {config.name} for {config.event.value}")

    def register_handler(self, name: str, handler: Callable) -> None:
        """注册命名处理器"""
        self._handlers[name] = handler
        logger.debug(f"Registered handler: {name}")

    def get_hooks(self, event_type: EventType) -> list[HookConfig]:
        """获取事件的 Hook 列表"""
        return self._hooks.get(event_type, [])

    async def dispatch(self, event: Event) -> list[HandlerResult]:
        """分发事件到所有 Hook 处理器"""
        results = []
        hooks = self.get_hooks(event.type)

        for hook in hooks:
            if not hook.enabled:
                continue

            result = await self._execute_hook(hook, event)
            results.append(result)

            # 如果是阻塞模式且失败，停止执行
            if hook.blocking and not result.success:
                logger.warning(f"Blocking hook {hook.name} failed, stopping execution")
                break

        return results

    async def _execute_hook(self, hook: HookConfig, event: Event) -> HandlerResult:
        """执行单个 Hook"""
        import time

        start = time.time()
        try:
            handler = self._handlers.get(hook.handler)
            if not handler:
                return HandlerResult(
                    hook_id=hook.id,
                    success=False,
                    error=f"Handler '{hook.handler}' not found",
                )

            # 根据类型执行
            if hook.handler_type == HandlerType.AGENT:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(event)
                else:
                    result = handler(event)
            else:
                # COMMAND/PROMPT 暂时不处理
                result = None

            duration_ms = (time.time() - start) * 1000
            return HandlerResult(hook_id=hook.id, success=True, result=result, duration_ms=duration_ms)

        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error(f"Hook execution error in {hook.name}: {e}")
            return HandlerResult(hook_id=hook.id, success=False, error=str(e), duration_ms=duration_ms)

    def list_hooks(self) -> dict[EventType, list[HookConfig]]:
        """列出所有 Hook"""
        return self._hooks.copy()

    def enable_hook(self, hook_id: str) -> bool:
        """启用 Hook"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.id == hook_id:
                    hook.enabled = True
                    return True
        return False

    def disable_hook(self, hook_id: str) -> bool:
        """禁用 Hook"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.id == hook_id:
                    hook.enabled = False
                    return True
        return False


# 全局 Hook 注册表
hook_registry = EventRegistry()


def get_hook_registry() -> EventRegistry:
    """获取全局 Hook 注册表"""
    return hook_registry


@dataclass
class Event:
    """事件"""

    type: EventType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    source: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.type, str):
            self.type = EventType(self.type)
        if isinstance(self.priority, int):
            self.priority = EventPriority(self.priority)


@dataclass
class TaskProgress(Event):
    """Streaming progress event.

    用于在任务执行过程中发布进度更新，
    支持 UI/WebSocket 实时显示执行进度。
    """

    task_id: str = ""
    phase: str = ""
    progress: float = 0.0
    iteration: int = 0
    partial_output: str | None = None

    def __post_init__(self):
        super().__post_init__()
        self.type = EventType.TASK_PROGRESS


class EventBus:
    """事件总线

    提供发布-订阅模式，解耦模块间通信
    支持:
    - 同步/异步处理
    - 事件优先级
    - 队列处理
    - Hook 注册表 (Claude Code 风格)
    """

    def __init__(self, use_queue: bool = False):
        # 同步订阅者
        self._subscribers: dict[EventType, list[tuple[EventPriority, Callable]]] = {}
        # 异步订阅者
        self._async_subscribers: dict[EventType, list[tuple[EventPriority, EventHandler]]] = {}
        # 事件历史
        self._event_history: list[Event] = []
        self._max_history = 1000
        # 队列模式
        self._use_queue = use_queue
        self._event_queue: asyncio.Queue | None = None
        self._running = False
        self._processor_task: asyncio.Task | None = None
        # Hook 注册表
        self._hook_registry = hook_registry

    def subscribe(
        self,
        event_type: EventType,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """订阅事件 (同步处理)

        Args:
            event_type: 事件类型
            handler: 处理函数
            priority: 优先级，默认 NORMAL
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append((priority, handler))
        # 按优先级排序
        self._subscribers[event_type].sort(key=lambda x: x[0].value, reverse=True)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.value} (priority: {priority.name})")

    def subscribe_async(
        self,
        event_type: EventType,
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
    ):
        """订阅事件 (异步处理)

        Args:
            event_type: 事件类型
            handler: 异步处理函数
            priority: 优先级，默认 NORMAL
        """
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append((priority, handler))
        # 按优先级排序
        self._async_subscribers[event_type].sort(key=lambda x: x[0].value, reverse=True)
        logger.debug(f"Subscribed async {handler.__name__} to {event_type.value} (priority: {priority.name})")

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                (p, h) for p, h in self._subscribers[event_type] if h != handler
            ]

    def publish(self, event: Event):
        """发布事件 (同步，直接处理)"""
        self._record_event(event)
        self._process_event(event)
        # 自动触发 Hook (同步)
        self._trigger_hooks(event)

    async def publish_async(self, event: Event):
        """发布事件 (异步)

        如果启用了队列模式，则放入队列
        否则直接处理
        """
        self._record_event(event)

        # 触发 Hook (异步)
        await self._trigger_hooks_async(event)

        if self._use_queue and self._running:
            await self._event_queue.put(event)
        else:
            await self._process_event_async(event)

    def _trigger_hooks(self, event: Event) -> list[HandlerResult]:
        """触发同步 Hook"""
        results = []
        try:
            # 同步执行 Hook (简化版本)
            hooks = self._hook_registry.get_hooks(event.type)
            for hook in hooks:
                if hook.enabled:
                    logger.debug(f"Triggering hook: {hook.name} for {event.type.value}")
        except Exception as e:
            logger.error(f"Hook trigger error: {e}")
        return results

    async def _trigger_hooks_async(self, event: Event) -> list[HandlerResult]:
        """触发异步 Hook"""
        try:
            results = await self._hook_registry.dispatch(event)
            for result in results:
                if not result.success:
                    logger.warning(f"Hook {result.hook_id} failed: {result.error}")
            return results
        except Exception as e:
            logger.error(f"Async hook trigger error: {e}")
            return []

    def _process_event(self, event: Event):
        """同步处理事件"""
        handlers = self._subscribers.get(event.type, [])
        for priority, handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error in {event.type.value}: {e}")

    async def _process_event_async(self, event: Event):
        """异步处理事件"""
        # 先处理高优先级订阅者
        async_handlers = self._async_subscribers.get(event.type, [])
        for priority, handler in async_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Async event handler error in {event.type.value}: {e}")

    # ==================== 队列模式 ====================

    async def start(self):
        """启动事件总线（队列模式）"""
        if self._running:
            return

        self._running = True
        self._event_queue = asyncio.Queue()
        self._processor_task = asyncio.create_task(self._process_loop())
        logger.info("EventBus started (queue mode)")

    async def stop(self):
        """停止事件总线"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped")

    async def _process_loop(self):
        """事件处理循环"""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event_async(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}")

    @property
    def queue_size(self) -> int:
        """获取队列大小"""
        if self._event_queue:
            return self._event_queue.qsize()
        return 0

    def _record_event(self, event: Event):
        """记录事件到历史"""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

    def get_history(
        self,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[Event]:
        """获取事件历史"""
        if event_type:
            return [e for e in self._event_history if e.type == event_type][-limit:]
        return self._event_history[-limit:]

    def clear_history(self):
        """清空历史"""
        self._event_history.clear()

    @property
    def subscriber_count(self) -> dict[EventType, int]:
        """订阅者数量"""
        result = {}
        for event_type in EventType:
            sync_count = len(self._subscribers.get(event_type, []))
            async_count = len(self._async_subscribers.get(event_type, []))
            result[event_type] = sync_count + async_count
        return result


# 全局事件总线实例
event_bus = EventBus()


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    return event_bus


# ====================
# 便捷函数
# ====================


def on(event_type: EventType):
    """装饰器: 订阅事件"""

    def decorator(func: Callable):
        event_bus.subscribe(event_type, func)
        return func

    return decorator


def on_async(event_type: EventType):
    """装饰器: 异步订阅事件"""

    def decorator(func: Callable):
        event_bus.subscribe_async(event_type, func)
        return func

    return decorator


def emit(event_type: EventType, **data):
    """便捷函数: 发布事件"""
    event = Event(type=event_type, data=data)
    event_bus.publish(event)


# ====================
# 预定义事件类型 (兼容 heartbeat 模块)
# ====================


class SystemEvents:
    """系统事件预定义

    提供字符串类型的事件常量，兼容现有代码
    """

    # Agent 事件
    TASK_STARTED = "task:started"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"

    # 经验事件
    EXPERIENCE_COLLECTED = "experience:collected"
    EXPERIENCE_STORED = "experience:stored"
    PATTERN_DETECTED = "pattern:detected"

    # 心跳事件
    HEARTBEAT_TICK = "heartbeat:tick"
    HEARTBEAT_PHASE = "heartbeat:phase"

    # 知识沉淀事件
    KNOWLEDGE_STORED = "knowledge:stored"
    LEARNING_LOGGED = "learning:logged"
    ERROR_LOGGED = "error:logged"

    # 系统事件
    SYSTEM_START = "system:start"
    SYSTEM_STOP = "system:stop"
    ERROR = "system:error"


# ====================
# 便捷装饰器 (带优先级)
# ====================


def on(event_type: EventType, priority: EventPriority = EventPriority.NORMAL):
    """装饰器: 订阅事件 (带优先级)

    Args:
        event_type: 事件类型
        priority: 优先级
    """

    def decorator(func: Callable):
        event_bus.subscribe(event_type, func, priority)
        return func

    return decorator


def on_async(event_type: EventType, priority: EventPriority = EventPriority.NORMAL):
    """装饰器: 异步订阅事件 (带优先级)

    Args:
        event_type: 事件类型
        priority: 优先级
    """

    def decorator(func: EventHandler):
        event_bus.subscribe_async(event_type, func, priority)
        return func

    return decorator
