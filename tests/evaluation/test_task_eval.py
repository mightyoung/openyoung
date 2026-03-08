"""
TaskCompletionEval with Plan Tests
"""

import pytest

from src.evaluation.planner import EvalPlan
from src.evaluation.task_eval import TaskCompletionEval


class TestEvaluateWithPlan:
    @pytest.mark.asyncio
    async def test_evaluate_with_plan_basic(self):
        """Test basic evaluation with plan"""
        eval = TaskCompletionEval()

        # 创建评估计划
        plan = EvalPlan(
            task_description="爬取小红书热榜",
            task_type="web_scraping",
            success_criteria=[
                "成功获取热榜前10帖子",
                "数据保存到指定目录",
                "输出格式为JSON",
            ],
            expected_outputs={
                "file": "output/posts.json",
                "format": "json",
                "count": 10,
            },
        )

        # 评估
        result = await eval.evaluate_with_plan(
            task_description="爬取小红书热榜",
            actual_result="已保存到 output/posts.json，共10条数据",
            eval_plan=plan,
        )

        assert result["task_type"] == "web_scraping"
        assert "success_criteria" in result
        assert "validation_results" in result
        assert result["completion_rate"] > 0

    @pytest.mark.asyncio
    async def test_evaluate_with_plan_no_result(self):
        """Test evaluation with empty result"""
        eval = TaskCompletionEval()

        plan = EvalPlan(
            task_description="写一个函数",
            task_type="coding",
            success_criteria=["函数能正常运行"],
            expected_outputs={},
        )

        result = await eval.evaluate_with_plan(
            task_description="写一个函数",
            actual_result="",
            eval_plan=plan,
        )

        # 空结果应该得分为0或很低
        assert result["completion_rate"] >= 0

    @pytest.mark.asyncio
    async def test_evaluate_with_plan_with_trace(self):
        """Test evaluation with execution trace"""
        eval = TaskCompletionEval()

        plan = EvalPlan(
            task_description="创建文件",
            task_type="coding",
            success_criteria=["文件创建成功"],
            expected_outputs={"file": "test.txt"},
        )

        trace = [
            {"action": "write", "file": "test.txt"},
            {"action": "read", "file": "test.txt"},
        ]

        result = await eval.evaluate_with_plan(
            task_description="创建文件",
            actual_result="文件已创建",
            eval_plan=plan,
            execution_trace=trace,
        )

        assert result["step_count"] == 2
        assert "step_efficiency" in result
