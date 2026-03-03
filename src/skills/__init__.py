"""
Skills - 技能加载与管理
"""

from .metadata import SkillMetadata, LoadedSkill, RetrievalConfig
from .loader import SkillLoader
from .registry import SkillRegistry
from .retriever import UnifiedSkillRetriever, RetrievalResult

# 导出主要类
__all__ = [
    "SkillMetadata",
    "LoadedSkill",
    "RetrievalConfig",
    "SkillLoader",
    "SkillRegistry",
    "UnifiedSkillRetriever",
    "RetrievalResult",
]

# 保持向后兼容
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional, List
import importlib.util
from pathlib import Path


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
        self._skills: Dict[str, Skill] = {}
        self._skill_paths: List[str] = []

    def register(self, skill: Skill) -> None:
        """注册技能"""
        self._skills[skill.name] = skill

    def unregister(self, name: str) -> bool:
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            return True
        return False

    def load(self, name: str) -> Optional[Skill]:
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

    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self._skills.keys())

    def get_skill(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self._skills.get(name)

    def discover_skills(self, path: str) -> List[Skill]:
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

    def get_skill_paths(self) -> List[str]:
        """获取工具路径"""
        return self._skill_paths.copy()
