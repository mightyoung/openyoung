"""
Style Profiler - 风格分析器

M1.3: 分析文档写作风格，用于生成符合项目风格的输出
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ToneStyle(Enum):
    """文档语调风格"""

    FORMAL = "formal"  # 正式
    CASUAL = "casual"  # 随意
    TECHNICAL = "technical"  # 技术性
    BUSINESS = "business"  # 商业
    ACADEMIC = "academic"  # 学术


class DocumentationType(Enum):
    """文档类型"""

    SPEC = "spec"  # 规格说明书
    API = "api"  # API文档
    GUIDE = "guide"  # 用户指南
    CHANGELOG = "changelog"  # 变更日志
    README = "readme"  # README
    UNKNOWN = "unknown"


@dataclass
class StyleProfile:
    """风格画像"""

    tone: ToneStyle = ToneStyle.TECHNICAL
    doc_type: DocumentationType = DocumentationType.UNKNOWN
    language: str = "zh"  # zh/en/mixed
    avg_sentence_length: float = 20.0
    has_numbered_sections: bool = False
    uses_bullet_points: bool = False
    technical_terms_density: float = 0.0
    code_examples_count: int = 0
    section_depth: int = 1
    consistency_score: float = 1.0  # 0-1, 风格一致性

    def __str__(self) -> str:
        return (
            f"StyleProfile(type={self.doc_type.value}, tone={self.tone.value}, "
            f"lang={self.language}, consistency={self.consistency_score:.2f})"
        )


class StyleProfiler:
    """风格分析器

    分析文档的写作风格，提取风格特征用于生成一致的输出
    """

    # 技术术语模式
    TECHNICAL_PATTERNS = [
        r"\b(?:API|REST|GraphQL|JSON|XML|SDK|CLI|UI|UX|CSS|HTML|JS|TS)\b",
        r"\b(?:async|await|promise|callback|hook|plugin|middleware)\b",
        r"\b(?:authentication|authorization|encryption|token|JWT)\b",
        r"\b(?:database|query|index|cache|proxy|load.*balanc)\b",
        r"\b(?:microservice|container|docker|k8s|deploy|orchestrat)\b",
    ]

    # 代码块模式
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```|`[^`]+`")

    # 标题模式
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE)

    # 编号章节模式
    NUMBERED_SECTION_PATTERN = re.compile(r"^\d+\.\d+(?:\.\d+)*\s+.+$", re.MULTILINE)

    # 列表模式
    BULLET_PATTERN = re.compile(r"^[\-\*]\s+|^(\d+)\.\s+", re.MULTILINE)

    def __init__(self):
        """初始化风格分析器"""
        self._tech_patterns = [re.compile(p, re.IGNORECASE) for p in self.TECHNICAL_PATTERNS]

    def analyze(self, content: str) -> StyleProfile:
        """分析文档风格

        Args:
            content: 文档内容

        Returns:
            StyleProfile: 风格画像
        """
        if not content or not content.strip():
            return StyleProfile()

        profile = StyleProfile()

        # 检测文档类型
        profile.doc_type = self._detect_doc_type(content)

        # 检测语言
        profile.language = self._detect_language(content)

        # 检测语调
        profile.tone = self._detect_tone(content)

        # 计算平均句子长度
        profile.avg_sentence_length = self._calc_avg_sentence_length(content)

        # 检测编号章节
        profile.has_numbered_sections = bool(self.NUMBERED_SECTION_PATTERN.search(content))

        # 检测列表使用
        profile.uses_bullet_points = bool(self.BULLET_PATTERN.search(content))

        # 计算技术术语密度
        profile.technical_terms_density = self._calc_technical_density(content)

        # 统计代码示例
        profile.code_examples_count = len(self.CODE_BLOCK_PATTERN.findall(content))

        # 计算章节深度
        profile.section_depth = self._calc_section_depth(content)

        # 计算风格一致性
        profile.consistency_score = self._calc_consistency(content)

        return profile

    def _detect_doc_type(self, content: str) -> DocumentationType:
        """检测文档类型"""
        content_lower = content.lower()

        # README检测
        if "# " + content.split("\n")[0].strip().lstrip("#") in content[:200]:
            if any(
                kw in content_lower[:500]
                for kw in ["install", "setup", "getting started", "安装", "快速开始"]
            ):
                return DocumentationType.GUIDE

        # API文档检测
        if "endpoint" in content_lower or "route" in content_lower or "请求" in content:
            if any(
                kw in content_lower for kw in ["get", "post", "put", "delete", "参数", "response"]
            ):
                return DocumentationType.API

        # Changelog检测
        if re.search(r"\d+\.\d+\.\d+", content) and any(
            kw in content_lower for kw in ["changed", "fixed", "added", "变更", "修复", "新增"]
        ):
            return DocumentationType.CHANGELOG

        # 规格说明书检测
        if any(
            kw in content_lower for kw in ["功能需求", "feature", "requirement", "规格", "spec"]
        ):
            return DocumentationType.SPEC

        # 指南检测
        if any(kw in content_lower[:1000] for kw in ["how to", "tutorial", "指南", "教程", "使用"]):
            return DocumentationType.GUIDE

        return DocumentationType.UNKNOWN

    def _detect_language(self, content: str) -> str:
        """检测文档语言"""
        # 中文字符范围
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", content))
        # 英文单词
        english_words = len(re.findall(r"[a-zA-Z]{2,}", content))

        if chinese_chars > english_words * 0.3:
            return "zh"
        elif english_words > chinese_chars * 2:
            return "en"
        return "mixed"

    def _detect_tone(self, content: str) -> ToneStyle:
        """检测文档语调"""
        content_lower = content.lower()

        # 技术性检测
        tech_indicators = sum(1 for p in self._tech_patterns if p.search(content))
        if tech_indicators >= 3:
            return ToneStyle.TECHNICAL

        # 商业/正式检测
        formal_indicators = [
            "综上所述",
            "因此",
            " hereby",
            " herein",
            " thereof",
            "综上所述",
            "基于以上",
            "根据",
            "规定",
        ]
        if sum(1 for ind in formal_indicators if ind in content_lower) >= 2:
            return ToneStyle.BUSINESS

        # 学术检测
        academic_indicators = [
            "研究表明",
            "证明",
            "指出",
            "认为",
            "research",
            "study",
            "analysis",
            "method",
        ]
        if sum(1 for ind in academic_indicators if ind in content_lower) >= 2:
            return ToneStyle.ACADEMIC

        # 随意检测
        casual_indicators = ["!", "😊", "😀", "哈哈", "注意", "tip:", "note:"]
        if sum(1 for ind in casual_indicators if ind in content) >= 2:
            return ToneStyle.CASUAL

        return ToneStyle.FORMAL

    def _calc_avg_sentence_length(self, content: str) -> float:
        """计算平均句子长度（按字符计）"""
        # 移除代码块
        text = self.CODE_BLOCK_PATTERN.sub("", content)
        # 按中英文句号/问号/感叹号分割
        sentences = re.split(r"[。.!?]", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 20.0

        total_len = sum(len(s) for s in sentences)
        return total_len / len(sentences)

    def _calc_technical_density(self, content: str) -> float:
        """计算技术术语密度"""
        # 移除代码块后统计
        text = self.CODE_BLOCK_PATTERN.sub("", content)
        total_words = len(re.findall(r"\b\w+\b", text))

        if total_words == 0:
            return 0.0

        tech_matches = sum(len(p.findall(text)) for p in self._tech_patterns)

        return min(tech_matches / total_words, 1.0)

    def _calc_section_depth(self, content: str) -> int:
        """计算章节深度（最大标题级别）"""
        headings = self.HEADING_PATTERN.findall(content)
        if not headings:
            return 1

        # 最大的#数量即最深层级
        max_level = max(len(h) for h in headings)
        return min(max_level, 6)

    def _calc_consistency(self, content: str) -> float:
        """计算风格一致性（0-1）"""
        # 检查标题格式一致性
        headings = self.HEADING_PATTERN.findall(content)

        if len(headings) < 2:
            return 1.0

        # 检查标题级别使用的一致性
        levels = [len(h) for h in headings]
        level_counts = {}
        for l in levels:
            level_counts[l] = level_counts.get(l, 0) + 1

        # 最常用的级别
        most_common = max(level_counts.values())

        # 一致性 = 最常用级别占比
        consistency = most_common / len(levels)

        return consistency

    def compare(self, profile1: StyleProfile, profile2: StyleProfile) -> float:
        """比较两个风格的相似度

        Args:
            profile1: 风格画像1
            profile2: 风格画像2

        Returns:
            float: 相似度 0-1
        """
        score = 0.0
        weights = {
            "tone": 0.2,
            "doc_type": 0.25,
            "language": 0.2,
            "sentence_length": 0.15,
            "bullet_points": 0.1,
            "tech_density": 0.1,
        }

        if profile1.tone == profile2.tone:
            score += weights["tone"]

        if profile1.doc_type == profile2.doc_type:
            score += weights["doc_type"]

        if profile1.language == profile2.language:
            score += weights["language"]

        # 句子长度相似度
        len_diff = abs(profile1.avg_sentence_length - profile2.avg_sentence_length)
        if len_diff < 5:
            score += weights["sentence_length"] * (1 - len_diff / 5)

        # 列表使用一致性
        if profile1.uses_bullet_points == profile2.uses_bullet_points:
            score += weights["bullet_points"]

        # 技术密度相似度
        density_diff = abs(profile1.technical_terms_density - profile2.technical_terms_density)
        score += weights["tech_density"] * (1 - density_diff)

        return score

    def apply_style(
        self,
        content: str,
        target_profile: StyleProfile,
        target_language: Optional[str] = None,
    ) -> str:
        """根据目标风格调整内容（基础版本）

        Args:
            content: 原始内容
            target_profile: 目标风格
            target_language: 目标语言（可选）

        Returns:
            str: 调整后的内容
        """
        # 语言转换
        if target_language and target_language != self._detect_language(content):
            # 基础实现：不做实际转换，只做标记
            pass

        # 添加风格标记注释
        style_comment = f"\n<!-- Style: {target_profile} -->\n"

        return style_comment + content


def profile_document(content: str) -> StyleProfile:
    """分析文档风格的便捷函数"""
    profiler = StyleProfiler()
    return profiler.analyze(content)
