"""
Scheduling Module - 任务调度模块

包含:
- DAG 调度器
- 失败传播器
- 重试策略

参考 Airflow, Prefect, Dagster 最佳实践
"""

from .dag_scheduler import (
    DAGScheduler,
    FailurePropagation,
    TaskNode,
    TaskResult,
)
from .failure_propagator import (
    FailurePropagator,
    FailureType,
)
from .retry_policy import (
    RetryableError,
    RetryPolicy,
    RetryStrategy,
)

__all__ = [
    "DAGScheduler",
    "TaskNode",
    "TaskResult",
    "FailurePropagation",
    "RetryPolicy",
    "RetryStrategy",
    "RetryableError",
    "FailurePropagator",
    "FailureType",
]
