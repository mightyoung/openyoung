"""
EvaluationHub - 评估中心
整合所有评估器
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .metrics import (
    MetricType,
    EvaluationDimension,
    MetricDefinition,
    BUILTIN_METRICS,
)
from .code_eval import CodeEval
from .task_eval import TaskCompletionEval
from .llm_judge import LLMJudgeEval
from .safety_eval import SafetyEval
from .indexer import IndexBuilder, EvalPackage, EvalDimension, EvalLevel


@dataclass
class EvaluationResult:
    """评估结果"""

    metric: str
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    evaluator: str = "unknown"


class EvaluationHub:
    """评估中心 - 管理和执行评估

    整合 CodeEval, TaskCompletionEval, LLMJudgeEval, SafetyEval
    提供统一的评估接口
    """

    def __init__(self, llm_client=None):
        self._metrics: Dict[str, Callable] = {}
        self._results: List[EvaluationResult] = []
        self._packages: Dict[str, Any] = {}

        # Initialize evaluators
        self._evaluators = {
            "code": CodeEval(),
            "task": TaskCompletionEval(),
            "llm_judge": LLMJudgeEval(llm_client),
            "safety": SafetyEval(),
        }

        # Initialize index builder
        self._index_builder = IndexBuilder()

    def register_metric(self, name: str, func: Callable):
        """注册评估指标"""
        self._metrics[name] = func

    def register_package(self, name: str, package: Any):
        """注册评估包"""
        self._packages[name] = package

    def register_evaluator(self, name: str, evaluator: Any):
        """注册自定义评估器"""
        self._evaluators[name] = evaluator

    async def evaluate(
        self,
        metric: str,
        input_data: Any,
        evaluator_type: str = "task",
    ) -> EvaluationResult:
        """执行评估

        Args:
            metric: 指标名称
            input_data: 输入数据
            evaluator_type: 评估器类型 (code/task/llm_judge/safety)

        Returns:
            评估结果
        """
        # 1. 尝试使用自定义指标
        if metric in self._metrics:
            func = self._metrics[metric]
            score = await func(input_data) if callable(func) else 0.0
            result = EvaluationResult(
                metric=metric,
                score=score,
                evaluator="custom",
            )
            self._results.append(result)
            return result

        # 2. 使用内置评估器
        evaluator = self._evaluators.get(evaluator_type)
        if not evaluator:
            return EvaluationResult(
                metric=metric,
                score=0.0,
                details={"error": f"Evaluator not found: {evaluator_type}"},
                evaluator="error",
            )

        try:
            result = await self._run_evaluator(
                evaluator, evaluator_type, metric, input_data
            )
            self._results.append(result)
            return result
        except Exception as e:
            return EvaluationResult(
                metric=metric,
                score=0.0,
                details={"error": str(e)},
                evaluator=evaluator_type,
            )

    async def evaluate_full(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """全面评估 - 运行所有评估器

        Args:
            input_data: 包含所有评估所需数据的字典

        Returns:
            完整的评估报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0.0,
            "dimensions": {},
            "results": [],
        }

        # Code Evaluation
        if "code" in input_data:
            code_result = await self.evaluate(
                metric="code_quality",
                input_data=input_data["code"],
                evaluator_type="code",
            )
            report["dimensions"]["correctness"] = code_result.score
            report["results"].append(code_result)

        # Task Completion Evaluation
        if "task" in input_data:
            task_result = await self.evaluate(
                metric="task_completion",
                input_data=input_data["task"],
                evaluator_type="task",
            )
            report["dimensions"]["efficacy"] = task_result.score
            report["results"].append(task_result)

        # LLM Judge Evaluation
        if "llm_judge" in input_data:
            judge_result = await self.evaluate(
                metric="quality",
                input_data=input_data["llm_judge"],
                evaluator_type="llm_judge",
            )
            report["dimensions"]["quality"] = judge_result.score
            report["results"].append(judge_result)

        # Safety Evaluation
        if "safety" in input_data:
            safety_result = await self.evaluate(
                metric="safety_score",
                input_data=input_data["safety"],
                evaluator_type="safety",
            )
            report["dimensions"]["safety"] = safety_result.score
            report["results"].append(safety_result)

        # 计算总体评分
        if report["dimensions"]:
            report["overall_score"] = sum(report["dimensions"].values()) / len(
                report["dimensions"]
            )

        return report

    async def _run_evaluator(
        self,
        evaluator: Any,
        evaluator_type: str,
        metric: str,
        input_data: Any,
    ) -> EvaluationResult:
        """运行评估器"""

        if evaluator_type == "code":
            result = await evaluator.evaluate(
                code=input_data.get("code", ""),
                expected_output=input_data.get("expected_output"),
                test_cases=input_data.get("test_cases"),
                language=input_data.get("language", "python"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("overall_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "task":
            result = await evaluator.evaluate(
                task_description=input_data.get("description", ""),
                expected_result=input_data.get("expected"),
                actual_result=input_data.get("actual"),
                execution_trace=input_data.get("trace"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("overall_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "llm_judge":
            result = await evaluator.evaluate(
                input_text=input_data.get("input", ""),
                output_text=input_data.get("output", ""),
                expected_output=input_data.get("expected"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("average_score", 0.0) / 5.0,  # 转换为 0-1
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "safety":
            result = await evaluator.evaluate(
                output_text=input_data.get("output", ""),
                input_text=input_data.get("input"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("safety_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        return EvaluationResult(
            metric=metric,
            score=0.0,
            details={"error": f"Unknown evaluator type: {evaluator_type}"},
            evaluator="error",
        )

    def list_metrics(self) -> List[str]:
        """列出所有指标"""
        return list(self._metrics.keys()) + list(BUILTIN_METRICS.keys())

    def list_packages(self) -> List[str]:
        """列出所有评估包"""
        return list(self._packages.keys())

    def list_evaluators(self) -> List[str]:
        """列出所有评估器"""
        return list(self._evaluators.keys())

    def get_results(self) -> List[EvaluationResult]:
        """获取评估结果"""
        return self._results

    def get_results_by_metric(self, metric: str) -> List[EvaluationResult]:
        """获取指定指标的结果"""
        return [r for r in self._results if r.metric == metric]

    def clear_results(self):
        """清空评估结果"""
        self._results.clear()

    def save_results(self, filepath: str) -> None:
        """保存评估结果到JSON文件"""
        import json
        from pathlib import Path
        data = []
        for r in self._results:
            data.append({
                "metric": r.metric,
                "score": r.score,
                "details": r.details,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "evaluator": r.evaluator,
            })
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_results(self, filepath: str) -> None:
        """从JSON文件加载评估结果"""
        import json
        from pathlib import Path
        if not Path(filepath).exists():
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for item in data:
            result = EvaluationResult(
                metric=item.get("metric", ""),
                score=item.get("score", 0.0),
                details=item.get("details", {}),
                timestamp=datetime.fromisoformat(item["timestamp"]) if item.get("timestamp") else datetime.now(),
                evaluator=item.get("evaluator", "unknown"),
            )
            self._results.append(result)

    def register_eval_package(self, package: EvalPackage):
        """清空评估结果"""
        self._results.clear()

    def register_eval_package(self, package: EvalPackage):
        """注册评估包到索引"""
        self._index_builder.register_package(package)

    def search_eval_packages(
        self,
        dimension: EvalDimension = None,
        level: EvalLevel = None,
        tags: List[str] = None
    ) -> List[EvalPackage]:
        """搜索评估包"""
        return self._index_builder.search(dimension, level, tags)

    def get_eval_package(self, name: str) -> EvalPackage:
        """获取评估包"""
        return self._index_builder.get_package(name)

    def list_all_eval_packages(self) -> List[EvalPackage]:
        """列出所有评估包"""
        return self._index_builder.list_all()


def create_evaluation_hub(llm_client=None) -> EvaluationHub:
    """创建 EvaluationHub 实例"""
    return EvaluationHub(llm_client)
