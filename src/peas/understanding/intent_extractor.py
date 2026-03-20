"""
Intent Extractor - 意图提取器

M1.2: 从ParsedDocument提取核心意图
"""

from dataclasses import dataclass, field
from typing import Optional

from ..types import ParsedDocument
from ..types.contract import IntentSpec


class IntentExtractor:
    """意图提取器

    从结构化文档提取核心意图和约束条件
    """

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
        # 简单实现：基于功能点提取意图
        goals = []
        constraints = []

        for fp in doc.feature_points:
            if fp.priority.value == "must":
                goals.append(fp.title)

        # 提取约束条件（从acceptance_criteria）
        for fp in doc.feature_points:
            if fp.acceptance_criteria:
                constraints.extend(fp.acceptance_criteria)

        return IntentSpec(
            primary_goals=goals,
            constraints=constraints[:10],  # 限制数量
            quality_bar="功能完整且通过验收标准",
        )

    async def extract_with_llm(self, doc: ParsedDocument) -> IntentSpec:
        """使用LLM提取意图（如果可用）

        Args:
            doc: 解析后的文档

        Returns:
            IntentSpec: 意图规格
        """
        if not self.llm:
            return await self.extract(doc)

        # TODO: 实现LLM提取逻辑
        return await self.extract(doc)


def extract_intent(doc: ParsedDocument) -> IntentSpec:
    """提取意图的便捷函数"""
    extractor = IntentExtractor()
    return extractor.extract(doc)
