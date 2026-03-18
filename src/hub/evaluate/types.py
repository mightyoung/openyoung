"""
Shared types for entropy management.
Kept separate to avoid circular imports between entropy.py and scanner.py.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EntropyType(str, Enum):
    """熵类型"""

    DOC_DRIFT = "doc_drift"  # 文档与代码不一致
    CONSTRAINT_VIOLATION = "constraint_violation"  # 约束违反
    DEAD_CODE = "dead_code"  # 死代码
    DEPENDENCY_DRIFT = "dependency_drift"  # 依赖漂移
    ARCHITECTURE_DECAY = "architecture_decay"  # 架构腐化


class Severity(str, Enum):
    """严重程度"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EntropyIssue:
    """熵问题"""

    entropy_type: EntropyType
    severity: Severity
    file_path: str | None = None
    symbol_name: str | None = None
    description: str = ""
    evidence: str = ""
    recommendation: str = ""
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class EntropyReport:
    """熵管理报告"""

    repo_root: str
    scanned_at: datetime = field(default_factory=datetime.now)
    total_files_scanned: int = 0
    issues: list[EntropyIssue] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.LOW)

    @property
    def total_issues(self) -> int:
        return len(self.issues)
