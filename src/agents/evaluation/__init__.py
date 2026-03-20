"""
Evaluation Package - Agent 评估相关模块

包含:
- harness_eval: Harness 评估接口
- metrics: 评估指标（从 hub.evaluate 导入）
"""

# Re-export from hub.evaluate
from src.hub.evaluate.harness import EvaluationHarness
from src.hub.evaluate.metrics import (
    EvalMetrics,
    TrialMetrics,
    compute_pass_at_k,
    compute_pass_rate,
)

__all__ = [
    "EvaluationHarness",
    "TrialMetrics",
    "EvalMetrics",
    "compute_pass_at_k",
    "compute_pass_rate",
]
