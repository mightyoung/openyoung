"""
Skills - 技能加载与管理
"""

from .creator import (
    CreatedSkill,
    SkillCategory,
    SkillCreator,
    SkillTemplate,
    TriggerType,
    create_skill,
    list_templates,
)
from .heartbeat import (
    HeartbeatConfig,
    HeartbeatPhase,
    HeartbeatResult,
    HeartbeatScheduler,
    get_heartbeat_scheduler,
)
from .learnings import (
    LearningEntry,
    LearningsManager,
    LearningType,
    Priority,
    get_learnings_manager,
)
from .loader import SkillLoader
from .metadata import LoadedSkill, RetrievalConfig, SkillMetadata
from .registry import SkillRegistry
from .retriever import RetrievalResult, UnifiedSkillRetriever
from .versioning import (
    ReleaseType,
    SkillRelease,
    SkillVersion,
    SkillVersionManager,
    get_version_manager,
)
from .external_sources import (
    ExternalSourcesConfig,
    ExternalSourcesFetcher,
    NewsItem,
    SourceConfig,
    SourceType,
    get_external_sources_fetcher,
)

# 导出主要类
__all__ = [
    # 原有模块
    "SkillMetadata",
    "LoadedSkill",
    "RetrievalConfig",
    "SkillLoader",
    "SkillRegistry",
    "UnifiedSkillRetriever",
    "RetrievalResult",
    # 新增模块 - 技能创建
    "SkillCreator",
    "SkillTemplate",
    "CreatedSkill",
    "SkillCategory",
    "TriggerType",
    "create_skill",
    "list_templates",
    # 新增模块 - 心跳
    "HeartbeatConfig",
    "HeartbeatPhase",
    "HeartbeatResult",
    "HeartbeatScheduler",
    "get_heartbeat_scheduler",
    # 新增模块 - 经验日志
    "LearningsManager",
    "LearningEntry",
    "LearningType",
    "Priority",
    "get_learnings_manager",
    # 新增模块 - 版本管理
    "SkillVersion",
    "SkillRelease",
    "ReleaseType",
    "SkillVersionManager",
    "get_version_manager",
    # 新增模块 - 外部信息源
    "ExternalSourcesConfig",
    "ExternalSourcesFetcher",
    "NewsItem",
    "SourceConfig",
    "SourceType",
    "get_external_sources_fetcher",
]

# 保持向后兼容
import importlib.util
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Skill:
    """技能定义"""

    name: str
    handler: Callable
    description: str = ""
    is_loaded: bool = False


class SkillManager:
    """技能管理器"""

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._skill_paths: list[str] = []

    def register(self, skill: Skill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> bool:
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def load(self, name: str) -> Skill | None:
        """加载技能"""
        skill = self._skills.get(name)
        if skill:
            skill.is_loaded = True
        return skill

    def unload(self, name: str) -> bool:
        """卸载技能"""
        skill = self._skills.get(name)
        if skill:
            skill.is_loaded = False
            return True
        return False

    def list_skills(self) -> list[str]:
        """列出所有技能"""
        return list(self._skills.keys())

    def get_skill(self, name: str) -> Skill | None:
        """获取技能"""
        return self._skills.get(name)

    def discover_skills(self, path: str) -> list[Skill]:
        """自动发现技能"""
        discovered = []
        skill_path = Path(path)

        if not skill_path.exists():
            return discovered

        for file in skill_path.glob("*.py"):
            if file.stem != "__init__":
                discovered.append(
                    Skill(
                        name=file.stem,
                        handler=lambda: None,
                        description=f"Discovered from {file.name}",
                    )
                )

        return discovered

    def execute_skill(self, name: str, *args, **kwargs) -> Any:
        """执行技能"""
        skill = self._skills.get(name)
        if not skill or not skill.is_loaded:
            raise ValueError(f"Skill '{name}' not loaded")

        return skill.handler(*args, **kwargs)

    def add_skill_path(self, path: str) -> None:
        """添加工具路径"""
        self._skill_paths.append(path)

    def get_skill_paths(self) -> list[str]:
        """获取工具路径"""
        return self._skill_paths.copy()
