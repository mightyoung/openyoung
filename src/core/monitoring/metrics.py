"""
Monitoring Module - 监控与可观测性

提供指标收集、日志聚合、追踪功能
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表
    HISTOGRAM = "histogram"  # 直方图
    TIMER = "timer"  # 计时器


@dataclass
class Metric:
    """指标数据"""

    name: str
    value: float
    metric_type: MetricType
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class MetricsCollector:
    """
    指标收集器

    支持计数器、仪表、直方图、计时器
    """

    def __init__(self, name: str = "openyoung"):
        self.name = name
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, list[float]] = defaultdict(list)

    # ========== 计数器 ==========

    def inc_counter(self, name: str, value: float = 1.0, labels: Optional[dict] = None):
        """增加计数器"""
        key = self._make_key(name, labels)
        self._counters[key] += value

    def get_counter(self, name: str, labels: Optional[dict] = None) -> float:
        """获取计数器值"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    # ========== 仪表 ==========

    def set_gauge(self, name: str, value: float, labels: Optional[dict] = None):
        """设置仪表值"""
        key = self._make_key(name, labels)
        self._gauges[key] = value

    def get_gauge(self, name: str, labels: Optional[dict] = None) -> Optional[float]:
        """获取仪表值"""
        key = self._make_key(name, labels)
        return self._gauges.get(key)

    # ========== 直方图 ==========

    def observe_histogram(self, name: str, value: float, labels: Optional[dict] = None):
        """观察直方图值"""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)

    def get_histogram_stats(self, name: str, labels: Optional[dict] = None) -> dict[str, float]:
        """获取直方图统计"""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "sum": 0, "min": 0, "max": 0, "avg": 0}

        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    # ========== 计时器 ==========

    def start_timer(self, name: str, labels: Optional[dict] = None) -> float:
        """开始计时"""
        return time.time()

    def stop_timer(self, name: str, start_time: float, labels: Optional[dict] = None):
        """停止计时并记录"""
        duration = time.time() - start_time
        key = self._make_key(name, labels)
        self._timers[key].append(duration)

    def get_timer_stats(self, name: str, labels: Optional[dict] = None) -> dict[str, float]:
        """获取计时器统计"""
        key = self._make_key(name, labels)
        values = self._timers.get(key, [])
        if not values:
            return {
                "count": 0,
                "sum": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
                "p50": 0,
                "p95": 0,
                "p99": 0,
            }

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "count": n,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / n,
            "p50": sorted_values[n // 2],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)],
        }

    # ========== 便捷方法 ==========

    def _make_key(self, name: str, labels: Optional[dict] = None) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: self.get_histogram_stats(k) for k in self._histograms},
            "timers": {k: self.get_timer_stats(k) for k in self._timers},
        }

    def reset(self):
        """重置所有指标"""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timers.clear()


# ========== 上下文管理器计时器 ==========


class Timer:
    """计时器上下文管理器"""

    def __init__(self, collector: MetricsCollector, name: str, labels: Optional[dict] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = self.collector.start_timer(self.name, self.labels)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.collector.stop_timer(self.name, self.start_time, self.labels)


# ========== 全局收集器 ==========

_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector(name: str = "openyoung") -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector(name)
    return _global_collector


def timer(name: str, labels: Optional[dict] = None):
    """计时器装饰器"""
    collector = get_metrics_collector()

    def decorator(func):
        def wrapper(*args, **kwargs):
            start = collector.start_timer(name, labels)
            try:
                return func(*args, **kwargs)
            finally:
                collector.stop_timer(name, start, labels)

        return wrapper

    return decorator


# ========== DAG 特定指标 ==========


class DAGMetrics:
    """DAG调度器指标"""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or get_metrics_collector()

    def record_task_submitted(self, dag_id: str):
        """记录任务提交"""
        self.collector.inc_counter("dag_tasks_submitted", labels={"dag_id": dag_id})

    def record_task_completed(self, dag_id: str, duration: float):
        """记录任务完成"""
        self.collector.inc_counter("dag_tasks_completed", labels={"dag_id": dag_id})
        self.collector.observe_histogram("dag_task_duration", duration, labels={"dag_id": dag_id})

    def record_task_failed(self, dag_id: str, error_type: str):
        """记录任务失败"""
        self.collector.inc_counter(
            "dag_tasks_failed", labels={"dag_id": dag_id, "error_type": error_type}
        )

    def record_retry(self, dag_id: str, task_id: str):
        """记录重试"""
        self.collector.inc_counter("dag_retries", labels={"dag_id": dag_id, "task_id": task_id})

    def get_dashboard_stats(self, dag_id: str) -> dict[str, Any]:
        """获取仪表板统计"""
        return {
            "submitted": self.collector.get_counter("dag_tasks_submitted", {"dag_id": dag_id}),
            "completed": self.collector.get_counter("dag_tasks_completed", {"dag_id": dag_id}),
            "failed": self.collector.get_counter("dag_tasks_failed", {"dag_id": dag_id}),
            "duration": self.collector.get_timer_stats("dag_task_duration", {"dag_id": dag_id}),
        }


# ========== Agent 特定指标 ==========


class AgentMetrics:
    """Agent指标"""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or get_metrics_collector()

    def record_request(self, agent_name: str):
        """记录请求"""
        self.collector.inc_counter("agent_requests_total", labels={"agent": agent_name})

    def record_success(self, agent_name: str, duration: float):
        """记录成功"""
        self.collector.inc_counter("agent_requests_success", labels={"agent": agent_name})
        self.collector.observe_histogram(
            "agent_request_duration", duration, labels={"agent": agent_name}
        )

    def record_error(self, agent_name: str, error_type: str):
        """记录错误"""
        self.collector.inc_counter(
            "agent_requests_error", labels={"agent": agent_name, "error": error_type}
        )

    def set_active(self, agent_name: str, count: int):
        """设置活跃数"""
        self.collector.set_gauge("agent_active_count", count, labels={"agent": agent_name})

    def get_stats(self, agent_name: str) -> dict[str, Any]:
        """获取统计"""
        return {
            "total": self.collector.get_counter("agent_requests_total", {"agent": agent_name}),
            "success": self.collector.get_counter("agent_requests_success", {"agent": agent_name}),
            "error": self.collector.get_counter("agent_requests_error", {"agent": agent_name}),
            "active": self.collector.get_gauge("agent_active_count", {"agent": agent_name}),
            "duration": self.collector.get_timer_stats(
                "agent_request_duration", {"agent": agent_name}
            ),
        }


# 导出
__all__ = [
    "MetricsCollector",
    "MetricType",
    "Metric",
    "Timer",
    "get_metrics_collector",
    "timer",
    "DAGMetrics",
    "AgentMetrics",
]
