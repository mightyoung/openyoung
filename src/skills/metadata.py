"""
Skill Metadata - 元数据数据结构
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class SkillMetadata:
    """Skill 元数据"""

    name: str
    description: str
    file_path: Path
    source: str = "local"  # package | evolved | local
    version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    disable_model_invocation: bool = False
    trigger_patterns: List[str] = field(default_factory=list)


@dataclass
class LoadedSkill:
    """已加载的 Skill"""

    metadata: SkillMetadata
    content: str
    loaded_at: str  # ISO format timestamp


@dataclass
class RetrievalConfig:
    """检索配置"""

    mode: str = "hybrid"  # package_only | evolved_only | hybrid
    semantic_enabled: bool = True
    semantic_top_k: int = 5
    semantic_threshold: float = 0.7
    final_top_k: int = 10
