"""
EvalSubAgent - 评估子代理
负责从 Hub 加载包、并行执行评估器、聚合结果
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from .indexer import EvalDimension, EvalLevel


class EvalResult:
    """单项评估结果"""

    def __init__(
        self,
        evaluator_name: str,
        dimension: str,
        level: str,
        score: float,
        passed: bool,
        feedback: str,
        execution_time_ms: int = 0,
        error: str | None = None,
    ):
        self.evaluator_name = evaluator_name
        self.dimension = dimension
        self.level = level
        self.score = score  # 0-1
        self.passed = passed
        self.feedback = feedback
        self.execution_time_ms = execution_time_ms
        self.error = error

    def to_dict(self) -> dict:
        return {
            "evaluator_name": self.evaluator_name,
            "dimension": self.dimension,
            "level": self.level,
            "score": self.score,
            "passed": self.passed,
            "feedback": self.feedback,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
        }


class EvaluationReport:
    """评估报告"""

    def __init__(
        self,
        request_id: str,
        overall_score: float,
        passed: bool,
        blocking_failed: bool,
        results: list[EvalResult],
        aggregated_at: str,
        total_evaluators: int,
        successful_evaluators: int,
        failed_evaluators: int,
        total_time_ms: int = 0,
    ):
        self.request_id = request_id
        self.overall_score = overall_score
        self.passed = passed
        self.blocking_failed = blocking_failed
        self.results = results
        self.aggregated_at = aggregated_at
        self.total_evaluators = total_evaluators
        self.successful_evaluators = successful_evaluators
        self.failed_evaluators = failed_evaluators
        self.total_time_ms = total_time_ms

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "blocking_failed": self.blocking_failed,
            "results": [r.to_dict() for r in self.results],
            "aggregated_at": self.aggregated_at,
            "total_evaluators": self.total_evaluators,
            "successful_evaluators": self.successful_evaluators,
            "failed_evaluators": self.failed_evaluators,
            "total_time_ms": self.total_time_ms,
        }


class EvalSubAgent:
    """评估子代理 - 负责执行评估

    功能:
    - 从 Hub 搜索评估包
    - 加载评估器
    - 并行/串行执行评估
    - 聚合评估结果
    """

    # 默认并发数
    DEFAULT_MAX_CONCURRENCY = 5

    def __init__(
        self,
        evaluation_hub,
        max_concurrency: int = None,
    ):
        """
        Args:
            evaluation_hub: EvaluationHub 实例
            max_concurrency: 最大并发数
        """
        self.hub = evaluation_hub
        self.max_concurrency = max_concurrency or self.DEFAULT_MAX_CONCURRENCY
        self._evaluator_cache: dict[str, Any] = {}

    async def evaluate(
        self,
        feature_codes: list[str],
        input_data: dict[str, Any],
        context: dict[str, Any] = None,
        dimensions: list[EvalDimension] = None,
        levels: list[EvalLevel] = None,
    ) -> EvaluationReport:
        """执行评估

        Args:
            feature_codes: 特征码列表，用于搜索评估包
            input_data: 输入数据
            context: 上下文信息
            dimensions: 评估维度过滤
            levels: 评估层级过滤

        Returns:
            EvaluationReport: 评估报告
        """
        start_time = datetime.now()

        # 1. 从 Hub 获取包
        packages = self.hub.search_packages(
            feature_codes=feature_codes,
            dimension=dimensions[0] if dimensions else None,
            level=levels[0] if levels else None,
        )

        if not packages:
            # 没有找到包，返回默认结果
            return self._create_empty_report(
                input_data,
                "No matching packages found",
                start_time,
            )

        # 2. 加载评估器
        evaluators = []
        for pkg in packages:
            pkg_evaluators = self.hub.load_evaluators(pkg)
            evaluators.extend(pkg_evaluators)

        if not evaluators:
            return self._create_empty_report(
                input_data,
                "No evaluators found in packages",
                start_time,
            )

        # 3. 并行执行评估器
        results = await self._execute_parallel(
            evaluators, input_data, context or {}
        )

        # 4. 聚合结果
        overall_score, passed, blocking_failed = self._aggregate(results)

        # 计算执行时间
        total_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        return EvaluationReport(
            request_id=str(uuid.uuid4()),
            overall_score=overall_score,
            passed=passed,
            blocking_failed=blocking_failed,
            results=results,
            aggregated_at=datetime.now().isoformat(),
            total_evaluators=len(evaluators),
            successful_evaluators=sum(1 for r in results if not r.error),
            failed_evaluators=sum(1 for r in results if r.error),
            total_time_ms=total_time_ms,
        )

    async def _execute_parallel(
        self,
        evaluators: list[Any],
        input_data: dict[str, Any],
        context: dict[str, Any],
    ) -> list[EvalResult]:
        """并行执行评估器

        Args:
            evaluators: 评估器列表
            input_data: 输入数据
            context: 上下文

        Returns:
            评估结果列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def run_evaluator(evaluator):
            async with semaphore:
                try:
                    # 检查评估器是否有 evaluate 方法
                    if hasattr(evaluator, "evaluate"):
                        # 调用评估器的 evaluate 方法
                        result = await evaluator.evaluate(input_data, context)
                        return self._convert_to_eval_result(result)
                    elif hasattr(evaluator, "run"):
                        # 另一种接口
                        result = await evaluator.run(input_data, context)
                        return self._convert_to_eval_result(result)
                    else:
                        return EvalResult(
                            evaluator_name=getattr(evaluator, "name", "unknown"),
                            dimension=getattr(evaluator, "dimension", "unknown"),
                            level=getattr(evaluator, "level", "unknown"),
                            score=0.0,
                            passed=False,
                            feedback="Evaluator has no evaluate method",
                            error="Invalid evaluator interface",
                        )
                except Exception as e:
                    return EvalResult(
                        evaluator_name=getattr(evaluator, "name", "unknown"),
                        dimension=getattr(evaluator, "dimension", "unknown"),
                        level=getattr(evaluator, "level", "unknown"),
                        score=0.0,
                        passed=False,
                        feedback=f"Evaluation error: {str(e)}",
                        error=str(e),
                    )

        # 并行执行所有评估器
        results = await asyncio.gather(
            *[run_evaluator(e) for e in evaluators],
            return_exceptions=True,
        )

        # 处理异常结果
        processed_results = []
        for r in results:
            if isinstance(r, Exception):
                processed_results.append(
                    EvalResult(
                        evaluator_name="unknown",
                        dimension="unknown",
                        level="unknown",
                        score=0.0,
                        passed=False,
                        feedback=str(r),
                        error=str(r),
                    )
                )
            else:
                processed_results.append(r)

        return processed_results

    def _convert_to_eval_result(self, result: Any) -> EvalResult:
        """将评估器返回的结果转换为 EvalResult"""
        # 如果已经是 EvalResult，直接返回
        if isinstance(result, EvalResult):
            return result

        # 如果是字典
        if isinstance(result, dict):
            return EvalResult(
                evaluator_name=result.get("evaluator_name", "unknown"),
                dimension=result.get("dimension", "unknown"),
                level=result.get("level", "unknown"),
                score=result.get("score", 0.0),
                passed=result.get("passed", False),
                feedback=result.get("feedback", ""),
                execution_time_ms=result.get("execution_time_ms", 0),
                error=result.get("error"),
            )

        # 如果是 EvaluationResult (来自 hub.py)
        if hasattr(result, "score"):
            return EvalResult(
                evaluator_name=getattr(result, "evaluator", "unknown"),
                dimension="unknown",
                level="unknown",
                score=result.score,
                passed=result.score >= 0.5,
                feedback=str(getattr(result, "details", {})),
            )

        # 无法转换
        return EvalResult(
            evaluator_name="unknown",
            dimension="unknown",
            level="unknown",
            score=0.0,
            passed=False,
            feedback="Unable to convert result",
            error="Unknown result type",
        )

    def _aggregate(
        self,
        results: list[EvalResult],
    ) -> tuple[float, bool, bool]:
        """聚合评估结果

        Args:
            results: 评估结果列表

        Returns:
            (overall_score, passed, blocking_failed)
        """
        if not results:
            return 0.0, False, True

        # 计算平均分
        valid_scores = [r.score for r in results if r.error is None]
        if valid_scores:
            overall_score = sum(valid_scores) / len(valid_scores)
        else:
            overall_score = 0.0

        # 判断是否通过（至少 50% 的评估器通过）
        passed_count = sum(1 for r in results if r.passed and r.error is None)
        passed = passed_count >= len(results) * 0.5

        # 判断是否有阻塞性失败
        # 正确性或安全性维度失败视为阻塞性
        blocking_dimensions = {"correctness", "safety"}
        blocking_failed = any(
            r.dimension in blocking_dimensions
            and not r.passed
            and r.error is None
            for r in results
        )

        return overall_score, passed, blocking_failed

    def _create_empty_report(
        self,
        input_data: dict[str, Any],
        message: str,
        start_time: datetime,
    ) -> EvaluationReport:
        """创建空的评估报告"""
        total_time_ms = int(
            (datetime.now() - start_time).total_seconds() * 1000
        )

        return EvaluationReport(
            request_id=str(uuid.uuid4()),
            overall_score=0.0,
            passed=False,
            blocking_failed=True,
            results=[
                EvalResult(
                    evaluator_name="system",
                    dimension="unknown",
                    level="unknown",
                    score=0.0,
                    passed=False,
                    feedback=message,
                    error="No packages",
                )
            ],
            aggregated_at=datetime.now().isoformat(),
            total_evaluators=0,
            successful_evaluators=0,
            failed_evaluators=1,
            total_time_ms=total_time_ms,
        )


def create_eval_subagent(evaluation_hub, **kwargs) -> EvalSubAgent:
    """创建 EvalSubAgent 实例的便捷函数"""
    return EvalSubAgent(evaluation_hub, **kwargs)
