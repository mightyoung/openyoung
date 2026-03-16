"""
Evaluation Metrics Tests
"""

import pytest
from src.evaluation.metrics import (
    MetricType,
    EvaluationDimension,
    MetricDefinition,
    BUILTIN_METRICS,
    get_metrics_by_type,
    get_metrics_by_dimension,
)


class TestMetricType:
    """Test MetricType enum"""

    def test_metric_types(self):
        assert MetricType.COST.value == "cost"
        assert MetricType.LATENCY.value == "latency"
        assert MetricType.EFFICACY.value == "efficacy"
        assert MetricType.EFFICIENCY.value == "efficiency"
        assert MetricType.ASSURANCE.value == "assurance"
        assert MetricType.RELIABILITY.value == "reliability"
        assert MetricType.QUALITY.value == "quality"


class TestEvaluationDimension:
    """Test EvaluationDimension enum"""

    def test_evaluation_dimensions(self):
        assert EvaluationDimension.CORRECTNESS.value == "correctness"
        assert EvaluationDimension.EFFICIENCY.value == "efficiency"
        assert EvaluationDimension.SAFETY.value == "safety"
        assert EvaluationDimension.USER_EXPERIENCE.value == "ux"
        assert EvaluationDimension.ROBUSTNESS.value == "robustness"


class TestMetricDefinition:
    """Test MetricDefinition dataclass"""

    def test_metric_definition_creation(self):
        metric = MetricDefinition(
            name="test_metric",
            type=MetricType.EFFICACY,
            dimension=EvaluationDimension.CORRECTNESS,
            description="Test metric",
            min_value=0.0,
            max_value=1.0,
            unit="score",
            higher_is_better=True,
        )
        assert metric.name == "test_metric"
        assert metric.type == MetricType.EFFICACY
        assert metric.dimension == EvaluationDimension.CORRECTNESS
        assert metric.higher_is_better is True

    def test_metric_definition_defaults(self):
        metric = MetricDefinition(
            name="default_metric",
            type=MetricType.EFFICACY,
            dimension=EvaluationDimension.CORRECTNESS,
            description="Test",
        )
        assert metric.min_value == 0.0
        assert metric.max_value == 1.0
        assert metric.unit == "score"
        assert metric.higher_is_better is True


class TestBuiltinMetrics:
    """Test BUILTIN_METRICS"""

    def test_builtin_metrics_not_empty(self):
        assert len(BUILTIN_METRICS) > 0

    def test_builtin_metrics_have_names(self):
        for name, metric in BUILTIN_METRICS.items():
            assert metric.name == name

    def test_builtin_metrics_have_types(self):
        for name, metric in BUILTIN_METRICS.items():
            assert isinstance(metric.type, MetricType)

    def test_builtin_metrics_have_dimensions(self):
        for name, metric in BUILTIN_METRICS.items():
            assert isinstance(metric.dimension, EvaluationDimension)

    def test_builtin_metrics_have_required_fields(self):
        """All metrics should have required fields"""
        for name, metric in BUILTIN_METRICS.items():
            assert metric.name is not None
            assert metric.type is not None
            assert metric.dimension is not None
            assert metric.description is not None
            assert metric.min_value is not None
            assert metric.max_value is not None


class TestMetricFunctions:
    """Test metric helper functions"""

    def test_get_metrics_by_type_efficacy(self):
        metrics = get_metrics_by_type(MetricType.EFFICACY)
        assert len(metrics) > 0
        for metric in metrics:
            assert metric.type == MetricType.EFFICACY

    def test_get_metrics_by_type_latency(self):
        metrics = get_metrics_by_type(MetricType.LATENCY)
        assert len(metrics) > 0
        for metric in metrics:
            assert metric.type == MetricType.LATENCY

    def test_get_metrics_by_dimension_correctness(self):
        metrics = get_metrics_by_dimension(EvaluationDimension.CORRECTNESS)
        assert len(metrics) > 0
        for metric in metrics:
            assert metric.dimension == EvaluationDimension.CORRECTNESS

    def test_get_metrics_by_dimension_efficiency(self):
        metrics = get_metrics_by_dimension(EvaluationDimension.EFFICIENCY)
        assert len(metrics) > 0
        for metric in metrics:
            assert metric.dimension == EvaluationDimension.EFFICIENCY
