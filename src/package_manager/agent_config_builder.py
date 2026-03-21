"""
Agent Config Builder - Create agent configurations from analysis results

Builds agent.yaml configuration files from project structure and analysis.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .import_analyzer import FlowSkill
from .subagent_registry import SubAgentBinding


class AgentConfigBuilder:
    """Build agent configuration from analysis results"""

    def __init__(self, packages_dir: str = "packages", subagents_dir: str = "subagents"):
        self.packages_dir = Path(packages_dir)
        self.subagents_dir = Path(subagents_dir)

    def build(
        self,
        host: str,
        owner: str,
        repo: str,
        agent_name: str,
        structure: dict[str, Any],
        flowskill: FlowSkill | None,
        config_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build agent configuration

        Args:
            host: Source host (github.com, gitlab.com, gitee.com)
            owner: Repository owner
            repo: Repository name
            agent_name: Agent name
            structure: Project structure analysis
            flowskill: Generated FlowSkill (optional)
            config_result: Parsed configuration files

        Returns:
            Build results with paths and metadata
        """
        results = {
            "agent": None,
            "flowskill": None,
            "skills": [],
            "mcps": [],
            "hooks": [],
            "evaluations": [],
            "subagents": [],
            "config": {},
            "source": host,
        }

        # Create agent directory
        agent_dir = self.packages_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Build agent config
        source_url = f"https://{host}.com/{owner}/{repo}"
        agent_config = {
            "name": agent_name,
            "version": "1.0.0",
            "description": f"Imported from {host}/{owner}/{repo}",
            "source_url": source_url,
            "source_host": host,
            "model": {
                "name": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "tools": ["read", "write", "edit", "bash", "glob", "grep"],
            "skills": [],
            "mcps": [],
            "sub_agents": [],
            "flowskill": None,
            "permission": {"_global": "ask", "rules": []},
        }

        # Add FlowSkill
        if flowskill:
            agent_config["flowskill"] = self._flowskill_to_dict(flowskill)
            results["flowskill"] = flowskill.name

        # Add system_prompt
        if structure.get("main_prompt"):
            agent_config["system_prompt"] = structure["main_prompt"][:4000]

        # Parse and add SubAgents
        for sa_prompt in structure.get("subagent_prompts", []):
            subagent = SubAgentBinding(
                name=sa_prompt.get("name", "unknown"),
                type="general",
                description=sa_prompt.get("description", ""),
            )
            results["subagents"].append(asdict(subagent))

            # Save SubAgent to library
            self._save_subagent(subagent)

        agent_config["sub_agents"] = [
            {
                "name": sa["name"],
                "type": sa.get("type", "general"),
                "description": sa.get("description", ""),
            }
            for sa in results["subagents"]
        ]

        # Add config references
        agent_config["skills"] = [s["path"] for s in config_result.get("skills", [])]
        agent_config["mcps"] = [m["path"] for m in config_result.get("mcps", [])]
        results["skills"] = [s["path"] for s in config_result.get("skills", [])]
        results["mcps"] = [m["path"] for m in config_result.get("mcps", [])]
        results["hooks"] = [h["path"] for h in config_result.get("hooks", [])]
        results["evaluations"] = [e["path"] for e in config_result.get("evaluations", [])]

        # Save agent config
        agent_yaml_path = agent_dir / "agent.yaml"
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(agent_config, f, allow_unicode=True, default_flow_style=False)

        results["agent"] = str(agent_yaml_path)

        # Save original config
        if structure.get("main_prompt"):
            config_dir = agent_dir / "original"
            config_dir.mkdir(exist_ok=True)
            with open(config_dir / "CLAUDE.md", "w", encoding="utf-8") as f:
                f.write(structure["main_prompt"])
            results["config"]["CLAUDE.md"] = str(config_dir / "CLAUDE.md")

        self._print_summary(agent_name, results, flowskill)

        return results

    def _flowskill_to_dict(self, flowskill: FlowSkill) -> dict[str, Any]:
        """Convert FlowSkill to dict"""
        return {
            "name": flowskill.name,
            "description": flowskill.description,
            "trigger_conditions": flowskill.trigger_conditions,
            "required_skills": flowskill.required_skills,
            "required_mcps": flowskill.required_mcps,
            "required_evaluations": flowskill.required_evaluations,
            "subagent_calls": flowskill.subagent_calls,
        }

    def _save_subagent(self, subagent: SubAgentBinding) -> None:
        """Save subagent to library"""
        self.subagents_dir.mkdir(parents=True, exist_ok=True)
        subagent_dir = self.subagents_dir / subagent.name
        subagent_dir.mkdir(parents=True, exist_ok=True)
        with open(subagent_dir / "agent.yaml", "w", encoding="utf-8") as f:
            yaml.dump(asdict(subagent), f, allow_unicode=True, default_flow_style=False)

    def _print_summary(
        self, agent_name: str, results: dict[str, Any], flowskill: FlowSkill | None
    ) -> None:
        """Print import summary"""
        print("[OK] Import complete!")
        print(f"  - Agent: {agent_name}")
        print(f"  - Skills: {len(results['skills'])}")
        print(f"  - MCPs: {len(results['mcps'])}")
        print(f"  - Hooks: {len(results['hooks'])}")
        print(f"  - SubAgents: {len(results['subagents'])}")
        if flowskill:
            print(f"  - FlowSkill: {flowskill.name}")
