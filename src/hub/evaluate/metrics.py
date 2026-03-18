"""
Metrics - 评估指标计算模块

实现 pass@k, pass^all, latency, cost 等指标计算
参考 Anthropic eval metrics 设计
"""

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .benchmark import EvalType


@dataclass
class TrialMetrics:
    """单次 Trial 的指标"""

    # 时间
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    latency_ms: float = 0.0

    # Token 使用
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # 成本
    cost_usd: float = 0.0

    # 执行统计
    num_turns: int = 0
    num_tool_calls: int = 0

    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return self.latency_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "num_turns": self.num_turns,
            "num_tool_calls": self.num_tool_calls,
        }


@dataclass
class GraderResult:
    """单个 Grader 的结果"""

    grader_name: str
    passed: bool
    score: float  # 0.0 - 1.0
    details: str
    output: Optional[str] = None  # 原始输出
    latency_ms: float = 0.0


@dataclass
class EvalTrial:
    """
    单次评估 Trial

    一次任务执行的结果
    """

    task_id: str
    trial_number: int  # 第几次尝试 (1-based)
    passed: bool  # 综合判定
    overall_score: float  # 综合得分 (0.0 - 1.0)

    # 详细结果
    grader_results: list[GraderResult]

    # 指标
    metrics: TrialMetrics

    # 轨迹 (完整执行记录)
    transcript: list[dict[str, Any]] = field(default_factory=list)

    # 错误
    error: Optional[str] = None
    error_trace: Optional[str] = None

    # 元数据
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "trial_number": self.trial_number,
            "passed": self.passed,
            "overall_score": self.overall_score,
            "grader_results": [
                {
                    "name": r.grader_name,
                    "passed": r.passed,
                    "score": r.score,
                    "details": r.details,
                }
                for r in self.grader_results
            ],
            "metrics": self.metrics.to_dict(),
            "num_transcript_entries": len(self.transcript),
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


@dataclass
class TaskMetrics:
    """单个任务的多 Trial 聚合指标"""

    task_id: str
    eval_type: EvalType

    # Pass@k 指标
    pass_at_1: float  # 1次尝试内成功
    pass_at_3: float  # 3次尝试内成功
    pass_at_k: float  # k次尝试内成功 (动态)
    pass_rate: float  # pass^k: 全部成功才通过

    # 聚合指标
    avg_latency_ms: float
    avg_cost_usd: float
    avg_score: float

    # 原始数据
    total_trials: int
    successful_trials: int
    first_success_trial: Optional[int]  # 首次成功的 trial number

    # 各 trial 结果
    trials: list[EvalTrial] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "eval_type": self.eval_type.value,
            "pass_at_1": self.pass_at_1,
            "pass_at_3": self.pass_at_3,
            "pass_at_k": self.pass_at_k,
            "pass_rate": self.pass_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost_usd": self.avg_cost_usd,
            "avg_score": self.avg_score,
            "total_trials": self.total_trials,
            "successful_trials": self.successful_trials,
            "first_success_trial": self.first_success_trial,
        }


@dataclass
class EvalMetrics:
    """
    完整评估的聚合指标

    对应 Anthropic evaluation 的汇总统计
    """

    suite_id: str
    eval_type: EvalType
    total_tasks: int

    # Pass@k 聚合
    pass_at_1: float
    pass_at_3: float
    pass_at_k: float

    # 回归测试专用 (pass^all = 100% 才算通过)
    regression_pass_rate: float  # pass^all: 所有任务在所有trial都通过
    capability_pass_rate: float  # 能力测试通过率

    # 聚合指标
    avg_latency_ms: float
    avg_cost_usd: float
    total_cost_usd: float
    total_tokens: int

    # 可靠性
    total_trials: int
    successful_trials: int
    failed_trials: int

    # 详细
    task_metrics: list[TaskMetrics] = field(default_factory=list)

    # 时间
    eval_started_at: datetime = field(default_factory=datetime.now)
    eval_finished_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "eval_type": self.eval_type.value,
            "total_tasks": self.total_tasks,
            "pass_at_1": self.pass_at_1,
            "pass_at_3": self.pass_at_3,
            "pass_at_k": self.pass_at_k,
            "regression_pass_rate": self.regression_pass_rate,
            "capability_pass_rate": self.capability_pass_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_cost_usd": self.avg_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "total_trials": self.total_trials,
            "successful_trials": self.successful_trials,
            "failed_trials": self.failed_trials,
            "eval_started_at": self.eval_started_at.isoformat(),
            "eval_finished_at": self.eval_finished_at.isoformat() if self.eval_finished_at else None,
        }

    def summary(self) -> str:
        """生成人类可读的摘要"""
        return (
            f"EvalReport: {self.suite_id}\n"
            f"  Type: {self.eval_type.value}\n"
            f"  Tasks: {self.total_tasks}\n"
            f"  pass@1: {self.pass_at_1:.1%}\n"
            f"  pass@3: {self.pass_at_3:.1%}\n"
            f"  pass@{self._infer_k()}: {self.pass_at_k:.1%}\n"
            f"  Avg Latency: {self.avg_latency_ms:.0f}ms\n"
            f"  Total Cost: ${self.total_cost_usd:.4f}\n"
            f"  Trials: {self.total_trials} total, {self.successful_trials} passed, {self.failed_trials} failed"
        )

    def _infer_k(self) -> int:
        if self.total_trials >= 3 and self.pass_at_3 < 1.0:
            return 3
        return 1


# ========== 核心指标计算 ==========


