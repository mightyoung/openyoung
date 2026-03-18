"""
Human Grader - 人工判定
用于需要人工审核的评估场景
"""

import time
from typing import Any, Optional

from ..benchmark import GraderConfig, GraderType, HumanGraderConfig
from .base import BaseGrader, GraderOutput


class HumanGrader(BaseGrader):
    """Human Adjudication Grader"""

    def __init__(self, config: GraderConfig):
        super().__init__(config)
        assert config.grader_type == GraderType.HUMAN, "Must be HUMAN"
        assert config.human_config is not None, "human_config is required"
        self.human_config: HumanGraderConfig = config.human_config

    async def grade(
        self,
        task_id: str,
        transcript: list[dict[str, Any]],
        outcome: dict[str, Any],
        context: dict[str, Any],
    ) -> GraderOutput:
        """
        执行人工判定

        HumanGrader 本身不执行判定，而是:
        1. 生成判定请求
        2. 返回 PENDING 状态
        3. 外部系统(如 WebUI)收集人工输入后更新结果
        """
        import time as t

        start = t.perf_counter()
        elapsed_ms = (t.perf_counter() - start) * 1000

        # 生成判定提示
        instruction = self._build_instruction(task_id, transcript, outcome, context)

        # 返回 PENDING 状态，等待人工输入
        # 外部系统通过 grader_name + task_id 存储人工判定结果
        return GraderOutput(
            grader_name=self.name,
            grader_type=GraderType.HUMAN,
            passed=False,  # PENDING
            score=0.0,  # PENDING
            details=f"[PENDING HUMAN REVIEW] {instruction}",
            raw_output=instruction,
            latency_ms=elapsed_ms,
        )

    def _build_instruction(
        self,
        task_id: str,
        transcript: list[dict[str, Any]],
        outcome: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """构建人工判定说明"""
        instruction = self.human_config.instruction

        # 添加任务信息
        task_desc = context.get("task_desc", "Unknown task")
        prompt_text = context.get("prompt", "Not available")

        # 提取关键信息
        final_output = str(outcome.get("result", outcome))[:500]

        full_instruction = f"""# Human Review Required

## Task: {task_id}
## Description: {task_desc}

## Agent Prompt
{prompt_text}

## Final Output
{final_output}

## Scoring Criteria
{chr(10).join(f"- {c}" for c in self.human_config.scoring_criteria)}

## Your Instruction
{instruction}

## Output Format
{self.human_config.output_format}
"""
        return full_instruction

    def parse_human_input(self, human_input: str) -> GraderOutput:
        """
        解析人工输入并生成最终判定结果

        由外部系统(如 WebUI)调用
        """
        # 简单解析 pass/fail
        input_lower = human_input.lower().strip()

        if "pass" in input_lower or "通过" in input_lower or "yes" in input_lower:
            passed = True
            score = 1.0
        elif "fail" in input_lower or "失败" in input_lower or "no" in input_lower:
            passed = False
            score = 0.0
        else:
            # 尝试解析分数
            import re

            score_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", human_input)
            if score_match:
                score = float(score_match.group(1)) / 10.0
                passed = score >= 0.7
            else:
                # 默认待定
                passed = False
                score = 0.0

        return GraderOutput(
            grader_name=self.name,
            grader_type=GraderType.HUMAN,
            passed=passed,
            score=score,
            details=human_input[:500],
            raw_output=human_input,
        )
