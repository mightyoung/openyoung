"""
Log Consumer - 日志消费者

消费 Rust 容器的结构化日志，实现可视化监测
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Dict, Optional

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """日志级别"""

    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class Component(Enum):
    """日志组件"""

    TARGET_AGENT = "target_agent"
    EVALUATOR = "evaluator"
    LLM_MIDDLEWARE = "llm_middleware"
    CIRCUIT_BREAKER = "circuit_breaker"
    SECURITY = "security"


class EventType(Enum):
    """事件类型"""

    # Target Agent 事件
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTION = "agent_action"
    AGENT_OBSERVATION = "agent_observation"
    AGENT_COMPLETED = "agent_completed"

    # Evaluator 事件
    EVALUATOR_STARTED = "evaluator_started"
    EVALUATOR_DIMENSION = "evaluator_dimension"
    EVALUATOR_ITERATION = "evaluator_iteration"
    EVALUATOR_COMPLETED = "evaluator_completed"

    # 迭代事件
    ITERATION_PASSED = "iteration_passed"
    ITERATION_FAILED = "iteration_failed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"

    # 任务事件
    TASK_SUCCESS = "task_success"
    TASK_FAILED = "task_failed"

    # LLM 事件
    LLM_CALL_STARTED = "llm_call_started"
    LLM_CALL_COMPLETED = "llm_call_completed"
    LLM_CALL_FAILED = "llm_call_failed"

    # 熔断器事件
    CIRCUIT_OPENED = "circuit_opened"
    CIRCUIT_CLOSED = "circuit_closed"
    CIRCUIT_HALF_OPEN = "circuit_half_open"


@dataclass
class LogEvent:
    """日志事件"""

    timestamp: str
    level: str
    component: str
    event: str
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    iteration: Optional[int] = None
    data: Optional[Dict[str, Any]] = None


class LogConsumer:
    """日志消费者

    消费 Rust 容器的日志事件流
    """

    def __init__(self, log_stream: AsyncIterator[bytes]):
        """
        初始化日志消费者

        Args:
            log_stream: 日志字节流
        """
        self._stream = log_stream
        self._event_queue: asyncio.Queue[LogEvent] = asyncio.Queue()
        self._running = False

    async def start(self):
        """启动日志消费者"""
        self._running = True
        asyncio.create_task(self._consume_events())

    async def stop(self):
        """停止日志消费者"""
        self._running = False

    async def _consume_events(self):
        """消费日志事件"""
        try:
            async for raw in self._stream:
                if not raw:
                    continue

                try:
                    event = self._parse_event(raw)
                    if event:
                        await self._event_queue.put(event)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse log: {raw[:100]}")
        except Exception as e:
            logger.error(f"Log consumer error: {e}")
        finally:
            self._running = False

    def _parse_event(self, raw: bytes) -> Optional[LogEvent]:
        """解析日志事件"""
        try:
            data = json.loads(raw.decode("utf-8"))
            return LogEvent(
                timestamp=data.get("timestamp", ""),
                level=data.get("level", "info"),
                component=data.get("component", ""),
                event=data.get("event", ""),
                trace_id=data.get("trace_id"),
                session_id=data.get("session_id"),
                iteration=data.get("iteration"),
                data=data.get("data"),
            )
        except Exception as e:
            logger.error(f"Failed to parse event: {e}")
            return None

    async def events(self) -> AsyncIterator[LogEvent]:
        """获取日志事件流"""
        while self._running or not self._event_queue.empty():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                continue

    def get_progress(self) -> Dict[str, Any]:
        """获取当前进度"""
        # 简化的进度计算
        return {
            "queue_size": self._event_queue.qsize(),
            "running": self._running,
        }


class EvaluationLogTracker:
    """评估日志跟踪器

    跟踪评估进度，提供可视化数据
    """

    def __init__(self, trace_id: str):
        self._trace_id = trace_id
        self._iterations: list[Dict[str, Any]] = []
        self._current_iteration: Optional[int] = None
        self._status: str = "pending"
        self._final_score: Optional[float] = None

    def track_event(self, event: LogEvent):
        """跟踪日志事件"""
        if event.trace_id != self._trace_id:
            return

        # 跟踪迭代
        if event.event == "evaluator_iteration":
            self._current_iteration = event.iteration
            if event.data:
                self._iterations.append(
                    {
                        "iteration": event.iteration,
                        "score": event.data.get("score", 0.0),
                        "passed": event.data.get("passed", False),
                    }
                )

        # 跟踪任务完成
        if event.event in ["task_success", "task_failed"]:
            self._status = "success" if event.event == "task_success" else "failed"
            if event.data:
                self._final_score = event.data.get("final_score")

    def get_progress(self) -> Dict[str, Any]:
        """获取进度"""
        return {
            "trace_id": self._trace_id,
            "status": self._status,
            "current_iteration": self._current_iteration,
            "iterations": self._iterations,
            "final_score": self._final_score,
            "total_iterations": len(self._iterations),
        }


# 便捷函数
def create_log_consumer(log_stream: AsyncIterator[bytes]) -> LogConsumer:
    """创建日志消费者"""
    return LogConsumer(log_stream)


async def monitor_evaluation(
    log_stream: AsyncIterator[bytes],
    trace_id: str,
) -> Dict[str, Any]:
    """
    监控评估过程

    Args:
        log_stream: 日志流
        trace_id: 追踪 ID

    Returns:
        最终评估结果
    """
    consumer = LogConsumer(log_stream)
    tracker = EvaluationLogTracker(trace_id)

    await consumer.start()

    async for event in consumer.events():
        tracker.track_event(event)

        # 打印进度
        progress = tracker.get_progress()
        if progress["current_iteration"]:
            logger.info(f"Iteration {progress['current_iteration']}: status={progress['status']}")

        # 检查是否完成
        if progress["status"] in ["success", "failed"]:
            break

    await consumer.stop()
    return tracker.get_progress()
