"""
SubAgent Discovery - Find sub-agents from multiple sources

Discovers sub-agents from AGENTS.md, roles/, agents/, and config files.
"""

from pathlib import Path

import yaml


class SubAgentDiscovery:
    """Discover sub-agents from project"""

    def discover_all(self, local_path: Path) -> list[dict[str, str]]:
        """Discover all sub-agents from multiple sources"""
        all_subagents = []
        seen_names = set()

        for sa in self._parse_all_agents_md_files(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        for sa in self._discover_from_roles(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        for sa in self._discover_from_agents_dir(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        for sa in self._discover_from_config(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        if all_subagents:
            print(f"[SubAgent] Total discovered: {len(all_subagents)} SubAgents")

        return all_subagents

    def _parse_all_agents_md_files(self, local_path: Path) -> list[dict[str, str]]:
        """Recursively find and parse all AGENTS.md files"""
        import re

        subagents = []

        for filename in ["AGENTS.md", "agents.md", "SUBAGENTS.md", "ROLES.md"]:
            for md_file in local_path.rglob(filename):
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")

                    pattern = re.compile(r"^#{2,3}\s+(\w+)\s*[-:]?\s*(.*)$", re.MULTILINE)
                    for match in pattern.finditer(content):
                        name = match.group(1).strip()
                        desc = match.group(2).strip()[:200]
                        subagents.append(
                            {
                                "name": name,
                                "description": desc,
                                "source": filename,
                                "file": str(md_file.relative_to(local_path)),
                            }
                        )
                except Exception as e:
                    print(f"[Warning] Failed to parse {md_file}: {e}")

        return subagents

    def _parse_agents_md(self, path: Path) -> list[dict[str, str]]:
        """Parse AGENTS.md file"""
        import re

        subagents = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            # Simple parse: ### Agent Name or ## Agent Name
            pattern = re.compile(r"^#{2,3}\s+(\w+)\s*[-:]?\s*(.*)$", re.MULTILINE)
            for match in pattern.finditer(content):
                name = match.group(1).strip()
                desc = match.group(2).strip()[:200]
                subagents.append({"name": name, "description": desc, "source": "agents.md"})
        except Exception as e:
            print(f"[Warning] Failed to parse AGENTS.md: {e}")

        return subagents

    def _discover_from_roles(self, local_path: Path) -> list[dict[str, str]]:
        """Discover sub-agents from roles/ directory"""
        import re

        subagents = []

        # Find all roles directories
        roles_dirs = []
        for item in local_path.rglob("roles"):
            if item.is_dir():
                roles_dirs.append(item)

        for roles_dir in roles_dirs:
            for role_file in roles_dir.glob("*.py"):
                if role_file.name.startswith("_") or role_file.name == "__init__.py":
                    continue

                try:
                    content = role_file.read_text(encoding="utf-8", errors="ignore")

                    class_pattern = re.compile(r"^class\s+(\w+)(?:Role)?\s*\(.*Role", re.MULTILINE)
                    for match in class_pattern.finditer(content):
                        name = match.group(1).lower()
                        desc = self._extract_role_description(content, match.start())[:200]
                        subagents.append(
                            {
                                "name": name,
                                "description": desc or f"Role from {role_file.name}",
                                "source": "roles/",
                                "file": str(role_file.relative_to(local_path)),
                            }
                        )
                except Exception as e:
                    print(f"[Warning] Failed to parse role file {role_file}: {e}")

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from roles/ directory")

        return subagents

    def _extract_role_description(self, content: str, class_start: int) -> str:
        """Extract description from role file"""
        import re

        doc_pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        for match in doc_pattern.finditer(content[class_start : class_start + 500]):
            desc = match.group(1).strip().split("\n")[0]
            if len(desc) > 10:
                return desc
        return ""

    def _discover_from_agents_dir(self, local_path: Path) -> list[dict[str, str]]:
        """Discover sub-agents from subagents/ or agents/ directory"""
        subagents = []

        for dir_name in ["subagents", "agents", "agent"]:
            subagents_dir = local_path / dir_name
            if not subagents_dir.exists():
                continue

            for agent_dir in subagents_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                for config_file in agent_dir.glob("*.yaml"):
                    try:
                        config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

                        name = config.get("name", agent_dir.name)
                        desc = config.get("description", f"Agent from {dir_name}/")
                        subagents.append(
                            {
                                "name": name,
                                "description": desc[:200],
                                "source": f"{dir_name}/",
                                "file": str(config_file.relative_to(local_path)),
                            }
                        )
                    except Exception as e:
                        print(f"[Warning] Failed to parse {config_file}: {e}")

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from agents directory")

        return subagents

    def _discover_from_config(self, local_path: Path) -> list[dict[str, str]]:
        """Discover sub-agents from config files"""
        subagents = []

        for config_file in local_path.rglob("agents.yaml"):
            try:
                config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

                agents_list = config.get("agents", []) or config.get("sub_agents", [])
                for agent in agents_list:
                    subagents.append(
                        {
                            "name": agent.get("name", "unknown"),
                            "description": agent.get("description", "")[:200],
                            "source": "agents.yaml",
                            "file": str(config_file.relative_to(local_path)),
                        }
                    )
            except Exception as e:
                print(f"[Warning] Failed to parse {config_file}: {e}")

        config_dir = local_path / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    content = config_file.read_text(encoding="utf-8", errors="ignore")
                    if "role:" in content.lower() or "agent:" in content.lower():
                        config = yaml.safe_load(content)
                        if isinstance(config, dict):
                            for key, value in config.items():
                                if isinstance(value, dict) and (
                                    "role" in str(key).lower() or "agent" in str(key).lower()
                                ):
                                    subagents.append(
                                        {
                                            "name": key,
                                            "description": f"From {config_file.name}",
                                            "source": "config/",
                                            "file": str(config_file.relative_to(local_path)),
                                        }
                                    )
                except Exception:
                    pass

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from config files")

        return subagents
