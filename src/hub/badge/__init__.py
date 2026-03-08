"""
Hub Badge Module
质量徽章系统
"""

from .system import (
    BADGE_DEFINITIONS,
    Badge,
    BadgeSystem,
    BadgeType,
    get_agent_badges,
)

__all__ = [
    "BadgeType",
    "Badge",
    "BADGE_DEFINITIONS",
    "BadgeSystem",
    "get_agent_badges",
]
