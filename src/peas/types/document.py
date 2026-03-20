"""
Document types for PEAS
"""

import html as html_escape
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

    @property
    def title_escaped(self) -> str:
        """获取HTML转义后的标题（用于安全显示）"""
        return html_escape.escape(self.title)

    @property
    def description_escaped(self) -> str:
        """获取HTML转义后的描述（用于安全显示）"""
        return html_escape.escape(self.description)


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

    @property
    def title_escaped(self) -> str:
        """获取HTML转义后的标题（用于安全显示）"""
        return html_escape.escape(self.title)

    @property
    def raw_content_escaped(self) -> str:
        """获取HTML转义后的原始内容（用于安全显示）

        当需要在HTML页面中显示raw_content时，使用此属性
        而不是直接访问 raw_content，以防止XSS攻击。
        """
        return html_escape.escape(self.raw_content)

    def __str__(self) -> str:
        return f"ParsedDocument({self.title}, {self.total_features} features)"
