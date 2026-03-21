"""
Project Analyzer - Project structure analysis and config parsing

Analyzes imported project structure, detects languages, skills, MCPs, hooks.
"""

import json
from pathlib import Path
from typing import Any

import yaml


class ProjectAnalyzer:
    """Project structure analyzer"""

    def analyze_structure(self, local_path: Path) -> dict[str, Any]:
        """Analyze project structure"""
        structure = {
            "languages": [],
            "has_claude_md": False,
            "has_agents_md": False,
            "has_skills": False,
            "has_mcps": False,
            "has_hooks": False,
            "has_evaluation": False,
            "skills": [],
            "mcps": [],
            "hooks": [],
            "evaluations": [],
            "main_prompt": "",
            "subagent_prompts": [],
            "files": [],
        }

        if not local_path or not local_path.exists():
            return structure

        # Scan files
        for item in local_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(local_path)
                structure["files"].append(str(rel_path))

                # Detect key files
                name = item.name.lower()
                if name == "claude.md":
                    structure["has_claude_md"] = True
                    structure["main_prompt"] = item.read_text(encoding="utf-8", errors="ignore")[:5000]
                elif name == "agents.md":
                    structure["has_agents_md"] = True
                elif "skill" in str(rel_path):
                    structure["has_skills"] = True
                    if item.suffix in [".yaml", ".yml", ".json", ".md"]:
                        structure["skills"].append(str(rel_path))
                elif "mcp" in str(rel_path):
                    structure["has_mcps"] = True
                    if item.suffix == ".json":
                        structure["mcps"].append(str(rel_path))
                elif "hook" in str(rel_path):
                    structure["has_hooks"] = True
                    structure["hooks"].append(str(rel_path))
                elif "eval" in str(rel_path):
                    structure["has_evaluation"] = True
                    structure["evaluations"].append(str(rel_path))

        # Detect languages
        ext_counts = {}
        for item in local_path.rglob("*"):
            if item.is_file() and item.name != ".git":
                ext = item.suffix
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1

        structure["languages"] = sorted(
            ext_counts.keys(), key=lambda x: ext_counts[x], reverse=True
        )[:5]

        return structure

    def parse_configs(self, local_path: Path) -> dict[str, Any]:
        """Parse configuration files"""
        configs = {
            "skills": [],
            "mcps": [],
            "hooks": [],
            "evaluations": [],
        }

        if not local_path:
            return configs

        # Parse skills
        for item in local_path.rglob("skill*.yaml"):
            try:
                config = yaml.safe_load(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["skills"].append({"path": str(item), "config": config})
            except (OSError, UnicodeDecodeError):
                pass

        # Parse SKILL.md files
        for item in local_path.rglob("SKILL.md"):
            try:
                content = item.read_text(encoding="utf-8", errors="ignore")
                skill_name = item.parent.name if item.parent.name else item.stem
                configs["skills"].append(
                    {
                        "path": str(item),
                        "config": {
                            "name": skill_name,
                            "type": "markdown",
                            "content_preview": content[:500],
                        },
                    }
                )
            except (OSError, UnicodeDecodeError):
                pass

        # Parse mcp.json
        for item in local_path.rglob("mcp.json"):
            try:
                config = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["mcps"].append({"path": str(item), "config": config})
            except (OSError, UnicodeDecodeError):
                pass

        # Check extensions_config.json
        for item in local_path.rglob("extensions_config*.json"):
            try:
                config = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["mcps"].append({"path": str(item), "config": config})
            except (OSError, UnicodeDecodeError):
                pass

        # Parse hooks
        for item in local_path.rglob("hooks*.json"):
            try:
                config = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["hooks"].append({"path": str(item), "config": config})
            except (OSError, UnicodeDecodeError):
                pass

        # Parse evaluation
        for item in local_path.rglob("*eval*.yaml"):
            try:
                config = yaml.safe_load(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["evaluations"].append({"path": str(item), "config": config})
            except (OSError, UnicodeDecodeError):
                pass

        return configs
