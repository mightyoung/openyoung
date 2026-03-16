"""
Skill Discovery Service - 技能发现服务

提供技能搜索、推荐、分类等功能
基于语义搜索和过滤
"""

from typing import Optional
from .models import (
    MarketplaceSkill,
    SkillCategory,
    SearchFilters,
    SearchResult,
)


class DiscoveryService:
    """技能发现服务

    提供高级搜索和推荐功能
    """

    def __init__(self, registry):
        """初始化发现服务

        Args:
            registry: MarketplaceRegistry实例
        """
        self._registry = registry

    def search(
        self,
        query: str = "",
        category: Optional[SkillCategory] = None,
        tags: list[str] = None,
        sort_by: str = "relevance",
        page: int = 1,
        page_size: int = 20,
    ) -> SearchResult:
        """搜索技能

        Args:
            query: 搜索关键词
            category: 技能分类
            tags: 标签过滤
            sort_by: 排序方式 (relevance, downloads, rating, newest)
            page: 页码
            page_size: 每页数量

        Returns:
            SearchResult: 搜索结果
        """
        filters = SearchFilters(
            query=query,
            category=category,
            tags=tags or [],
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )
        return self._registry.search_skills(filters)

    def get_featured(self, limit: int = 10) -> list[MarketplaceSkill]:
        """获取精选技能

        基于评分和下载量排序

        Args:
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 精选技能列表
        """
        # 获取评分最高的技能
        filters = SearchFilters(
            sort_by="rating",
            sort_order="desc",
            min_rating=4.0,
            page=1,
            page_size=limit,
        )
        result = self._registry.search_skills(filters)
        return result.skills

    def get_trending(self, limit: int = 10) -> list[MarketplaceSkill]:
        """获取热门技能

        基于下载量排序

        Args:
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 热门技能列表
        """
        filters = SearchFilters(
            sort_by="downloads",
            sort_order="desc",
            page=1,
            page_size=limit,
        )
        result = self._registry.search_skills(filters)
        return result.skills

    def get_by_category(
        self,
        category: SkillCategory,
        limit: int = 20,
    ) -> list[MarketplaceSkill]:
        """获取分类下的技能

        Args:
            category: 技能分类
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 分类技能列表
        """
        filters = SearchFilters(
            category=category,
            sort_by="downloads",
            page=1,
            page_size=limit,
        )
        result = self._registry.search_skills(filters)
        return result.skills

    def get_by_tag(
        self,
        tag: str,
        limit: int = 20,
    ) -> list[MarketplaceSkill]:
        """获取标签下的技能

        Args:
            tag: 标签
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 标签技能列表
        """
        filters = SearchFilters(
            tags=[tag],
            sort_by="downloads",
            page=1,
            page_size=limit,
        )
        result = self._registry.search_skills(filters)
        return result.skills

    def get_recent(self, limit: int = 10) -> list[MarketplaceSkill]:
        """获取最新技能

        Args:
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 最新技能列表
        """
        filters = SearchFilters(
            sort_by="newest",
            page=1,
            page_size=limit,
        )
        result = self._registry.search_skills(filters)
        return result.skills

    def get_related(
        self,
        skill: MarketplaceSkill,
        limit: int = 5,
    ) -> list[MarketplaceSkill]:
        """获取相关技能

        基于相同分类和标签

        Args:
            skill: 目标技能
            limit: 返回数量

        Returns:
            list[MarketplaceSkill]: 相关技能列表
        """
        filters = SearchFilters(
            category=skill.category,
            tags=skill.tags[:3],  # 最多使用前3个标签
            sort_by="downloads",
            page=1,
            page_size=limit + 1,  # 多取一个以排除自己
        )
        result = self._registry.search_skills(filters)

        # 排除自己
        return [s for s in result.skills if s.id != skill.id][:limit]

    def get_all_categories(self) -> dict[SkillCategory, int]:
        """获取所有分类及技能数量

        Returns:
            dict[SkillCategory, int]: 分类到数量的映射
        """
        # 简单实现：遍历所有分类统计
        result = {}
        for category in SkillCategory:
            filters = SearchFilters(
                category=category,
                page=1,
                page_size=1,
            )
            search_result = self._registry.search_skills(filters)
            if search_result.total_count > 0:
                result[category] = search_result.total_count
        return result

    def get_all_tags(self) -> list[tuple[str, int]]:
        """获取所有标签及使用次数

        Returns:
            list[tuple[str, int]]: (标签, 使用次数)列表
        """
        skills = self._registry.list_skills(limit=1000)
        tag_counts = {}
        for skill in skills:
            for tag in skill.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 按使用次数排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tags
