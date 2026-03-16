"""
评估记录模型 - Phase 1 数据基础设施

提供 EvaluationRecord 和 EvaluationDimension 作为评估平台的数据模型
支持多维度评估、迭代跟踪、趋势分析
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EvaluationStatus(str, Enum):
    """评估状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


class EvaluatorType(str, Enum):
    """评估器类型"""
    CODE = "code"
    TASK = "task"
    LLM_JUDGE = "llm_judge"
    SAFETY = "safety"


@dataclass
class EvaluationDimension:
    """评估维度

    支持多维度评估，如 correctness, safety, efficiency, robustness
    """

    name: str  # 维度名称: correctness, safety, efficiency, robustness
    score: float = 0.0  # 分数 0.0-1.0
    threshold: float = 0.7  # 通过阈值
    passed: bool = False  # 是否通过
    reasoning: str = ""  # 推理过程
    evidence: list[str] = field(default_factory=list)  # 证据列表
    weight: float = 1.0  # 权重

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "score": self.score,
            "threshold": self.threshold,
            "passed": self.passed,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationDimension":
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            score=data.get("score", 0.0),
            threshold=data.get("threshold", 0.7),
            passed=data.get("passed", False),
            reasoning=data.get("reasoning", ""),
            evidence=data.get("evidence", []),
            weight=data.get("weight", 1.0),
        )


@dataclass
class EvaluationRecord:
    """评估记录

    完整的评估结果，包括多维度评估、迭代信息、反馈
    """

    # 基础标识
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = ""  # 关联的执行记录ID

    # 评估维度
    dimensions: list[EvaluationDimension] = field(default_factory=list)

    # 综合评分
    overall_score: float = 0.0
    passed: bool = False

    # 评估器信息
    evaluator_type: EvaluatorType = EvaluatorType.LLM_JUDGE
    feedback: str = ""  # 评估反馈/改进建议

    # 迭代信息
    iteration: int = 0
    max_iterations: int = 5

    # 时间
    evaluated_at: datetime = field(default_factory=datetime.now)

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    # 标签
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "execution_id": self.execution_id,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall_score": self.overall_score,
            "passed": self.passed,
            "evaluator_type": self.evaluator_type.value,
            "feedback": self.feedback,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationRecord":
        """从字典创建"""
        # 处理时间字段
        evaluated_at = data.get("evaluated_at")
        if evaluated_at and isinstance(evaluated_at, str):
            evaluated_at = datetime.fromisoformat(evaluated_at)

        # 处理评估维度
        dimensions = []
        for d in data.get("dimensions", []):
            if isinstance(d, dict):
                dimensions.append(EvaluationDimension.from_dict(d))
            elif isinstance(d, EvaluationDimension):
                dimensions.append(d)

        # 处理评估器类型
        evaluator_type = data.get("evaluator_type", "llm_judge")
        if isinstance(evaluator_type, str):
            evaluator_type = EvaluatorType(evaluator_type)

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            execution_id=data.get("execution_id", ""),
            dimensions=dimensions,
            overall_score=data.get("overall_score", 0.0),
            passed=data.get("passed", False),
            evaluator_type=evaluator_type,
            feedback=data.get("feedback", ""),
            iteration=data.get("iteration", 0),
            max_iterations=data.get("max_iterations", 5),
            evaluated_at=evaluated_at or datetime.now(),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

    def calculate_overall_score(self) -> float:
        """计算综合评分（加权平均）"""
        if not self.dimensions:
            return 0.0

        total_weight = sum(d.weight for d in self.dimensions)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(d.score * d.weight for d in self.dimensions)
        return weighted_sum / total_weight

    def check_passed(self, default_threshold: float = 0.7) -> bool:
        """检查是否通过（所有维度都通过）"""
        if not self.dimensions:
            return False

        # 使用每个维度的阈值
        return all(
            d.passed or d.score >= (d.threshold or default_threshold)
            for d in self.dimensions
        )

    def update(self):
        """更新综合评分和通过状态"""
        self.overall_score = self.calculate_overall_score()
        self.passed = self.check_passed()

    def add_dimension(self, dimension: EvaluationDimension):
        """添加评估维度"""
        self.dimensions.append(dimension)
        self.update()

    def get_dimension(self, name: str) -> EvaluationDimension | None:
        """获取指定维度"""
        for d in self.dimensions:
            if d.name == name:
                return d
        return None


@dataclass
class EvaluationQuery:
    """评估查询条件"""

    execution_id: str | None = None
    agent_name: str | None = None
    status: EvaluationStatus | None = None
    passed: bool | None = None
    min_score: float | None = None
    max_score: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    tags: list[str] = field(default_factory=list)
    limit: int = 50
    offset: int = 0


@dataclass
class EvaluationSummary:
    """评估摘要"""

    total_count: int
    passed_count: int
    failed_count: int
    average_score: float
    median_score: float
    pass_rate: float

    # 按维度统计
    dimension_stats: dict[str, dict[str, float]] = field(default_factory=dict)

    # 趋势
    trend: str = "stable"  # up, down, stable
    trend_delta: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_count": self.total_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "average_score": self.average_score,
            "median_score": self.median_score,
            "pass_rate": self.pass_rate,
            "dimension_stats": self.dimension_stats,
            "trend": self.trend,
            "trend_delta": self.trend_delta,
        }
