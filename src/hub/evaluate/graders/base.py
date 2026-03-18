"""
Base Grader - 所有 Grader 的抽象基类
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from ..benchmark import GraderConfig, GraderType


@dataclass
class GraderOutput:
    """Grader 输出"""

    grader_name: str
    grader_type: GraderType

    # 判定结果
    passed: bool
    score: float  # 0.0 - 1.0
    details: str

    # 原始输出 (调试用)
    raw_output: Optional[str] = None

    # 指标
    latency_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "grader_name": self.grader_name,
            "grader_type": self.grader_type.value,
            "passed": self.passed,
            "score": self.score,
            "details": self.details,
            "raw_output": self.raw_output,
            "latency_ms": self.latency_ms,
            "error": self.error,
        }


class BaseGrader(ABC):
    """
    Grader 抽象基类

    所有 Grader 必须实现 grade() 方法
    """

    def __init__(self, config: GraderConfig):
        self.config = config
        self.name = config.name
        self.grader_type = config.grader_type
        self.required = config.required
        self.weight = config.weight
        self.timeout_sec = config.timeout_sec

    @abstractmethod
    async def grade(
        self,
        task_id: str,
        transcript: list[dict[str, Any]],
        outcome: dict[str, Any],
        context: dict[str, Any],
    ) -> GraderOutput:
        """
        执行评判

        Args:
            task_id: 任务 ID
            transcript: 执行轨迹 (tool calls, messages, etc.)
            outcome: 最终环境状态
            context: 额外上下文 (working_dir, expected_output, etc.)

        Returns:
            GraderOutput: 评判结果
        """
        raise NotImplementedError

    async def _run_with_timing(self, coro) -> tuple[Any, float]:
        """执行协程并计时"""
        start = time.perf_counter()
        result = await coro
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed
