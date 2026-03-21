"""
FlowSkill Generator - Generate FlowSkill from project structure

Creates FlowSkill configuration for agent execution flows.
"""

from pathlib import Path
from typing import Any

from .import_analyzer import FlowSkill


class FlowSkillGenerator:
    """Generate FlowSkill from project structure"""

    def generate(
        self, local_path: Path, structure: dict[str, Any], repo_name: str = None
    ) -> FlowSkill | None:
        """Generate FlowSkill - analyze code execution flow"""
        key_files = []
        for pattern in ["*.py", "*.js", "*.ts", "*.sh", "Makefile", "package.json"]:
            key_files.extend(local_path.glob(pattern))

        code_context = ""
        for f in list(key_files)[:10]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")[:2000]
                code_context += f"\n# {f.name}\n{content}\n"
            except (OSError, UnicodeDecodeError):
                pass

        main_prompt = structure.get("main_prompt", "")

        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "react",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        lang = (
            structure.get("languages", ["unknown"])[0] if structure.get("languages") else "unknown"
        )
        lang = lang.lstrip(".")
        lang = ext_to_lang.get(f".{lang}", lang)

        if not repo_name:
            repo_name = local_path.name if local_path else "default"
            if local_path and local_path.parent and local_path.parent.name == "original":
                repo_name = local_path.parent.parent.name

        flowskill = FlowSkill(
            name=f"flow-{repo_name}",
            description=self._extract_flow_description(main_prompt),
            trigger_conditions=self._extract_triggers(main_prompt),
            required_skills=structure.get("skills", []),
            required_mcps=structure.get("mcps", []),
            required_evaluations=structure.get("evaluations", []),
            subagent_calls=self._extract_subagent_calls(structure.get("subagent_prompts", [])),
        )

        return flowskill

    def _extract_flow_description(self, prompt: str) -> str:
        """Extract flow description from prompt"""
        lines = prompt.split("\n")
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ["step", "process", "flow", "workflow"]):
                return " -> ".join(lines[i : i + 3]).strip()[:200]
        return "Default agent execution flow"

    def _extract_triggers(self, prompt: str) -> list[str]:
        """Extract trigger conditions"""
        triggers = []
        keywords = ["when", "if", "trigger", "on"]

        for line in prompt.split("\n"):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords) and len(line) < 100:
                triggers.append(line.strip()[:100])

        return triggers[:5]

    def _extract_subagent_calls(self, subagent_prompts: list[dict]) -> list[dict[str, Any]]:
        """Extract sub-agent calls"""
        calls = []
        for sa in subagent_prompts[:6]:
            calls.append(
                {
                    "name": sa.get("name", "unknown"),
                    "condition": f"task matches '{sa.get('description', '')}'",
                    "type": "general",
                }
            )
        return calls
