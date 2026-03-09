"""
Badge System - 质量徽章系统
为 Agent 授予各种质量徽章
"""

from dataclasses import dataclass
from enum import Enum


class BadgeType(Enum):
    """徽章类型"""

    VERIFIED = "verified"  # 官方验证
    TOP_RATED = "top_rated"  # 高评分
    TRENDING = "trending"  # 趋势上升
    NEW = "new"  # 新增
    POPULAR = "popular"  # 热门
    WELL_DOCUMENTED = "well_documented"  # 文档完善


@dataclass
class Badge:
    """徽章"""

    badge_type: BadgeType
    name: str  # 显示名称
    icon: str  # 图标
    color: str  # 颜色
    description: str  # 描述
    earned_at: str | None = None  # 获得时间（可选，用于实际授予时设置）


# 徽章定义
BADGE_DEFINITIONS = {
    BadgeType.VERIFIED: Badge(
        badge_type=BadgeType.VERIFIED,
        name="Verified",
        icon="🟢",
        color="green",
        description="官方验证的 Agent",
    ),
    BadgeType.TOP_RATED: Badge(
        badge_type=BadgeType.TOP_RATED,
        name="Top Rated",
        icon="🟡",
        color="gold",
        description="评分 >= 4.5",
    ),
    BadgeType.TRENDING: Badge(
        badge_type=BadgeType.TRENDING,
        name="Trending",
        icon="🔥",
        color="red",
        description="最近 7 天增长最快",
    ),
    BadgeType.NEW: Badge(
        badge_type=BadgeType.NEW,
        name="New",
        icon="🆕",
        color="blue",
        description="最近 30 天内添加",
    ),
    BadgeType.POPULAR: Badge(
        badge_type=BadgeType.POPULAR,
        name="Popular",
        icon="⭐",
        color="yellow",
        description="使用次数 >= 100",
    ),
    BadgeType.WELL_DOCUMENTED: Badge(
        badge_type=BadgeType.WELL_DOCUMENTED,
        name="Well Documented",
        icon="📚",
        color="cyan",
        description="文档评分 >= 0.8",
    ),
}


class BadgeSystem:
    """徽章系统"""

    def __init__(self):
        pass

    async def evaluate_badges(self, agent_name: str, agent_data: dict) -> list[Badge]:
        """评估 Agent 可获得的徽章

        Args:
            agent_name: Agent 名称
            agent_data: Agent 数据

        Returns:
            List[Badge]: 徽章列表
        """
        badges = []

        # 1. Popular - 使用次数 >= 100
        downloads = agent_data.get("downloads", 0)
        if downloads >= 100:
            badges.append(BADGE_DEFINITIONS[BadgeType.POPULAR])

        # 2. Top Rated - 评分 >= 4.5
        rating = agent_data.get("rating", 0)
        if rating >= 4.5:
            badges.append(BADGE_DEFINITIONS[BadgeType.TOP_RATED])

        # 3. Well Documented - 文档评分 >= 0.8
        doc_score = agent_data.get("dimensions", {}).get("documentation", 0)
        if doc_score >= 0.8:
            badges.append(BADGE_DEFINITIONS[BadgeType.WELL_DOCUMENTED])

        # 4. New - 最近 30 天内添加
        created_at = agent_data.get("created_at", "")
        if created_at:
            try:
                from datetime import datetime

                created = datetime.fromisoformat(created_at)
                days_since = (datetime.now() - created).days
                if days_since <= 30:
                    badges.append(BADGE_DEFINITIONS[BadgeType.NEW])
            except:
                pass

        # 5. Trending - 计算趋势分数
        if await self._is_trending(agent_data):
            badges.append(BADGE_DEFINITIONS[BadgeType.TRENDING])

        # 6. Verified - 需要手动标记（暂时通过质量评分判断）
        quality = agent_data.get("quality_score", 0)
        if quality >= 0.7:
            badges.append(BADGE_DEFINITIONS[BadgeType.VERIFIED])

        return badges

    async def _is_trending(self, agent_data: dict) -> bool:
        """判断是否趋势上升"""
        recent_downloads = agent_data.get("recent_downloads", 0)
        total_downloads = agent_data.get("downloads", 1)

        # 最近 7 天下载占比超过 30% 视为趋势上升
        if total_downloads > 0 and recent_downloads / total_downloads >= 0.3:
            return True
        return False

    def calculate_trending_score(
        self, recent_downloads: int, total_downloads: int, rating: float, days_since_release: int
    ) -> float:
        """计算趋势分数

        公式：
        - velocity_score: 下载增长速度 (0-10)
        - rating_score: 评分 (0-5)
        - freshness_score: 新鲜度 (0-1)
        """
        # 速度分数
        if total_downloads > 0:
            velocity_score = (recent_downloads / total_downloads) * 10
        else:
            velocity_score = 0

        # 评分分数
        rating_score = rating

        # 新鲜度分数 (30 天后为 0)
        freshness_score = max(0, 1 - days_since_release / 30)

        # 加权总分
        return velocity_score * 0.5 + rating_score * 0.3 + freshness_score * 0.2

    def format_badges(self, badges: list[Badge]) -> str:
        """格式化徽章为字符串"""
        if not badges:
            return ""

        parts = []
        for badge in badges:
            parts.append(f"{badge.icon} {badge.name}")

        return " ".join(parts)


# ========== 便捷函数 ==========


async def get_agent_badges(agent_name: str, agent_data: dict) -> list[Badge]:
    """获取 Agent 的徽章"""
    system = BadgeSystem()
    return await system.evaluate_badges(agent_name, agent_data)
