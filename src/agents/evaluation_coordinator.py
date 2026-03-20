"""
Evaluation Coordinator - 评估协调器

负责协调整个评估流程，从 YoungAgent 中提取评估逻辑。

Note: 评估功能已迁移到 src/hub/evaluate/ (Harness 系统)
本文件保留以维持 young_agent.py 兼容性，核心逻辑已停用。

集成统一异常处理:
- 异常转换
- 上下文增强
- 错误日志
"""

import re
from dataclasses import dataclass, field
from typing import Any

from src.core.exception_handler import (
    EvaluationError,
    ExceptionContext,
    get_exception_handler,
    handle_exceptions,
)

# ========== Stubs — 替换 src.evaluation 依赖 ==========


class EvalPlanner:
    """评估计划生成器 (stub) — 评估迁移到 Harness 系统"""

    async def generate_plan(self, task_description: str) -> Any:
        class _StubPlan:
            task_type = "general"
            success_criteria = []
            validation_methods = []

        return _StubPlan()


# ========== Dataclasses ==========


@dataclass
class EvaluationContext:
    """评估上下文"""

    task_description: str
    task_result: str
    duration_ms: int = 0
    tokens_used: int = 0
    model: str = ""
    session_id: str = ""


@dataclass
class EvaluationReport:
    """评估报告"""

    score: float  # 0-1 综合评分
    base_score: float  # LLMJudge 基础分
    completion_rate: float  # 任务完成度
    task_type: str  # 任务类型
    judge_result: dict[str, Any]  # LLMJudge 原始结果
    eval_plan: Any  # 评估计划
    threshold_violations: list  # 阈值违反
    weights_used: dict[str, float]  # 使用的权重
    details: dict[str, Any] = field(default_factory=dict)


