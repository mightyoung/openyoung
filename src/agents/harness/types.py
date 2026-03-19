"""
Harness Types - Streaming interface types

定义 streaming 所需的类型:
- PartialResult: 流向调用者的部分结果
- ExecutionResult: HarnessEngine 内部执行结果
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ExecutionPhase(Enum):
    """执行阶段"""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"

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

    RETRY = "retry"
    REPLAN = "replan"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    FAIL = "fail"


class EvaluationResult(Enum):
    """评估结果"""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    PENDING = "pending"


class ExecutionStatus(Enum):
    """执行状态"""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PartialResult:
    """Streaming partial result - yielded to caller"""

    phase: ExecutionPhase
    progress: float  # 0.0 - 1.0
    iteration: int
    status: ExecutionStatus
    data: dict[str, Any] = field(default_factory=dict)
    partial_output: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "phase": self.phase.value if isinstance(self.phase, ExecutionPhase) else self.phase,
            "progress": self.progress,
            "iteration": self.iteration,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            "data": self.data,
            "partial_output": self.partial_output,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class StreamingExecutionResult:
    """Execution result used internally by streaming execution"""

    phase: ExecutionPhase
    iteration: int
    status: ExecutionStatus
    evaluation: EvaluationResult = EvaluationResult.PENDING
    feedback_action: FeedbackAction = FeedbackAction.RETRY
    result: Any = None
    partial_output: Optional[str] = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
