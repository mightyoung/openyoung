"""
Intent Extractor - 意图提取器

M1.2: 从ParsedDocument提取核心意图
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from ..types import FeaturePoint, ParsedDocument, Priority
from ..types.contract import IntentSpec


class IntentExtractor:
    """意图提取器

    从结构化文档提取核心意图和约束条件
    支持：
    - 基于功能点提取意图
    - 基于关键词模式提取
    - 意图优先级排序
    - 约束条件分类
    """

    # 意图关键词模式
    GOAL_PATTERNS = [
        (r"(?:实现|提供|支持|开发|构建|创建)(.+)", "实现类"),
        (r"(?:添加|增加|新增)(.+)", "添加类"),
        (r"(?:优化|改进|提升)(.+)", "优化类"),
        (r"(?:修复|解决|处理)(.+)", "修复类"),
        (r"(?:管理|配置|设置)(.+)", "管理类"),
    ]

    # 约束关键词
    CONSTRAINT_KEYWORDS = {
        "性能": ["性能", "响应时间", "延迟", "吞吐量", "performance", "latency"],
        "安全": ["安全", "认证", "授权", "加密", "security", "auth"],
        "可用性": ["可用性", "可靠性", "容错", "availability", "reliability"],
        "兼容性": ["兼容", "适配", "跨平台", "compatibility", "cross-platform"],
        "可维护性": ["可维护", "可扩展", "模块化", "maintainability", "scalable"],
    }

    def __init__(self, llm_client=None):
        """初始化意图提取器

        Args:
            llm_client: 可选的LLM客户端，用于复杂提取
        """
        self.llm = llm_client

    async def extract(self, doc: ParsedDocument) -> IntentSpec:
        """从文档提取核心意图

        Args:
            doc: 解析后的文档

        Returns:
            IntentSpec: 意图规格
        """
        # 提取目标
        goals = self._extract_goals(doc)

        # 提取约束
        constraints = self._extract_constraints(doc)

        # 生成质量门槛
        quality_bar = self._generate_quality_bar(doc)

        return IntentSpec(
            primary_goals=goals,
            constraints=constraints[:10],
            quality_bar=quality_bar,
        )

    def _extract_goals(self, doc: ParsedDocument) -> list[str]:
        """提取目标列表"""
        goals = []

        # 1. 基于must优先级功能点
        for fp in doc.feature_points:
            if fp.priority == Priority.MUST:
                goals.append(fp.title)

        # 2. 基于关键词模式提取
        for fp in doc.feature_points:
            title = fp.title
            for pattern, category in self.GOAL_PATTERNS:
                match = re.search(pattern, title)
                if match and match.group(1).strip() not in goals:
                    goals.append(match.group(1).strip())

        # 3. 去重并限制数量
        seen = set()
        unique_goals = []
        for g in goals:
            g_lower = g.lower()
            if g_lower not in seen:
                seen.add(g_lower)
                unique_goals.append(g)

        return unique_goals[:5]  # 最多5个核心目标

    def _extract_constraints(self, doc: ParsedDocument) -> list[str]:
        """提取约束条件"""
        constraints = []
        constraint_categories = {cat: [] for cat in self.CONSTRAINT_KEYWORDS}

        # 1. 从acceptance_criteria提取
        for fp in doc.feature_points:
            if fp.acceptance_criteria:
                for criteria in fp.acceptance_criteria:
                    # 分类约束
                    categorized = self._categorize_constraint(criteria)
                    if categorized:
                        constraint_categories[categorized].append(criteria)
                    else:
                        constraints.append(criteria)

        # 2. 从文档内容提取约束关键词
        content_lower = doc.raw_content.lower()
        for category, keywords in self.CONSTRAINT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in content_lower:
                    if category not in constraints:
                        constraints.append(f"{category}相关约束")

        # 3. 添加分类后的约束
        for cat, consts in constraint_categories.items():
            if consts:
                constraints.extend(consts[:2])  # 每个分类最多2个

        return list(dict.fromkeys(constraints))  # 去重保持顺序

    def _categorize_constraint(self, text: str) -> Optional[str]:
        """将约束分类"""
        text_lower = text.lower()
        for category, keywords in self.CONSTRAINT_KEYWORDS.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return category
        return None

    def _generate_quality_bar(self, doc: ParsedDocument) -> str:
        """生成质量门槛描述"""
        must_count = len(doc.must_features)
        should_count = len(doc.should_features)

        if must_count > 0:
            return f"必须完成{must_count}个MUST功能点，{should_count}个SHOULD功能点应尽可能完成"
        return "功能完整且通过验收标准"

    async def extract_with_llm(self, doc: ParsedDocument) -> IntentSpec:
        """使用LLM提取意图（如果可用）

        Args:
            doc: 解析后的文档

        Returns:
            IntentSpec: 意图规格
        """
        if not self.llm:
            return await self.extract(doc)

        # 构建提示词
        prompt = self._build_llm_prompt(doc)

        try:
            response = await self.llm.generate(prompt)
            return self._parse_llm_response(response, doc)
        except Exception:
            # LLM提取失败，回退到规则提取
            return await self.extract(doc)

    def _build_llm_prompt(self, doc: ParsedDocument) -> str:
        """构建LLM提示词"""
        features_text = "\n".join(
            f"- {fp.title} ({fp.priority.value})" for fp in doc.feature_points
        )

        return f"""从以下需求文档中提取核心意图：

标题：{doc.title}

功能点：
{features_text}

请提取：
1. primary_goals: 核心目标（最多5个）
2. constraints: 约束条件（最多10个）
3. quality_bar: 质量门槛描述

以JSON格式输出。"""

    def _parse_llm_response(self, response: str, doc: ParsedDocument) -> IntentSpec:
        """解析LLM响应"""
        try:
            import json

            # 尝试提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())
                return IntentSpec(
                    primary_goals=data.get("primary_goals", [])[:5],
                    constraints=data.get("constraints", [])[:10],
                    quality_bar=data.get("quality_bar", "功能完整且通过验收标准"),
                )
        except Exception:
            pass

        # 解析失败，回退
        return IntentSpec(
            primary_goals=["文档理解"],
            constraints=[],
            quality_bar="功能完整且通过验收标准",
        )

    def extract_implicit_intents(self, doc: ParsedDocument) -> list[str]:
        """提取隐含意图

        从文档中推断用户未明确说明但实际需要的意图

        Args:
            doc: 解析后的文档

        Returns:
            list[str]: 隐含意图列表
        """
        implicit = []

        # 1. 如果有数据处理，可能需要错误处理
        has_data_processing = any(
            kw in fp.title.lower()
            for fp in doc.feature_points
            for kw in ["解析", "处理", "转换", "parse", "process"]
        )
        if has_data_processing:
            implicit.append("错误处理和边界情况处理")

        # 2. 如果有用户交互，可能需要日志记录
        has_user_interaction = any(
            kw in fp.title.lower()
            for fp in doc.feature_points
            for kw in ["用户", "交互", "界面", "user", "ui"]
        )
        if has_user_interaction:
            implicit.append("操作日志记录")

        # 3. 如果有外部依赖，需要考虑超时和重试
        has_external_deps = any(
            kw in fp.description.lower()
            for fp in doc.feature_points
            for kw in ["api", "http", "请求", "external"]
        )
        if has_external_deps:
            implicit.append("超时处理和重试机制")

        return implicit


def extract_intent(doc: ParsedDocument) -> IntentSpec:
    """提取意图的便捷函数"""
    extractor = IntentExtractor()
    return extractor.extract(doc)
