"""
Distributed tracing for PEAS
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional


class Span:
    """追踪跨度"""

    def __init__(self, name: str, trace_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id or self._generate_trace_id()
        self.span_id = self._generate_span_id()
        self.start_time = datetime.utcnow()
        self.end_time: Optional[datetime] = None
        self.attributes: Dict[str, Any] = {}
        self.events: list = []

    @staticmethod
    def _generate_trace_id() -> str:
        import uuid

        return uuid.uuid4().hex[:16]

    @staticmethod
    def _generate_span_id() -> str:
        import uuid

        return uuid.uuid4().hex[:8]

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict] = None) -> None:
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.utcnow().isoformat(),
                "attributes": attributes or {},
            }
        )

    def end(self) -> None:
        self.end_time = datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000
            if self.end_time
            else None,
            "attributes": self.attributes,
            "events": self.events,
        }


class Tracer:
    """PEAS追踪器"""

    def __init__(self, service_name: str = "peas"):
        self.service_name = service_name
        self._spans: list = []

    def start_span(self, name: str, trace_id: Optional[str] = None) -> Span:
        """开始一个新的span"""
        span = Span(name, trace_id)
        span.set_attribute("service.name", self.service_name)
        self._spans.append(span)
        return span

    def get_traces(self) -> list:
        """获取所有追踪记录"""
        return [s.to_dict() for s in self._spans]

    def export_json(self) -> str:
        """导出为JSON格式"""
        return json.dumps(self.get_traces(), indent=2)


# 全局tracer实例
_default_tracer: Optional[Tracer] = None


def get_tracer(service_name: str = "peas") -> Tracer:
    """获取全局tracer实例"""
    global _default_tracer
    if _default_tracer is None:
        _default_tracer = Tracer(service_name)
    return _default_tracer
