"""
Core Types - Evaluation Module

Evaluation-related type definitions

Note: Core evaluation types are defined in src/evaluation/metrics.py
This module provides re-exports for convenience and type consistency.
"""

# Re-export from evaluation.metrics for centralized access
from src.evaluation.metrics import (
    EvaluationDimension,
    MetricDefinition,
    MetricType,
)

__all__ = [
    "EvaluationDimension",
    "MetricDefinition",
    "MetricType",
]
