"""
YoungAgent Initialization Methods

提取自 young_agent.py 的所有 _init_* 和 _create_* 方法。
包含：FlowSkill, TaskExecutor, Telemetry, Hooks, MCP, Checkpoint, Memory, SubAgents, Skills 初始化。
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

import yaml


def init_flow_skill(self, config) -> None:
    """初始化 FlowSkill - 执行流程编排

    支持多种方式加载 FlowSkill：
    1. 从 config.flow 指定
    2. 从导入的 agent 配置加载
    3. 从环境变量加载
    """
    # 1. 首先尝试从 config 加载
    flow_name = (
        getattr(config, "flow", {}).get("default", "development")
        if hasattr(config, "flow")
        else None
    )
    flow_config = getattr(config, "flow_skill", None)

    # 2. 尝试从导入的 agent 配置加载
    if not flow_name and hasattr(config, "flowskill") and config.flowskill:
        if isinstance(config.flowskill, dict):
            flow_name = config.flowskill.get("name", "development")
        elif isinstance(config.flowskill, str):
            flow_name = config.flowskill

    # 3. 默认使用 development
    if not flow_name:
        flow_name = "development"

    try:
        _load_flow_skill_by_name(self, flow_name, flow_config)
    except Exception as e:
        self._logger.warning(f"FlowSkill init failed: {e}")
        self._flow_skill = None


def _load_flow_skill_by_name(self, flow_name: str, flow_config: dict = None) -> None:
    """根据名称加载 FlowSkill"""
    if flow_name == "development":
        from src.flow.development import DevelopmentFlow

        project_root = flow_config.get("project_root", ".") if flow_config else "."
        self._flow_skill = DevelopmentFlow(project_root=project_root)
        print(f"[FlowSkill] Loaded: {flow_name}")
    elif flow_name == "sequential":
        from src.flow.sequential import SequentialFlow

        self._flow_skill = SequentialFlow()
        print(f"[FlowSkill] Loaded: {flow_name}")
    elif flow_name == "parallel":
        from src.flow.parallel import ParallelFlow

        self._flow_skill = ParallelFlow()
        print(f"[FlowSkill] Loaded: {flow_name}")
    elif flow_name == "conditional":
        from src.flow.conditional import ConditionalFlow

        self._flow_skill = ConditionalFlow()
        print(f"[FlowSkill] Loaded: {flow_name}")
    elif flow_name == "loop":
        from src.flow.loop import LoopFlow

        self._flow_skill = LoopFlow()
        print(f"[FlowSkill] Loaded: {flow_name}")
    else:
        from src.flow.development import DevelopmentFlow

        self._flow_skill = DevelopmentFlow(project_root=".")
        print("[FlowSkill] Loaded: development (default)")


def init_task_executor(self) -> None:
    """初始化 TaskExecutor"""
    from src.agents.task_executor import TaskExecutor

    self._task_executor = TaskExecutor(
        tool_executor=self._tool_executor,
        config=self.config,
        flow_skill=self._flow_skill,
        dispatcher=self._dispatcher,
        max_tool_calls=self._max_tool_calls,
    )
    self._task_executor.set_history(self._history)


def init_telemetry(self) -> None:
    """初始化 OpenTelemetry 遥测"""
    try:
        import os

        from src.telemetry import OPENTELEMETRY_AVAILABLE, init_telemetry

        # 检查是否启用遥测
        enabled = os.getenv("OPENYOUNG_TELEMETRY", "false").lower() == "true"

        if enabled and OPENTELEMETRY_AVAILABLE:
            service_name = f"openyoung-{self.config.name}"
            self._telemetry_enabled = init_telemetry(
                service_name=service_name, enable_console=False
            )
    except Exception:
        # 遥测初始化失败不影响主流程
        pass


def init_hooks(self) -> None:
    """初始化 Hooks - 加载已配置的 hooks"""
    try:
        from src.package_manager.hooks_loader import HooksLoader

        self._hooks_loader = HooksLoader(packages_dir="packages")
        discovered = self._hooks_loader.discover_hooks()

        # 加载所有 hooks
        all_hooks = []
        for name in discovered:
            hooks = self._hooks_loader.load_hooks(name)
            all_hooks.extend(hooks)

        self._hooks = all_hooks
        if self._hooks:
            print(f"[Hooks] Loaded {len(self._hooks)} hooks")
    except Exception as e:
        self._logger.warning(f"Hooks init failed: {e}")
        self._hooks = []


def init_mcp_servers(self) -> None:
    """初始化 MCP 服务器 - 自动发现已配置的 MCP"""
    try:
        from src.package_manager.mcp_manager import MCPServerManager

        self._mcp_manager = MCPServerManager(packages_dir="packages")
        servers = self._mcp_manager.discover_mcp_servers()

        if not servers:
            print("[MCP] No MCP servers found")
            return

        # 只打印发现的服务器，实际启动需要单独配置
        print(f"[MCP] Found {len(servers)} MCP servers: {', '.join(servers.keys())}")
        print("[MCP] Use 'openyoung mcp start <name>' to start a server")
    except Exception as e:
        self._logger.warning(f"MCP init failed: {e}")
        self._mcp_manager = None


def init_checkpoint(self) -> None:
    """初始化 CheckpointManager"""
    # Skip if checkpoint_manager was already injected
    if self._checkpoint_manager_injected and self._checkpoint_manager is not None:
        return

    try:
        from src.core.memory.impl.checkpoint import CheckpointManager

        checkpoint_dir = self._data_dir + "/checkpoints"
        self._checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
        print(f"[Checkpoint] Initialized at {checkpoint_dir}")
    except Exception as e:
        self._logger.warning(f"Checkpoint init failed: {e}")
        self._checkpoint_manager = None


def init_memory_facade(self) -> None:
    """初始化 MemoryFacade 分层记忆系统"""
    # Skip if memory_facade was already injected
    if self._memory_facade_injected and self._memory_facade is not None:
        return

    try:
        # 使用 Bridge 层创建记忆系统，支持自动降级
        from src.core.memory import get_memory_facade

        # 获取 event loop，如果不存在则创建
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # 尝试获取 MemoryFacade
        self._memory_facade = loop.run_until_complete(get_memory_facade())
        print("[MemoryFacade] Initialized (Layered Memory System)")
    except Exception as e:
        self._logger.warning(f"MemoryFacade init failed: {e}")
        self._memory_facade = None


def init_builtin_subagents(self) -> None:
    """初始化 SubAgents - 从配置加载，参考 Claude Code Task 协议"""
    from src.agents.sub_agent import SubAgent
    from src.core.types import SubAgentConfig, SubAgentType

    # 默认内置 SubAgents
    default_agents = [
        SubAgentConfig(
            name="explore",
            type=SubAgentType.EXPLORE,
            description="快速探索代码库，只读操作",
            model="deepseek-chat",
        ),
        SubAgentConfig(
            name="general",
            type=SubAgentType.GENERAL,
            description="通用任务处理",
            model="deepseek-chat",
        ),
        SubAgentConfig(
            name="search",
            type=SubAgentType.SEARCH,
            description="复杂搜索任务",
            model="deepseek-chat",
        ),
        SubAgentConfig(
            name="builder",
            type=SubAgentType.BUILDER,
            description="构建和执行任务",
            model="deepseek-coder",
        ),
        SubAgentConfig(
            name="reviewer",
            type=SubAgentType.REVIEWER,
            description="代码审查",
            model="deepseek-chat",
        ),
        SubAgentConfig(
            name="eval", type=SubAgentType.EVAL, description="评估任务", model="deepseek-chat"
        ),
    ]

    # 添加默认 SubAgents（传入 LLM 和工具执行器）
    for sc in default_agents:
        self._sub_agents[sc.name] = SubAgent(
            sc, llm_client=self._llm, tool_executor=self._tool_executor
        )

    # 从配置加载用户定义的 SubAgents（覆盖默认）
    if hasattr(self.config, "sub_agents") and self.config.sub_agents:
        for sc in self.config.sub_agents:
            self._sub_agents[sc.name] = SubAgent(
                sc, llm_client=self._llm, tool_executor=self._tool_executor
            )
            print(f"[SubAgent] Loaded: {sc.name} ({sc.type.value})")


def load_skills(self) -> None:
    """加载配置的 Skills - 参考 Anthropic SKILL.md 格式"""
    # 初始化
    packages_dir = Path(__file__).parent.parent.parent / "packages"
    src_skills_dir = Path(__file__).parent.parent / "skills"
    self._loaded_skills = {}

    # 1. 加载 always_skills (从 src/skills/ 目录)
    always_skills = getattr(self.config, "always_skills", []) or []
    for skill_name in always_skills:
        skill_path = src_skills_dir / skill_name / "skill.yaml"
        if skill_path.exists():
            with open(skill_path, encoding="utf-8") as f:
                skill_config = yaml.safe_load(f)

            skill_dir = skill_path.parent
            content_file = skill_dir / skill_config.get("entry", "SKILL.md")

            if content_file.exists():
                content = content_file.read_text(encoding="utf-8")
                self._loaded_skills[skill_name] = {
                    "config": skill_config,
                    "content": content,
                    "path": str(skill_dir),
                }
                print(f"[Skill] Loaded (always): {skill_name}")
            else:
                self._loaded_skills[skill_name] = {
                    "config": skill_config,
                    "content": "",
                    "path": str(skill_dir),
                }
                print(f"[Skill] Loaded (always, config only): {skill_name}")
        else:
            print(f"[Skill] Not found (always): {skill_name}")

    # 2. 加载配置的 skills (支持完整路径或名称)
    if not hasattr(self.config, "skills") or not self.config.skills:
        return

    for skill_ref in self.config.skills:
        # 支持两种格式:
        # 1. 完整路径: packages/deer-flow/original/skills/public/chart-visualization/SKILL.md
        # 2. skill名称: chart-visualization 或 skill-chart-visualization
        skill_name = None
        skill_path = None

        # 检查是否是完整路径
        skill_ref_str = str(skill_ref)
        if skill_ref_str.startswith("packages/") or skill_ref_str.startswith("./"):
            # 完整路径 - 直接作为 SKILL.md 路径
            full_path = Path(skill_ref_str)
            if full_path.exists():
                # 尝试读取 SKILL.md 或 skill.yaml
                if full_path.name == "SKILL.md" and full_path.parent.exists():
                    skill_dir = full_path.parent
                    skill_name = skill_dir.name
                    content = full_path.read_text(encoding="utf-8")
                    self._loaded_skills[skill_name] = {
                        "config": {"name": skill_name, "type": "markdown"},
                        "content": content,
                        "path": str(skill_dir),
                    }
                    print(f"[Skill] Loaded: {skill_name} (from path)")
                    continue
                elif full_path.is_dir() and (full_path / "SKILL.md").exists():
                    skill_dir = full_path
                    skill_name = skill_dir.name
                    content = (full_path / "SKILL.md").read_text(encoding="utf-8")
                    self._loaded_skills[skill_name] = {
                        "config": {"name": skill_name, "type": "markdown"},
                        "content": content,
                        "path": str(skill_dir),
                    }
                    print(f"[Skill] Loaded: {skill_name} (from dir)")
                    continue
            # 尝试作为 skill.yaml 路径
            yaml_path = Path(skill_ref_str)
            if yaml_path.name == "skill.yaml" and yaml_path.exists():
                skill_dir = yaml_path.parent
                skill_name = skill_dir.name
                with open(yaml_path, encoding="utf-8") as f:
                    skill_config = yaml.safe_load(f)
                entry = skill_config.get("entry", "SKILL.md")
                content_file = skill_dir / entry
                content = content_file.read_text(encoding="utf-8") if content_file.exists() else ""
                self._loaded_skills[skill_name] = {
                    "config": skill_config,
                    "content": content,
                    "path": str(skill_dir),
                }
                print(f"[Skill] Loaded: {skill_name} (from yaml)")
                continue

        # 否则作为 skill 名称处理
        skill_name = skill_ref_str
        skill_paths = [
            packages_dir / f"skill-{skill_name}",
            packages_dir / skill_name,
        ]

        for sp in skill_paths:
            if sp.exists() and (sp / "skill.yaml").exists():
                skill_path = sp / "skill.yaml"
                break

        if skill_path:
            with open(skill_path, encoding="utf-8") as f:
                skill_config = yaml.safe_load(f)

            # 加载 skill 内容
            skill_dir = skill_path.parent
            entry_file = skill_config.get("entry", "skill.md")
            content_file = skill_dir / entry_file

            if content_file.exists():
                content = content_file.read_text(encoding="utf-8")
                self._loaded_skills[skill_name] = {
                    "config": skill_config,
                    "content": content,
                    "path": str(skill_dir),
                }
                print(f"[Skill] Loaded: {skill_name}")
            else:
                # 只加载配置
                self._loaded_skills[skill_name] = {
                    "config": skill_config,
                    "content": "",
                    "path": str(skill_dir),
                }
                print(f"[Skill] Loaded (config only): {skill_name}")
        else:
            print(f"[Skill] Not found: {skill_name}")

    # 构建 system prompt
    _build_skill_prompt(self)


def _build_skill_prompt(self) -> None:
    """构建包含 skills 的 system prompt"""
    if not self._loaded_skills:
        return

    skill_instructions = []
    for name, data in self._loaded_skills.items():
        config = data["config"]
        content = data["content"]

        desc = config.get("description", "")
        entry = config.get("entry", "skill.md")

        instruction = f"\n## Skill: {name}\n"
        instruction += f"Description: {desc}\n"
        instruction += f"Entry: {entry}\n"

        if content:
            instruction += f"\n{content[:500]}..."

        skill_instructions.append(instruction)

    # 追加到 system prompt
    skills_section = "\n\n".join(skill_instructions)
    self.config.system_prompt += f"\n\n# Available Skills\n{skills_section}\n"
    print(f"[Skill] Built system prompt with {len(self._loaded_skills)} skills")


def init_default_genes(self) -> None:
    """初始化默认 genes"""
    try:
        from src.evolver.models import Gene, GeneCategory

        # 创建默认 gene
        gene = Gene(
            id=f"default_gene_{datetime.now().strftime('%Y%m%d')}",
            version="1.0.0",
            category=GeneCategory.REPAIR,
            signals=["success", "failure", "task_complete"],
            preconditions=[],
            strategy=["analyze_result", "improve_if_needed"],
            constraints={},
        )
        self._evolver._matcher.register_gene(gene)
    except Exception as e:
        self._logger.warning(f"Default genes init failed: {e}")


# --- Factory methods ---


def create_harness(self):
    """创建 Harness 实例"""
    try:
        from src.harness import Harness

        return Harness()
    except Exception as e:
        self._logger.warning(f"Harness init failed: {e}")
        return None


def create_datacenter(self):
    """创建 DataCenter 实例"""
    try:
        from src.datacenter.datacenter import DataCenter

        return DataCenter()
    except Exception as e:
        self._logger.warning(f"DataCenter init failed: {e}")
        return None


def create_evolver(self):
    """创建 EvolutionEngine 实例"""
    try:
        from src.evolver.engine import EvolutionEngine

        engine = EvolutionEngine()
        # 预加载基础 genes
        init_default_genes(self)
        return engine
    except Exception as e:
        self._logger.warning(f"EvolutionEngine init failed: {e}")
        return None