class EvaluationCoordinator:
    """评估协调器

    从 YoungAgent 提取的评估逻辑，统一管理评估流程。

    Note: 评估功能已迁移到 src/hub/evaluate/ (Harness 系统)
    本类核心逻辑已停用，仅保留结构和占位实现。

    支持：
    - LLM-as-Judge 智能评估
    - 基于评估计划的完成度计算
    - 阈值检查
    - 动态权重

    集成统一异常处理:
    - EvaluationError: 评估相关错误
    """

    def __init__(self, llm_client=None):
        self._llm_client = llm_client
        self._judge = None
        self._planner = EvalPlanner()
        # 初始化异常处理器
        self._exception_handler = get_exception_handler()

        # 任务类型权重配置
        self.TASK_TYPE_WEIGHTS = {
            "coding": {"base_score": 0.6, "completion_rate": 0.3, "efficiency": 0.1},
            "general": {"base_score": 0.5, "completion_rate": 0.3, "efficiency": 0.2},
            "conversation": {"base_score": 0.5, "completion_rate": 0.2, "efficiency": 0.3},
            "research": {"base_score": 0.6, "completion_rate": 0.3, "efficiency": 0.1},
            "analysis": {"base_score": 0.5, "completion_rate": 0.3, "efficiency": 0.2},
            "web_scraping": {"base_score": 0.5, "completion_rate": 0.3, "efficiency": 0.2},
            "data_processing": {"base_score": 0.7, "completion_rate": 0.2, "efficiency": 0.1},
            "search": {"base_score": 0.6, "completion_rate": 0.2, "efficiency": 0.2},
            "file_operation": {"base_score": 0.6, "completion_rate": 0.3, "efficiency": 0.1},
        }
        self.DEFAULT_WEIGHTS = {"base_score": 0.5, "completion_rate": 0.3, "efficiency": 0.2}

        # 阈值配置
        self.DIMENSION_THRESHOLDS = {
            "correctness": {"threshold": 0.7, "blocking": True, "weight": 0.4},
            "safety": {"threshold": 0.9, "blocking": True, "weight": 0.2},
            "efficiency": {"threshold": 0.4, "blocking": False, "weight": 0.2},
            "clarity": {"threshold": 0.5, "blocking": False, "weight": 0.2},
        }

    def _get_judge(self):
        """获取或创建 LLMJudge 实例 (stub)"""
        # LLMJudgeEval 已移除 — 评估使用 Harness 系统
        return None

    @handle_exceptions(reraise=False, default=None)
    async def evaluate(self, context: EvaluationContext) -> EvaluationReport:
        """执行评估流程

        Args:
            context: 评估上下文

        Returns:
            EvaluationReport: 评估报告
        """
        # 1. 生成评估计划
        eval_plan = await self._planner.generate_plan(context.task_description)
        task_type = eval_plan.task_type or "general"
        print(f"[EvalPlan] Task type: {task_type}")
        print(f"[EvalPlan] Success criteria: {len(eval_plan.success_criteria)} items")

        # 2. LLMJudge 智能评估
        judge = self._get_judge()
        try:
            judge_result = await judge.evaluate(
                input_text=context.task_description,
                output_text=context.task_result,
                expected_output=None,
            )
        except Exception as e:
            # 异常转换
            context_exception = ExceptionContext(
                function="evaluate",
                additional_data={"task_type": task_type},
            )
            self._exception_handler.handle_exception(e, context_exception, reraise=False)
            # 返回默认评分
            return EvaluationReport(
                score=0.5,
                base_score=0.5,
                completion_rate=0.5,
                task_type=task_type,
                judge_result={"error": str(e)},
                eval_plan=eval_plan,
                threshold_violations=[],
                weights_used=self.DEFAULT_WEIGHTS,
                details={"error": True},
            )

        # LLMJudge 返回 1-5 分，转换为 0-1
        base_score = judge_result.get("average_score", 3.0) / 5.0
        print(
            f"[LLMJudge] Score: {base_score:.2f} (raw: {judge_result.get('average_score', 'N/A')})"
        )

        # 3. 计算任务完成度
        completion_rate = self._calculate_completion_rate(
            task_description=context.task_description,
            task_result=context.task_result,
            eval_plan=eval_plan,
        )

        # 4. 计算加权评分
        quality_score = self._calculate_weighted_score(
            task_type=task_type,
            base_score=base_score,
            completion_rate=completion_rate,
            efficiency=1.0,
        )
        quality_score = max(quality_score, 0.1)  # 至少给 0.1 分

        # 5. 阈值检查
        threshold_violations = self._check_threshold_violations(judge_result)
        if threshold_violations:
            blocking_violations = [v for v in threshold_violations if v["blocking"]]
            if blocking_violations:
                print(f"[Threshold] Blocking violations: {len(blocking_violations)}")
                for v in blocking_violations:
                    print(f"  - {v['dimension']}: {v['score']:.2f} < {v['threshold']}")
                # 阻塞性失败，降低评分
                quality_score *= 0.5

        return EvaluationReport(
            score=quality_score,
            base_score=base_score,
            completion_rate=completion_rate,
            task_type=task_type,
            judge_result=judge_result,
            eval_plan=eval_plan,
            threshold_violations=threshold_violations,
            weights_used=self.TASK_TYPE_WEIGHTS.get(task_type, self.DEFAULT_WEIGHTS),
            details={
                "duration_ms": context.duration_ms,
                "tokens_used": context.tokens_used,
                "model": context.model,
            },
        )

    def _calculate_completion_rate(
        self,
        task_description: str,
        task_result: str,
        eval_plan: Any,
    ) -> float:
        """计算任务完成度"""
        completion_rate = 0.0

        # 检查是否需要文件创建
        requires_file_creation = any(
            "文件" in c or "保存" in c or "保存到" in c for c in eval_plan.success_criteria
        )

        task_type = eval_plan.task_type or "general"

        # 基于 success_criteria 计算
        if eval_plan.success_criteria:
            completed_criteria = 0
            result_lower = task_result.lower()

            for criterion in eval_plan.success_criteria:
                matched = False
                # 提取关键词
                keywords = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]{2,}", criterion)
                for kw in keywords:
                    if len(kw) >= 2 and kw.lower() in result_lower:
                        matched = True
                        break

                # 针对特定任务类型的特殊匹配
                if eval_plan.task_type == "web_scraping":
                    nums = re.findall(r"\d+", criterion)
                    if nums and any(n in task_result for n in nums):
                        matched = True
                    if "保存" in criterion or "位置" in criterion:
                        if "保存" in task_result or "output" in result_lower:
                            matched = True
                    if "格式" in criterion or "JSON" in criterion.upper():
                        if "json" in result_lower or "csv" in result_lower:
                            matched = True

                if matched:
                    completed_criteria += 1

            completion_rate = completed_criteria / len(eval_plan.success_criteria)

        # 对于不需要文件创建的任务，提供合理默认值
        if not requires_file_creation and completion_rate == 0.0:
            if task_type in ["analysis", "research", "general", "conversation"]:
                if len(task_result) > 100:
                    completion_rate = 0.7
                elif len(task_result) > 50:
                    completion_rate = 0.5
                elif len(task_result) > 20:
                    completion_rate = 0.3

        # 使用 validation_methods 增强
        if eval_plan.validation_methods:
            validation_bonus = 0.0
            result_lower = task_result.lower()
            for method in eval_plan.validation_methods:
                method_lower = method.lower()
                if "json" in method_lower and "json" in result_lower:
                    validation_bonus += 0.1
                if "csv" in method_lower and "csv" in result_lower:
                    validation_bonus += 0.1
            completion_rate = min(completion_rate + validation_bonus, 1.0)

        return completion_rate

    def _calculate_weighted_score(
        self,
        task_type: str,
        base_score: float,
        completion_rate: float,
        efficiency: float,
    ) -> float:
        """计算加权评分"""
        weights = self.TASK_TYPE_WEIGHTS.get(task_type, self.DEFAULT_WEIGHTS)

        quality_score = (
            base_score * weights["base_score"]
            + completion_rate * weights["completion_rate"]
            + efficiency * weights["efficiency"]
        )

        return quality_score

    def _check_threshold_violations(self, judge_result: dict) -> list:
        """检查阈值违反"""
        violations = []

        scores = judge_result.get("scores", [])
        for score_item in scores:
            # 支持 JudgeScore 对象或字典
            if hasattr(score_item, "dimension"):
                dimension = score_item.dimension
                score_value = score_item.score / 5.0  # 转换为 0-1
            else:
                dimension = score_item.get("dimension", "")
                score_value = score_item.get("score", 0) / 5.0  # 转换为 0-1

            if dimension in self.DIMENSION_THRESHOLDS:
                config = self.DIMENSION_THRESHOLDS[dimension]
                if score_value < config["threshold"]:
                    violations.append(
                        {
                            "dimension": dimension,
                            "score": score_value,
                            "threshold": config["threshold"],
                            "blocking": config["blocking"],
                        }
                    )

        return violations
