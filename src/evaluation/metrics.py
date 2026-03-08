"""
Evaluation Metrics - 评估指标定义
基于 CLEAR 框架: Cost, Latency, Efficacy, Assurance, Reliability
"""

from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    """指标类型"""

    COST = "cost"
    LATENCY = "latency"
    EFFICACY = "efficacy"
    EFFICIENCY = "efficiency"
    ASSURANCE = "assurance"
    RELIABILITY = "reliability"
    QUALITY = "quality"


class EvaluationDimension(Enum):
    """评估维度"""

    CORRECTNESS = "correctness"
    EFFICIENCY = "efficiency"
    SAFETY = "safety"
    USER_EXPERIENCE = "ux"
    ROBUSTNESS = "robustness"


@dataclass
class MetricDefinition:
    """指标定义"""

    name: str
    type: MetricType
    dimension: EvaluationDimension
    description: str
    min_value: float = 0.0
    max_value: float = 1.0
    unit: str = "score"
    higher_is_better: bool = True


# === 内置指标定义 ===

BUILTIN_METRICS = {
    # 功效指标
    "success_rate": MetricDefinition(
        name="success_rate",
        type=MetricType.EFFICACY,
        dimension=EvaluationDimension.CORRECTNESS,
        description="任务完成成功率",
        min_value=0.0,
        max_value=1.0,
        unit="percentage",
        higher_is_better=True,
    ),
    "task_completion": MetricDefinition(
        name="task_completion",
        type=MetricType.EFFICACY,
        dimension=EvaluationDimension.CORRECTNESS,
        description="任务完成度",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
    # 效率指标
    "token_efficiency": MetricDefinition(
        name="token_efficiency",
        type=MetricType.EFFICIENCY,
        dimension=EvaluationDimension.EFFICIENCY,
        description="Token 使用效率",
        min_value=0.0,
        max_value=float("inf"),
        unit="tokens",
        higher_is_better=False,
    ),
    "step_efficiency": MetricDefinition(
        name="step_efficiency",
        type=MetricType.EFFICIENCY,
        dimension=EvaluationDimension.EFFICIENCY,
        description="步骤效率",
        min_value=0.0,
        max_value=float("inf"),
        unit="steps",
        higher_is_better=False,
    ),
    "latency_p50": MetricDefinition(
        name="latency_p50",
        type=MetricType.LATENCY,
        dimension=EvaluationDimension.EFFICIENCY,
        description="P50 延迟",
        min_value=0.0,
        max_value=float("inf"),
        unit="ms",
        higher_is_better=False,
    ),
    "latency_p95": MetricDefinition(
        name="latency_p95",
        type=MetricType.LATENCY,
        dimension=EvaluationDimension.EFFICIENCY,
        description="P95 延迟",
        min_value=0.0,
        max_value=float("inf"),
        unit="ms",
        higher_is_better=False,
    ),
    # 可靠性指标
    "consistency": MetricDefinition(
        name="consistency",
        type=MetricType.RELIABILITY,
        dimension=EvaluationDimension.ROBUSTNESS,
        description="多次运行一致性",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
    "error_recovery": MetricDefinition(
        name="error_recovery",
        type=MetricType.RELIABILITY,
        dimension=EvaluationDimension.ROBUSTNESS,
        description="错误恢复能力",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
    # 安全指标
    "safety_score": MetricDefinition(
        name="safety_score",
        type=MetricType.ASSURANCE,
        dimension=EvaluationDimension.SAFETY,
        description="安全评分",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
    "harmful_content_rate": MetricDefinition(
        name="harmful_content_rate",
        type=MetricType.ASSURANCE,
        dimension=EvaluationDimension.SAFETY,
        description="有害内容比例",
        min_value=0.0,
        max_value=1.0,
        unit="percentage",
        higher_is_better=False,
    ),
    # 质量指标
    "code_quality": MetricDefinition(
        name="code_quality",
        type=MetricType.QUALITY,
        dimension=EvaluationDimension.CORRECTNESS,
        description="代码质量评分",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
    "instruction_following": MetricDefinition(
        name="instruction_following",
        type=MetricType.QUALITY,
        dimension=EvaluationDimension.CORRECTNESS,
        description="指令遵循度",
        min_value=0.0,
        max_value=1.0,
        unit="score",
        higher_is_better=True,
    ),
}


def get_metrics_by_type(metric_type: MetricType) -> list[MetricDefinition]:
    """获取指定类型的指标"""
    return [m for m in BUILTIN_METRICS.values() if m.type == metric_type]


def get_metrics_by_dimension(dimension: EvaluationDimension) -> list[MetricDefinition]:
    """获取指定维度的指标"""
    return [m for m in BUILTIN_METRICS.values() if m.dimension == dimension]
