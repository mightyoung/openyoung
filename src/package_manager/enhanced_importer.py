"""
GitHub Repository Importer (Enhanced)
增强版 GitHub 仓库导入器 - 支持 git clone + agent 分析
支持 GitHub、GitLab、Gitee 等多种 git 仓库
"""

import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

from .git_importer import GitImporterFactory
from .subagent_registry import SubAgentBinding


@dataclass
class GitHubFile:
    """GitHub 文件"""
    path: str
    content: str
    is_yaml: bool
    is_json: bool


@dataclass
class FlowSkill:
    """FlowSkill 配置 - Agent 执行流程"""
    name: str
    description: str
    trigger_conditions: list[str]
    required_skills: list[str]
    required_mcps: list[str]
    required_evaluations: list[str]
    subagent_calls: list[dict[str, Any]]


class EnhancedGitHubImporter:
    """增强版 GitHub 仓库导入器"""

    def __init__(self, packages_dir: str = "packages", subagents_dir: str = "subagents"):
        self.packages_dir = Path(packages_dir)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.subagents_dir = Path(subagents_dir)
        self.subagents_dir.mkdir(parents=True, exist_ok=True)

        self.temp_dir = Path("/tmp") / "openyoung_imports"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def import_from_url(self, url: str, agent_name: str = None,
                       use_git_clone: bool = True, analyze_with_agent: bool = True,
                       validate: bool = True, lazy_clone: bool = False) -> dict[str, Any]:
        """从 Git/GitLab/Gitee URL 导入

        Args:
            url: 仓库 URL (GitHub/GitLab/Gitee)
            agent_name: 可选的 Agent 名称
            use_git_clone: 是否使用 git clone (更完整)
            analyze_with_agent: 是否使用 agent 分析代码
            validate: 是否执行导入后验证
            lazy_clone: 是否延迟 clone（仅获取元数据，不完整克隆）

        Returns:
            导入结果
        """
        # 使用通用 Git 导入器工厂
        factory_result = GitImporterFactory.from_url(url)
        if not factory_result:
            return {"error": f"Unsupported repository URL: {url}"}

        importer, host, owner, repo = factory_result

        if not agent_name:
            agent_name = repo

        print(f"[{host.capitalize()}] Importing {owner}/{repo} as '{agent_name}'...")

        # Step 1: 获取仓库元数据（API 优先，快速）
        metadata = self._fetch_repo_metadata(host, owner, repo)
        if metadata:
            print(f"[{host.capitalize()}] Repository: {metadata.get('name', repo)} - {metadata.get('description', '')[:50]}...")

        # Step 2: 如果是 lazy_clone，仅返回元数据
        if lazy_clone:
            return {
                "agent_name": agent_name,
                "host": host,
                "owner": owner,
                "repo": repo,
                "metadata": metadata,
                "status": "lazy_mode",
                "message": "Use execute_imported_agent() to trigger full clone",
            }

        # Step 3: 获取仓库文件
        local_path = None
        # 保存到 packages 目录下的 agent 目录
        agent_repo_dir = self.packages_dir / agent_name / "original"
        agent_repo_dir.mkdir(parents=True, exist_ok=True)

        if use_git_clone:
            temp_path = importer.clone(owner, repo)
            if not temp_path:
                return {"error": "Failed to clone repository"}
            # 复制到 packages 目录
            import shutil
            for item in temp_path.iterdir():
                dest = agent_repo_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            local_path = agent_repo_dir
            print(f"[{host.capitalize()}] Cloned to: {local_path}")
        else:
            # API 方式需要子类实现
            local_path = self._fetch_repo_files(host, owner, repo)
            if not local_path:
                return {"error": "Failed to fetch repository files"}

        # Step 4: 分析项目结构
        project_structure = self._analyze_project_structure(local_path)
        print(f"[{host.capitalize()}] Project structure: {project_structure}")

        # Step 5: 生成 FlowSkill (如果启用 agent 分析)
        flowskill = None
        if analyze_with_agent:
            flowskill = self._generate_flowskill(local_path, project_structure)
            if flowskill:
                print(f"[{host.capitalize()}] Generated FlowSkill: {flowskill.name}")

        # Step 6: 解析配置文件
        config_result = self._parse_configs(local_path)

        # Step 7: 创建 Agent 配置
        result = self._create_agent_config(
            host, owner, repo, agent_name, project_structure, flowskill, config_result
        )

        # Step 8: 导入验证
        if validate:
            validation_result = self._validate_import(agent_name, project_structure, config_result)
            result["validation"] = validation_result

        # 保存 local_path 供后续使用
        result["local_path"] = local_path
        result["host"] = host
        result["owner"] = owner
        result["repo"] = repo

        return result

    def _fetch_repo_metadata(self, host: str, owner: str, repo: str) -> dict[str, Any] | None:
        """通过 API 获取仓库元数据（快速）"""

        try:
            if host == "github.com":
                url = f"https://api.github.com/repos/{owner}/{repo}"
                headers = {}
                token = os.getenv("GITHUB_TOKEN")
                if token:
                    headers["Authorization"] = f"token {token}"
                response = httpx.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": data.get("name"),
                        "description": data.get("description"),
                        "stars": data.get("stargazers_count", 0),
                        "language": data.get("language"),
                        "default_branch": data.get("default_branch"),
                        "url": data.get("html_url"),
                    }
            elif host == "gitlab.com":
                import urllib.parse
                encoded = urllib.parse.quote(f"{owner}/{repo}")
                url = f"https://gitlab.com/api/v4/projects/{encoded}"
                response = httpx.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": data.get("name"),
                        "description": data.get("description"),
                        "stars": data.get("star_count", 0),
                        "language": data.get("language"),
                        "default_branch": data.get("default_branch"),
                        "url": data.get("web_url"),
                    }
            elif host == "gitee.com":
                url = f"https://gitee.com/api/v5/repos/{owner}/{repo}"
                response = httpx.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "name": data.get("name"),
                        "description": data.get("description"),
                        "stars": data.get("stargazers_count", 0),
                        "language": data.get("language"),
                        "default_branch": data.get("default_branch"),
                        "url": data.get("html_url"),
                    }
        except Exception as e:
            print(f"[Metadata] Failed to fetch: {e}")
        return None

    async def execute_imported_agent(self, agent_name: str, task: str) -> str:
        """执行导入的 agent

        Args:
            agent_name: Agent 名称
            task: 任务描述

        Returns:
            执行结果
        """
        from src.agents.young_agent import YoungAgent
        from src.core.types import AgentConfig, AgentMode
        from src.package_manager.agent_loader import AgentLoader

        print(f"[Execute] Running agent '{agent_name}' with task: {task[:50]}...")

        # 1. 加载 agent 配置
        loader = AgentLoader()
        try:
            config = loader.load_agent(agent_name)
        except Exception:
            # 如果没有配置，创建默认配置
            config = AgentConfig(
                name=agent_name,
                mode=AgentMode.PRIMARY,
            )

        # 2. 创建 YoungAgent 实例
        agent = YoungAgent(config)

        # 3. 执行任务
        result = await agent.run(task)

        # 4. 返回结果
        return result

    def _git_clone(self, owner: str, repo: str) -> Path | None:
        """Git clone 仓库到本地"""
        import subprocess

        repo_url = f"https://github.com/{owner}/{repo}.git"
        local_path = self.temp_dir / f"{owner}_{repo}"

        # 如果已存在，先删除
        if local_path.exists():
            shutil.rmtree(local_path)

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                print(f"[GitHub] Cloned to {local_path}")
                return local_path
            else:
                print(f"[Error] Git clone failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"[Error] Git clone error: {e}")
            return None

    def _parse_github_url(self, url: str) -> tuple:
        """解析 GitHub URL"""
        url = url.strip().rstrip("/")

        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None

    def _fetch_repo_files(self, host: str, owner: str, repo: str) -> Path | None:
        """通过 API 获取仓库 (备用方案)"""
        # 简化的 API 获取实现
        return None

    def _validate_import(self, agent_name: str, structure: dict[str, Any],
                       config_result: dict[str, Any]) -> dict[str, Any]:
        """验证导入结果 - 质量门禁"""

        validation = {
            "passed": True,
            "score": 1.0,
            "warnings": [],
            "errors": [],
        }

        # 检查项目结构 - 每个缺失扣 0.2
        if not structure.get("languages"):
            validation["warnings"].append("No programming languages detected")
            validation["score"] -= 0.2

        if not structure.get("has_claude_md"):
            validation["warnings"].append("No CLAUDE.md found - agent behavior may not be optimal")
            validation["score"] -= 0.2

        # 检查是否有 SubAgents (从任何来源)
        subagents = structure.get("subagent_prompts", [])
        if not subagents:
            validation["warnings"].append("No sub-agents found from roles/, agents/, or AGENTS.md")
            validation["score"] -= 0.1

        # 检查配置文件 - 缺失扣 0.15
        if not config_result.get("skills") and not config_result.get("mcps"):
            validation["warnings"].append("No skills or MCPs configured")
            validation["score"] -= 0.15

        # 确保分数不低于 0
        validation["score"] = max(0, validation["score"])

        # 质量阈值判断
        if validation["score"] < 0.6:
            validation["passed"] = False
            validation["errors"].append(f"Quality score {validation['score']:.2f} below threshold 0.6")

        # 添加质量报告
        validation["report"] = {
            "languages": structure.get("languages", []),
            "has_claude_md": structure.get("has_claude_md", False),
            "has_agents_md": structure.get("has_agents_md", False),
            "skills_count": len(config_result.get("skills", [])),
            "mcps_count": len(config_result.get("mcps", [])),
        }

        return validation

    def _analyze_project_structure(self, local_path: Path) -> dict[str, Any]:
        """分析项目结构"""
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

        # 扫描文件
        for item in local_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(local_path)
                structure["files"].append(str(rel_path))

                # 检测关键文件
                name = item.name.lower()
                if name == "claude.md":
                    structure["has_claude_md"] = True
                    structure["main_prompt"] = item.read_text(encoding="utf-8", errors="ignore")[:5000]
                elif name == "agents.md":
                    structure["has_agents_md"] = True
                elif "skill" in str(rel_path):
                    structure["has_skills"] = True
                    if item.suffix in [".yaml", ".yml", ".json"]:
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

        # 检测语言
        ext_counts = {}
        for item in local_path.rglob("*"):
            if item.is_file() and item.name != ".git":
                ext = item.suffix
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1

        structure["languages"] = sorted(ext_counts.keys(), key=lambda x: ext_counts[x], reverse=True)[:5]

        # 发现 SubAgents - 从多个来源
        structure["subagent_prompts"] = self._discover_all_subagents(local_path)

        return structure

    def _parse_agents_md(self, path: Path) -> list[dict[str, str]]:
        """解析 AGENTS.md 文件"""
        subagents = []
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")

            # 简单解析: ### Agent Name 或 ## Agent Name
            pattern = re.compile(r"^#{2,3}\s+(\w+)\s*[-:]?\s*(.*)$", re.MULTILINE)
            for match in pattern.finditer(content):
                name = match.group(1).strip()
                desc = match.group(2).strip()[:200]
                subagents.append({"name": name, "description": desc, "source": "agents.md"})
        except Exception as e:
            print(f"[Warning] Failed to parse AGENTS.md: {e}")

        return subagents

    def _discover_subagents_from_roles(self, local_path: Path) -> list[dict[str, str]]:
        """从 roles/ 目录发现 SubAgents

        适用于 MetaGPT 等使用 roles/ 目录定义 Agent 的项目
        支持直接路径和子目录中的 roles/ (如 metagpt/roles/)
        """
        subagents = []

        # 查找所有 roles 目录
        roles_dirs = []
        for item in local_path.rglob("roles"):
            if item.is_dir():
                roles_dirs.append(item)
                print(f"[Debug] Found roles dir: {item}")

        for roles_dir in roles_dirs:
            # 遍历 roles 目录
            for role_file in roles_dir.glob("*.py"):
                if role_file.name.startswith("_") or role_file.name == "__init__.py":
                    continue

                try:
                    content = role_file.read_text(encoding="utf-8", errors="ignore")

                    # 提取类名作为 Agent 名称
                    # 支持两种格式: class EngineerRole 和 class Engineer(Role)
                    class_pattern = re.compile(r"^class\s+(\w+)(?:Role)?\s*\(.*Role", re.MULTILINE)
                    for match in class_pattern.finditer(content):
                        name = match.group(1).lower()
                        # 尝试从类的文档字符串获取描述
                        desc = self._extract_role_description(content, match.start())[:200]
                        subagents.append({
                            "name": name,
                            "description": desc or f"Role from {role_file.name}",
                            "source": "roles/",
                            "file": str(role_file.relative_to(local_path))
                        })
                except Exception as e:
                    print(f"[Warning] Failed to parse role file {role_file}: {e}")

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from roles/ directory")

        return subagents

    def _extract_role_description(self, content: str, class_start: int) -> str:
        """从角色文件提取描述"""
        # 查找类后面的文档字符串
        doc_pattern = re.compile(r'"""(.*?)"""', re.DOTALL)
        for match in doc_pattern.finditer(content[class_start:class_start+500]):
            desc = match.group(1).strip().split("\n")[0]
            if len(desc) > 10:
                return desc
        return ""

    def _discover_subagents_from_subagents_dir(self, local_path: Path) -> list[dict[str, str]]:
        """从 subagents/ 或 agents/ 目录发现 SubAgents"""
        subagents = []

        # 尝试多个可能的目录名
        for dir_name in ["subagents", "agents", "agent"]:
            subagents_dir = local_path / dir_name
            if not subagents_dir.exists():
                continue

            # 遍历子目录
            for agent_dir in subagents_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                # 查找 agent.yaml 或类似配置文件
                for config_file in agent_dir.glob("*.yaml"):
                    try:
                        import yaml
                        config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

                        name = config.get("name", agent_dir.name)
                        desc = config.get("description", f"Agent from {dir_name}/")
                        subagents.append({
                            "name": name,
                            "description": desc[:200],
                            "source": f"{dir_name}/",
                            "file": str(config_file.relative_to(local_path))
                        })
                    except Exception as e:
                        print(f"[Warning] Failed to parse {config_file}: {e}")

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from agents directory")

        return subagents

    def _discover_subagents_from_config(self, local_path: Path) -> list[dict[str, str]]:
        """从配置文件发现 SubAgents (agents.yaml, config.yaml 等)"""
        subagents = []

        # 查找配置文件
        for config_file in local_path.rglob("agents.yaml"):
            try:
                import yaml
                config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

                agents_list = config.get("agents", []) or config.get("sub_agents", [])
                for agent in agents_list:
                    subagents.append({
                        "name": agent.get("name", "unknown"),
                        "description": agent.get("description", "")[:200],
                        "source": "agents.yaml",
                        "file": str(config_file.relative_to(local_path))
                    })
            except Exception as e:
                print(f"[Warning] Failed to parse {config_file}: {e}")

        # 查找 config 目录下的多 agent 配置
        config_dir = local_path / "config"
        if config_dir.exists():
            for config_file in config_dir.glob("*.yaml"):
                try:
                    content = config_file.read_text(encoding="utf-8", errors="ignore")
                    # 查找 "role" 或 "agent" 相关的配置段
                    if "role:" in content.lower() or "agent:" in content.lower():
                        import yaml
                        config = yaml.safe_load(content)
                        # 简单提取角色名
                        if isinstance(config, dict):
                            for key, value in config.items():
                                if isinstance(value, dict) and ("role" in str(key).lower() or "agent" in str(key).lower()):
                                    subagents.append({
                                        "name": key,
                                        "description": f"From {config_file.name}",
                                        "source": "config/",
                                        "file": str(config_file.relative_to(local_path))
                                    })
                except Exception:
                    pass

        if subagents:
            print(f"[SubAgent] Discovered {len(subagents)} from config files")

        return subagents

    def _discover_all_subagents(self, local_path: Path) -> list[dict[str, str]]:
        """综合发现 SubAgents - 从多个来源"""
        all_subagents = []
        seen_names = set()

        # 1. 从 AGENTS.md
        for sa in self._parse_all_agents_md_files(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        # 2. 从 roles/ 目录
        for sa in self._discover_subagents_from_roles(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        # 3. 从 subagents/ 或 agents/ 目录
        for sa in self._discover_subagents_from_subagents_dir(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        # 4. 从配置文件
        for sa in self._discover_subagents_from_config(local_path):
            if sa["name"] not in seen_names:
                all_subagents.append(sa)
                seen_names.add(sa["name"])

        if all_subagents:
            print(f"[SubAgent] Total discovered: {len(all_subagents)} SubAgents")

        return all_subagents

    def _parse_all_agents_md_files(self, local_path: Path) -> list[dict[str, str]]:
        """递归查找并解析所有 AGENTS.md 文件"""
        subagents = []

        # 支持多种文件名
        for filename in ["AGENTS.md", "agents.md", "SUBAGENTS.md", "ROLES.md"]:
            for md_file in local_path.rglob(filename):
                try:
                    content = md_file.read_text(encoding="utf-8", errors="ignore")

                    # 解析标题和描述
                    pattern = re.compile(r"^#{2,3}\s+(\w+)\s*[-:]?\s*(.*)$", re.MULTILINE)
                    for match in pattern.finditer(content):
                        name = match.group(1).strip()
                        desc = match.group(2).strip()[:200]
                        subagents.append({
                            "name": name,
                            "description": desc,
                            "source": filename,
                            "file": str(md_file.relative_to(local_path))
                        })
                except Exception as e:
                    print(f"[Warning] Failed to parse {md_file}: {e}")

        return subagents

    def _generate_flowskill(self, local_path: Path, structure: dict[str, Any]) -> FlowSkill | None:
        """生成 FlowSkill - 分析代码执行流程"""
        # 读取关键文件进行分析
        key_files = []
        for pattern in ["*.py", "*.js", "*.ts", "*.sh", "Makefile", "package.json"]:
            key_files.extend(local_path.glob(pattern))

        code_context = ""
        for f in list(key_files)[:10]:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")[:2000]
                code_context += f"\n# {f.name}\n{content}\n"
            except:
                pass

        # 解析 CLAUDE.md 获取执行流程
        main_prompt = structure.get("main_prompt", "")

        # 生成 FlowSkill 配置
        flowskill = FlowSkill(
            name=f"flow-{structure.get('languages', ['unknown'])[0] if structure.get('languages') else 'default'}",
            description=self._extract_flow_description(main_prompt),
            trigger_conditions=self._extract_triggers(main_prompt),
            required_skills=structure.get("skills", []),
            required_mcps=structure.get("mcps", []),
            required_evaluations=structure.get("evaluations", []),
            subagent_calls=self._extract_subagent_calls(structure.get("subagent_prompts", [])),
        )

        return flowskill

    def _extract_flow_description(self, prompt: str) -> str:
        """从提示词提取流程描述"""
        # 简单提取: 查找 "Steps", "Process", "Flow" 等关键词
        lines = prompt.split("\n")
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ["step", "process", "flow", "workflow"]):
                return " -> ".join(lines[i:i+3]).strip()[:200]
        return "Default agent execution flow"

    def _extract_triggers(self, prompt: str) -> list[str]:
        """提取触发条件"""
        triggers = []
        keywords = ["when", "if", "trigger", "on"]

        for line in prompt.split("\n"):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords) and len(line) < 100:
                triggers.append(line.strip()[:100])

        return triggers[:5]

    def _extract_subagent_calls(self, subagent_prompts: list[dict]) -> list[dict[str, Any]]:
        """提取子代理调用"""
        calls = []
        for sa in subagent_prompts[:6]:
            calls.append({
                "name": sa.get("name", "unknown"),
                "condition": f"task matches '{sa.get('description', '')}'",
                "type": "general",
            })
        return calls

    def _parse_configs(self, local_path: Path) -> dict[str, Any]:
        """解析配置文件"""
        configs = {
            "skills": [],
            "mcps": [],
            "hooks": [],
            "evaluations": [],
        }

        if not local_path:
            return configs

        # 解析 skills
        for item in local_path.rglob("skill*.yaml"):
            try:
                config = yaml.safe_load(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["skills"].append({"path": str(item), "config": config})
            except:
                pass

        # 解析 mcp.json
        for item in local_path.rglob("mcp.json"):
            try:
                config = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["mcps"].append({"path": str(item), "config": config})
            except:
                pass

        # 解析 hooks
        for item in local_path.rglob("hooks*.json"):
            try:
                config = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["hooks"].append({"path": str(item), "config": config})
            except:
                pass

        # 解析 evaluation
        for item in local_path.rglob("*eval*.yaml"):
            try:
                config = yaml.safe_load(item.read_text(encoding="utf-8", errors="ignore"))
                if config:
                    configs["evaluations"].append({"path": str(item), "config": config})
            except:
                pass

        return configs

    def _create_agent_config(
        self,
        host: str,
        owner: str,
        repo: str,
        agent_name: str,
        structure: dict[str, Any],
        flowskill: FlowSkill | None,
        config_result: dict[str, Any],
    ) -> dict[str, Any]:
        """创建 Agent 配置"""
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

        # 创建 Agent 目录
        agent_dir = self.packages_dir / agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # 构建 Agent 配置
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

        # 添加 FlowSkill
        if flowskill:
            agent_config["flowskill"] = {
                "name": flowskill.name,
                "description": flowskill.description,
                "trigger_conditions": flowskill.trigger_conditions,
                "required_skills": flowskill.required_skills,
                "required_mcps": flowskill.required_mcps,
                "required_evaluations": flowskill.required_evaluations,
                "subagent_calls": flowskill.subagent_calls,
            }
            results["flowskill"] = flowskill.name

        # 添加 system_prompt
        if structure.get("main_prompt"):
            agent_config["system_prompt"] = structure["main_prompt"][:4000]

        # 解析并添加 SubAgents
        for sa_prompt in structure.get("subagent_prompts", []):
            subagent = SubAgentBinding(
                name=sa_prompt.get("name", "unknown"),
                type="general",
                description=sa_prompt.get("description", ""),
            )
            results["subagents"].append(asdict(subagent))

            # 保存 SubAgent 到库
            self.subagents_dir.mkdir(parents=True, exist_ok=True)
            subagent_dir = self.subagents_dir / subagent.name
            subagent_dir.mkdir(parents=True, exist_ok=True)
            with open(subagent_dir / "agent.yaml", "w", encoding="utf-8") as f:
                yaml.dump(asdict(subagent), f, allow_unicode=True, default_flow_style=False)

        agent_config["sub_agents"] = [
            {"name": sa["name"], "type": sa.get("type", "general"), "description": sa.get("description", "")}
            for sa in results["subagents"]
        ]

        # 添加配置引用
        agent_config["skills"] = [s["path"] for s in config_result.get("skills", [])]
        agent_config["mcps"] = [m["path"] for m in config_result.get("mcps", [])]
        results["skills"] = [s["path"] for s in config_result.get("skills", [])]
        results["mcps"] = [m["path"] for m in config_result.get("mcps", [])]
        results["hooks"] = [h["path"] for h in config_result.get("hooks", [])]
        results["evaluations"] = [e["path"] for e in config_result.get("evaluations", [])]

        # 保存 Agent 配置
        agent_yaml_path = agent_dir / "agent.yaml"
        with open(agent_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(agent_config, f, allow_unicode=True, default_flow_style=False)

        results["agent"] = str(agent_yaml_path)

        # 保存原始配置
        if structure.get("main_prompt"):
            config_dir = agent_dir / "original"
            config_dir.mkdir(exist_ok=True)
            with open(config_dir / "CLAUDE.md", "w", encoding="utf-8") as f:
                f.write(structure["main_prompt"])
            results["config"]["CLAUDE.md"] = str(config_dir / "CLAUDE.md")

        print("[OK] Import complete!")
        print(f"  - Agent: {agent_name}")
        print(f"  - Skills: {len(results['skills'])}")
        print(f"  - MCPs: {len(results['mcps'])}")
        print(f"  - Hooks: {len(results['hooks'])}")
        print(f"  - SubAgents: {len(results['subagents'])}")
        if flowskill:
            print(f"  - FlowSkill: {flowskill.name}")

        return results


def import_github_enhanced(github_url: str, packages_dir: str = "packages",
                           subagents_dir: str = "subagents",
                           use_git_clone: bool = True,
                           analyze_with_agent: bool = True) -> dict[str, Any]:
    """从 GitHub 导入 (增强版 CLI 入口)"""
    importer = EnhancedGitHubImporter(packages_dir, subagents_dir)
    return importer.import_from_url(github_url, use_git_clone=use_git_clone,
                                    analyze_with_agent=analyze_with_agent)


# 兼容旧接口
from dataclasses import asdict
