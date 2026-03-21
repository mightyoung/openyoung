"""
Markdown Parser - 解析Markdown设计文档

M1.1: 核心Parser实现
"""

import html as html_escape
import re
from pathlib import Path
from typing import Optional

from ..types import FeaturePoint, ParsedDocument, Priority

# Security: Input size limits
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB


def _escape_for_html(text: str) -> str:
    """Escape text for safe HTML display (XSS prevention)

    This should be used when rendering parsed content in HTML contexts.
    """
    return html_escape.escape(text)


# ============================================================================
# Pre-compiled Regex Patterns (module level for performance)
# ============================================================================

# Markdown标题正则
_HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")

# 功能点标记模式 - 预编译
_FEATURE_MARKER_PATTERNS = [
    re.compile(r"^[-*]\s+\[?\s*(?:feature|功能|feat|FR)[:\s]+(.+)$", re.IGNORECASE),
    re.compile(r"^[-*]\s+\[?\s*(?:requirement|需求|REQ)[:\s]+(.+)$", re.IGNORECASE),
]

# 优先级检测模式 - 预编译
_PRIORITY_PATTERNS = {
    Priority.MUST: [
        re.compile(r"(?:must|必须|强制|required|必选)", re.IGNORECASE),
        re.compile(r"\(M\)"),
        re.compile(r"\[M\]"),
    ],
    Priority.SHOULD: [
        re.compile(r"(?:should|应该|建议|recommended)", re.IGNORECASE),
        re.compile(r"\(S\)"),
        re.compile(r"\[S\]"),
    ],
    Priority.COULD: [
        re.compile(r"(?:could|可以|可选|optional)", re.IGNORECASE),
        re.compile(r"\(C\)"),
        re.compile(r"\[C\]"),
    ],
}

# Given-When-Then验收标准模式
_GWT_PATTERN = re.compile(r"(?:given|when|then|假设|当|则|前提|条件)[:\s]+([^\n]+)", re.IGNORECASE)


