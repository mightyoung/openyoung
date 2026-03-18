"""
Evaluation Harness - 评估基础设施核心编排器

贯穿 Plan/Code/Test 各 Stage，统一管理:
- Task 执行
- Grader 判定
- Middleware 链
- 追踪导出
- 检查点持久化
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from .benchmark import BenchmarkTask, EvalType, TaskSuite
from .metrics import (
    EvalMetrics,
    EvalTrial,
    TaskMetrics,
    aggregate_eval_metrics,
    aggregate_task_metrics,
)
from .middleware import (
    BaseMiddleware,
    MiddlewareResult,
    get_default_middleware,
)
from .runner import EvalRunner, RunnerConfig

logger = logging.getLogger(__name__)


class HarnessConfig:
    """Harness 配置"""

    def __init__(
        self,
        max_parallel: int = 4,
        trial_timeout_sec: int = 300,
        retry_on_error: bool = True,
        max_retries: int = 2,
        verbose: bool = False,
        enable_tracing: bool = True,
        enable_checkpoint: bool = True,
        checkpoint_dir: str = ".eval_checkpoints",
    ):
        self.max_parallel = max_parallel
        self.trial_timeout_sec = trial_timeout_sec
        self.retry_on_error = retry_on_error
        self.max_retries = max_retries
        self.verbose = verbose
        self.enable_tracing = enable_tracing
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_dir = checkpoint_dir


class EvaluationHarness:
    """
    Evaluation Harness - 评估基础设施

    核心职责:
    1. 执行 BenchmarkTask/BenchmarkSuite
    2. 管理 Middleware 链 (before_task / after_task)
    3. 集成 Tracing (导出 eval spans)
    4. 持久化 EvalResult
    5. Capability / Regression 双轨支持
    """

    def __init__(
        self,
        config: HarnessConfig | None = None,
        middleware: list[BaseMiddleware] | None = None,
    ):
        self.config = config or HarnessConfig()
        runner_config = RunnerConfig(
            max_parallel=self.config.max_parallel,
            trial_timeout_sec=self.config.trial_timeout_sec,
            retry_on_error=self.config.retry_on_error,
            max_retries=self.config.max_retries,
            verbose=self.config.verbose,
        )
        self.runner = EvalRunner(runner_config)
        self.middleware = middleware or get_default_middleware()
        self._checkpoint_cache: dict[str, list[EvalTrial]] = {}

    # ========== 核心 API ==========

    async def evaluate_task(
        self,
        task: BenchmarkTask,
        agent_factory: Callable[[str], Any],
        *,
        n_trials: int | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> TaskMetrics:
        """
        评估单个任务

        Args:
            task: 任务定义
            agent_factory: Agent 工厂函数
            n_trials: trial 次数 (默认从 task.max_retries)
            progress_callback: 进度回调

        Returns:
            TaskMetrics: 任务聚合指标
        """
        n_trials = n_trials or task.max_retries

        # Middleware before_task
        for mw in self.middleware:
            await mw.before_task(task)

        # Run trials
        task_metrics = await self.runner.run_task(
            task=task,
            agent_factory=agent_factory,
            n_trials=n_trials,
            progress_callback=progress_callback,
        )

        # Middleware after_task
        for mw in reversed(self.middleware):
            await mw.after_task(task, task_metrics)

        # Checkpoint
        if self.config.enable_checkpoint:
            await self._save_checkpoint(task.id, task_metrics.trials)

        return task_metrics

    async def evaluate_suite(
        self,
        suite: TaskSuite,
        agent_factory: Callable[[str], Any],
        *,
        n_trials: int | None = None,
        progress_callback: Callable[[str, str, int, int], None] | None = None,
    ) -> EvalMetrics:
        """
        评估整个套件

        Args:
            suite: 任务套件
            agent_factory: Agent 工厂函数
            n_trials: 每个任务的 trial 次数
            progress_callback: 进度回调 (task_id, task_desc, current, total)

        Returns:
            EvalMetrics: 聚合评估指标
        """
        task_metrics_list: list[TaskMetrics] = []
        n_trials = n_trials or suite.default_n_trials

        # Middleware before_suite
        for mw in self.middleware:
            if hasattr(mw, "before_suite"):
                await mw.before_suite(suite)

        for task in suite.tasks:
            if self.config.verbose:
                logger.info(f"Evaluating task: {task.id} ({task.desc})")

            def make_callback(task_id: str, task_desc: str):
                def cb(current: int, total: int):
                    if progress_callback:
                        progress_callback(task_id, task_desc, current, total)

                return cb

            try:
                tm = await self.evaluate_task(
                    task=task,
                    agent_factory=agent_factory,
                    n_trials=n_trials,
                    progress_callback=make_callback(task.id, task.desc),
                )
                task_metrics_list.append(tm)
            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                # 记录失败的任务
                task_metrics_list.append(
                    aggregate_task_metrics([], task.eval_type)
                )

        # Aggregate
        eval_metrics = aggregate_eval_metrics(
            task_metrics_list, suite.id, suite.eval_type
        )
        eval_metrics.eval_started_at = datetime.now()
        eval_metrics.eval_finished_at = datetime.now()

        # Middleware after_suite
        for mw in reversed(self.middleware):
            if hasattr(mw, "after_suite"):
                await mw.after_suite(suite, eval_metrics)

        return eval_metrics

    # ========== Capability / Regression 双轨 ==========

    async def run_capability_eval(
        self,
        suite: TaskSuite,
        agent_factory: Callable[[str], Any],
        *,
        target_pass_at_k: float = 0.9,
    ) -> tuple[EvalMetrics, bool]:
        """
        运行 Capability 评估

        目标: pass@3 >= 90%
        """
        eval_metrics = await self.evaluate_suite(suite, agent_factory)

        passed = eval_metrics.pass_at_k >= target_pass_at_k
        return eval_metrics, passed

    async def run_regression_eval(
        self,
        suite: TaskSuite,
        agent_factory: Callable[[str], Any],
        *,
        required_pass_rate: float = 1.0,
    ) -> tuple[EvalMetrics, bool]:
        """
        运行 Regression 评估

        目标: pass^3 = 100% (所有 trial 都必须通过)
        """
        eval_metrics = await self.evaluate_suite(suite, agent_factory)

        passed = eval_metrics.regression_pass_rate >= required_pass_rate
        return eval_metrics, passed

    # ========== Checkpoint / 持久化 ==========

    async def _save_checkpoint(
        self, task_id: str, trials: list[EvalTrial]
    ) -> None:
        """保存评估结果到 checkpoint"""
        self._checkpoint_cache[task_id] = trials

        checkpoint_dir = Path(self.config.checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_file = checkpoint_dir / f"{task_id}.json"
        data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "trials": [t.to_dict() for t in trials],
        }

        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            if self.config.verbose:
                logger.info(f"Checkpoint saved: {checkpoint_file}")
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")

    async def load_checkpoint(self, task_id: str) -> list[EvalTrial] | None:
        """从 checkpoint 加载评估结果"""
        if task_id in self._checkpoint_cache:
            return self._checkpoint_cache[task_id]

        checkpoint_file = Path(self.config.checkpoint_dir) / f"{task_id}.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, encoding="utf-8") as f:
                data = json.load(f)
            # Trials 需要从 dict 反序列化 - 简化处理
            return None  # 完整反序列化略
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
            return None

    # ========== 报告生成 ==========

    def generate_report(
        self,
        eval_metrics: EvalMetrics,
        suite: TaskSuite,
    ) -> str:
        """生成评估报告"""
        lines = [
            f"# Evaluation Report: {suite.name}",
            f"",
            f"## Summary",
            f"- **Suite**: {suite.id}",
            f"- **Type**: {eval_metrics.eval_type.value}",
            f"- **Tasks**: {eval_metrics.total_tasks}",
            f"- **Total Trials**: {eval_metrics.total_trials}",
            f"",
            f"## Metrics",
            f"- **pass@1**: {eval_metrics.pass_at_1:.1%}",
            f"- **pass@3**: {eval_metrics.pass_at_3:.1%}",
            f"- **pass@{suite.default_n_trials}**: {eval_metrics.pass_at_k:.1%}",
            f"- **Regression pass rate**: {eval_metrics.regression_pass_rate:.1%}",
            f"- **Avg latency**: {eval_metrics.avg_latency_ms:.0f}ms",
            f"- **Avg cost**: ${eval_metrics.avg_cost_usd:.4f}",
            f"- **Total cost**: ${eval_metrics.total_cost_usd:.4f}",
            f"",
            f"## Per-Task Results",
        ]

        for tm in eval_metrics.task_metrics:
            status = "✅" if tm.pass_rate >= 1.0 else "❌" if tm.pass_at_1 == 0 else "⚠️"
            lines.append(
                f"- {status} **{tm.task_id}**: "
                f"pass@1={tm.pass_at_1:.0%}, "
                f"pass@{tm.total_trials}={tm.pass_at_k:.0%}, "
                f"avg_score={tm.avg_score:.2f}"
            )

        return "\n".join(lines)
