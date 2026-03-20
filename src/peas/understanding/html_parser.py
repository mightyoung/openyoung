"""
HTML Parser - 解析HTML设计文档

M1.2: HTML原型解析器
支持从Figma/HTML导出提取feature points
"""

import html as html_escape
import re
from dataclasses import dataclass
from html.parser import HTMLParser as BaseHTMLParser
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
# HTML Element Patterns (module level for performance)
# ============================================================================

# 按钮元素模式
_BUTTON_PATTERNS = [
    re.compile(r"button|btn", re.IGNORECASE),
    re.compile(r"submit|submit[\s_-]?button", re.IGNORECASE),
]

# 表单元素模式
_FORM_PATTERNS = [
    re.compile(r"form|input|textarea|select", re.IGNORECASE),
    re.compile(r"checkbox|radio", re.IGNORECASE),
    re.compile(r"field", re.IGNORECASE),
]

# 导航元素模式
_NAVIGATION_PATTERNS = [
    re.compile(r"nav|menu|navbar|header|footer", re.IGNORECASE),
    re.compile(r"navigation|sidebar", re.IGNORECASE),
]

# 交互元素模式
_INTERACTIVE_PATTERNS = [
    re.compile(r"link|a[\s_-]?tag", re.IGNORECASE),
    re.compile(r"clickable|click", re.IGNORECASE),
    re.compile(r"toggle|tab|accordion", re.IGNORECASE),
]

# 数据显示模式
_DATA_PATTERNS = [
    re.compile(r"table|grid|list|card", re.IGNORECASE),
    re.compile(r"display|show|view|browse", re.IGNORECASE),
]

# 优先级标记模式
_PRIORITY_MARKERS = {
    Priority.MUST: [
        re.compile(r"(?:must|required|必填|必需|必须)", re.IGNORECASE),
        re.compile(r"\*[\s*]*必[\s*]*\*", re.IGNORECASE),
    ],
    Priority.SHOULD: [
        re.compile(r"(?:should|建议|推荐|应该)", re.IGNORECASE),
    ],
    Priority.COULD: [
        re.compile(r"(?:could|optional|可选|可以)", re.IGNORECASE),
    ],
}


