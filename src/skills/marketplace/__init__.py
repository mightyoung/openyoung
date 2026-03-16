"""
Skill Marketplace - 技能市场模块

提供技能发现、安装、发布、评价等功能
基于 npm registry 和 Vercel Skills 设计
"""

from .discovery import DiscoveryService
from .install import InstallService
from .models import (
    InstallOptions,
    MarketplaceSkill,
    PublishOptions,
    ReleaseType,
    ReviewList,
    SearchFilters,
    SearchResult,
    SkillCategory,
    SkillDownload,
    # Type aliases
    SkillList,
    # Models
    SkillManifest,
    SkillReview,
    # Enums
    SkillStatus,
    SkillUpdate,
)
from .publish import PublishService
from .rating import RatingService
from .registry import MarketplaceRegistry

__all__ = [
    # Enums
    "SkillStatus",
    "ReleaseType",
    "SkillCategory",
    # Models
    "SkillManifest",
    "MarketplaceSkill",
    "SkillReview",
    "SkillDownload",
    "SkillUpdate",
    "SearchFilters",
    "SearchResult",
    "InstallOptions",
    "PublishOptions",
    # Registry
    "MarketplaceRegistry",
    # Discovery
    "DiscoveryService",
    # Publish
    "PublishService",
    # Install
    "InstallService",
    # Rating
    "RatingService",
    # Type aliases
    "SkillList",
    "ReviewList",
]
