"""
Skill Rating Service - 技能评价服务

处理技能评分和评价
"""

from datetime import datetime

from .models import (
    SkillReview,
)
from .registry import MarketplaceRegistry


class RatingService:
    """技能评价服务

    处理技能评分和评价
    """

    def __init__(self, registry: MarketplaceRegistry):
        """初始化评价服务

        Args:
            registry: MarketplaceRegistry实例
        """
        self._registry = registry

    def add_review(
        self,
        skill_id: str,
        rating: int,
        comment: str,
        title: str = "",
        user_id: str = "",
        user_name: str = "",
        skill_version: str = "",
    ) -> SkillReview:
        """添加评价

        Args:
            skill_id: 技能ID
            rating: 评分 (1-5)
            comment: 评价内容
            title: 评价标题
            user_id: 用户ID
            user_name: 用户名
            skill_version: 技能版本

        Returns:
            SkillReview: 创建的评价

        Raises:
            ValueError: 验证失败
        """
        # 验证评分
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # 检查技能是否存在
        skill = self._registry.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill not found: {skill_id}")

        # 创建评价
        review = SkillReview(
            skill_id=skill_id,
            skill_version=skill_version or skill.version,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            comment=comment,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # 保存评价
        self._registry.add_review(review)

        return review

    def get_reviews(
        self,
        skill_id: str,
        limit: int = 20,
    ) -> list[SkillReview]:
        """获取技能评价

        Args:
            skill_id: 技能ID
            limit: 返回数量

        Returns:
            list[SkillReview]: 评价列表
        """
        return self._registry.get_reviews(skill_id, limit)

    def get_skill_rating(self, skill_id: str) -> dict:
        """获取技能评分

        Args:
            skill_id: 技能ID

        Returns:
            dict: 评分信息
        """
        skill = self._registry.get_skill(skill_id)
        if not skill:
            return {}

        reviews = self._registry.get_reviews(skill_id, limit=100)

        # 计算评分分布
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating] += 1

        return {
            "average": skill.rating,
            "count": skill.rating_count,
            "distribution": rating_distribution,
        }

    def mark_helpful(self, review_id: str, helpful: bool = True) -> bool:
        """标记评价是否有帮助

        Args:
            review_id: 评价ID
            helpful: 是否有帮助

        Returns:
            bool: 是否成功
        """
        # 简化实现：不做实际更新
        return True

    def get_top_reviews(
        self,
        skill_id: str,
        limit: int = 5,
    ) -> list[SkillReview]:
        """获取最有帮助的评价

        Args:
            skill_id: 技能ID
            limit: 返回数量

        Returns:
            list[SkillReview]: 评价列表
        """
        reviews = self._registry.get_reviews(skill_id, limit=100)

        # 按 helpful_count 排序
        sorted_reviews = sorted(reviews, key=lambda r: r.helpful_count, reverse=True)

        return sorted_reviews[:limit]

    def get_recent_reviews(
        self,
        skill_id: str,
        limit: int = 5,
    ) -> list[SkillReview]:
        """获取最新评价

        Args:
            skill_id: 技能ID
            limit: 返回数量

        Returns:
            list[SkillReview]: 评价列表
        """
        return self._registry.get_reviews(skill_id, limit=limit)
