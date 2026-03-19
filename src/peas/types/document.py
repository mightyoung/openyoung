"""
Document types for PEAS
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Priority(Enum):
    """需求优先级"""
    MUST = "must"
    SHOULD = "should"
    COULD = "could"


@dataclass
class FeaturePoint:
    """功能点"""
    id: str  # "FP-001"
    title: str
    description: str
    priority: Priority
    acceptance_criteria: list[str] = field(default_factory=list)
    related_section: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.id}] {self.title} ({self.priority.value})"


@dataclass
class ParsedDocument:
    """解析后的文档"""
    title: str
    sections: list[str]
    feature_points: list[FeaturePoint]
    raw_content: str
    metadata: dict = field(default_factory=dict)

    @property
    def total_features(self) -> int:
        return len(self.feature_points)

    @property
    def must_features(self) -> list[FeaturePoint]:
        return [fp for fp in self.feature_points if fp.priority == Priority.MUST]

    @property
    def should_features(self) -> list[FeaturePoint]:
        return [fp for fp in self.feature_points if fp.priority == Priority.SHOULD]

    def __str__(self) -> str:
        return f"ParsedDocument({self.title}, {self.total_features} features)"
