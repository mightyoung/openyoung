"""
OpenTelemetry 集成模块

提供可观测性能力:
- 自动 instrumentation
- LLM 调用追踪
- Agent 执行追踪
- 指标收集

依赖: opentelemetry-api, opentelemetry-sdk
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, Optional

logger = logging.getLogger(__name__)

# OpenTelemetry 依赖检查
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import SpanKind, Status, StatusCode
    from opentelemetry.trace.propagation import set_span_in_context
    from opentelemetry.context import Context

    # Metrics support
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter

    # OTLP exporter
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        OTLP_AVAILABLE = True
    except ImportError:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
            OTLP_AVAILABLE = True
        except ImportError:
            OTLP_AVAILABLE = False
            OTLPSpanExporter = None
            OTLPMetricExporter = None

    # Prometheus exporter
    try:
        from opentelemetry.exporter.prometheus import PrometheusExporter
        PROMETHEUS_AVAILABLE = True
    except ImportError:
        try:
            # Fallback for older versions
            from opentelemetry.sdk.metrics.export import PrometheusExporter as PrometheusExporter
            PROMETHEUS_AVAILABLE = True
        except ImportError:
            PROMETHEUS_AVAILABLE = False
            PrometheusExporter = None

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # 创建一个简单的 mock 以便在未安装时也能导入
    trace = None
    traceback = None
    StatusCode = None
    SpanKind = None
    metrics = None
    OTLP_AVAILABLE = False
    PROMETHEUS_AVAILABLE = False
    OTLPSpanExporter = None
    OTLPMetricExporter = None
    PrometheusExporter = None
    logger.warning("OpenTelemetry not available. Telemetry will be disabled.")


class SpanStatus(Enum):
    """Span 状态"""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


@dataclass
class TelemetryConfig:
    """遥测配置"""
    service_name: str = "openyoung"
    enable_console_export: bool = True
    enable_metrics: bool = True
    sample_rate: float = 1.0  # 0-1
    resource_attributes: Dict[str, str] = field(default_factory=dict)

    # Exporter 配置
    enable_otlp_export: bool = False
    otlp_endpoint: str = "http://localhost:4317"
    otlp_protocol: str = "grpc"  # grpc or http
    enable_prometheus_export: bool = False
    prometheus_port: int = 9090

    # Metrics export interval (seconds)
    metrics_export_interval: int = 60


class OpenTelemetryConfig:
    """OpenTelemetry 配置管理器"""

    _initialized = False
    _provider: Optional[Any] = None
    _tracer: Optional[Any] = None
    _meter_provider: Optional[Any] = None
    _meter: Optional[Any] = None

    def __init__(self, config: Optional[TelemetryConfig] = None):
        self.config = config or TelemetryConfig()

    def initialize(self) -> bool:
        """初始化 OpenTelemetry

        Returns:
            是否成功初始化
        """
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available, skipping initialization")
            return False

        if self._initialized:
            return True

        try:
            # 创建资源
            resource = Resource.create({
                "service.name": self.config.service_name,
                **self.config.resource_attributes
            })

            # ========== 1. 初始化 Tracing ==========
            self._init_tracing(resource)

            # ========== 2. 初始化 Metrics ==========
            if self.config.enable_metrics:
                self._init_metrics(resource)

            self._tracer = trace.get_tracer(__name__)
            self._initialized = True
            logger.info(f"OpenTelemetry initialized: service={self.config.service_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            return False

    def _init_tracing(self, resource):
        """初始化追踪系统"""
        # 创建 tracer provider
        self._provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self._provider)

        # Console exporter
        if self.config.enable_console_export:
            self._provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        # OTLP exporter
        if self.config.enable_otlp_export and OTLP_AVAILABLE and OTLPSpanExporter:
            try:
                otlp_exporter = OTLPSpanExporter(
                    endpoint=self.config.otlp_endpoint,
                    insecure=True if "http" in self.config.otlp_endpoint else False
                )
                self._provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP tracing enabled: {self.config.otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to setup OTLP tracer: {e}")

    def _init_metrics(self, resource):
        """初始化指标系统"""
        if not metrics:
            logger.warning("Metrics not available")
            return

        try:
            readers = []

            # Console metrics exporter
            if self.config.enable_console_export:
                try:
                    readers.append(ConsoleMetricExporter())
                except Exception:
                    pass

            # OTLP metrics exporter
            if self.config.enable_otlp_export and OTLP_AVAILABLE and OTLPMetricExporter:
                try:
                    otlp_metric_exporter = OTLPMetricExporter(
                        endpoint=self.config.otlp_endpoint,
                        insecure=True
                    )
                    readers.append(PeriodicExportingMetricReader(
                        otlp_metric_exporter,
                        export_interval_millis=self.config.metrics_export_interval * 1000
                    ))
                    logger.info(f"OTLP metrics enabled: {self.config.otlp_endpoint}")
                except Exception as e:
                    logger.warning(f"Failed to setup OTLP metrics: {e}")

            # Prometheus metrics exporter
            if self.config.enable_prometheus_export and PROMETHEUS_AVAILABLE and PrometheusExporter:
                try:
                    prometheus_exporter = PrometheusExporter(
                        port=self.config.prometheus_port,
                        prefix=self.config.service_name
                    )
                    readers.append(prometheus_exporter)
                    logger.info(f"Prometheus metrics enabled: port={self.config.prometheus_port}")
                except Exception as e:
                    logger.warning(f"Failed to setup Prometheus exporter: {e}")

            # 创建 meter provider
            if readers:
                self._meter_provider = MeterProvider(
                    resource=resource,
                    metric_readers=readers
                )
                metrics.set_meter_provider(self._meter_provider)
                self._meter = metrics.get_meter(__name__)
                logger.info(f"Meter initialized with {len(readers)} readers")
            else:
                # 即使没有 reader 也创建 provider
                self._meter_provider = MeterProvider(resource=resource)
                metrics.set_meter_provider(self._meter_provider)
                self._meter = metrics.get_meter(__name__)

        except Exception as e:
            logger.warning(f"Failed to initialize metrics: {e}")

    def get_tracer(self):
        """获取 tracer"""
        if not self._initialized:
            self.initialize()
        return self._tracer

    def get_meter(self):
        """获取 meter"""
        if not self._initialized:
            self.initialize()
        return self._meter

    def shutdown(self):
        """关闭"""
        if self._provider:
            self._provider.shutdown()
            self._initialized = False


# 全局配置实例
_default_config: Optional[TelemetryConfig] = None
_default_otel: Optional[OpenTelemetryConfig] = None


def init_telemetry(
    service_name: str = "openyoung",
    enable_console: bool = True,
    **kwargs
) -> bool:
    """初始化遥测系统

    Args:
        service_name: 服务名称
        enable_console: 启用 console 输出
        **kwargs: 其他配置选项

    Returns:
        是否成功
    """
    global _default_config, _default_otel

    _default_config = TelemetryConfig(
        service_name=service_name,
        enable_console_export=enable_console,
        **kwargs
    )
    _default_otel = OpenTelemetryConfig(_default_config)
    success = _default_otel.initialize()

    # 初始化指标收集器
    if success and _default_otel.get_meter():
        try:
            get_metrics_collector().initialize(_default_otel.get_meter())
        except Exception as e:
            logger.warning(f"Failed to initialize metrics collector: {e}")

    return success


def get_tracer():
    """获取全局 tracer"""
    global _default_otel
    if _default_otel is None:
        _default_otel = OpenTelemetryConfig()
        _default_otel.initialize()
    return _default_otel.get_tracer()


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: Any = None
) -> Generator[Any, None, None]:
    """创建追踪 span

    Args:
        name: span 名称
        attributes: 属性
        kind: span 类型

    Yields:
        span 对象
    """
    if not OPENTELEMETRY_AVAILABLE:
        yield None
        return

    tracer = get_tracer()
    if not tracer:
        yield None
        return

    # 确定 span 类型
    span_kind = kind or SpanKind.INTERNAL

    with tracer.start_as_current_span(
        name,
        kind=span_kind,
        attributes=attributes or {}
    ) as span:
        try:
            yield span
        except Exception as e:
            if span:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
            raise


def add_span_attribute(key: str, value: Any):
    """添加 span 属性"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """添加 span 事件"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes=attributes or {})


