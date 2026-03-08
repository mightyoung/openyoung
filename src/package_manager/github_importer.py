"""
GitHub Repository Importer
从 GitHub 仓库自动分析并导入 Agent 配置
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass
class GitHubFile:
    """GitHub 文件"""

    path: str
    content: str
    is_yaml: bool
    is_json: bool


class GitHubImporter:
    """GitHub 仓库导入器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self.packages_dir.mkdir(parents=True, exist_ok=True)

    def import_from_url(self, github_url: str, agent_name: str = None) -> dict[str, Any]:
        """从 GitHub URL 导入

        Args:
            github_url: GitHub 仓库 URL (如 https://github.com/affaan-m/everything-claude-code)
            agent_name: 可选的 Agent 名称

        Returns:
            导入结果
        """
        # 解析 owner/repo
        owner, repo = self._parse_github_url(github_url)
        if not owner or not repo:
            return {"error": f"Invalid GitHub URL: {github_url}"}

        # 使用用户指定的名称或从 repo 推断
        if not agent_name:
            agent_name = repo

        print(f"[GitHub] Importing {owner}/{repo} as '{agent_name}'...")

        # 获取仓库内容
        files = self._fetch_repo_files(owner, repo)
        if not files:
            return {"error": "Failed to fetch repository files"}

        # 分析并导入
        return self._import_files(owner, repo, files, agent_name)

    def _parse_github_url(self, url: str) -> tuple:
        """解析 GitHub URL"""
        # https://github.com/owner/repo 或 owner/repo
        url = url.strip().rstrip("/")

        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None

    def _fetch_repo_files(self, owner: str, repo: str) -> list[GitHubFile]:
        """获取仓库文件列表"""
        files = []

        # 使用 GitHub API 获取默认分支
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json"}

        # 添加 token 如果有
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            response = httpx.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            repo_info = response.json()
            default_branch = repo_info.get("default_branch", "main")
        except Exception as e:
            print(f"[Error] Failed to get repo info: {e}")
            return []

        # 获取目录结构
        tree_url = (
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        )

        try:
            response = httpx.get(tree_url, headers=headers, timeout=30)
            response.raise_for_status()
            tree = response.json()
            tree_items = tree.get("tree", [])
        except Exception as e:
            print(f"[Error] Failed to get repo tree: {e}")
            return []

        # 筛选关键文件
        target_patterns = [
            "CLAUDE.md",
            "AGENTS.md",
            ".claude",
            "skill",
            "mcp",
            "hooks",
            "agent.yaml",
            "agent.json",
        ]

        for item in tree_items:
            if item.get("type") != "blob":
                continue

            path = item.get("path", "")
            # 检查是否是目标文件
            if not any(p in path.lower() for p in target_patterns):
                continue

            # 跳过大型文件
            if item.get("size", 0) > 500000:
                continue

            # 获取文件内容
            file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            try:
                response = httpx.get(file_url, headers=headers, timeout=30)
                response.raise_for_status()
                content_data = response.json()

                content = content_data.get("content", "")
                if content:
                    # Base64 解码
                    import base64

                    try:
                        content = base64.b64decode(content).decode("utf-8")
                    except:
                        pass

                    gh_file = GitHubFile(
                        path=path,
                        content=content,
                        is_yaml=path.endswith((".yaml", ".yml")),
                        is_json=path.endswith(".json"),
                    )
                    files.append(gh_file)

            except Exception as e:
                print(f"[Warning] Failed to fetch {path}: {e}")

        print(f"[GitHub] Found {len(files)} relevant files")
        return files

    def _import_files(
        self, owner: str, repo: str, files: list[GitHubFile], agent_name: str = None
    ) -> dict[str, Any]:
        """导入文件"""
        results = {
            "agent": None,
            "skills": [],
            "mcps": [],
            "hooks": [],
            "config": {},
        }

        if not agent_name:
            agent_name = f"agent-{repo}"

        # 1. 查找 Agent 配置
        claude_md = None
        agents_md = None
        for f in files:
            if f.path.endswith("CLAUDE.md"):
                claude_md = f.content
            elif f.path.endswith("AGENTS.md"):
                agents_md = f.content
            elif "agent.yaml" in f.path or "agent.json" in f.path:
                # 已有 agent 配置
                pass

        # 2. 创建 Agent 配置
        agent_config = self._create_agent_config(agent_name, repo, claude_md, agents_md, files)

        # 3. 保存 Agent 配置
        agent_dir = self.packages_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        agent_yaml_path = agent_dir / "agent.yaml"
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(agent_config, f, allow_unicode=True, default_flow_style=False)

        results["agent"] = str(agent_yaml_path)
        print(f"[OK] Agent config: {agent_yaml_path}")

        # 4. 保存原始配置
        if claude_md or agents_md:
            config_dir = agent_dir / "original"
            config_dir.mkdir(exist_ok=True)

            if claude_md:
                with open(config_dir / "CLAUDE.md", "w", encoding="utf-8") as f:
                    f.write(claude_md)
                results["config"]["CLAUDE.md"] = str(config_dir / "CLAUDE.md")

            if agents_md:
                with open(config_dir / "AGENTS.md", "w", encoding="utf-8") as f:
                    f.write(agents_md)
                results["config"]["AGENTS.md"] = str(config_dir / "AGENTS.md")

        # 5. 分析 skills
        skills = [f for f in files if "skill" in f.path.lower()]
        for skill in skills[:5]:  # 最多5个
            skill_name = skill.path.split("/")[0] if "/" in skill.path else "skill"
            if skill_name not in results["skills"]:
                results["skills"].append(skill_name)

        # 6. 分析 mcps
        mcps = [f for f in files if "mcp" in f.path.lower()]
        for mcp in mcps[:3]:
            mcp_name = mcp.path.split("/")[0] if "/" in mcp.path else "mcp"
            if mcp_name not in results["mcps"]:
                results["mcps"].append(mcp_name)

        # 7. 分析 hooks
        hooks = [f for f in files if "hook" in f.path.lower()]
        for hook in hooks[:3]:
            hook_name = hook.path.split("/")[0] if "/" in hook.path else "hooks"
            if hook_name not in results["hooks"]:
                results["hooks"].append(hook_name)

        print("[OK] Import complete!")
        print(f"  - Agent: {agent_name}")
        print(f"  - Skills: {len(results['skills'])}")
        print(f"  - MCPs: {len(results['mcps'])}")
        print(f"  - Hooks: {len(results['hooks'])}")

        return results

    def _create_agent_config(
        self,
        agent_name: str,
        repo: str,
        claude_md: str,
        agents_md: str,
        files: list[GitHubFile],
    ) -> dict[str, Any]:
        """创建 Agent 配置"""

        # 从 CLAUDE.md 提取 prompt
        system_prompt = ""
        if claude_md:
            # 简单提取：取前2000字符
            system_prompt = claude_md[:2000]

        # 从 AGENTS.md 提取 subagents
        sub_agents = []
        if agents_md:
            # 简单解析：查找 ### 或 ## 后的标题作为 agent 名
            import re

            agent_pattern = re.compile(r"^#{1,3}\s+(\w+)\s*[-:]?\s*(.*)$", re.MULTILINE)
            for match in agent_pattern.finditer(agents_md):
                name = match.group(1).lower()
                desc = match.group(2).strip()[:100]

                if len(sub_agents) < 6:  # 最多6个
                    sub_agents.append(
                        {
                            "name": name,
                            "type": "general",
                            "description": desc,
                            "model": "deepseek-chat",
                        }
                    )

        # 构建配置
        config = {
            "name": agent_name,
            "version": "1.0.0",
            "description": f"Imported from {repo}",
            "model": {
                "name": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "tools": ["read", "write", "edit", "bash", "glob", "grep"],
            "skills": [],
            "sub_agents": sub_agents,
            "permission": {"_global": "ask", "rules": []},
        }

        if system_prompt:
            config["system_prompt"] = system_prompt

        return config


def import_github(github_url: str, packages_dir: str = "packages") -> dict[str, Any]:
    """从 GitHub 导入 (CLI 入口)"""
    importer = GitHubImporter(packages_dir)
    return importer.import_from_url(github_url)
