"""
Tracing - OpenTelemetry/LangSmith 集成
支持导出到 OpenTelemetry、LangSmith 等追踪系统
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TraceSpan:
    """追踪跨度"""

    name: str
    span_id: str = ""
    parent_id: str = ""
    trace_id: str = ""

    # 时间
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    # 属性
    attributes: dict[str, Any] = field(default_factory=dict)

    # 事件
    events: list[dict] = field(default_factory=list)

    # 状态
    status_code: int = 0
    status_message: str = ""

    def __post_init__(self):
        """自动生成 span_id 和 trace_id"""
        import uuid

        if not self.span_id:
            object.__setattr__(self, "span_id", str(uuid.uuid4())[:16])
        if not self.trace_id:
            object.__setattr__(self, "trace_id", str(uuid.uuid4()))

    def duration_ms(self) -> float:
        """获取持续时间(毫秒)"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms(),
            "attributes": self.attributes,
            "events": self.events,
            "status_code": self.status_code,
            "status_message": self.status_message,
        }


class TracingExporter:
    """追踪导出器基类"""

    def export_span(self, span: TraceSpan):
        """导出跨度"""
        raise NotImplementedError

    def export_spans(self, spans: list[TraceSpan]):
        """批量导出跨度"""
        for span in spans:
            self.export_span(span)


class OpenTelemetryExporter(TracingExporter):
    """OpenTelemetry 导出器"""

    def __init__(self, endpoint: str = None, headers: dict[str, str] = None):
        self.endpoint = endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
        )
        self.headers = headers or {}

    def export_span(self, span: TraceSpan):
        """导出到 OpenTelemetry 兼容的后端"""
        # 转换为 OpenTelemetry 格式
        otel_span = {
            "name": span.name,
            "span_id": span.span_id,
            "parent_span_id": span.parent_id,
            "trace_id": span.trace_id,
            "start_time_unix_nano": int(span.start_time.timestamp() * 1e9),
            "end_time_unix_nano": int(span.end_time.timestamp() * 1e9) if span.end_time else 0,
            "attributes": span.attributes,
            "events": span.events,
            "status": {
                "code": span.status_code,
                "message": span.status_message,
            },
        }

        # 如果配置了端点，发送到 OTLP
        if self.endpoint:
            self._send_to_otlp([otel_span])

        return otel_span

    def _send_to_otlp(self, spans: list[dict]):
        """发送到 OTLP 端点"""
        try:
            import requests

            payload = {"resource_spans": [{"spans": spans}]}

            headers = {"Content-Type": "application/json"}
            headers.update(self.headers)

            # 使用 v1/traces 端点
            response = requests.post(
                f"{self.endpoint}/v1/traces", json=payload, headers=headers, timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"[Warning] OTLP export failed: {e}")
            return False


class LangSmithExporter(TracingExporter):
    """LangSmith 导出器"""

    def __init__(self, api_key: str = None, project_name: str = "openyoung"):
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        self.project_name = project_name
        self.base_url = "https://api.langsmith.com"

    def export_span(self, span: TraceSpan):
        """导出到 LangSmith"""
        if not self.api_key:
            print("[Warning] LangSmith API key not configured")
            return None

        # LangSmith 格式
        ls_record = {
            "name": span.name,
            "run_id": span.span_id or span.trace_id,
            "trace_id": span.trace_id,
            "parent_run_id": span.parent_id,
            "start_time": span.start_time.isoformat(),
            "end_time": span.end_time.isoformat() if span.end_time else None,
            "execution_time_ms": span.duration_ms(),
            "status": "success" if span.status_code == 0 else "error",
            "error": span.status_message if span.status_code != 0 else None,
            "metadata": span.attributes,
            "inputs": span.attributes.get("inputs", {}),
            "outputs": span.attributes.get("outputs", {}),
        }

        # 发送到 LangSmith
        self._send_to_langsmith(ls_record)

        return ls_record

    def _send_to_langsmith(self, record: dict):
        """发送到 LangSmith API"""
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.post(
                f"{self.base_url}/v1/runs",
                json={"project_name": self.project_name, "runs": [record]},
                headers=headers,
                timeout=5,
            )
            return response.status_code in (200, 201)
        except Exception as e:
            print(f"[Warning] LangSmith export failed: {e}")
            return False


class ConsoleExporter(TracingExporter):
    """控制台导出器（调试用）"""

    def export_span(self, span: TraceSpan):
        """输出到控制台"""
        print(f"[Trace] {span.name} ({span.duration_ms():.2f}ms)")
        if span.attributes:
            print(f"  Attributes: {json.dumps(span.attributes, ensure_ascii=False, indent=4)}")
        if span.status_code != 0:
            print(f"  Error: {span.status_message}")


class MultiExporter(TracingExporter):
    """多导出器组合"""

    def __init__(self):
        self.exporters: list[TracingExporter] = []

    def add_exporter(self, exporter: TracingExporter):
        """添加导出器"""
        self.exporters.append(exporter)

    def export_span(self, span: TraceSpan):
        """导出到所有导出器"""
        for exporter in self.exporters:
            exporter.export_span(span)


class TracingContext:
    """追踪上下文管理器"""

    def __init__(self, name: str, exporter: TracingExporter = None, attributes: dict = None):
        self.name = name
        self.exporter = exporter or ConsoleExporter()
        self.attributes = attributes or {}
        self.span = TraceSpan(name=name, attributes=self.attributes)

    def __enter__(self):
        import uuid

        self.span.span_id = str(uuid.uuid4())[:16]
        self.span.trace_id = str(uuid.uuid4())
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.span.end_time = datetime.now()

        if exc_type:
            self.span.status_code = 1
            self.span.status_message = str(exc_val)

        self.exporter.export_span(self.span)


class TracingManager:
    """追踪管理器"""

    def __init__(self):
        self.exporter = MultiExporter()
        self.spans: list[TraceSpan] = []

        # 添加默认控制台导出器
        self.exporter.add_exporter(ConsoleExporter())

    def add_exporter(self, exporter: TracingExporter):
        """添加导出器"""
        self.exporter.add_exporter(exporter)

    def start_span(self, name: str, attributes: dict = None, parent_id: str = None) -> TraceSpan:
        """开始跨度"""
        import uuid

        span = TraceSpan(
            name=name,
            span_id=str(uuid.uuid4())[:16],
            parent_id=parent_id or "",
            trace_id=str(uuid.uuid4()),
            attributes=attributes or {},
        )
        self.spans.append(span)
        return span

    def end_span(self, span: TraceSpan, status_code: int = 0, status_message: str = ""):
        """结束跨度"""
        span.end_time = datetime.now()
        span.status_code = status_code
        span.status_message = status_message
        self.exporter.export_span(span)

    def trace(self, name: str, attributes: dict = None):
        """追踪上下文管理器"""
        return TracingContext(name, self.exporter, attributes)

    def export_all(self):
        """导出所有跨度"""
        for span in self.spans:
            self.exporter.export_span(span)
        self.spans.clear()


# ========== 便捷函数 ==========


def get_tracing_manager() -> TracingManager:
    """获取追踪管理器"""
    return TracingManager()


def create_otel_exporter(endpoint: str = None) -> OpenTelemetryExporter:
    """创建 OpenTelemetry 导出器"""
    return OpenTelemetryExporter(endpoint)


def create_langsmith_exporter(api_key: str = None, project: str = "openyoung") -> LangSmithExporter:
    """创建 LangSmith 导出器"""
    return LangSmithExporter(api_key, project)
