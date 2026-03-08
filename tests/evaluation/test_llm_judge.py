"""
LLMJudge and Metrics Tests
"""

import pytest

from src.evaluation.llm_judge import JudgeScore, LLMJudgeEval
from src.evaluation.metrics import MetricDefinition, MetricType, EvaluationDimension


class TestJudgeScore:
    """Test JudgeScore dataclass"""

    def test_judge_score_creation(self):
        score = JudgeScore(
            dimension="correctness",
            score=4.5,
            reasoning="Output is correct and complete"
        )
        assert score.dimension == "correctness"
        assert score.score == 4.5
        assert "correct" in score.reasoning.lower()


class TestLLMJudgeEval:
    """Test LLMJudgeEval"""

    def test_judge_initialization(self):
        judge = LLMJudgeEval()
        assert judge is not None
        assert hasattr(judge, "DEFAULT_RUBRIC")
        assert "correctness" in judge.DEFAULT_RUBRIC
        assert "efficiency" in judge.DEFAULT_RUBRIC

    def test_rubric_structure(self):
        """Test rubric has required fields"""
        rubric = LLMJudgeEval.DEFAULT_RUBRIC
        for dimension, config in rubric.items():
            assert "name" in config
            assert "description" in config
            assert "score_mapping" in config

    @pytest.mark.asyncio
    async def test_evaluate_without_llm(self):
        """Test evaluation without LLM returns mock result"""
        judge = LLMJudgeEval()
        result = await judge.evaluate(
            input_text="Write a function",
            output_text="def hello(): return 'world'",
        )
        assert "scores" in result or "error" in result

    def test_set_rubric(self):
        """Test custom rubric setting"""
        judge = LLMJudgeEval()
        custom_rubric = {
            "test_dim": {
                "name": "Test",
                "description": "Test dimension",
                "score_mapping": {1: "bad", 5: "good"}
            }
        }
        judge.set_rubric(custom_rubric)
        rubric = judge.get_rubric()
        assert "test_dim" in rubric

    def test_get_rubric(self):
        """Test rubric retrieval"""
        judge = LLMJudgeEval()
        rubric = judge.get_rubric()
        assert "correctness" in rubric


class TestMetrics:
    """Test metrics module"""

    def test_metric_type_enum(self):
        assert MetricType.EFFICACY.value == "efficacy"
        assert MetricType.LATENCY.value == "latency"

    def test_evaluation_dimension_enum(self):
        assert EvaluationDimension.CORRECTNESS.value == "correctness"
        assert EvaluationDimension.EFFICIENCY.value == "efficiency"

    def test_metric_definition_creation(self):
        metric = MetricDefinition(
            name="test_metric",
            type=MetricType.EFFICACY,
            dimension=EvaluationDimension.CORRECTNESS,
            description="Test metric"
        )
        assert metric.name == "test_metric"
        assert metric.type == MetricType.EFFICACY
