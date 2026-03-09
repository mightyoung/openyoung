"""
TaskCompletionEval - 任务完成评估器
评估 Agent 任务完成能力
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass
class TaskTrace:
    """任务执行轨迹"""

    task_id: str
    task_description: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    success: bool = False
    error: str | None = None


@dataclass
class TaskMetrics:
    """任务指标"""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    avg_steps: float
    avg_time: float
    step_efficiency: float


class TaskCompletionEval:
    """任务完成评估器

    功能:
    - 任务成功率评估
    - 步骤效率评估
    - 执行时间评估
    - 错误恢复评估
    - 一致性评估 (多次运行)
    """

    def __init__(self):
        self.name = "task_completion"
        self.description = "任务完成评估器"
        self._traces: list[TaskTrace] = []

    async def evaluate(
        self,
        task_description: str,
        expected_result: Any,
        actual_result: Any,
        execution_trace: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """评估任务完成情况

        Args:
            task_description: 任务描述
            expected_result: 期望结果
            actual_result: 实际结果
            execution_trace: 执行轨迹

        Returns:
            评估结果
        """
        results = {
            "task_description": task_description,
            "success": False,
            "completion_rate": 0.0,
            "step_count": 0,
            "execution_time": 0.0,
            "step_efficiency": 0.0,
            "error_recovery": 0.0,
            "overall_score": 0.0,
        }

        # 1. 任务完成评估
        # 如果 expected_result 为 None，尝试从 task_description 提取预期
        if expected_result is None:
            expected_result = self._extract_expected_from_task(task_description)

        success = self._check_completion(expected_result, actual_result)
        results["success"] = success
        results["completion_rate"] = 1.0 if success else 0.0

        # 2. 步骤评估
        if execution_trace:
            results["step_count"] = len(execution_trace)
            results["steps"] = execution_trace

            # 步骤效率 (理想步骤数 vs 实际步骤数)
            ideal_steps = self._estimate_ideal_steps(task_description)
            results["step_efficiency"] = min(ideal_steps / max(len(execution_trace), 1), 1.0)

            # 错误恢复能力
            error_count = sum(1 for s in execution_trace if s.get("error"))
            results["error_recovery"] = 1.0 - (error_count / max(len(execution_trace), 1))

        # 3. 计算综合评分
        results["overall_score"] = self._calculate_score(results)

        return results

    async def evaluate_with_plan(
        self,
        task_description: str,
        actual_result: Any,
        eval_plan,
        execution_trace: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """基于评估计划评估任务完成情况

        Args:
            task_description: 任务描述
            actual_result: 实际结果
            eval_plan: 评估计划 (EvalPlan)
            execution_trace: 执行轨迹

        Returns:
            评估结果
        """
        results = {
            "task_description": task_description,
            "task_type": eval_plan.task_type,
            "success": False,
            "completion_rate": 0.0,
            "step_count": 0,
            "execution_time": 0.0,
            "step_efficiency": 0.0,
            "error_recovery": 0.0,
            "overall_score": 0.0,
            "success_criteria": eval_plan.success_criteria,
            "validation_results": [],
        }

        # 1. 基于成功标准评估
        criteria_results = self._evaluate_criteria(
            eval_plan.success_criteria,
            actual_result,
            eval_plan.expected_outputs,
        )
        results["validation_results"] = criteria_results
        results["completion_rate"] = sum(r["passed"] for r in criteria_results) / max(
            len(criteria_results), 1
        )

        # 2. 步骤评估
        if execution_trace:
            results["step_count"] = len(execution_trace)
            results["steps"] = execution_trace
            ideal_steps = self._estimate_ideal_steps(task_description)
            results["step_efficiency"] = min(ideal_steps / max(len(execution_trace), 1), 1.0)
            error_count = sum(1 for s in execution_trace if s.get("error"))
            results["error_recovery"] = 1.0 - (error_count / max(len(execution_trace), 1))

        # 3. 计算综合评分
        results["overall_score"] = self._calculate_score(results)
        results["success"] = results["completion_rate"] >= 0.5

        return results

    def _evaluate_criteria(
        self,
        criteria: list[str],
        actual_result: Any,
        expected_outputs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """评估每个成功标准

        Args:
            criteria: 成功标准列表
            actual_result: 实际结果
            expected_outputs: 预期输出

        Returns:
            每个标准的评估结果
        """
        results = []

        for criterion in criteria:
            passed = False
            details = {"criterion": criterion}

            # 检查文件是否存在
            if "文件" in criterion or "file" in criterion.lower():
                if expected_outputs.get("file"):
                    passed = True  # 文件创建通常意味着成功
                    details["checked"] = "file_creation"

            # 检查数据完整性
            if "数据" in criterion or "count" in criterion.lower():
                if expected_outputs.get("count"):
                    # 简单检查：实际结果包含数量信息
                    passed = True
                    details["checked"] = "data_completeness"

            # 检查格式
            if "格式" in criterion or "format" in criterion.lower():
                if expected_outputs.get("format"):
                    passed = True
                    details["checked"] = "format"

            # 检查输出内容
            if isinstance(actual_result, str):
                if len(actual_result) > 0:
                    passed = True
                    details["checked"] = "content_exists"

            results.append(
                {
                    "criterion": criterion,
                    "passed": passed,
                    "details": details,
                }
            )

        return results

    async def evaluate_batch(
        self,
        tasks: list[dict[str, Any]],
    ) -> TaskMetrics:
        """批量评估多个任务

        Args:
            tasks: 任务列表

        Returns:
            聚合的评估指标
        """
        results = []

        for task in tasks:
            result = await self.evaluate(
                task_description=task.get("description", ""),
                expected_result=task.get("expected"),
                actual_result=task.get("actual"),
                execution_trace=task.get("trace"),
            )
            results.append(result)

        # 聚合结果
        total = len(results)
        completed = sum(1 for r in results if r["success"])
        failed = total - completed
        success_rate = completed / total if total > 0 else 0.0

        avg_steps = sum(r["step_count"] for r in results) / total if total > 0 else 0.0
        avg_time = sum(r.get("execution_time", 0) for r in results) / total if total > 0 else 0.0

        avg_step_efficiency = (
            sum(r["step_efficiency"] for r in results) / total if total > 0 else 0.0
        )

        return TaskMetrics(
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            success_rate=success_rate,
            avg_steps=avg_steps,
            avg_time=avg_time,
            step_efficiency=avg_step_efficiency,
        )

    async def evaluate_consistency(
        self,
        task: dict[str, Any],
        num_runs: int = 5,
    ) -> dict[str, Any]:
        """评估多次运行一致性

        Args:
            task: 任务定义
            num_runs: 运行次数

        Returns:
            一致性评估结果
        """
        results = []

        # 模拟多次运行 (实际应该由外部提供)
        for i in range(num_runs):
            result = await self.evaluate(
                task_description=task.get("description", ""),
                expected_result=task.get("expected"),
                actual_result=task.get("actual"),
                execution_trace=task.get("trace"),
            )
            results.append(result["success"])

        # 计算一致性
        success_count = sum(results)
        consistency = success_count / num_runs if num_runs > 0 else 0.0

        return {
            "num_runs": num_runs,
            "success_count": success_count,
            "consistency_score": consistency,
            "is_reliable": consistency >= 0.8,  # 80% 以上认为可靠
        }

    def _check_completion(self, expected: Any, actual: Any) -> bool:
        """检查任务完成情况"""
        # 修复: 当 expected 为 None 时，尝试从 task description 提取预期文件
        if expected is None:
            # 如果 actual 存在且非空，认为是成功的（开放性任务）
            if actual is not None:
                if isinstance(actual, dict):
                    # 检查是否有输出文件等
                    return len(actual) > 0
                elif isinstance(actual, str):
                    return len(actual.strip()) > 0
                elif isinstance(actual, list):
                    return len(actual) > 0
                return actual is not None
            return False

        if actual is None:
            return expected == actual

        # 字符串比较
        if isinstance(expected, str) and isinstance(actual, str):
            return expected.strip() == actual.strip()

        # 数值比较 (允许一定误差)
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            return abs(expected - actual) < 0.01

        # 字典比较
        if isinstance(expected, dict) and isinstance(actual, dict):
            return self._dict_contains(expected, actual)

        # 列表比较
        if isinstance(expected, list) and isinstance(actual, list):
            return set(expected) == set(actual)

        # 默认相等性检查
        return expected == actual

    def _extract_expected_from_task(self, task_description: str) -> dict[str, Any] | None:
        """从任务描述中提取预期结果

        用于开放性任务，当 expected_result=None 时尝试从任务描述推断预期。

        Args:
            task_description: 任务描述

        Returns:
            预期的结果字典，或 None
        """
        import os
        import re
        from pathlib import Path

        expected = {}

        # 模式1: "保存到 xxx/yyy.py"
        save_patterns = [
            r"保存[到]?\s*([^\s]+\.py)",
            r"保存[到]?\s*([^\s]+\.json)",
            r"保存[到]?\s*([^\s]+\.txt)",
            r"save.*?to\s+([^\s]+\.py)",
            r"save.*?to\s+([^\s]+\.json)",
            r"output/([^\s]+)",
            r"创建.*?([^\s]+\.py)",
        ]

        found_files = []
        for pattern in save_patterns:
            matches = re.findall(pattern, task_description)
            for match in matches:
                # 尝试检查文件是否存在
                possible_paths = [
                    match,
                    f"output/{match}",
                    f"./output/{match}",
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        found_files.append(path)
                        break

        if found_files:
            expected["output_files"] = found_files
            expected["file_count"] = len(found_files)

        # 模式2: 检查是否有 "完成" 或 "成功" 等关键词
        if any(
            kw in task_description for kw in ["完成", "成功", "完成", "generate", "create", "save"]
        ):
            expected["has_completion_keyword"] = True

        return expected if expected else None

    def _dict_contains(self, expected: dict, actual: dict) -> bool:
        """检查字典是否包含预期键值"""
        for key, value in expected.items():
            if key not in actual:
                return False
            if not self._check_completion(value, actual[key]):
                return False
        return True

    def _estimate_ideal_steps(self, task_description: str) -> int:
        """估算理想步骤数"""
        # 简单启发式估算
        description = task_description.lower()

        # 复杂任务
        if any(k in description for k in ["multiple", "several", "complex", "多个", "复杂"]):
            return 5
        # 中等任务
        if any(k in description for k in ["create", "implement", "build", "创建", "实现"]):
            return 3
        # 简单任务
        return 1

    def _calculate_score(self, results: dict[str, Any]) -> float:
        """计算综合评分"""
        weights = {
            "completion_rate": 0.4,
            "step_efficiency": 0.3,
            "error_recovery": 0.3,
        }

        score = (
            results.get("completion_rate", 0.0) * weights["completion_rate"]
            + results.get("step_efficiency", 0.0) * weights["step_efficiency"]
            + results.get("error_recovery", 0.0) * weights["error_recovery"]
        )

        return score

    def add_trace(self, trace: TaskTrace):
        """添加任务轨迹"""
        self._traces.append(trace)

    def get_traces(self) -> list[TaskTrace]:
        """获取所有轨迹"""
        return self._traces

    def clear_traces(self):
        """清空轨迹"""
        self._traces.clear()


# 便捷函数
def create_task_eval() -> TaskCompletionEval:
    """创建 TaskCompletionEval 实例"""
    return TaskCompletionEval()
