"""
Reflection Mechanism - 反思机制

提供结果自检、错误恢复功能
参考 AutoGPT, ReAct 的反思模式
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ReflectionType(Enum):
    """反思类型"""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class ReflectionResult:
    """反思结果"""

    reflection_type: ReflectionType
    assessment: str  # 评估描述
    confidence: float  # 置信度 0-1
    issues: list[str] = field(default_factory=list)  # 发现的问题
    suggestions: list[str] = field(default_factory=list)  # 改进建议
    should_retry: bool = False
    retry_reason: str = ""


@dataclass
class ExecutionRecord:
    """执行记录"""

    id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    task: str = ""
    input_data: Any = None
    output_data: Any = None
    error: str = ""
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class ReflectionMechanism:
    """反思机制"""

    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
        self.execution_history: list[ExecutionRecord] = []

    async def reflect(
        self,
        task: str,
        result: Any,
        expected_output: Optional[str] = None,
    ) -> ReflectionResult:
        """
        反思执行结果

        Args:
            task: 原始任务
            result: 执行结果
            expected_output: 期望输出

        Returns:
            ReflectionResult: 反思结果
        """
        # 基础检查
        issues = []
        suggestions = []

        # 1. 检查结果是否为空
        if result is None:
            issues.append("结果为空")
            suggestions.append("检查执行过程是否正确")
            return ReflectionResult(
                reflection_type=ReflectionType.FAILURE,
                assessment="执行未产生结果",
                confidence=1.0,
                issues=issues,
                suggestions=suggestions,
                should_retry=True,
                retry_reason="结果为空",
            )

        # 2. 检查结果类型
        if isinstance(result, str):
            if len(result.strip()) == 0:
                issues.append("结果为空字符串")
                return ReflectionResult(
                    reflection_type=ReflectionType.FAILURE,
                    assessment="结果为空",
                    confidence=1.0,
                    issues=issues,
                    suggestions=["检查执行过程"],
                    should_retry=True,
                )

            # 检查错误关键词
            error_keywords = ["error", "failed", "exception", "Traceback"]
            has_error = any(kw in result.lower() for kw in error_keywords)
            if has_error:
                issues.append("结果包含错误信息")
                suggestions.append("分析错误信息并修复")
                return ReflectionResult(
                    reflection_type=ReflectionType.ERROR,
                    assessment="执行出错",
                    confidence=0.9,
                    issues=issues,
                    suggestions=suggestions,
                    should_retry=True,
                    retry_reason="执行错误",
                )

        # 3. 与期望输出对比
        if expected_output and isinstance(result, str):
            # 简单的关键词匹配
            expected_keywords = expected_output.split()
            matched = sum(1 for kw in expected_keywords if kw.lower() in result.lower())
            match_rate = matched / len(expected_keywords) if expected_keywords else 0

            if match_rate < self.confidence_threshold:
                issues.append(f"期望输出匹配度仅 {match_rate:.0%}")
                suggestions.append("重新理解任务要求")

                return ReflectionResult(
                    reflection_type=ReflectionType.PARTIAL,
                    assessment=f"部分成功 (匹配度 {match_rate:.0%})",
                    confidence=match_rate,
                    issues=issues,
                    suggestions=suggestions,
                    should_retry=True,
                    retry_reason="输出不匹配",
                )

        # 4. 计算置信度
        confidence = self._calculate_confidence(result, issues)

        # 5. 判断是否成功
        if confidence >= self.confidence_threshold and not issues:
            return ReflectionResult(
                reflection_type=ReflectionType.SUCCESS,
                assessment="执行成功",
                confidence=confidence,
                issues=[],
                suggestions=[],
                should_retry=False,
            )
        elif confidence >= 0.5:
            return ReflectionResult(
                reflection_type=ReflectionType.PARTIAL,
                assessment="部分成功",
                confidence=confidence,
                issues=issues,
                suggestions=suggestions,
                should_retry=True,
                retry_reason="部分成功，建议重试",
            )
        else:
            return ReflectionResult(
                reflection_type=ReflectionType.FAILURE,
                assessment="执行失败",
                confidence=confidence,
                issues=issues,
                suggestions=suggestions,
                should_retry=True,
                retry_reason="执行失败",
            )

    def _calculate_confidence(self, result: Any, issues: list[str]) -> float:
        """计算置信度"""
        base_confidence = 1.0

        # 根据问题数量降低置信度
        if issues:
            base_confidence -= len(issues) * 0.2

        # 根据结果类型调整
        if isinstance(result, dict):
            # 检查是否有错误字段
            if "error" in result or "failed" in result:
                base_confidence -= 0.3
        elif isinstance(result, str):
            # 检查长度是否合理
            if len(result) < 10:
                base_confidence -= 0.2

        return max(0.0, min(1.0, base_confidence))

    def record_execution(self, record: ExecutionRecord):
        """记录执行历史"""
        self.execution_history.append(record)

    def get_recent_executions(self, limit: int = 10) -> list[ExecutionRecord]:
        """获取最近的执行记录"""
        return self.execution_history[-limit:]

    def analyze_patterns(self) -> dict[str, Any]:
        """分析执行模式"""
        if not self.execution_history:
            return {"pattern": "no_data"}

        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if not r.error)

        avg_duration = sum(r.duration_ms for r in self.execution_history) / total

        return {
            "total_executions": total,
            "success_rate": success / total if total > 0 else 0,
            "average_duration_ms": avg_duration,
            "recent_errors": [r.error for r in self.execution_history[-5:] if r.error],
        }


class ErrorRecovery:
    """错误恢复机制"""

    def __init__(self):
        self.error_patterns: dict[str, str] = {}

    def register_pattern(self, error_pattern: str, recovery_action: str):
        """注册错误模式与恢复动作"""
        self.error_patterns[error_pattern] = recovery_action

    def get_recovery_action(self, error: str) -> Optional[str]:
        """获取恢复动作"""
        for pattern, action in self.error_patterns.items():
            if pattern.lower() in error.lower():
                return action
        return None

    async def recover(self, error: str, context: dict) -> dict:
        """
        执行恢复

        Args:
            error: 错误信息
            context: 错误上下文

        Returns:
            恢复结果
        """
        recovery_action = self.get_recovery_action(error)

        if recovery_action:
            return {
                "recovered": True,
                "action": recovery_action,
                "context": context,
            }

        # 默认恢复
        return {
            "recovered": False,
            "action": "retry",
            "suggestion": "请检查错误并手动修复",
        }
