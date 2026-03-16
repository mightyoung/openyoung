"""
Metadata Extractor - 元数据提取器

从 GitHub 仓库提取 Agent 元数据:
- 仓库分析
- 代码结构提取
- README 摘要
- 技能提取
- 子 Agent 配置提取
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .schema import (
    AgentCapability,
    AgentMetadata,
    AgentTier,
    CompatibilityInfo,
    SkillDefinition,
    SubAgentConfig,
    create_basic_metadata,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """提取结果"""

    metadata: AgentMetadata
    warnings: list[str] = None

    def __post_init__(self):
        self.warnings = self.warnings or []


class MetadataExtractor:
    """元数据提取器

    从 GitHub 仓库或本地代码提取 Agent 元数据
    """

    def __init__(self):
        self._llm_enricher = None

    def set_llm_enricher(self, enricher):
        """设置 LLM 丰富器"""
        self._llm_enricher = enricher

    async def extract_from_github(
        self,
        repo_url: str,
        access_token: Optional[str] = None,
    ) -> ExtractionResult:
        """从 GitHub 仓库提取元数据

        Args:
            repo_url: GitHub 仓库 URL
            access_token: 可选的访问令牌

        Returns:
            提取结果
        """
        warnings = []

        # 1. 解析仓库 URL
        owner, repo_name = self._parse_repo_url(repo_url)
        if not owner or not repo_name:
            raise ValueError(f"Invalid repository URL: {repo_url}")

        # 2. 获取仓库信息
        repo_info = await self._get_github_repo(owner, repo_name, access_token)

        # 3. 分析代码结构
        code_structure = await self._analyze_code_structure(repo_info)

        # 4. 提取技能
        skills = await self._extract_skills(code_structure)

        # 5. 提取子 Agent
        subagents = await self._extract_subagents(code_structure)

        # 6. 构建基础元数据
        metadata = AgentMetadata(
            agent_id=f"{owner}/{repo_name}",
            name=repo_info.get("name", repo_name),
            description=repo_info.get("description", ""),
            version=repo_info.get("version", "1.0.0"),
            source_repo=repo_url,
            tier=self._infer_tier(code_structure),
            badges=self._extract_badges(repo_info, code_structure),
        )

        # 7. 提取能力
        metadata.capabilities = self._extract_capabilities(code_structure)
        metadata.skills = skills
        metadata.subagents = subagents

        # 8. 兼容性信息
        metadata.compatibility = CompatibilityInfo(
            required_skills=[s.skill_id for s in skills],
            min_context_length=8192,
        )

        # 9. LLM 丰富（可选）
        if self._llm_enricher:
            try:
                metadata = await self._llm_enricher.enrich(metadata, code_structure)
            except Exception as e:
                warnings.append(f"LLM enrichment failed: {e}")

        return ExtractionResult(metadata=metadata, warnings=warnings)

    async def extract_from_local(self, path: str) -> ExtractionResult:
        """从本地目录提取元数据

        Args:
            path: 本地目录路径

        Returns:
            提取结果
        """
        warnings = []
        base_path = Path(path)

        if not base_path.exists():
            raise ValueError(f"Path does not exist: {path}")

        # 分析代码结构
        code_structure = await self._analyze_local_structure(base_path)

        # 构建元数据
        metadata = create_basic_metadata(
            agent_id=base_path.name,
            name=base_path.name,
            description="",
            tier=self._infer_tier(code_structure),
        )

        # 提取能力
        metadata.capabilities = self._extract_capabilities(code_structure)
        metadata.skills = await self._extract_skills(code_structure)
        metadata.subagents = await self._extract_subagents(code_structure)

        # 读取 README
        readme = self._extract_readme(base_path)
        if readme:
            metadata.description = readme

        return ExtractionResult(metadata=metadata, warnings=warnings)

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        """解析 GitHub URL"""
        # https://github.com/owner/repo
        # git@github.com:owner/repo.git
        match = re.match(r"github\.com[/:]([^/]+)/([^/.]+)", url)
        if match:
            return match.group(1), match.group(2)
        return None, None

    async def _get_github_repo(self, owner: str, repo: str, token: Optional[str]) -> dict[str, Any]:
        """获取 GitHub 仓库信息"""
        import json
        import urllib.request

        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        return {
            "name": data.get("name", repo),
            "description": data.get("description", ""),
            "stars": data.get("stargazers_count", 0),
            "language": data.get("language", ""),
            "version": "1.0.0",  # 需要从代码中提取
        }

    async def _analyze_code_structure(self, repo_info: dict[str, Any]) -> dict[str, Any]:
        """分析代码结构"""
        # TODO: 实现实际的代码分析
        return {
            "languages": [repo_info.get("language", "Python")] if repo_info.get("language") else [],
            "has_agents": True,
            "has_skills": True,
            "has_subagents": False,
            "files": [],
        }

    async def _analyze_local_structure(self, base_path: Path) -> dict[str, Any]:
        """分析本地代码结构"""
        structure = {
            "languages": [],
            "has_agents": False,
            "has_skills": False,
            "has_subagents": False,
            "files": [],
        }

        # 扫描文件
        for ext in ["*.py", "*.js", "*.ts"]:
            structure["files"].extend(base_path.rglob(ext))

        # 检测 Agent
        if (base_path / "agent.py").exists() or (base_path / "agent.ts").exists():
            structure["has_agents"] = True

        # 检测 Skills
        if (base_path / "skills").exists():
            structure["has_skills"] = True

        # 检测子 Agent
        if (base_path / "subagents").exists() or (base_path / "agents").exists():
            structure["has_subagents"] = True

        return structure

    def _extract_capabilities(self, code_structure: dict[str, Any]) -> list[AgentCapability]:
        """提取能力列表"""
        capabilities = []

        if code_structure.get("has_agents"):
            capabilities.append(
                AgentCapability(
                    name="agent_execution",
                    description="Can execute agent tasks",
                    category="execution",
                    keywords=["agent", "task", "execution"],
                )
            )

        if code_structure.get("has_skills"):
            capabilities.append(
                AgentCapability(
                    name="skill_execution",
                    description="Can execute defined skills",
                    category="execution",
                    keywords=["skill", "tool"],
                )
            )

        return capabilities

    async def _extract_skills(self, code_structure: dict[str, Any]) -> list[SkillDefinition]:
        """提取技能定义"""
        # TODO: 实现实际的技能提取
        skills = []

        if code_structure.get("has_skills"):
            skills.append(
                SkillDefinition(
                    skill_id="code_analysis",
                    name="Code Analysis",
                    description="Analyze code structure and quality",
                    type="tool",
                )
            )

        return skills

    async def _extract_subagents(self, code_structure: dict[str, Any]) -> list[SubAgentConfig]:
        """提取子 Agent 配置"""
        # TODO: 实现实际的子 Agent 提取
        return []

    def _extract_badges(
        self, repo_info: dict[str, Any], code_structure: dict[str, Any]
    ) -> list[str]:
        """提取徽章"""
        badges = []

        stars = repo_info.get("stars", 0)
        if stars > 1000:
            badges.append("popular")
        if stars > 100:
            badges.append("established")

        language = repo_info.get("language", "").lower()
        if language == "python":
            badges.append("python")
        elif language == "typescript":
            badges.append("typescript")

        if code_structure.get("has_subagents"):
            badges.append("multi-agent")

        return badges

    def _extract_readme(self, base_path: Path) -> str:
        """提取 README 内容"""
        for readme_name in ["README.md", "README.txt", "readme.md"]:
            readme_path = base_path / readme_name
            if readme_path.exists():
                content = readme_path.read_text()
                # 截取前 500 字符
                return content[:500] if len(content) > 500 else content
        return ""

    def _infer_tier(self, code_structure: dict[str, Any]) -> AgentTier:
        """推断 Agent 层级"""
        if code_structure.get("has_subagents"):
            return AgentTier.ORCHESTRATOR
        elif code_structure.get("has_agents"):
            return AgentTier.SPECIALIZED
        return AgentTier.FOUNDATION
