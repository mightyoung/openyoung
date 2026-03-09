"""
Telemetry Package - 可观测性系统
"""

from .otel import (
    OPENTELEMETRY_AVAILABLE,
    AgentTelemetry,
    FlowTelemetry,
    LLMTelemetry,
    OpenTelemetryConfig,
    TelemetryConfig,
    add_span_attribute,
    add_span_event,
    get_tracer,
    init_telemetry,
    record_exception,
    trace_span,
    traced,
)

__all__ = [
    # Config
    "TelemetryConfig",
    "OpenTelemetryConfig",
    # Functions
    "init_telemetry",
    "get_tracer",
    "trace_span",
    "add_span_attribute",
    "add_span_event",
    "record_exception",
    "traced",
    # Specialized telemetry
    "LLMTelemetry",
    "AgentTelemetry",
    "FlowTelemetry",
    # Flags
    "OPENTELEMETRY_AVAILABLE",
]
