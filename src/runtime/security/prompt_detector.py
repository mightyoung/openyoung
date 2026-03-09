"""
提示注入检测器

基于模式匹配检测提示注入攻击
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class InjectionSeverity(Enum):
    """注入严重程度"""

    BLOCK = "block"  # 阻止执行
    WARN = "warn"  # 警告但允许
    REVIEW = "review"  # 需要人工审核
    SANITIZE = "sanitize"  # 清理后执行


@dataclass
class DetectionResult:
    """检测结果"""

    is_malicious: bool
    severity: InjectionSeverity
    matched_patterns: list[str]
    confidence: float
    sanitized_content: Optional[str] = None

    def __str__(self) -> str:
        return (
            f"DetectionResult(malicious={self.is_malicious}, "
            f"severity={self.severity.value}, patterns={self.matched_patterns}, "
            f"confidence={self.confidence:.2f})"
        )


class PromptInjector:
    """提示注入检测器

    基于 IronClaw 的模式库，实现多层次检测
    """

    # 基于 IronClaw 的模式库
    PATTERNS: dict[str, list[str]] = {
        "ignore_instructions": [
            r"(?i)ignore\s+(all\s+)?(previous|prior|earlier)\s+instructions?",
            r"(?i)disregard\s+(all\s+)?(previous|prior|earlier)",
            r"(?i)forget\s+(everything|all)\s+you\s+(know|were\s+told)",
            r"(?i)discard\s+(all\s+)?(previous|prior|earlier)",
            r"(?i)overrule\s+(all\s+)?(previous|prior|earlier)",
            r"(?i)new\s+instructions",
            r"(?i)instead\s+of\s+(your|the)\s+(previous|original)",
            r"(?i)override\s+(your|this)\s+instruction",
            r"(?i)supersede",
        ],
        "role_override": [
            r"(?i)you\s+are\s+(now|no\s+longer)\s+[a-z]+",
            r"(?i)act\s+as\s+(if|a|the)\s+[a-z]+",
            r"(?i)pretend\s+(to\s+be|you\s+are)",
            r"(?i)roleplay\s+as",
            r"(?i)play\s+the\s+role\s+of",
            r"(?i)assume\s+the\s+role\s+of",
            r"(?i)you\s+can\s+be\s+a\s+[a-z]+",
            r"(?i)you\s+have\s+permission\s+to",
            r"(?i)your\s+(new|alternate)\s+persona",
            r"(?i)ignore\s+your\s+(system|original)\s+prompt",
        ],
        "context_injection": [
            r"<\|[a-z_]+\|>",  # Special tokens
            r"<\|endofprompt\|>",
            r"<\|endoftext\|>",
            r"^system:\s*",  # Only at line start
            r"^assistant:\s*",
            r"^user:\s*",
            r"^human:\s*",
            r"===.*===",  # Separator tokens
            r"---.*---",
            r"<</[a-z_]+>>",  # XML-style tags
        ],
        "jailbreak": [
            r"(?i)\bDAN\b",  # Do Anything Now
            r"(?i)developer\s+mode",
            r"(?i)jailbreak",
            r"(?i)bypass\s+(safety|restriction)",
            r"(?i)unrestricted\s+mode",
            r"(?i)no\s+filter",
            r"(?i)without\s+(safety|ethical)\s+(limit|filter)",
            r"(?i)evil\s+mode",
            r"(?i)master\s+mode",
            r"(?i)supervisor\s+mode",
        ],
        "manipulation": [
            r"(?i)please\s+(do|can\s+you)\s+.*\?",  # Polite requests
            r"(?i)i\s+need\s+you\s+to\s+",
            r"(?i)i\s+want\s+you\s+to\s+",
            r"(?i)it\s+is\s+important\s+that\s+",
            r"(?i)for\s+(educational|research)\s+purpose",
            r"(?i)this\s+is\s+(just|a)\s+(hypothetical|test)",
            r"(?i)let's\s+play\s+a\s+game",
            r"(?i)let's\s+imagine\s+",
            r"(?i)in\s+the\s+scenario\s+",
            r"(?i)what\s+if\s+i\s+told\s+you",
        ],
        "data_extraction": [
            r"(?i)tell\s+me\s+(your|all)\s+(instruction|prompt|system)",
            r"(?i)show\s+me\s+(your|all)\s+(instruction|prompt)",
            r"(?i)output\s+your\s+(instruction|prompt)",
            r"(?i)what\s+are\s+your\s+(instruction|rule|guideline)",
            r"(?i)repeat\s+(your|all)\s+(instruction|rule)",
            r"(?i)print\s+(your|all)\s+(instruction|system)",
        ],
    }

    # 严重程度权重
    SEVERITY_WEIGHTS: dict[str, InjectionSeverity] = {
        "ignore_instructions": InjectionSeverity.BLOCK,
        "role_override": InjectionSeverity.BLOCK,
        "context_injection": InjectionSeverity.WARN,
        "jailbreak": InjectionSeverity.BLOCK,
        "manipulation": InjectionSeverity.REVIEW,
        "data_extraction": InjectionSeverity.BLOCK,
        "custom_blocklist": InjectionSeverity.BLOCK,  # 自定义黑名单应该被阻止
    }

    def __init__(
        self,
        block_threshold: float = 0.8,
        allowed_patterns: list[str] | None = None,
        blocked_patterns: list[str] | None = None,
    ):
        """初始化检测器

        Args:
            block_threshold: 阻止执行的置信度阈值
            allowed_patterns: 自定义白名单模式（可选）
            blocked_patterns: 自定义黑名单模式（可选）
        """
        self.block_threshold = block_threshold

        # 合并默认模式和自定义模式
        self._allowed_patterns = allowed_patterns or []
        self._blocked_patterns = blocked_patterns or []

        self._compiled_patterns: dict[str, list[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """预编译所有正则表达式"""
        for category, patterns in self.PATTERNS.items():
            self._compiled_patterns[category] = [
                re.compile(pattern) for pattern in patterns
            ]

    # Unicode 混淆映射表
    UNICODE_LEET_MAP = {
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",  # Cyrillic
        "ɑ": "a", "ҽ": "e", "ο": "o", "ρ": "p", "с": "c", "υ": "y",  # Greek-like
        "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    }

    def _normalize_unicode(self, content: str) -> str:
        """标准化 Unicode 混淆

        Args:
            content: 原始内容

        Returns:
            标准化后的内容
        """
        normalized = content
        for unicode_char, ascii_char in self.UNICODE_LEET_MAP.items():
            normalized = normalized.replace(unicode_char, ascii_char)
        return normalized

    def detect(self, content: str) -> DetectionResult:
        """检测提示注入

        Args:
            content: 待检测的内容

        Returns:
            DetectionResult: 检测结果
        """
        matched_categories: list[str] = []

        # === 白名单/黑名单模式检查 ===
        # 如果有自定义模式，先检查这些
        if self._allowed_patterns:
            # 白名单模式：内容必须匹配至少一个白名单模式
            allowed_match = False
            for pattern in self._allowed_patterns:
                if re.search(pattern, content):
                    allowed_match = True
                    break
            if not allowed_match:
                # 不在白名单中，直接标记为恶意
                return DetectionResult(
                    is_malicious=True,
                    severity=InjectionSeverity.BLOCK,
                    matched_patterns=["not_in_allowlist"],
                    confidence=1.0,
                    sanitized_content=None,
                )

        if self._blocked_patterns:
            # 黑名单模式：检查是否匹配黑名单
            for pattern in self._blocked_patterns:
                if re.search(pattern, content):
                    matched_categories.append("custom_blocklist")

        # === 原有模式检测 ===
        # 检测 Unicode 混淆
        normalized_content = self._normalize_unicode(content)

        # 多模式匹配
        for category, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                # 同时检查原始和标准化后的内容
                if pattern.search(content) or pattern.search(normalized_content):
                    matched_categories.append(category)
                    break  # 每个类别只记录一次

        # 计算置信度
        confidence = self._calculate_confidence(matched_categories)

        # 确定严重程度
        severity = self._calculate_severity(matched_categories)

        # 决定是否阻止
        is_malicious = (
            len(matched_categories) > 0
            and confidence >= self.block_threshold
            and severity == InjectionSeverity.BLOCK
        )

        return DetectionResult(
            is_malicious=is_malicious,
            severity=severity,
            matched_patterns=matched_categories,
            confidence=confidence,
        )

    def _calculate_confidence(self, matched_categories: list[str]) -> float:
        """计算置信度

        Args:
            matched_categories: 匹配的类别列表

        Returns:
            置信度 (0-1)
        """
        if not matched_categories:
            return 0.0

        # 基础置信度
        base = 0.6  # 提高基础置信度

        # 每增加一个类别增加置信度
        category_bonus = 0.15 * len(matched_categories)

        # 严重类别加成
        severe_categories = [
            "ignore_instructions",
            "role_override",
            "jailbreak",
            "data_extraction",
            "custom_blocklist",  # 自定义黑名单也是严重类别
        ]
        severe_count = sum(1 for c in matched_categories if c in severe_categories)
        severe_bonus = 0.15 * severe_count

        confidence = min(base + category_bonus + severe_bonus, 0.99)
        return confidence

    def _calculate_severity(
        self, matched_categories: list[str]
    ) -> InjectionSeverity:
        """计算严重程度

        Args:
            matched_categories: 匹配的类别列表

        Returns:
            InjectionSeverity: 最高严重程度
        """
        if not matched_categories:
            return InjectionSeverity.SANITIZE

        # 找出最高严重程度
        severity_order = [
            InjectionSeverity.BLOCK,
            InjectionSeverity.REVIEW,
            InjectionSeverity.WARN,
            InjectionSeverity.SANITIZE,
        ]

        max_severity = InjectionSeverity.SANITIZE
        for category in matched_categories:
            category_severity = self.SEVERITY_WEIGHTS.get(
                category, InjectionSeverity.WARN
            )
            if severity_order.index(category_severity) < severity_order.index(
                max_severity
            ):
                max_severity = category_severity

        return max_severity

    def sanitize(self, content: str) -> str:
        """清理内容中的注入尝试

        Args:
            content: 待清理的内容

        Returns:
            清理后的内容
        """
        sanitized = content

        # 移除特殊 token
        sanitized = re.sub(r"<\|[a-z_]+\|>", "", sanitized)
        sanitized = re.sub(r"<\|endof.*?\|>", "", sanitized)

        # 移除分隔符
        sanitized = re.sub(r"===.*?===", "", sanitized)
        sanitized = re.sub(r"---.*?---", "", sanitized)

        # 移除 XML 风格标签
        sanitized = re.sub(r"<</?[a-z_]+>>", "", sanitized)

        return sanitized.strip()


# ========== Convenience Functions ==========


def detect_prompt_injection(content: str) -> DetectionResult:
    """便捷函数：检测提示注入"""
    detector = PromptInjector()
    return detector.detect(content)


def sanitize_content(content: str) -> str:
    """便捷函数：清理内容"""
    detector = PromptInjector()
    return detector.sanitize(content)
