"""
Agent Components - 可配置的 Agent 组件

提取 YoungAgent 中的配置和可配置部分，便于维护和扩展。
"""

from .weights import TASK_TYPE_WEIGHTS, DEFAULT_WEIGHTS, calculate_weighted_score
from .thresholds import DIMENSION_THRESHOLDS, check_threshold_violations

__all__ = [
    "TASK_TYPE_WEIGHTS",
    "DEFAULT_WEIGHTS",
    "DIMENSION_THRESHOLDS",
    "calculate_weighted_score",
    "check_threshold_violations",
]
