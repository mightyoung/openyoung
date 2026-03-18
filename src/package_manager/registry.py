"""
AgentRegistry - 轻量级 Agent 注册中心
基于文件夹 + YAML 配置，使用 pip 管理依赖
"""

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from .base_registry import BaseRegistry


@dataclass
class AgentSpec:
    """Agent 规格定义"""

    name: str
    version: str = "1.0.0"
    description: str = ""
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[str] = None
    skills: list[str] = None
    package_path: str = ""  # 相对路径

    def __post_init__(self):
        if self.tools is None:
            self.tools = ["read", "write", "edit", "bash", "glob", "grep"]
        if self.skills is None:
            self.skills = []


class AgentRegistry(BaseRegistry):
    """
    轻量级 Agent 注册中心

    目录结构:
    packages/
    ├── agent-coder/
    │   ├── pyproject.toml      # pip 依赖
    │   ├── agent.yaml          # Agent 配置
    │   └── src/
    └── agent-reviewer/
        ├── pyproject.toml
        ├── agent.yaml
        └── src/
    """

    DEFAULT_PACKAGES_DIR = "packages"

    def __init__(self, packages_dir: str | None = None):
        packages_dir = packages_dir or "packages"
        super().__init__(packages_dir)
        self.packages_dir = self.base_dir
        self._cache: dict[str, AgentSpec] = {}

    # ========== 扫描与发现 ==========

    def discover_agents(self) -> list[AgentSpec]:
        """扫描并发现所有 Agent"""
        agents = []

        if not self.packages_dir.exists():
            return agents

        for item in self.packages_dir.iterdir():
            if item.is_dir():
                agent = self._load_agent_from_dir(item)
                if agent:
                    agents.append(agent)
                    self._cache[agent.name] = agent

        return agents

    def _load_agent_from_dir(self, dir_path: Path) -> AgentSpec | None:
        """从目录加载 Agent 配置"""
        agent_yaml = dir_path / "agent.yaml"

        if not agent_yaml.exists():
            return None

        try:
            with open(agent_yaml, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            return AgentSpec(
                name=config.get("name", dir_path.name),
                version=config.get("version", "1.0.0"),
                description=config.get("description", ""),
                model=config.get("model", {}).get("name", "deepseek-chat"),
                temperature=config.get("model", {}).get("temperature", 0.7),
                max_tokens=config.get("model", {}).get("max_tokens", 4096),
                tools=config.get("tools", ["read", "write", "edit", "bash", "glob", "grep"]),
                skills=config.get("skills", []),
                package_path=str(dir_path.relative_to(self.packages_dir)),
            )
        except Exception as e:
            print(f"[Warning] Failed to load {agent_yaml}: {e}")
            return None

    def get_agent(self, name: str) -> AgentSpec | None:
        """获取指定 Agent"""
        if name in self._cache:
            return self._cache[name]

        # 重新扫描
        self.discover_agents()
        return self._cache.get(name)

    def list_agents(self) -> list[str]:
        """列出所有可用 Agent"""
        agents = self.discover_agents()
        return [a.name for a in agents]

    # ========== 向量索引 ==========

    def index_agent(self, agent_name: str) -> bool:
        """索引 Agent 到向量存储

        Args:
            agent_name: Agent 名称

        Returns:
            bool: 索引是否成功
        """
        agent = self.get_agent(agent_name)
        if not agent:
            return False

        try:
            # 构建索引文本
            text = self._build_index_text(agent)

            # 获取向量存储（使用默认路径）
            from src.core.memory.impl.vector_store import VectorStore

            vs = VectorStore()  # 使用默认 db_path

            # 添加到向量存储
            vs.add(content=text, namespace="agents", tags=[agent_name], importance=0.8)
            print(f"[AgentRegistry] Indexed: {agent_name}")
            return True
        except Exception as e:
            print(f"[AgentRegistry] Index error: {e}")
            return False

    def index_all_agents(self) -> int:
        """索引所有 Agent

        Returns:
            int: 成功索引的数量
        """
        agents = self.discover_agents()
        count = 0
        for agent in agents:
            if self.index_agent(agent.name):
                count += 1
        return count

    def _build_index_text(self, agent: AgentSpec) -> str:
        """构建索引文本"""
        parts = [
            f"Agent: {agent.name}",
            f"Version: {agent.version}",
            f"Description: {agent.description}",
            f"Model: {agent.model}",
            f"Tools: {', '.join(agent.tools or [])}",
            f"Skills: {', '.join(agent.skills or [])}",
        ]
        return " | ".join(parts)

    def get_agent_dict(self, name: str) -> dict[str, Any] | None:
        """获取 Agent 字典格式（包含所有字段）"""
        agent = self.get_agent(name)
        if not agent:
            return None
        return asdict(agent)

    # ========== 使用追踪 ==========

    def track_usage(self, agent_name: str) -> bool:
        """追踪 agent 使用

        Args:
            agent_name: Agent 名称

        Returns:
            bool: 是否成功记录
        """
        import sqlite3
        from datetime import datetime

        try:
            db_path = Path.home() / ".openyoung" / "agent_usage.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_usage (
                    agent_name TEXT PRIMARY KEY,
                    use_count INTEGER DEFAULT 1,
                    last_used TEXT,
                    created_at TEXT
                )
            """)

            # 更新使用记录
            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO agent_usage (agent_name, use_count, last_used, created_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(agent_name) DO UPDATE SET
                    use_count = use_count + 1,
                    last_used = ?
            """,
                (agent_name, now, now, now),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[AgentRegistry] Track usage error: {e}")
            return False

    def get_usage_stats(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取使用统计

        Args:
            limit: 返回数量

        Returns:
            List[Dict]: 使用统计列表
        """
        import sqlite3

        try:
            db_path = Path.home() / ".openyoung" / "agent_usage.db"
            if not db_path.exists():
                return []

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT agent_name, use_count, last_used
                FROM agent_usage
                ORDER BY use_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append({"agent_name": row[0], "use_count": row[1], "last_used": row[2]})

            conn.close()
            return results
        except Exception as e:
            print(f"[AgentRegistry] Get usage stats error: {e}")
            return []

    # ========== pip 集成 ==========

    def install_agent(self, name: str, version: str | None = None) -> bool:
        """安装 Agent 依赖 (使用 pip)"""
        agent = self.get_agent(name)
        if not agent:
            print(f"[Error] Agent not found: {name}")
            return False

        package_dir = self.packages_dir / agent.package_path
        pyproject = package_dir / "pyproject.toml"

        if not pyproject.exists():
            print(f"[Info] No pyproject.toml for {name}, skipping pip install")
            return True

        try:
            cmd = ["pip", "install", "-e", str(package_dir)]
            if version:
                cmd.append(f"=={version}")

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] Installed {name}")
                return True
            else:
                print(f"[Error] Install failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"[Error] Install failed: {e}")
            return False

    def install_all(self) -> dict[str, bool]:
        """安装所有 Agent 依赖"""
        results = {}
        agents = self.discover_agents()

        for agent in agents:
            results[agent.name] = self.install_agent(agent.name)

        return results

    # ========== 模板生成 ==========

    def create_agent_template(self, name: str, template: str = "default") -> Path:
        """创建 Agent 模板"""
        agent_dir = self.packages_dir / f"agent-{name}"
        agent_dir.mkdir(parents=True, exist_ok=True)

        # agent.yaml
        agent_yaml = agent_dir / "agent.yaml"
        template_content = self._get_template(template)
        agent_yaml.write_text(template_content.format(name=name), encoding="utf-8")

        # pyproject.toml
        pyproject = agent_dir / "pyproject.toml"
        pyproject.write_text(
            f"""[project]
name = "agent-{name}"
version = "0.1.0"
description = "Agent: {name}"
requires-python = ">=3.10"
dependencies = [
]
""",
            encoding="utf-8",
        )

        print(f"[OK] Created agent template: {agent_dir}")
        return agent_dir

    def _get_template(self, template: str) -> str:
        """获取模板内容"""
        templates = {
            "default": """name: "{name}"
version: "0.1.0"
description: "Agent: {name}"

model:
  name: "deepseek-chat"
  temperature: 0.7
  max_tokens: 4096

tools:
  - read
  - write
  - edit
  - bash
  - glob
  - grep

skills: []

permission:
  _global: ask
  rules: []
""",
            "coder": """name: "{name}"
version: "0.1.0"
description: "Coder Agent: {name}"

model:
  name: "deepseek-coder"
  temperature: 0.3
  max_tokens: 8192

tools:
  - read
  - write
  - edit
  - bash
  - glob
  - grep

skills:
  - coding-standards
  - tdd-london-swarm

permission:
  _global: ask
  rules: []
""",
            "reviewer": """name: "{name}"
version: "0.1.0"
description: "Reviewer Agent: {name}"

model:
  name: "deepseek-chat"
  temperature: 0.5
  max_tokens: 4096

tools:
  - read
  - glob
  - grep

skills:
  - code-review

permission:
  _global: ask
  rules: []
""",
        }
        return templates.get(template, templates["default"])

    # ========== 导出 ==========

    def export_registry(self) -> dict[str, Any]:
        """导出注册表 JSON"""
        agents = self.discover_agents()
        return {
            "version": "1.0.0",
            "packages_dir": str(self.packages_dir),
            "agents": [asdict(a) for a in agents],
        }

    def save_registry(self, path: str | None = None):
        """保存注册表到文件"""
        path = Path(path) if path else self.packages_dir / "registry.json"
        registry = self.export_registry()
        path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Saved registry to {path}")