class _HTMLFeatureExtractor(BaseHTMLParser):
    """HTML特征提取器"""

    def __init__(self):
        super().__init__()
        self._feature_counter = 0
        self._sections = []
        self._current_section = None
        self._feature_points: list[FeaturePoint] = []
        self._current_feature: Optional[FeaturePoint] = None
        self._current_content = ""
        self._title = "Untitled HTML Document"
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]):
        """处理开始标签"""
        attrs_dict = {k: v for k, v in attrs if v is not None}

        # 提取标题
        if tag.lower() == "title":
            self._in_title = True
            return

        # 提取h1-h6作为章节
        if tag.lower() in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            if self._current_feature:
                self._finalize_feature()
            level = int(tag[1])
            if level > 1:
                self._current_section = self._current_content.strip() or "Untitled Section"
                if self._current_section not in self._sections:
                    self._sections.append(self._current_section)
            return

        # 检测按钮元素
        if tag.lower() == "button":
            self._extract_element_feature("button", attrs_dict, "按钮")
            return

        # 检测输入元素
        if tag.lower() in ["input", "textarea", "select"]:
            input_type = attrs_dict.get("type", "text")
            self._extract_element_feature(f"{tag}:{input_type}", attrs_dict, "表单输入")
            return

        # 检测链接
        if tag.lower() == "a":
            href = attrs_dict.get("href", "")
            text = attrs_dict.get("text", "")
            if href or text:
                self._extract_element_feature("link", attrs_dict, "链接")
            return

        # 检测导航
        if tag.lower() == "nav":
            if self._current_feature:
                self._finalize_feature()
            self._current_section = "Navigation"
            if "Navigation" not in self._sections:
                self._sections.append("Navigation")
            return

        # 检测卡片/列表项
        if tag.lower() in ["card", "item", "list", "row"]:
            self._extract_element_feature("list-item", attrs_dict, "列表项")
            return

    def handle_endtag(self, tag: str):
        """处理结束标签"""
        if tag.lower() == "title":
            self._in_title = False
            # 使用第一个非空内容作为标题
            if self._current_content.strip():
                self._title = self._current_content.strip()[:100]
            self._current_content = ""
            return

        if tag.lower() in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            self._current_content = ""
            return

    def handle_data(self, data: str):
        """处理文本内容"""
        if self._in_title:
            self._current_content += data

        if self._current_feature:
            self._current_content += data

    def handle_comment(self, data: str):
        """从HTML注释中提取功能点

        注意: 为了避免重复，这里只处理明确以 Feature: 开头的注释
        其他格式的注释由 _extract_comments_as_features 方法统一处理
        """
        data_stripped = data.strip()

        # 只匹配明确以 Feature: 开头的注释（行首匹配）
        feature_match = re.match(
            r"^(?:feature|功能|requirement|需求|req)[:\s]+([^\n\-]+)", data_stripped, re.IGNORECASE
        )
        if feature_match:
            title = feature_match.group(1).strip()
            priority = self._detect_priority(data_stripped)

            self._feature_counter += 1
            self._current_feature = FeaturePoint(
                id=f"FP-{self._feature_counter:03d}",
                title=title,
                description=title,
                priority=priority,
                related_section=self._current_section,
            )

    def _extract_element_feature(self, element_type: str, attrs: dict, default_desc: str):
        """提取元素为功能点"""
        # 从id、name、placeholder、aria-label等属性提取
        feature_name = (
            attrs.get("id")
            or attrs.get("name")
            or attrs.get("aria-label")
            or attrs.get("placeholder")
            or attrs.get("title")
            or default_desc
        )

        if not feature_name:
            return

        # 检查是否应该创建新功能点
        # 如果当前没有未完成的功能点，或者属性中有明确的功能标记
        should_create = (
            self._current_feature is None or "data-feature" in attrs or "data-requirement" in attrs
        )

        if should_create:
            if self._current_feature:
                self._finalize_feature()

            # 检测优先级
            priority = self._detect_priority(" ".join(attrs.values()))

            # 检测验收标准
            acceptance = []
            if "data-acceptance" in attrs:
                acceptance = [attrs["data-acceptance"]]

            self._feature_counter += 1
            self._current_feature = FeaturePoint(
                id=f"FP-{self._feature_counter:03d}",
                title=feature_name,
                description=f"{element_type} - {feature_name}",
                priority=priority,
                related_section=self._current_section,
                acceptance_criteria=acceptance,
            )

    def _finalize_feature(self):
        """完成当前功能点"""
        if self._current_feature:
            # 更新描述
            if not self._current_feature.description:
                self._current_feature.description = self._current_content.strip()[:200]
            self._feature_points.append(self._current_feature)
            self._current_feature = None
            self._current_content = ""

    def _detect_priority(self, text: str) -> Priority:
        """检测优先级"""
        text_lower = text.lower()

        for priority, patterns in _PRIORITY_MARKERS.items():
            for pattern in patterns:
                if pattern.search(text_lower):
                    return priority

        return Priority.SHOULD

    def get_result(self, raw_content: str) -> ParsedDocument:
        """获取解析结果"""
        # 确保最后一个功能点被添加
        self._finalize_feature()

        return ParsedDocument(
            title=self._title,
            sections=self._sections,
            feature_points=self._feature_points,
            raw_content=raw_content,
            metadata={
                "parser_version": "1.0",
                "content_length": len(raw_content),
                "source_type": "html",
            },
        )


