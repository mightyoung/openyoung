"""
TaskCompletionEval - 任务完成评估器
评估 Agent 任务完成能力
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio


@dataclass
class TaskTrace:
    """任务执行轨迹"""

    task_id: str
    task_description: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None


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
        self._traces: List[TaskTrace] = []

    async def evaluate(
        self,
        task_description: str,
        expected_result: Any,
        actual_result: Any,
        execution_trace: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
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
        success = self._check_completion(expected_result, actual_result)
        results["success"] = success
        results["completion_rate"] = 1.0 if success else 0.0

        # 2. 步骤评估
        if execution_trace:
            results["step_count"] = len(execution_trace)
            results["steps"] = execution_trace

            # 步骤效率 (理想步骤数 vs 实际步骤数)
            ideal_steps = self._estimate_ideal_steps(task_description)
            results["step_efficiency"] = min(
                ideal_steps / max(len(execution_trace), 1), 1.0
            )

            # 错误恢复能力
            error_count = sum(1 for s in execution_trace if s.get("error"))
            results["error_recovery"] = 1.0 - (
                error_count / max(len(execution_trace), 1)
            )

        # 3. 计算综合评分
        results["overall_score"] = self._calculate_score(results)

        return results

    async def evaluate_batch(
        self,
        tasks: List[Dict[str, Any]],
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
        avg_time = (
            sum(r.get("execution_time", 0) for r in results) / total
            if total > 0
            else 0.0
        )

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
        task: Dict[str, Any],
        num_runs: int = 5,
    ) -> Dict[str, Any]:
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
        if expected is None or actual is None:
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
        if any(
            k in description for k in ["multiple", "several", "complex", "多个", "复杂"]
        ):
            return 5
        # 中等任务
        if any(
            k in description for k in ["create", "implement", "build", "创建", "实现"]
        ):
            return 3
        # 简单任务
        return 1

    def _calculate_score(self, results: Dict[str, Any]) -> float:
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

    def get_traces(self) -> List[TaskTrace]:
        """获取所有轨迹"""
        return self._traces

    def clear_traces(self):
        """清空轨迹"""
        self._traces.clear()


# 便捷函数
def create_task_eval() -> TaskCompletionEval:
    """创建 TaskCompletionEval 实例"""
    return TaskCompletionEval()
