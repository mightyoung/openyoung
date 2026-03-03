"""
Unified Skill Retriever - 统一技能检索
双轨检索: Package + Semantic
"""

from typing import List, Dict, Any, Optional


class Skill:
    """技能"""

    def __init__(self, name: str, description: str, tags: List[str] = None):
        self.name = name
        self.description = description
        self.tags = tags or []


class UnifiedSkillRetriever:
    """统一技能检索器 - 双轨检索"""

    def __init__(self):
        self._package_skills: Dict[str, List[Skill]] = {}  # package -> skills
        self._all_skills: List[Skill] = []

    def register_skill(self, skill: Skill, package: str = "default"):
        """注册技能"""
        if package not in self._package_skills:
            self._package_skills[package] = []
        self._package_skills[package].append(skill)
        self._all_skills.append(skill)

    def retrieve_by_keyword(self, keyword: str) -> List[Skill]:
        """基于关键词检索"""
        results = []
        keyword_lower = keyword.lower()
        for skill in self._all_skills:
            if (
                keyword_lower in skill.name.lower()
                or keyword_lower in skill.description.lower()
            ):
                results.append(skill)
        return results

    def retrieve_by_tags(self, tags: List[str]) -> List[Skill]:
        """基于标签检索"""
        results = []
        tags_lower = [t.lower() for t in tags]
        for skill in self._all_skills:
            for tag in skill.tags:
                if tag.lower() in tags_lower:
                    results.append(skill)
                    break
        return results

    def retrieve_unified(
        self, query: str, tags: Optional[List[str]] = None
    ) -> List[Skill]:
        """统一检索 - 结合关键词和标签"""
        keyword_results = self.retrieve_by_keyword(query)

        if tags:
            tag_results = self.retrieve_by_tags(tags)
            # 合并结果，按出现次数排序
            seen = set()
            merged = []
            for s in keyword_results + tag_results:
                if s.name not in seen:
                    seen.add(s.name)
                    merged.append(s)
            return merged

        return keyword_results

    def list_skills(self) -> List[Skill]:
        """列出所有技能"""
        return self._all_skills