class HTMLParser:
    """HTML文档解析器

    解析HTML格式的设计文档/原型，提取：
    - 标题
    - 章节结构
    - 功能点列表 (从HTML元素和注释中)
    - 验收标准 (从data-acceptance等属性)

    支持从Figma导出的HTML、HTML原型文件等
    """

    def __init__(self):
        pass

    def parse(self, content: str) -> ParsedDocument:
        """解析HTML文档

        Args:
            content: HTML格式的设计文档内容

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

        # 使用HTMLParser提取特征
        extractor = _HTMLFeatureExtractor()
        extractor.feed(content)

        # 总是提取结构化特征（标题、章节等）
        # 因为基于元素的提取可能不包含所有章节
        self._extract_structural_features(content, extractor)

        # 从注释中提取功能点（使用正则表达式）
        self._extract_comments_as_features(content, extractor)

        return extractor.get_result(content)

    def _extract_structural_features(
        self, content: str, extractor: Optional[_HTMLFeatureExtractor] = None
    ) -> _HTMLFeatureExtractor:
        """从HTML结构中提取功能点"""
        if extractor is None:
            extractor = _HTMLFeatureExtractor()

        # 提取页面标题
        title_match = re.search(r"<title[^>]*>([^<]+)</title>", content, re.IGNORECASE)
        if title_match:
            extractor._title = title_match.group(1).strip()

        # 提取h1作为主标题
        h1_match = re.search(r"<h1[^>]*>([^<]+)</h1>", content, re.IGNORECASE)
        if h1_match and extractor._title == "Untitled HTML Document":
            extractor._title = h1_match.group(1).strip()

        # 提取所有标题作为章节
        heading_matches = re.findall(r"<h([1-6])[^>]*>([^<]+)</h\1>", content, re.IGNORECASE)
        for level, title in heading_matches:
            level = int(level)
            if level > 1:
                section = title.strip()
                if section not in extractor._sections:
                    extractor._sections.append(section)

        # 提取常见元素作为功能点
        self._extract_elements_as_features(content, extractor)

        return extractor

    def _extract_comments_as_features(self, content: str, extractor: _HTMLFeatureExtractor):
        """从HTML注释中提取功能点"""
        # 使用正则表达式提取HTML注释
        comment_pattern = re.compile(r"<!--(.*?)-->", re.DOTALL)
        comments = comment_pattern.findall(content)

        # 用于跟踪已处理的注释，避免重复
        processed_comments = set()

        for comment in comments:
            comment = comment.strip()
            # 使用注释内容的前50个字符作为唯一标识
            comment_key = comment[:50].lower()

            # 跳过已处理的注释
            if comment_key in processed_comments:
                continue
            processed_comments.add(comment_key)

            # 检查功能点标记 - 支持 Feature:, Must:, Should:, Could:, Requirement:, 需求:, 必填:
            # 匹配模式: 标记: 描述 (必须从行首开始匹配)
            match = re.match(
                r"^(?:feature|功能|requirement|需求|req|must|should|could|必填|必须|应该|建议|可选)[:\s]+([^\n\-]+)",
                comment,
                re.IGNORECASE,
            )
            if match:
                title = match.group(1).strip()
                priority = extractor._detect_priority(comment)

                extractor._feature_counter += 1
                fp = FeaturePoint(
                    id=f"FP-{extractor._feature_counter:03d}",
                    title=title,
                    description=title,
                    priority=priority,
                    related_section=extractor._current_section,
                )
                extractor._feature_points.append(fp)

    def _extract_elements_as_features(self, content: str, extractor: _HTMLFeatureExtractor):
        """从HTML元素中提取功能点"""
        element_patterns = [
            # 表单相关
            (r'<form[^>]*(?:id|name)=["\']([^"\']+)["\'][^>]*>', "表单"),
            (r'<input[^>]*(?:type=["\']submit["\'])', "提交按钮"),
            (r'<button[^>]*(?:id|name|text)=["\']([^"\']+)["\'][^>]*>', "按钮"),
            (r'<input[^>]*(?:type=["\']checkbox["\'])', "复选框"),
            (r'<input[^>]*(?:type=["\']radio["\'])', "单选按钮"),
            (r'<select[^>]*(?:id|name)=["\']([^"\']+)["\'][^>]*>', "下拉选择"),
            (r'<textarea[^>]*(?:id|name)=["\']([^"\']+)["\'][^>]*>', "文本域"),
            # 导航相关
            (r'<nav[^>]*(?:id|name)=["\']([^"\']+)["\'][^>]*>', "导航"),
            (r'<a[^>]*(?:href)=["\']([^"\']+)["\'][^>]*>', "链接"),
            # 交互相关
            (r"<modal[^>]*>", "模态框"),
            (r"<dialog[^>]*>", "对话框"),
            (r"<tab[^>]*>", "标签页"),
            (r"<accordion[^>]*>", "折叠面板"),
            # 数据显示
            (r'<table[^>]*(?:id|name)=["\']([^"\']+)["\'][^>]*>', "表格"),
            (r"<card[^>]*>", "卡片"),
            (r"<list[^>]*>", "列表"),
        ]

        for pattern, desc in element_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                element_name = match.group(1) if match.lastindex else desc

                extractor._feature_counter += 1
                fp = FeaturePoint(
                    id=f"FP-{extractor._feature_counter:03d}",
                    title=element_name if element_name else desc,
                    description=f"{desc}: {element_name}",
                    priority=Priority.SHOULD,
                    related_section=extractor._current_section,
                )
                extractor._feature_points.append(fp)

    def parse_file(self, file_path: str, *, allowed_dir: Optional[str] = None) -> ParsedDocument:
        """从文件解析

        Args:
            file_path: HTML文件路径
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
def parse_html(content: str) -> ParsedDocument:
    """解析HTML文档的便捷函数"""
    parser = HTMLParser()
    return parser.parse(content)


def parse_html_file(file_path: str) -> ParsedDocument:
    """从文件解析HTML文档的便捷函数"""
    parser = HTMLParser()
    return parser.parse_file(file_path)
