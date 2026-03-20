"""
Runner - 评估执行引擎
负责运行单个 Trial，执行 Task，收集结果
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .benchmark import (
    BenchmarkTask,
    EvalType,
    GraderConfig,
    GradingMode,
    TaskSuite,
)
from .graders import BaseGrader, CodeGrader, HumanGrader, ModelGrader
from .metrics import (
    EvalTrial,
    GraderResult,
    TaskMetrics,
    TrialMetrics,
    aggregate_task_metrics,
    compute_pass_at_k,
    compute_pass_rate,
    compute_weighted_score,
)


@dataclass
class RunnerConfig:
    """Runner 配置"""

    max_parallel: int = 4  # 并行执行的最大 trial 数
    trial_timeout_sec: int = 300  # 单个 trial 超时
    retry_on_error: bool = True  # 出错时重试
    max_retries: int = 2  # 最大重试次数
    verbose: bool = False  # 详细输出


class EvalRunner:
    """
    评估执行引擎

    负责:
    1. 运行 Task (单次 trial)
    2. 执行 Grader 判定
    3. 聚合 Trial 结果为 TaskMetrics
    """

    def __init__(self, config: RunnerConfig | None = None, tracing_manager=None):
        self.config = config or RunnerConfig()
        self._graders: dict[str, BaseGrader] = {}
        self._tracing = tracing_manager  # Optional eval span recording

    # ========== 公开 API ==========

    async def run_suite(
        self,
        suite: TaskSuite,
        agent_factory: Callable[[str], Any],
        *,
        n_trials: int | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> list[TaskMetrics]:
        """
        运行整个任务套件

        Args:
            suite: 任务套件
            agent_factory: Agent 工厂函数, 接收 task_id 返回 agent 实例
            n_trials: 每个任务的 trial 次数 (默认 suite.default_n_trials)
            progress_callback: 进度回调 (task_id, current, total)

        Returns:
            list[TaskMetrics]: 每个任务的聚合指标
        """
        n_trials = n_trials or suite.default_n_trials
        results: list[TaskMetrics] = []

        for task in suite.tasks:
            task_metrics = await self.run_task(
                task=task,
                agent_factory=agent_factory,
                n_trials=n_trials,
                progress_callback=progress_callback,
            )
            results.append(task_metrics)

        return results

    async def run_task(
        self,
        task: BenchmarkTask,
        agent_factory: Callable[[str], Any],
        *,
        n_trials: int = 1,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TaskMetrics:
        """
        运行单个任务, 多次 trial

        Args:
            task: 任务定义
            agent_factory: Agent 工厂函数
            n_trials: trial 次数
            progress_callback: 进度回调

        Returns:
            TaskMetrics: 聚合后的任务指标
        """
        trials: list[EvalTrial] = []

        for trial_num in range(1, n_trials + 1):
            if self.config.verbose:
                print(f"  Trial {trial_num}/{n_trials} for task {task.id}")

            trial = await self.run_trial(
                task=task,
                agent=agent_factory(task.id),
                trial_number=trial_num,
            )
            trials.append(trial)

            if progress_callback:
                progress_callback(task.id, trial_num, n_trials)

            # 短暂延迟，避免 API 限流
            if trial_num < n_trials:
                await asyncio.sleep(0.5)

        return aggregate_task_metrics(trials, task.eval_type)

    async def run_trial(
        self,
        task: BenchmarkTask,
        agent: Any,
        trial_number: int = 1,
    ) -> EvalTrial:
        """
        运行单个 Trial

        流程:
        1. 执行 Agent (获取 transcript + outcome)
        2. 运行所有 Grader
        3. 聚合判定结果
        """
        started_at = datetime.now()
        trial_metrics = TrialMetrics(start_time=started_at)
        error = None
        error_trace = None

        try:
            # 1. 执行 Agent
            if self.config.verbose:
                print(f"    Executing agent for task {task.id}...")

            transcript, outcome, metrics = await self._execute_agent(
                agent=agent,
                prompt=task.prompt,
                timeout_sec=task.timeout_sec,
            )

            # 更新 trial 指标
            trial_metrics.prompt_tokens = metrics.get("prompt_tokens", 0)
            trial_metrics.completion_tokens = metrics.get("completion_tokens", 0)
            trial_metrics.total_tokens = metrics.get("total_tokens", 0)
            trial_metrics.cost_usd = metrics.get("cost_usd", 0.0)
            trial_metrics.num_turns = metrics.get("num_turns", 0)
            trial_metrics.num_tool_calls = metrics.get("num_tool_calls", 0)
            trial_metrics.latency_ms = metrics.get("latency_ms", 0.0)

            # 2. 构建 context
            context = {
                "task_desc": task.desc,
                "prompt": task.prompt,
                "expected_output": task.expected_output or "",
                "working_dir": task.working_dir or "",
            }

            # 3. 运行 Graders
            if self.config.verbose:
                print(f"    Running {len(task.graders)} graders...")

            grader_results = await self._run_graders(
                graders=task.graders,
                task_id=task.id,
                transcript=transcript,
                outcome=outcome,
                context=context,
            )

            # 4. 聚合结果
            passed, overall_score = self._aggregate_grading(
                grader_results=grader_results,
                grading_mode=task.grading_mode,
                graders=task.graders,
            )

            finished_at = datetime.now()
            trial_metrics.end_time = finished_at

            return EvalTrial(
                task_id=task.id,
                trial_number=trial_number,
                passed=passed,
                overall_score=overall_score,
                grader_results=grader_results,
                metrics=trial_metrics,
                transcript=transcript,
                finished_at=finished_at,
            )

        except asyncio.TimeoutError:
            error = f"Trial timed out after {task.timeout_sec}s"
            error_trace = ""
            trial_metrics.latency_ms = task.timeout_sec * 1000
            finished_at = datetime.now()
            trial_metrics.end_time = finished_at
            return EvalTrial(
                task_id=task.id,
                trial_number=trial_number,
                passed=False,
                overall_score=0.0,
                grader_results=[],
                metrics=trial_metrics,
                transcript=[],
                error=error,
                error_trace=error_trace,
                finished_at=finished_at,
            )

        except Exception as e:
            error = str(e)
            error_trace = ""
            finished_at = datetime.now()
            trial_metrics.end_time = finished_at
            return EvalTrial(
                task_id=task.id,
                trial_number=trial_number,
                passed=False,
                overall_score=0.0,
                grader_results=[],
                metrics=trial_metrics,
                transcript=[],
                error=error,
                error_trace=error_trace,
                finished_at=finished_at,
            )

    # ========== 内部方法 ==========

    async def _execute_agent(
        self,
        agent: Any,
        prompt: str,
        timeout_sec: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        """
        执行 Agent

        Returns:
            transcript: 执行轨迹
            outcome: 最终结果
            metrics: 执行指标
        """
        try:
            result = await asyncio.wait_for(
                agent.run(prompt),
                timeout=timeout_sec,
            )

            # 统一返回格式
            if isinstance(result, dict):
                transcript = result.get("transcript", [])
                outcome = result.get("outcome", result)
                metrics = result.get("metrics", {})
            else:
                transcript = []
                outcome = {"result": str(result)}
                metrics = {}

            return transcript, outcome, metrics

        except asyncio.TimeoutError:
            raise

    async def _run_graders(
        self,
        graders: list[GraderConfig],
        task_id: str,
        transcript: list[dict[str, Any]],
        outcome: dict[str, Any],
        context: dict[str, Any],
    ) -> list[GraderResult]:
        """运行所有 Grader"""
        results: list[GraderResult] = []

        for grader_config in graders:
            grader = self._get_grader(grader_config)
            output = await grader.grade(
                task_id=task_id,
                transcript=transcript,
                outcome=outcome,
                context=context,
            )

            results.append(
                GraderResult(
                    grader_name=output.grader_name,
                    passed=output.passed,
                    score=output.score,
                    details=output.details,
                    output=output.raw_output,
                    latency_ms=output.latency_ms,
                )
            )

        return results

    def _get_grader(self, config: GraderConfig) -> BaseGrader:
        """获取或创建 Grader 实例"""
        if config.name in self._graders:
            return self._graders[config.name]

        if config.grader_type.value == "code":
            grader = CodeGrader(config)
        elif config.grader_type.value == "model":
            grader = ModelGrader(config)
        elif config.grader_type.value == "human":
            grader = HumanGrader(config)
        else:
            raise ValueError(f"Unsupported grader type: {config.grader_type}")

        self._graders[config.name] = grader
        return grader

    def _aggregate_grading(
        self,
        grader_results: list[GraderResult],
        grading_mode: GradingMode,
        graders: list[GraderConfig],
    ) -> tuple[bool, float]:
        """聚合 Grader 判定结果"""
        if not grader_results:
            return False, 0.0

        if grading_mode == GradingMode.BINARY:
            # 所有必需 grader 必须通过
            required_names = {g.name for g in graders if g.required}
            required_results = [r for r in grader_results if r.grader_name in required_names]
            passed = all(r.passed for r in required_results)
            score = compute_weighted_score(grader_results)

        elif grading_mode == GradingMode.WEIGHTED:
            # 加权平均
            score = compute_weighted_score(grader_results)
            passed = score >= 0.7

        elif grading_mode == GradingMode.HYBRID:
            # 部分必需通过 + 加权平均
            required_names = {g.name for g in graders if g.required}
            required_results = [r for r in grader_results if r.grader_name in required_names]
            required_passed = all(r.passed for r in required_results)
            score = compute_weighted_score(grader_results)
            passed = required_passed and score >= 0.5

        else:
            passed = all(r.passed for r in grader_results)
            score = compute_weighted_score(grader_results)

        return passed, score


# ========== 便捷函数 ==========


async def run_quick_eval(
    task: BenchmarkTask,
    agent_factory: Callable[[str], Any],
    n_trials: int = 1,
) -> TaskMetrics:
    """快速运行单任务评估"""
    runner = EvalRunner(RunnerConfig(verbose=True))
    return await runner.run_task(task, agent_factory, n_trials=n_trials)