def record_exception(exception: Exception):
    """记录异常"""
    if not OPENTELEMETRY_AVAILABLE:
        return

    span = trace.get_current_span()
    if span:
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))


class MetricsCollector:
    """指标收集器

    收集和记录系统指标:
    - LLM 调用计数和延迟
    - Agent 执行计数和成功率
    - 工具使用统计
    - Flow 步骤统计
    """

    _instance: Optional["MetricsCollector"] = None
    _counters: Dict[str, Any] = {}
    _histograms: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, meter) -> bool:
        """初始化指标收集器

        Args:
            meter: OpenTelemetry meter

        Returns:
            是否成功
        """
        if self._initialized:
            return True

        try:
            # 创建 counters
            self._counters = {
                "llm_calls_total": meter.create_counter(
                    "llm_calls_total",
                    description="Total number of LLM calls"
                ),
                "llm_errors_total": meter.create_counter(
                    "llm_errors_total",
                    description="Total number of LLM errors"
                ),
                "agent_executions_total": meter.create_counter(
                    "agent_executions_total",
                    description="Total number of agent executions"
                ),
                "agent_success_total": meter.create_counter(
                    "agent_success_total",
                    description="Total number of successful agent executions"
                ),
                "agent_errors_total": meter.create_counter(
                    "agent_errors_total",
                    description="Total number of agent errors"
                ),
                "tool_usage_total": meter.create_counter(
                    "tool_usage_total",
                    description="Total number of tool usages"
                ),
                "flow_steps_total": meter.create_counter(
                    "flow_steps_total",
                    description="Total number of flow steps"
                ),
            }

            # 创建 histograms
            self._histograms = {
                "llm_duration_ms": meter.create_histogram(
                    "llm_duration_ms",
                    description="LLM call duration in milliseconds",
                    unit="ms"
                ),
                "llm_tokens_total": meter.create_histogram(
                    "llm_tokens_total",
                    description="Total tokens per LLM call",
                    unit="tokens"
                ),
                "agent_duration_ms": meter.create_histogram(
                    "agent_duration_ms",
                    description="Agent execution duration in milliseconds",
                    unit="ms"
                ),
                "flow_step_duration_ms": meter.create_histogram(
                    "flow_step_duration_ms",
                    description="Flow step duration in milliseconds",
                    unit="ms"
                ),
            }

            self._initialized = True
            logger.info("MetricsCollector initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MetricsCollector: {e}")
            return False

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """记录 LLM 调用

        Args:
            model: 模型名称
            prompt_tokens: prompt token 数
            completion_tokens: completion token 数
            duration_ms: 耗时 (毫秒)
            error: 错误信息
        """
        if not self._initialized:
            return

        total_tokens = prompt_tokens + completion_tokens

        # 记录计数
        self._counters["llm_calls_total"].add(1, {"model": model})
        if error:
            self._counters["llm_errors_total"].add(1, {"model": model, "error": error})

        # 记录 histogram
        self._histograms["llm_duration_ms"].record(duration_ms, {"model": model})
        self._histograms["llm_tokens_total"].record(total_tokens, {"model": model})

    def record_agent_execution(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool,
        tools_count: int = 0
    ):
        """记录 Agent 执行

        Args:
            agent_name: Agent 名称
            duration_ms: 耗时 (毫秒)
            success: 是否成功
            tools_count: 使用的工具数
        """
        if not self._initialized:
            return

        # 记录计数
        self._counters["agent_executions_total"].add(1, {"agent_name": agent_name})
        if success:
            self._counters["agent_success_total"].add(1, {"agent_name": agent_name})
        else:
            self._counters["agent_errors_total"].add(1, {"agent_name": agent_name})

        # 记录 histogram
        self._histograms["agent_duration_ms"].record(
            duration_ms,
            {"agent_name": agent_name, "success": str(success)}
        )

    def record_tool_usage(self, tool_name: str):
        """记录工具使用

        Args:
            tool_name: 工具名称
        """
        if not self._initialized:
            return

        self._counters["tool_usage_total"].add(1, {"tool_name": tool_name})

    def record_flow_step(
        self,
        flow_name: str,
        step_name: str,
        duration_ms: float,
        success: bool
    ):
        """记录 Flow 步骤

        Args:
            flow_name: Flow 名称
            step_name: 步骤名称
            duration_ms: 耗时 (毫秒)
            success: 是否成功
        """
        if not self._initialized:
            return

        self._counters["flow_steps_total"].add(1, {
            "flow_name": flow_name,
            "step_name": step_name
        })

        self._histograms["flow_step_duration_ms"].record(
            duration_ms,
            {"flow_name": flow_name, "step_name": step_name, "success": str(success)}
        )


