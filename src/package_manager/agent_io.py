"""
Agent Package Exporter/Importer
Agent 组合包的导出与载入功能
"""

import json
import shutil
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class AgentExporter:
    """Agent 组合包导出器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)

    def export_agent(
        self,
        agent_name: str,
        output_dir: str,
        include_skills: bool = True,
        include_subagents: bool = True,
    ) -> bool:
        """导出 Agent 为独立包

        Args:
            agent_name: Agent 名称
            output_dir: 输出目录
            include_skills: 是否包含引用的 skills
            include_subagents: 是否包含子代理

        Returns:
            bool: 导出是否成功
        """
        # 查找 agent 配置
        agent_path = None
        for item in self.packages_dir.iterdir():
            if item.is_dir():
                if item.name == f"agent-{agent_name}" or item.name == agent_name:
                    yaml_file = item / "agent.yaml"
                    if yaml_file.exists():
                        agent_path = item
                        break

        if not agent_path:
            print(f"[Error] Agent not found: {agent_name}")
            return False

        # 创建输出目录
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        # 读取配置
        with open(agent_path / "agent.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 复制 agent 配置
        export_dir = output / f"agent-{agent_name}"
        export_dir.mkdir(exist_ok=True)

        with open(export_dir / "agent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True)

        # 导出引用的 skills
        if include_skills:
            skills = config.get("skills", [])
            for skill_name in skills:
                skill_path = self.packages_dir / f"skill-{skill_name}"
                if skill_path.exists():
                    dest = export_dir / "skills" / f"skill-{skill_name}"
                    shutil.copytree(skill_path, dest, dirs_exist_ok=True)
                    print(f"[Export] Skill: {skill_name}")

        # 导出 pyproject.toml
        pyproject = agent_path / "pyproject.toml"
        if pyproject.exists():
            shutil.copy2(pyproject, export_dir / "pyproject.toml")

        # 生成 metadata
        metadata = {
            "name": f"agent-{agent_name}",
            "version": config.get("version", "1.0.0"),
            "exported_at": datetime.now().isoformat(),
            "type": "agent",
            "config": {
                "model": config.get("model", {}).get("name"),
                "tools": config.get("tools", []),
                "skills": config.get("skills", []),
                "sub_agents_count": len(config.get("sub_agents", [])),
            },
        }

        with open(export_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"[OK] Exported to: {export_dir}")
        return True


class AgentImporter:
    """Agent 组合包导入器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self.packages_dir.mkdir(parents=True, exist_ok=True)

    def import_agent(self, source_path: str) -> bool:
        """从目录导入 Agent

        Args:
            source_path: 源目录路径

        Returns:
            bool: 导入是否成功
        """
        source = Path(source_path)

        if not source.exists():
            print(f"[Error] Source not found: {source_path}")
            return False

        # 查找 agent.yaml
        agent_yaml = source / "agent.yaml"
        if not agent_yaml.exists():
            # 尝试在子目录查找
            for item in source.rglob("agent.yaml"):
                agent_yaml = item
                break

        if not agent_yaml.exists():
            print(f"[Error] No agent.yaml found in: {source_path}")
            return False

        # 读取配置
        with open(agent_yaml, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        agent_name = config.get("name", source.name)
        dest_dir = self.packages_dir / f"agent-{agent_name}"

        # 检查是否已存在
        if dest_dir.exists():
            print(f"[Warning] Agent already exists: {agent_name}")
            # 备份
            backup = self.packages_dir / f"agent-{agent_name}.backup"
            shutil.move(str(dest_dir), str(backup))
            print(f"[Backup] Old agent backed up to: {backup}")

        # 复制文件
        shutil.copytree(agent_yaml.parent, dest_dir, dirs_exist_ok=True)

        # 复制 skills
        skills_dir = source / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    dest_skill = self.packages_dir / skill_dir.name
                    shutil.copytree(skill_dir, dest_skill, dirs_exist_ok=True)
                    print(f"[Import] Skill: {skill_dir.name}")

        print(f"[OK] Imported: {agent_name} -> {dest_dir}")
        return True


def export_agent(agent_name: str, output_dir: str = "./exports"):
    """导出 Agent (CLI 入口)"""
    exporter = AgentExporter()
    return exporter.export_agent(agent_name, output_dir)


def import_agent(source_path: str):
    """导入 Agent (CLI 入口)"""
    importer = AgentImporter()
    return importer.import_agent(source_path)
