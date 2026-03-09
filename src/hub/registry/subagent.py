"""
SubAgent Registry
SubAgent 库管理 - 维护供主 Agent 调用的子 Agent 配置
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from src.package_manager.base_registry import BaseRegistry


@dataclass
class SubAgentBinding:
    """SubAgent 绑定配置"""

    name: str
    type: str = "general"
    description: str = ""
    skills: list[str] = None
    mcps: list[str] = None
    evaluations: list[str] = None
    model: str = "deepseek-chat"
    temperature: float = 0.7
    instructions: str = ""
    hidden: bool = False

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.mcps is None:
            self.mcps = []
        if self.evaluations is None:
            self.evaluations = []


class SubAgentRegistry(BaseRegistry):
    """SubAgent 注册表"""

    def __init__(self, subagents_dir: str = "subagents"):
        super().__init__(subagents_dir)
        self.subagents_dir = self.base_dir

    def discover_subagents(self) -> list[str]:
        """发现所有 SubAgent"""
        subagents = []
        if not self.subagents_dir.exists():
            return subagents

        for item in self.subagents_dir.iterdir():
            if item.is_dir():
                config_file = item / "agent.yaml"
                if config_file.exists():
                    subagents.append(item.name)
            elif item.suffix in [".yaml", ".yml", ".json"]:
                subagents.append(item.stem)

        return subagents

    def load_subagent(self, name: str) -> SubAgentBinding | None:
        """加载 SubAgent 配置"""
        # 尝试多种格式
        for ext in ["yaml", "yml", "json"]:
            config_file = self.subagents_dir / name / f"agent.{ext}"
            if config_file.exists():
                return self._load_from_file(config_file)

            # 直接文件
            config_file = self.subagents_dir / f"{name}.{ext}"
            if config_file.exists():
                return self._load_from_file(config_file)

        return None

    def _load_from_file(self, path: Path) -> SubAgentBinding | None:
        """从文件加载配置"""
        try:
            if path.suffix == ".json":
                with open(path, encoding="utf-8") as f:
                    config = json.load(f)
            else:
                with open(path, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

            return SubAgentBinding(
                name=config.get("name", path.stem),
                type=config.get("type", "general"),
                description=config.get("description", ""),
                skills=config.get("skills", []),
                mcps=config.get("mcps", []),
                evaluations=config.get("evaluations", []),
                model=config.get("model", "deepseek-chat"),
                temperature=config.get("temperature", 0.7),
                instructions=config.get("instructions", ""),
                hidden=config.get("hidden", False),
            )
        except Exception as e:
            print(f"[Error] Failed to load subagent {path}: {e}")
            return None

    def save_subagent(self, subagent: SubAgentBinding) -> Path:
        """保存 SubAgent 配置"""
        agent_dir = self.subagents_dir / subagent.name
        agent_dir.mkdir(parents=True, exist_ok=True)

        config_file = agent_dir / "agent.yaml"
        config = {
            "name": subagent.name,
            "type": subagent.type,
            "description": subagent.description,
            "skills": subagent.skills,
            "mcps": subagent.mcps,
            "evaluations": subagent.evaluations,
            "model": subagent.model,
            "temperature": subagent.temperature,
            "instructions": subagent.instructions,
            "hidden": subagent.hidden,
        }

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        return config_file

    def list_subagents(self) -> list[dict[str, Any]]:
        """列出所有 SubAgent"""
        subagents = []
        for name in self.discover_subagents():
            subagent = self.load_subagent(name)
            if subagent:
                subagents.append(asdict(subagent))
        return subagents

    def delete_subagent(self, name: str) -> bool:
        """删除 SubAgent"""
        agent_dir = self.subagents_dir / name
        if agent_dir.exists():
            import shutil

            shutil.rmtree(agent_dir)
            return True
        return False


# CLI 入口
def create_subagent_registry(subagents_dir: str = "subagents") -> SubAgentRegistry:
    """创建 SubAgent 注册表"""
    return SubAgentRegistry(subagents_dir)
