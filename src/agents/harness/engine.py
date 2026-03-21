"""
Harness Engine - 执行流程控制引擎

实现三阶段评估模型:
- UNIT: 单元测试阶段
- INTEGRATION: 集成测试阶段
- E2E: 端到端测试阶段

参考:
- LangGraph: https://langchain-ai.github.io/langgraph/
- DataGrid AI: https://www.datagrid.com/blog/7-tips-build-self-improving-ai-agents-feedback-loops
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

from src.agents.harness.types import (
    ExecutionStatus,
    StreamingExecutionResult,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class ExecutionPhase(Enum):
    """执行阶段"""

    UNIT = "unit"  # 单元测试阶段
    INTEGRATION = "integration"  # 集成测试阶段
    E2E = "e2e"  # 端到端测试阶段

    def next(self) -> Optional["ExecutionPhase"]:
        """获取下一阶段"""
        order = [ExecutionPhase.UNIT, ExecutionPhase.INTEGRATION, ExecutionPhase.E2E]
        try:
            idx = order.index(self)
            return order[idx + 1] if idx + 1 < len(order) else None
        except (ValueError, IndexError):
            return None


class FeedbackAction(Enum):
    """反馈动作"""

    RETRY = "retry"  # 重试当前任务
    REPLAN = "replan"  # 重新规划任务
    ESCALATE = "escalate"  # 升级处理
    COMPLETE = "complete"  # 任务完成
    FAIL = "fail"  # 任务失败


class EvaluationResult(Enum):
    """评估结果"""

    PASS = "pass"  # 通过
    FAIL = "fail"  # 失败
    SKIP = "skip"  # 跳过
    PENDING = "pending"  # 待评估


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PhaseConfig:
    """阶段配置"""

    phase: ExecutionPhase
    enabled: bool = True
    max_retries: int = 3
    timeout: float = 300.0
    evaluator: Optional[Callable] = None


@dataclass
class HarnessConfig:
    """Harness 配置"""

    max_iterations: int = 10  # 最大迭代次数
    max_total_time: float = 3600.0  # 最大总时间（秒）
    enable_phases: bool = True  # 是否启用多阶段
    budget_per_task: float = 100.0  # 每个任务的预算（时间单位）
    phases: list[PhaseConfig] = field(default_factory=list)

    def __post_init__(self):
        if not self.phases:
            # 默认阶段配置
            self.phases = [
                PhaseConfig(
                    phase=ExecutionPhase.UNIT,
                    max_retries=3,
                    timeout=60.0,
                ),
                PhaseConfig(
                    phase=ExecutionPhase.INTEGRATION,
                    max_retries=2,
                    timeout=120.0,
                ),
                PhaseConfig(
                    phase=ExecutionPhase.E2E,
                    max_retries=1,
                    timeout=180.0,
                ),
            ]


@dataclass
class ExecutionResult:
    """执行结果"""

    phase: ExecutionPhase
    result: Any
    evaluation: EvaluationResult
    feedback_action: FeedbackAction
    duration: float
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HarnessStats:
    """执行统计"""

    total_iterations: int = 0
    phase_results: dict[str, ExecutionResult] = field(default_factory=dict)
    total_duration: float = 0.0
    budget_consumed: float = 0.0


# ============================================================================
# Harness Engine
# ============================================================================


class HarnessEngine:
    """Harness 引擎

    核心功能:
    - 三阶段评估 (UNIT → INTEGRATION → E2E)
    - 反馈循环 (RETRY/REPLAN/ESCALATE/COMPLETE)
    - 任务预算控制
    """

    def __init__(self, config: Optional[HarnessConfig] = None):
        self.config = config or HarnessConfig()
        self._executor: Optional[Callable] = None
        self._evaluator: Optional[Callable] = None
        self._replanner: Optional[Callable] = None
        self._stats = HarnessStats()

    def set_executor(self, executor: Callable):
        """设置任务执行器"""
        self._executor = executor

    def set_evaluator(self, evaluator: Callable):
        """设置评估器"""
        self._evaluator = evaluator

    def set_replanner(self, replanner: Callable):
        """设置重规划器"""
        self._replanner = replanner

    async def execute(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """执行任务

        Args:
            task_description: 任务描述
            context: 上下文

        Returns:
            执行结果
        """
        logger.info(f"Starting harness execution for task: {task_description}")

        context = context or {}
        start_time = time.time()
        budget_consumed = 0.0

        # 执行阶段循环
        current_phase = ExecutionPhase.UNIT if self.config.enable_phases else ExecutionPhase.E2E
        phase_results = {}
        iteration = 0

        while iteration < self.config.max_iterations:
            # 检查总时间预算
            elapsed = time.time() - start_time
            if elapsed >= self.config.max_total_time:
                logger.warning(f"Total time budget exceeded: {elapsed:.1f}s")
                break

            budget_consumed = iteration * self.config.budget_per_task
            if budget_consumed >= self.config.budget_per_task * self.config.max_iterations:
                logger.warning(f"Budget exhausted: {budget_consumed}")
                break

            logger.info(
                f"Iteration {iteration + 1}/{self.config.max_iterations}, Phase: {current_phase.value}"
            )

            # 获取当前阶段配置
            phase_config = self._get_phase_config(current_phase)
            if not phase_config or not phase_config.enabled:
                logger.info(f"Phase {current_phase.value} disabled, skipping")
                current_phase = current_phase.next() or current_phase
                continue

            # 执行任务
            try:
                result = await self._execute_phase(
                    task_description,
                    current_phase,
                    phase_config,
                    context,
                )

                phase_results[current_phase.value] = result
                self._stats.phase_results[current_phase.value] = result

                # 评估结果
                evaluation = result.evaluation

                # 根据评估结果决定反馈动作
                feedback = await self._determine_feedback_action(
                    result,
                    iteration,
                    phase_results,
                )

                # 处理反馈动作
                if feedback == FeedbackAction.COMPLETE:
                    logger.info("Task completed successfully")
                    return {
                        "status": "success",
                        "result": result.result,
                        "iterations": iteration + 1,
                        "duration": time.time() - start_time,
                        "phases": {k: v.result for k, v in phase_results.items()},
                    }

                elif feedback == FeedbackAction.RETRY:
                    logger.info(f"Retrying task at phase {current_phase.value}")
                    iteration += 1

                elif feedback == FeedbackAction.REPLAN:
                    logger.info("Replanning task")
                    if self._replanner:
                        task_description = await self._replanner(task_description, result)
                    iteration += 1

                elif feedback == FeedbackAction.ESCALATE:
                    logger.warning("Escalating task")
                    return {
                        "status": "escalated",
                        "result": result.result,
                        "iterations": iteration + 1,
                        "error": result.error,
                        "phases": {k: v.result for k, v in phase_results.items()},
                    }

                elif feedback == FeedbackAction.FAIL:
                    logger.error(f"Task failed at phase {current_phase.value}")
                    return {
                        "status": "failed",
                        "error": result.error or "Unknown error",
                        "iterations": iteration + 1,
                        "phases": {k: v.result for k, v in phase_results.items()},
                    }

            except Exception as e:
                logger.error(f"Phase {current_phase.value} raised exception: {e}")
                iteration += 1
                # 继续到下一阶段或重试

            # 移动到下一阶段
            next_phase = current_phase.next()
            if next_phase:
                current_phase = next_phase
            else:
                # 所有阶段完成，检查是否有失败的
                if any(v.evaluation == EvaluationResult.FAIL for v in phase_results.values()):
                    break
                # 成功完成所有阶段
                return {
                    "status": "success",
                    "iterations": iteration + 1,
                    "phases": {k: v.result for k, v in phase_results.items()},
                }

            iteration += 1

        # 达到最大迭代次数
        logger.warning(f"Max iterations reached: {self.config.max_iterations}")
        return {
            "status": "max_iterations",
            "iterations": iteration,
            "phases": {k: v.result for k, v in phase_results.items()},
        }

    async def execute_streaming(
        self,
        task_description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[StreamingExecutionResult, None]:
        """Streaming execution - yields at each phase/step.

        Args:
            task_description: 任务描述
            context: 上下文

        Yields:
            StreamingExecutionResult at each phase/step
        """
        logger.info(f"Starting streaming harness execution for task: {task_description}")

        context = context or {}
        start_time = time.time()

        current_phase = ExecutionPhase.UNIT if self.config.enable_phases else ExecutionPhase.E2E
        phase_results = {}
        iteration = 0

        while iteration < self.config.max_iterations:
            # Check total time budget
            elapsed = time.time() - start_time
            if elapsed >= self.config.max_total_time:
                logger.warning(f"Total time budget exceeded: {elapsed:.1f}s")
                break

            # Yield progress before phase
            yield StreamingExecutionResult(
                phase=current_phase,
                iteration=iteration,
                status=ExecutionStatus.RUNNING,
                partial_output=f"Starting {current_phase.value} phase...",
            )

            # Get phase config
            phase_config = self._get_phase_config(current_phase)
            if not phase_config or not phase_config.enabled:
                logger.info(f"Phase {current_phase.value} disabled, skipping")
                current_phase = current_phase.next() or current_phase
                continue

            # Execute phase
            try:
                result = await self._execute_phase(
                    task_description,
                    current_phase,
                    phase_config,
                    context,
                )

                phase_results[current_phase.value] = result

                # Yield result after phase
                yield StreamingExecutionResult(
                    phase=result.phase,
                    iteration=iteration,
                    status=ExecutionStatus.COMPLETED
                    if result.evaluation == EvaluationResult.PASS
                    else ExecutionStatus.FAILED,
                    evaluation=result.evaluation,
                    feedback_action=result.feedback_action,
                    result=result.result,
                    partial_output=f"Completed {result.phase.value} phase",
                    error=result.error,
                    duration=result.duration,
                    metadata={"phase_result": result.evaluation.value},
                    timestamp=datetime.now(),
                )

                # Determine feedback action
                feedback = await self._determine_feedback_action(
                    result,
                    iteration,
                    phase_results,
                )

                if feedback == FeedbackAction.COMPLETE:
                    logger.info("Task completed successfully")
                    break

                elif feedback in (FeedbackAction.RETRY, FeedbackAction.REPLAN):
                    iteration += 1

                elif feedback == FeedbackAction.ESCALATE:
                    logger.warning("Escalating task")
                    break

                elif feedback == FeedbackAction.FAIL:
                    logger.error(f"Task failed at phase {current_phase.value}")
                    break

            except Exception as e:
                logger.error(f"Phase {current_phase.value} raised exception: {e}")
                yield StreamingExecutionResult(
                    phase=current_phase,
                    iteration=iteration,
                    status=ExecutionStatus.FAILED,
                    error=str(e),
                    partial_output=f"Error in {current_phase.value} phase: {str(e)}",
                    timestamp=datetime.now(),
                )
                iteration += 1

            # Move to next phase
            next_phase = current_phase.next()
            if next_phase:
                current_phase = next_phase
            else:
                # All phases completed
                if any(v.evaluation == EvaluationResult.FAIL for v in phase_results.values()):
                    break
                break

            iteration += 1

    def _get_phase_config(self, phase: ExecutionPhase) -> Optional[PhaseConfig]:
        """获取阶段配置"""
        for pc in self.config.phases:
            if pc.phase == phase:
                return pc
        return None

    async def _execute_phase(
        self,
        task_description: str,
        phase: ExecutionPhase,
        config: PhaseConfig,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """执行单个阶段"""
        start_time = time.time()

        # 构建阶段特定的输入
        phase_context = {
            **context,
            "phase": phase.value,
        }

        try:
            # 执行任务
            if asyncio.iscoroutinefunction(self._executor):
                result = await asyncio.wait_for(
                    self._executor(task_description, phase_context),
                    timeout=config.timeout,
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self._executor, task_description, phase_context),
                    timeout=config.timeout,
                )

            # 评估结果
            evaluation = EvaluationResult.PASS
            if self._evaluator:
                eval_result = await self._evaluator(result, phase, context)
                evaluation = EvaluationResult.PASS if eval_result else EvaluationResult.FAIL

            duration = time.time() - start_time

            return ExecutionResult(
                phase=phase,
                result=result,
                evaluation=evaluation,
                feedback_action=FeedbackAction.COMPLETE
                if evaluation == EvaluationResult.PASS
                else FeedbackAction.RETRY,
                duration=duration,
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return ExecutionResult(
                phase=phase,
                result=None,
                evaluation=EvaluationResult.FAIL,
                feedback_action=FeedbackAction.RETRY,
                duration=duration,
                error=f"Phase timeout after {config.timeout}s",
            )

        except Exception as e:
            duration = time.time() - start_time
            return ExecutionResult(
                phase=phase,
                result=None,
                evaluation=EvaluationResult.FAIL,
                feedback_action=FeedbackAction.RETRY,
                duration=duration,
                error=str(e),
            )

    async def _determine_feedback_action(
        self,
        result: ExecutionResult,
        iteration: int,
        phase_results: dict[str, ExecutionResult],
    ) -> FeedbackAction:
        """根据评估结果确定反馈动作"""
        # 如果有评估器，使用评估器的结果
        if result.feedback_action != FeedbackAction.COMPLETE:
            return result.feedback_action

        # 基础逻辑
        if result.evaluation == EvaluationResult.PASS:
            # 检查是否还有其他阶段需要执行
            return FeedbackAction.COMPLETE

        # 失败情况
        phase_config = self._get_phase_config(result.phase)
        if phase_config and iteration < phase_config.max_retries:
            return FeedbackAction.RETRY

        # 超过重试次数
        return FeedbackAction.FAIL

    def get_stats(self) -> HarnessStats:
        """获取执行统计"""
        return self._stats


# ============================================================================
# Convenience Functions
# ============================================================================


def create_harness(
    max_iterations: int = 10,
    enable_phases: bool = True,
) -> HarnessEngine:
    """创建 Harness 引擎"""
    config = HarnessConfig(
        max_iterations=max_iterations,
        enable_phases=enable_phases,
    )
    return HarnessEngine(config)
