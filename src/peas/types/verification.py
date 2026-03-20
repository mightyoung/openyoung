"""
Verification types for PEAS
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class VerificationStatus(Enum):
    """验证状态"""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"


class DriftLevel(Enum):
    """偏离级别"""

    NONE = 0
    MINOR = 1
    MODERATE = 2
    SEVERE = 3
    CRITICAL = 4

    def __str__(self) -> str:
        return f"DriftLevel.{self.name}"


class FeedbackAction(Enum):
    """反馈动作"""

    COMPLETE = "complete"
    RETRY = "retry"
    REPLAN = "replan"
    ESCALATE = "escalate"


@dataclass
class FeatureStatus:
    """功能点状态"""

    req_id: str
    status: VerificationStatus
    evidence: list[str] = field(default_factory=list)
    notes: Optional[str] = None

    def is_verified(self) -> bool:
        return self.status == VerificationStatus.VERIFIED

    def is_failed(self) -> bool:
        return self.status == VerificationStatus.FAILED

    def __str__(self) -> str:
        return f"FeatureStatus({self.req_id}: {self.status.value})"


@dataclass
class DriftReport:
    """偏离报告"""

    drift_score: float  # 0-100
    level: DriftLevel
    verified_count: int
    failed_count: int
    total_count: int
    recommendations: list[str] = field(default_factory=list)

    @property
    def alignment_rate(self) -> float:
        """对齐率"""
        if self.total_count == 0:
            return 100.0
        return (self.verified_count / self.total_count) * 100

    @property
    def is_aligned(self) -> bool:
        """是否对齐"""
        return self.level in (DriftLevel.NONE, DriftLevel.MINOR)

    def __str__(self) -> str:
        return (
            f"DriftReport(score={self.drift_score:.1f}%, "
            f"level={self.level.name}, "
            f"aligned={self.alignment_rate:.1f}%)"
        )
