"""
Dependency Resolver - Agent 依赖解析器
解析 Agent 配置中的 Skills/MCPs/Hooks 依赖
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class DependencyInfo:
    """依赖信息"""

    type: str  # "skill", "mcp", "hook"
    name: str
    source: str | None = None  # 来源路径或 URL
    required: bool = True
    optional: bool = False


@dataclass
class AgentDependency:
    """Agent 依赖"""

    agent_name: str
    skills: list[DependencyInfo] = field(default_factory=list)
    mcps: list[DependencyInfo] = field(default_factory=list)
    hooks: list[DependencyInfo] = field(default_factory=list)

    @property
    def all_dependencies(self) -> list[DependencyInfo]:
        """所有依赖"""
        return self.skills + self.mcps + self.hooks

    @property
    def required_dependencies(self) -> list[DependencyInfo]:
        """必需的依赖"""
        return [d for d in self.all_dependencies if d.required and not d.optional]

    @property
    def optional_dependencies(self) -> list[DependencyInfo]:
        """可选的依赖"""
        return [d for d in self.all_dependencies if d.optional]


class DependencyResolver:
    """依赖解析器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self.skills_dir = Path("skills")
        self.hooks_dir = Path("hooks")

    def resolve_from_config(self, config: dict[str, Any]) -> AgentDependency:
        """从配置解析依赖

        支持的配置格式：
        - required_skills: ["skill-github-import", ...]
        - required_mcps: ["mcp-github", ...]
        - required_hooks: ["hooks-auto-commit", ...]
        """
        agent_name = config.get("name", "unknown")

        dep = AgentDependency(agent_name=agent_name)

        # 解析 required_skills
        for skill in config.get("required_skills", []):
            dep.skills.append(self._parse_skill_dependency(skill))

        # 解析 required_mcps
        for mcp in config.get("required_mcps", []):
            dep.mcps.append(self._parse_mcp_dependency(mcp))

        # 解析 required_hooks
        for hook in config.get("required_hooks", []):
            dep.hooks.append(self._parse_hook_dependency(hook))

        # 从 flowskill 配置解析
        flowskill = config.get("flowskill", {})
        if flowskill:
            # 从 required_skills 解析
            for skill in flowskill.get("required_skills", []):
                dep.skills.append(self._parse_skill_dependency(skill, required=False))

            # 从 required_mcps 解析
            for mcp in flowskill.get("required_mcps", []):
                dep.mcps.append(self._parse_mcp_dependency(mcp, required=False))

        return dep

    def resolve_from_file(self, agent_path: str) -> AgentDependency:
        """从文件解析依赖"""
        agent_path = Path(agent_path)
        agent_yaml = agent_path / "agent.yaml"

        if not agent_yaml.exists():
            raise FileNotFoundError(f"Agent config not found: {agent_yaml}")

        with open(agent_yaml, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return self.resolve_from_config(config)

    def check_installed(self, dependency: DependencyInfo) -> bool:
        """检查依赖是否已安装"""
        if dependency.type == "skill":
            # 检查 skills 目录
            skill_path = self.skills_dir / dependency.name
            return skill_path.exists()
        elif dependency.type == "mcp":
            # 检查 packages/mcp-* 目录
            mcp_path = self.packages_dir / f"mcp-{dependency.name}"
            return mcp_path.exists()
        elif dependency.type == "hook":
            # 检查 hooks 目录
            hook_path = self.hooks_dir / dependency.name
            return hook_path.exists()
        return False

    def find_missing(self, dep: AgentDependency) -> AgentDependency:
        """找出缺失的依赖"""
        missing = AgentDependency(agent_name=dep.agent_name)

        for skill in dep.skills:
            if not self.check_installed(skill):
                missing.skills.append(skill)

        for mcp in dep.mcps:
            if not self.check_installed(mcp):
                missing.mcps.append(mcp)

        for hook in dep.hooks:
            if not self.check_installed(hook):
                missing.hooks.append(hook)

        return missing

    def _parse_skill_dependency(self, skill: Any, required: bool = True) -> DependencyInfo:
        """解析 Skill 依赖"""
        if isinstance(skill, str):
            return DependencyInfo(type="skill", name=skill, required=required)
        elif isinstance(skill, dict):
            return DependencyInfo(
                type="skill",
                name=skill.get("name", skill.get("path", "unknown")),
                source=skill.get("source"),
                required=skill.get("required", required),
                optional=skill.get("optional", False),
            )
        return DependencyInfo(type="skill", name="unknown", required=False)

    def _parse_mcp_dependency(self, mcp: Any, required: bool = True) -> DependencyInfo:
        """解析 MCP 依赖"""
        if isinstance(mcp, str):
            return DependencyInfo(type="mcp", name=mcp, required=required)
        elif isinstance(mcp, dict):
            return DependencyInfo(
                type="mcp",
                name=mcp.get("name", mcp.get("server", "unknown")),
                source=mcp.get("source"),
                required=mcp.get("required", required),
                optional=mcp.get("optional", False),
            )
        return DependencyInfo(type="mcp", name="unknown", required=False)

    def _parse_hook_dependency(self, hook: Any, required: bool = True) -> DependencyInfo:
        """解析 Hook 依赖"""
        if isinstance(hook, str):
            return DependencyInfo(type="hook", name=hook, required=required)
        elif isinstance(hook, dict):
            return DependencyInfo(
                type="hook",
                name=hook.get("name", hook.get("path", "unknown")),
                source=hook.get("source"),
                required=hook.get("required", required),
                optional=hook.get("optional", False),
            )
        return DependencyInfo(type="hook", name="unknown", required=False)


# ========== 便捷函数 ==========


def resolve_agent_dependencies(agent_path: str) -> tuple[AgentDependency, AgentDependency]:
    """解析 Agent 依赖，返回 (all, missing)

    Args:
        agent_path: Agent 配置目录路径

    Returns:
        (所有依赖, 缺失的依赖)
    """
    resolver = DependencyResolver()
    all_deps = resolver.resolve_from_file(agent_path)
    missing_deps = resolver.find_missing(all_deps)
    return all_deps, missing_deps
