"""追踪导出单元测试"""
import sys

import pytest

sys.path.insert(0, '.')

from datetime import datetime

from src.datacenter.tracing import (
    ConsoleExporter,
    LangSmithExporter,
    MultiExporter,
    OpenTelemetryExporter,
    TraceSpan,
    TracingManager,
)


def test_trace_span_creation():
    """测试 TraceSpan 创建"""
    span = TraceSpan(name="test_span")
    assert span.name == "test_span"
    assert span.span_id != ""


def test_trace_span_duration():
    """测试持续时间计算"""
    span = TraceSpan(name="test")
    span.end_time = datetime.now()
    duration = span.duration_ms()
    assert duration >= 0


def test_trace_span_to_dict():
    """测试 TraceSpan 序列化"""
    span = TraceSpan(name="test_dict", attributes={"key": "value"})
    d = span.to_dict()
    assert d["name"] == "test_dict"
    assert d["attributes"]["key"] == "value"


def test_tracing_manager():
    """测试追踪管理器"""
    tm = TracingManager()
    assert tm is not None
    assert len(tm.exporter.exporters) >= 1  # ConsoleExporter by default


def test_start_and_end_span():
    """测试开始和结束跨度"""
    tm = TracingManager()
    span = tm.start_span("test_span", {"attr": "value"})
    assert span.name == "test_span"
    tm.end_span(span, status_code=0)
    assert span.end_time is not None


def test_trace_context_manager():
    """测试上下文管理器"""
    tm = TracingManager()
    with tm.trace("context_test", {"test": True}) as span:
        assert span.name == "context_test"
    assert span.end_time is not None


def test_otel_exporter():
    """测试 OpenTelemetry 导出器"""
    otel = OpenTelemetryExporter("http://localhost:4317")
    assert otel.endpoint == "http://localhost:4317"


def test_langsmith_exporter():
    """测试 LangSmith 导出器"""
    ls = LangSmithExporter(project_name="test-project")
    assert ls.project_name == "test-project"


def test_multi_exporter():
    """测试多导出器"""
    me = MultiExporter()
    me.add_exporter(ConsoleExporter())
    assert len(me.exporters) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
