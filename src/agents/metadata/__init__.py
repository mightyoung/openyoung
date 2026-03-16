"""
Agent Metadata Module - Agent 元数据模块

包含:
- AgentMetadata: 元数据结构
- MetadataSchema: 元数据模式定义
- MetadataExtractor: 元数据提取器
- ProgressiveLoader: 渐进式加载器

参考:
- SkillsGate: 索引 45,000+ GitHub Agent 技能
- Anthropic Skills: Claude 技能系统
"""

from .cache import MetadataCache
from .enricher import MetadataEnricher
from .extractor import MetadataExtractor
from .loader import ProgressiveLoader
from .schema import (
    AgentCapability,
    AgentMetadata,
    AgentTier,
    CompatibilityInfo,
    MetadataLevel,
    PerformanceMetrics,
    SkillDefinition,
    SubAgentConfig,
)

__all__ = [
    "AgentMetadata",
    "AgentCapability",
    "SkillDefinition",
    "SubAgentConfig",
    "CompatibilityInfo",
    "PerformanceMetrics",
    "AgentTier",
    "MetadataLevel",
    "MetadataExtractor",
    "MetadataEnricher",
    "ProgressiveLoader",
    "MetadataCache",
]