def compute_pass_at_k(results: list[bool], k: int) -> float:
    """
    计算 pass@k

    pass@k = 至少有一次在 k 次尝试内成功

    对于 n 个 trial, 每个 trial 只有 1 个结果 (passed/failed)
    pass@k = 1 - (所有 trial 都失败) 的概率
    如果 n 个 trial 都有相同的通过率 p, 则:
    pass@k = 1 - (1-p)^n  (对于 pass@1 场景的另一种解释)

    但对于 eval 中的 n trials 独立执行同一任务:
    - 每个 trial 是一次独立的执行尝试
    - pass@k 表示在 n 次独立尝试中, 至少有一次成功

    简化实现: pass@1 = first trial passed
    pass@3 = any of first 3 trials passed (如果 n >= 3)
    """
    n = len(results)
    if n == 0:
        return 0.0

    actual_k = min(k, n)

    if actual_k == 1:
        return float(results[0])

    return float(any(results[:actual_k]))


def compute_pass_rate(results: list[bool]) -> float:
    """
    计算 pass^all (pass rate)

    所有 trial 都必须成功才算通过
    这是一种更严格的可靠性度量

    用于 regression 测试: pass^3 = 1.0 表示连续 3 次都成功
    """
    if not results:
        return 0.0
    return float(all(results))


def compute_weighted_score(grader_results: list[GraderResult]) -> float:
    """计算加权得分"""
    if not grader_results:
        return 0.0
    total_score = sum(r.score for r in grader_results)
    return total_score / len(grader_results)


def aggregate_task_metrics(trials: list[EvalTrial], eval_type: EvalType) -> TaskMetrics:
    """聚合多个 trial 的指标"""
    if not trials:
        return TaskMetrics(
            task_id="unknown",
            eval_type=eval_type,
            pass_at_1=0.0,
            pass_at_3=0.0,
            pass_at_k=0.0,
            pass_rate=0.0,
            avg_latency_ms=0.0,
            avg_cost_usd=0.0,
            avg_score=0.0,
            total_trials=0,
            successful_trials=0,
            first_success_trial=None,
            trials=[],
        )

    task_id = trials[0].task_id
    n = len(trials)

    passed_list = [t.passed for t in trials]
    first_success = None
    for i, t in enumerate(trials):
        if t.passed:
            first_success = t.trial_number
            break

    total_latency = sum(t.metrics.latency_ms for t in trials)
    total_cost = sum(t.metrics.cost_usd for t in trials)
    total_score = sum(t.overall_score for t in trials)
    successful = sum(1 for t in trials if t.passed)

    return TaskMetrics(
        task_id=task_id,
        eval_type=eval_type,
        pass_at_1=compute_pass_at_k(passed_list, 1),
        pass_at_3=compute_pass_at_k(passed_list, 3),
        pass_at_k=compute_pass_at_k(passed_list, n),
        pass_rate=compute_pass_rate(passed_list),
        avg_latency_ms=total_latency / n,
        avg_cost_usd=total_cost / n,
        avg_score=total_score / n,
        total_trials=n,
        successful_trials=successful,
        first_success_trial=first_success,
        trials=trials,
    )


def aggregate_eval_metrics(
    task_metrics_list: list[TaskMetrics], suite_id: str, eval_type: EvalType
) -> EvalMetrics:
    """聚合整个评估套件的指标"""
    if not task_metrics_list:
        return EvalMetrics(
            suite_id=suite_id,
            eval_type=eval_type,
            total_tasks=0,
            pass_at_1=0.0,
            pass_at_3=0.0,
            pass_at_k=0.0,
            regression_pass_rate=0.0,
            capability_pass_rate=0.0,
            avg_latency_ms=0.0,
            avg_cost_usd=0.0,
            total_cost_usd=0.0,
            total_tokens=0,
            total_trials=0,
            successful_trials=0,
            failed_trials=0,
        )

    total_tasks = len(task_metrics_list)
    total_trials = sum(tm.total_trials for tm in task_metrics_list)
    successful_trials = sum(tm.successful_trials for tm in task_metrics_list)

    total_latency = sum(tm.avg_latency_ms * tm.total_trials for tm in task_metrics_list)
    total_cost = sum(tm.avg_cost_usd * tm.total_trials for tm in task_metrics_list)

    regression_tasks = [tm for tm in task_metrics_list if tm.eval_type == EvalType.REGRESSION]
    capability_tasks = [tm for tm in task_metrics_list if tm.eval_type == EvalType.CAPABILITY]

    return EvalMetrics(
        suite_id=suite_id,
        eval_type=eval_type,
        total_tasks=total_tasks,
        pass_at_1=sum(tm.pass_at_1 for tm in task_metrics_list) / total_tasks,
        pass_at_3=sum(tm.pass_at_3 for tm in task_metrics_list) / total_tasks,
        pass_at_k=sum(tm.pass_at_k for tm in task_metrics_list) / total_tasks,
        regression_pass_rate=sum(r.pass_rate for r in regression_tasks) / len(regression_tasks)
        if regression_tasks
        else 1.0,
        capability_pass_rate=sum(c.pass_rate for c in capability_tasks) / len(capability_tasks)
        if capability_tasks
        else 0.0,
        avg_latency_ms=total_latency / total_trials if total_trials else 0.0,
        avg_cost_usd=total_cost / total_tasks,
        total_cost_usd=total_cost,
        total_tokens=0,
        total_trials=total_trials,
        successful_trials=successful_trials,
        failed_trials=total_trials - successful_trials,
        task_metrics=task_metrics_list,
    )
