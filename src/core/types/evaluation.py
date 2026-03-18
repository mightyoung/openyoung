"""
Core Types - Evaluation Module

Evaluation-related type definitions

Note: Evaluation types migrated to src/hub/evaluate/ (Harness system).
This module provides lightweight stubs for backwards compatibility.
"""

from enum import Enum


class MetricType(Enum):
    """评估指标类型"""
    ACCURACY = "accuracy"
    CORRECTNESS = "correctness"
    COMPLETION = "completion"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    CLARITY = "clarity"


class EvaluationDimension(str, Enum):
    """评估维度"""
    CORRECTNESS = "correctness"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    CLARITY = "clarity"


class MetricDefinition:
    """指标定义"""
    def __init__(self, name: str, metric_type: MetricType, weight: float = 1.0):
        self.name = name
        self.metric_type = metric_type
        self.weight = weight


__all__ = [
    "EvaluationDimension",
    "MetricDefinition",
    "MetricType",
]