class MarkdownParser:
    """Markdown文档解析器

    解析Markdown格式的设计文档，提取：
    - 标题
    - 章节结构
    - 功能点列表
    - 验收标准 (Given-When-Then模式)
    """

    # Markdown标题正则
    HEADING_PATTERN = _HEADING_PATTERN

    # 功能点标记模式
    FEATURE_MARKERS = _FEATURE_MARKER_PATTERNS

    # 优先级检测模式 - 简化匹配，直接查找关键词
    PRIORITY_PATTERNS = _PRIORITY_PATTERNS

    # Given-When-Then验收标准模式
    GWT_PATTERN = _GWT_PATTERN

    def __init__(self):
        self._feature_counter = 0
        self._section_stack = []

    def parse(self, content: str) -> ParsedDocument:
        """解析Markdown文档

        Args:
            content: Markdown格式的设计文档内容

        Returns:
            ParsedDocument: 结构化的文档对象

        Raises:
            ValueError: If content exceeds MAX_CONTENT_SIZE
        """
        # Security: Validate input size before processing
        if len(content.encode("utf-8")) > MAX_CONTENT_SIZE:
            raise ValueError(
                f"Content size exceeds maximum allowed size of {MAX_CONTENT_SIZE} bytes"
            )

        lines = content.split("\n")
        self._feature_counter = 0
        self._section_stack = []

        # 1. 提取标题
        title = self._extract_title(lines)

        # 2. 提取章节
        sections = self._extract_sections(lines)

        # 3. 提取功能点
        feature_points = self._extract_feature_points(lines)

        return ParsedDocument(
            title=title,
            sections=sections,
            feature_points=feature_points,
            raw_content=content,
            metadata={"parser_version": "1.0", "line_count": len(lines)},
        )

    def _extract_title(self, lines: list[str]) -> str:
        """提取文档标题"""
        for line in lines:
            match = self.HEADING_PATTERN.match(line.strip())
            if match and match.group(1) == "#":
                return match.group(2).strip()

        # 如果没有找到标题，返回第一行非空行
        for line in lines:
            if line.strip():
                return line.strip()[:100]  # 截断最长100字符

        return "Untitled Document"

    def _extract_sections(self, lines: list[str]) -> list[str]:
        """提取章节标题"""
        sections = []

        for line in lines:
            match = self.HEADING_PATTERN.match(line.strip())
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()

                # 保持层级结构
                while len(self._section_stack) >= level:
                    self._section_stack.pop()

                if level > 1:  # 不包含顶级标题
                    sections.append(title)

                self._section_stack.append(title)

        return sections

    def _extract_feature_points(self, lines: list[str]) -> list[FeaturePoint]:
        """提取功能点列表"""
        feature_points = []
        current_section = None
        current_fp = None
        current_fp_lines = []  # 跟踪功能点后续行
        gwt_criteria = []
        in_gwt_section = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测章节变化
            match = self.HEADING_PATTERN.match(stripped)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()

                if level > 1:  # 子标题
                    current_section = heading_text

                # 检测是否进入验收标准章节
                if "验收" in heading_text or "acceptance" in heading_text.lower():
                    in_gwt_section = True
                else:
                    in_gwt_section = False
                continue

            # 在验收标准章节收集Given-When-Then
            if in_gwt_section:
                gwt_matches = self.GWT_PATTERN.findall(stripped)
                if gwt_matches:
                    gwt_criteria.extend(gwt_matches)
                continue

            # 检测功能点标记
            matched = False
            for pattern in self.FEATURE_MARKERS:
                match = pattern.match(stripped)
                if match:
                    # 保存前一个功能点
                    if current_fp:
                        # 检查前面收集的行中的优先级
                        for fp_line in current_fp_lines:
                            priority = self._detect_priority(fp_line)
                            if priority == Priority.MUST:
                                current_fp.priority = Priority.MUST
                                break

                        if gwt_criteria:
                            current_fp.acceptance_criteria = gwt_criteria.copy()
                            gwt_criteria = []
                        feature_points.append(current_fp)

                    # 创建新功能点
                    self._feature_counter += 1
                    title = match.group(1).strip()
                    priority = self._detect_priority(title)

                    current_fp = FeaturePoint(
                        id=f"FP-{self._feature_counter:03d}",
                        title=title,
                        description=title,
                        priority=priority,
                        related_section=current_section,
                    )
                    current_fp_lines = []
                    matched = True
                    break

            if not matched and current_fp:
                # 收集功能点后续行用于优先级检测
                current_fp_lines.append(stripped)
                # 检测Given-When-Then在功能点描述中
                gwt_matches = self.GWT_PATTERN.findall(stripped)
                if gwt_matches:
                    gwt_criteria.extend(gwt_matches)

        # 保存最后一个功能点
        if current_fp:
            # 检查前面收集的行中的优先级
            for fp_line in current_fp_lines:
                priority = self._detect_priority(fp_line)
                if priority == Priority.MUST:
                    current_fp.priority = Priority.MUST
                    break
            if gwt_criteria:
                current_fp.acceptance_criteria = gwt_criteria
            feature_points.append(current_fp)

        return feature_points

    def _detect_priority(self, text: str) -> Priority:
        """检测优先级"""
        text_lower = text.lower()

        for priority, patterns in self.PRIORITY_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return priority

        # 默认优先级
        return Priority.SHOULD

    def parse_file(self, file_path: str, *, allowed_dir: Optional[str] = None) -> ParsedDocument:
        """从文件解析

        Args:
            file_path: Markdown文件路径
            allowed_dir: Optional directory to restrict file access to (prevents path traversal)

        Returns:
            ParsedDocument: 结构化的文档对象

        Raises:
            ValueError: If file_path escapes the allowed directory
        """
        # Security: Resolve and validate path to prevent directory traversal
        resolved_path = Path(file_path).resolve()

        if allowed_dir is not None:
            allowed_path = Path(allowed_dir).resolve()
            # Ensure the resolved path is within the allowed directory
            try:
                resolved_path.relative_to(allowed_path)
            except ValueError:
                raise ValueError(
                    f"File path '{file_path}' escapes allowed directory '{allowed_dir}'"
                )

        with open(resolved_path, encoding="utf-8") as f:
            content = f.read()
        return self.parse(content)


# 便捷函数
def parse_markdown(content: str) -> ParsedDocument:
    """解析Markdown文档的便捷函数"""
    parser = MarkdownParser()
    return parser.parse(content)


def parse_markdown_file(file_path: str) -> ParsedDocument:
    """从文件解析Markdown文档的便捷函数"""
    parser = MarkdownParser()
    return parser.parse_file(file_path)
