"""
Evaluation Module Tests
"""

import pytest

from src.evaluation.code_eval import CodeEval
from src.evaluation.hub import EvaluationHub, EvaluationResult
from src.evaluation.safety_eval import SafetyEval
from src.evaluation.task_eval import TaskCompletionEval


class TestEvaluationHub:
    def test_hub_creation(self):
        hub = EvaluationHub()
        assert hub is not None
        assert "code" in hub._evaluators
        assert "task" in hub._evaluators
        assert "safety" in hub._evaluators

    def test_register_metric(self):
        hub = EvaluationHub()

        async def custom_metric(data):
            return 0.85

        hub.register_metric("custom", custom_metric)
        assert "custom" in hub._metrics

    def test_register_evaluator(self):
        hub = EvaluationHub()

        class CustomEval:
            pass

        hub.register_evaluator("custom", CustomEval())
        assert "custom" in hub._evaluators


class TestTaskCompletionEval:
    @pytest.mark.asyncio
    async def test_evaluate_with_expected_result(self):
        eval = TaskCompletionEval()
        result = await eval.evaluate(
            task_description="Write hello world",
            expected_result="hello world",
            actual_result="hello world",
        )
        assert result["success"] is True
        assert result["completion_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_evaluate_no_match(self):
        eval = TaskCompletionEval()
        result = await eval.evaluate(
            task_description="Write hello world",
            expected_result="hello world",
            actual_result="goodbye",
        )
        assert result["completion_rate"] == 0.0


class TestCodeEval:
    def test_code_eval_creation(self):
        eval = CodeEval()
        assert eval is not None

    @pytest.mark.asyncio
    async def test_evaluate_valid_code(self):
        eval = CodeEval()
        result = await eval.evaluate(
            code="print('hello')",
            expected_output="hello",
            language="python",
        )
        assert "syntax_valid" in result

    @pytest.mark.asyncio
    async def test_evaluate_invalid_code(self):
        eval = CodeEval()
        result = await eval.evaluate(
            code="print('hello",  # Missing closing quote
            language="python",
        )
        assert result["syntax_valid"] is False


class TestSafetyEval:
    def test_safety_eval_creation(self):
        eval = SafetyEval()
        assert eval is not None
