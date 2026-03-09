"""
Tracing Infrastructure - 2026 AI Agent Best Practice

基于 OpenTelemetry 标准实现 Tracing:
- 步骤级 spans
- 错误追踪
- 性能监控
- 可扩展到 OpenTelemetry

参考:
- LangGraph OpenTelemetry Integration
- Microsoft Foundry Agent Tracing
- LangChain Tracing Best Practices
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpanKind(Enum):
    """Span 类型"""

    INTERNAL = "internal"
    LLM = "llm"
    TOOL = "tool"
    AGENT = "agent"


class SpanStatus(Enum):
    """Span 状态"""

    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class Span:
    """Tracing Span"""

    name: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_id: str | None = None
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32])
    kind: SpanKind = SpanKind.INTERNAL
    status: SpanStatus = SpanStatus.UNSET
    status_message: str = ""

    # 时间戳
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float | None = None

    # 属性
    attributes: dict[str, Any] = field(default_factory=dict)

    # 事件
    events: list[dict[str, Any]] = field(default_factory=list)

    def end(self, status: SpanStatus = SpanStatus.OK, message: str = ""):
        """结束 Span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        self.status_message = message

    def set_attribute(self, key: str, value: Any):
        """设置属性"""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] = None):
        """添加事件"""
        self.events.append(
            {
                "name": name,
                "timestamp": time.time(),
                "attributes": attributes or {},
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "kind": self.kind.value,
            "status": self.status.value,
            "status_message": self.status_message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """Tracer - 创建和管理 Spans"""

    def __init__(self, service_name: str = "openyoung"):
        self.service_name = service_name
        self._spans: list[Span] = []
        self._current_span: Span | None = None
        self._trace_id: str | None = None

    def start_trace(self, name: str, trace_id: str = None) -> Span:
        """开始新的 Trace"""
        self._trace_id = trace_id or uuid.uuid4().hex[:32]
        span = Span(
            name=name,
            trace_id=self._trace_id,
            parent_id=self._current_span.span_id if self._current_span else None,
            kind=SpanKind.AGENT,
        )
        self._current_span = span
        self._spans.append(span)
        return span

    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL) -> Span:
        """开始新的 Span"""
        span = Span(
            name=name,
            trace_id=self._trace_id or uuid.uuid4().hex[:32],
            parent_id=self._current_span.span_id if self._current_span else None,
            kind=kind,
        )
        self._current_span = span
        self._spans.append(span)
        return span

    def end_span(self, status: SpanStatus = SpanStatus.OK, message: str = ""):
        """结束当前 Span"""
        if self._current_span:
            self._current_span.end(status, message)
            # 返回父 Span
            if self._current_span.parent_id:
                for span in reversed(self._spans):
                    if span.span_id == self._current_span.parent_id:
                        self._current_span = span
                        break
            else:
                self._current_span = None

    def add_event(self, name: str, attributes: dict[str, Any] = None):
        """向当前 Span 添加事件"""
        if self._current_span:
            self._current_span.add_event(name, attributes)

    def set_attribute(self, key: str, value: Any):
        """设置当前 Span 属性"""
        if self._current_span:
            self._current_span.set_attribute(key, value)

    def record_exception(self, exception: Exception):
        """记录异常"""
        if self._current_span:
            self._current_span.end(SpanStatus.ERROR, str(exception))
            self._current_span.add_event(
                "exception",
                {
                    "type": type(exception).__name__,
                    "message": str(exception),
                },
            )

    def get_spans(self) -> list[Span]:
        """获取所有 Spans"""
        return self._spans

    def get_trace(self) -> list[dict[str, Any]]:
        """获取 Trace (序列化的 Spans)"""
        return [span.to_dict() for span in self._spans]

    def export_json(self, filepath: str):
        """导出到 JSON 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.get_trace(), f, indent=2, ensure_ascii=False)

    def clear(self):
        """清空 Spans"""
        self._spans.clear()
        self._current_span = None
        self._trace_id = None


# 全局 Tracer 实例
_global_tracer: Tracer | None = None


def get_tracer(service_name: str = "openyoung") -> Tracer:
    """获取全局 Tracer"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer


# 上下文管理器用于方便使用
class traceSpan:
    """Span 上下文管理器"""

    def __init__(self, tracer: Tracer, name: str, kind: SpanKind = SpanKind.INTERNAL):
        self.tracer = tracer
        self.name = name
        self.kind = kind

    def __enter__(self):
        self.span = self.tracer.start_span(self.name, self.kind)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.tracer.record_exception(exc_val)
        else:
            self.tracer.end_span()
