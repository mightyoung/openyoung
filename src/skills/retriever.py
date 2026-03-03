"""
Unified Skill Retriever - 统一检索层
"""

from dataclasses import dataclass
from typing import List
from .metadata import SkillMetadata, RetrievalConfig


@dataclass
class RetrievalResult:
    """检索结果"""

    skill: SkillMetadata
    score: float
    match_type: str  # exact | semantic | tag


class UnifiedSkillRetriever:
    """统一检索器 - 支持多种检索模式"""

    def __init__(self, config: RetrievalConfig):
        self.config = config
        self._skills: List[SkillMetadata] = []
        self._embedding_index = None

    async def initialize(self, skills: List[SkillMetadata]):
        """初始化检索器"""
        self._skills = skills

        # 尝试初始化 embedding 索引
        try:
            await self._init_embedding_index()
        except Exception:
            pass

    async def _init_embedding_index(self):
        """初始化 Embedding 索引"""
        # TODO: 集成真实的 embedding 服务
        # 当前使用简单的关键词索引作为回退
        self._keyword_index: dict[str, List[SkillMetadata]] = {}

        for skill in self._skills:
            # 从描述和标签构建关键词索引
            keywords = skill.description.lower().split()
            keywords.extend(skill.tags)

            for keyword in keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = []
                self._keyword_index[keyword].append(skill)

    async def retrieve(self, query: str) -> List[RetrievalResult]:
        """检索相关 Skills"""
        results: List[RetrievalResult] = []

        # 1. 精确匹配
        exact_results = self._exact_match(query)
        results.extend(exact_results)

        # 2. 标签匹配
        if len(results) < self.config.semantic_top_k:
            tag_results = self._tag_match(query)
            for r in tag_results:
                if r.skill.name not in [x.skill.name for x in results]:
                    results.append(r)

        # 3. 语义匹配 (如果可用)
        if self._embedding_index and len(results) < self.config.semantic_top_k:
            semantic_results = await self._semantic_match(query)
            for r in semantic_results:
                if r.skill.name not in [x.skill.name for x in results]:
                    results.append(r)

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[: self.config.final_top_k]

    def _exact_match(self, query: str) -> List[RetrievalResult]:
        """精确匹配 - Skill 名称完全匹配"""
        results = []
        query_lower = query.lower()

        for skill in self._skills:
            if skill.name.lower() == query_lower:
                results.append(
                    RetrievalResult(skill=skill, score=1.0, match_type="exact")
                )

        return results

    def _tag_match(self, query: str) -> List[RetrievalResult]:
        """标签匹配"""
        results = []
        query_lower = query.lower()

        for skill in self._skills:
            # 检查标签
            for tag in skill.tags:
                if query_lower in tag.lower():
                    results.append(
                        RetrievalResult(skill=skill, score=0.8, match_type="tag")
                    )
                    break
            else:
                # 检查触发模式
                for pattern in skill.trigger_patterns:
                    if query_lower in pattern.lower():
                        results.append(
                            RetrievalResult(skill=skill, score=0.7, match_type="tag")
                        )
                        break

        return results

    async def _semantic_match(self, query: str) -> List[RetrievalResult]:
        """语义匹配 - 基于 Embedding"""
        # TODO: 实现真实的语义匹配
        # 当前回退到关键词搜索
        if not hasattr(self, "_keyword_index"):
            return []

        results = []
        query_words = query.lower().split()

        for skill in self._skills:
            score = 0.0
            matched_count = 0

            for word in query_words:
                if word in self._keyword_index:
                    if skill in self._keyword_index[word]:
                        matched_count += 1

            if matched_count > 0:
                score = min(matched_count / len(query_words), 1.0) * 0.6
                results.append(
                    RetrievalResult(skill=skill, score=score, match_type="semantic")
                )

        return results