# 全局指标收集器实例
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class LLMTelemetry:
    """LLM 调用遥测"""

    @staticmethod
    def trace_llm_call(
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """追踪 LLM 调用

        Args:
            model: 模型名称
            prompt_tokens: prompt token 数
            completion_tokens: completion token 数
            duration_ms: 耗时 (毫秒)
            error: 错误信息
        """
        # 只有在 OpenTelemetry 可用时才创建 span
        if OPENTELEMETRY_AVAILABLE and SpanKind:
            with trace_span(
                "llm_call",
                attributes={
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                    "duration_ms": duration_ms,
                    "error": error or "",
                },
                kind=SpanKind.CLIENT
            ) as span:
                if error and span:
                    span.set_status(Status(StatusCode.ERROR, error))

        # 记录指标
        if OPENTELEMETRY_AVAILABLE:
            try:
                get_metrics_collector().record_llm_call(
                    model, prompt_tokens, completion_tokens, duration_ms, error
                )
            except Exception as e:
                logger.debug(f"Failed to record metrics: {e}")


class AgentTelemetry:
    """Agent 执行遥测"""

    @staticmethod
    def trace_agent_execution(
        agent_name: str,
        task: str,
        duration_ms: float,
        success: bool,
        tools_used: Optional[List[str]] = None,
        error: Optional[str] = None
    ):
        """追踪 Agent 执行

        Args:
            agent_name: Agent 名称
            task: 任务描述
            duration_ms: 耗时 (毫秒)
            success: 是否成功
            tools_used: 使用的工具列表
            error: 错误信息
        """
        tools_used = tools_used or []

        # 只有在 OpenTelemetry 可用时才创建 span
        if OPENTELEMETRY_AVAILABLE and SpanKind:
            with trace_span(
                "agent_execution",
                attributes={
                    "agent_name": agent_name,
                    "task": task,
                    "duration_ms": duration_ms,
                    "success": success,
                    "tools_used": ",".join(tools_used),
                    "error": error or "",
                },
                kind=SpanKind.SERVER
            ) as span:
                if error and span:
                    span.set_status(Status(StatusCode.ERROR, error))

        # 记录指标
        if OPENTELEMETRY_AVAILABLE:
            try:
                get_metrics_collector().record_agent_execution(
                    agent_name, duration_ms, success, len(tools_used)
                )
                # 记录每个工具的使用
                for tool in tools_used:
                    get_metrics_collector().record_tool_usage(tool)
            except Exception as e:
                logger.debug(f"Failed to record metrics: {e}")


class FlowTelemetry:
    """工作流遥测"""

    @staticmethod
    def trace_flow_step(
        flow_name: str,
        step_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """追踪 Flow 步骤

        Args:
            flow_name: Flow 名称
            step_name: 步骤名称
            duration_ms: 耗时 (毫秒)
            success: 是否成功
            error: 错误信息
        """
        # 只有在 OpenTelemetry 可用时才创建 span
        if OPENTELEMETRY_AVAILABLE and SpanKind:
            with trace_span(
                "flow_step",
                attributes={
                    "flow_name": flow_name,
                    "step_name": step_name,
                    "duration_ms": duration_ms,
                    "success": success,
                    "error": error or "",
                },
                kind=SpanKind.INTERNAL
            ) as span:
                if error and span:
                    span.set_status(Status(StatusCode.ERROR, error))

        # 记录指标
        if OPENTELEMETRY_AVAILABLE:
            try:
                get_metrics_collector().record_flow_step(
                    flow_name, step_name, duration_ms, success
                )
            except Exception as e:
                logger.debug(f"Failed to record metrics: {e}")


# 便捷装饰器
def traced(func: Callable) -> Callable:
    """追踪函数执行的装饰器

    Args:
        func: 要追踪的函数

    Returns:
        装饰后的函数
    """
    if not OPENTELEMETRY_AVAILABLE:
        return func

    def wrapper(*args, **kwargs):
        with trace_span(f"function.{func.__name__}"):
            return func(*args, **kwargs)

    return wrapper


__all__ = [
    "TelemetryConfig",
    "OpenTelemetryConfig",
    "SpanStatus",
    "init_telemetry",
    "get_tracer",
    "trace_span",
    "add_span_attribute",
    "add_span_event",
    "record_exception",
    "LLMTelemetry",
    "AgentTelemetry",
    "FlowTelemetry",
    "MetricsCollector",
    "get_metrics_collector",
    "traced",
    "OPENTELEMETRY_AVAILABLE",
    "OTLP_AVAILABLE",
    "PROMETHEUS_AVAILABLE",
]
