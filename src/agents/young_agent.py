"""
YoungAgent - Main Agent Class with full system integration
"""

import json
import uuid
from datetime import datetime
from typing import Any

from src.agents.components import (
    DEFAULT_WEIGHTS,
    DIMENSION_THRESHOLDS,
    TASK_TYPE_WEIGHTS,
    calculate_weighted_score,
    check_threshold_violations,
)
from src.agents.dispatcher import TaskDispatcher
from src.agents.evaluation_coordinator import EvaluationContext, EvaluationCoordinator
from src.agents.permission import PermissionEvaluator
from src.agents.ralph_loop import AgentCategory, RalphLoop, RalphLoopConfig
from src.agents.sub_agent import SubAgent
from src.core.types import (
    Message,
    MessageRole,
    SubAgentConfig,
    Task,
)
from src.evaluation.planner import EvalPlanner
from src.package_manager.manager import PackageManager

# AI Docker - Runtime
from src.runtime import AISandbox, PoolConfig, SandboxConfig, SandboxPool
from src.tools.executor import ToolExecutor


def validate_file_creation(task_description: str, agent_result: str) -> dict:
    """验证文件是否真实创建

    从任务描述中提取可能的文件路径，然后检查这些路径是否存在。
    如果任务描述中提到保存到文件，但文件未创建，则返回失败。

    Args:
        task_description: 任务描述
        agent_result: Agent 的执行结果

    Returns:
        验证结果: {"verified": bool, "files_found": list, "files_expected": list, "message": str}
    """
    import os
    import re
    from pathlib import Path

    # 从任务描述中提取可能的文件路径
    expected_files = []

    # 模式1: "保存到 xxx/yyy.py"
    patterns = [
        r"保存[到]?\s*([^\s]+\.py)",
        r"保存[到]?\s*([^\s]+\.json)",
        r"保存[到]?\s*([^\s]+\.txt)",
        r"save.*?to\s+([^\s]+\.py)",
        r"save.*?to\s+([^\s]+\.json)",
        r"保存[到]?\s*([^\s]+)",
        r"output/([^\s]+)",
        r"创建.*?([^\s]+\.py)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, task_description)
        expected_files.extend(matches)

    # 清理路径
    expected_files = [f.strip() for f in expected_files if f.strip()]

    # 检查文件是否存在
    found_files = []
    # 支持多种路径：相对路径、output/、绝对路径、/tmp/、~/
    base_dirs = [
        "",  # 当前目录
        "output/",  # output 目录
        "./output/",  # ./output 目录
        "/Users/muyi/Downloads/dev/openyoung/output/",  # 绝对路径
        "/tmp/",  # 临时目录
        os.path.expanduser("~/"),  # 家目录
    ]

    for file_path in expected_files:
        # 1. 先检查绝对路径（如果以 / 或 ~ 开头）
        if file_path.startswith("/"):
            if os.path.exists(file_path):
                found_files.append(file_path)
                continue
        elif file_path.startswith("~"):
            expanded = os.path.expanduser(file_path)
            if os.path.exists(expanded):
                found_files.append(expanded)
                continue

        # 2. 尝试不同的基准目录
        for base_dir in base_dirs:
            full_path = os.path.join(base_dir, file_path)
            if os.path.exists(full_path):
                found_files.append(full_path)
                break
            # 也检查不带扩展名的版本
            if not os.path.splitext(file_path)[1]:
                for ext in [".py", ".json", ".txt", ".md"]:
                    if os.path.exists(full_path + ext):
                        found_files.append(full_path + ext)
                        break

    # 如果没有找到任何预期的文件，检查 output 或 /tmp 目录中是否有任何新文件
    if not found_files:
        search_dirs = []
        if "output" in task_description.lower():
            search_dirs.append(Path("output"))
        # 也检查 /tmp 目录
        tmp_dir = Path("/tmp")
        if tmp_dir.exists():
            search_dirs.append(tmp_dir)

        if search_dirs:
            # 获取最近修改的文件（5分钟内）
            import time

            now = time.time()
            for search_dir in search_dirs:
                if search_dir.exists():
                    recent_files = []
                    try:
                        for f in search_dir.rglob("*"):
                            if f.is_file() and (now - f.stat().st_mtime) < 300:
                                recent_files.append(str(f))
                    except PermissionError:
                        continue
                    if recent_files:
                        found_files.extend(recent_files[:5])  # 最多5个
                        break

    # 判断验证是否通过
    verified = len(found_files) > 0 if expected_files else True

    message = ""
    if expected_files:
        if found_files:
            message = f"Found {len(found_files)}/{len(expected_files)} expected files"
        else:
            message = f"No expected files found (expected {len(expected_files)})"
    else:
        message = "No specific file paths in task description"

    return {
        "verified": verified,
        "files_found": found_files,
        "files_expected": expected_files,
        "message": message,
    }


class YoungAgent:
    def __init__(
        self,
        config,
        package_manager=None,
        # Dependency injection - optional components
        llm_client=None,
        tool_executor=None,
        checkpoint_manager=None,
        harness=None,
        datacenter=None,
        evaluation_hub=None,
        evolver=None,
        # AI Docker - Runtime sandbox
        sandbox=None,
        sandbox_pool=None,
    ):
        """Initialize YoungAgent with optional dependency injection.

        Args:
            config: Agent configuration
            package_manager: Package manager instance (optional)
            llm_client: LLM client instance (optional, for testing)
            tool_executor: Tool executor instance (optional, for testing)
            checkpoint_manager: Checkpoint manager instance (optional, for testing)
            harness: Test harness instance (optional, for testing)
            datacenter: Data center instance (optional, for testing)
            evaluation_hub: Evaluation hub instance (optional, for testing)
            evolver: Evolution engine instance (optional, for testing)
            sandbox: AISandbox instance (optional, for AI Docker)
            sandbox_pool: SandboxPool instance (optional, for AI Docker)
        """
        self.config = config
        self.mode = config.mode
        self._session_id = str(uuid.uuid4())
        self._history = []
        self._max_history = 100  # 限制历史记录数量，防止内存泄漏
        self._sub_agents = {}
        self._stats = {"total_tokens": 0, "tool_calls": 0, "errors": 0}
        self._permission = PermissionEvaluator(config.permission)
        self._dispatcher = TaskDispatcher(self._sub_agents)
        self._flow_skill = None
        self._package_manager = package_manager or PackageManager()

        # ========== Dependency Injection ==========
        # Use injected dependencies if provided, otherwise create internally
        self._llm = llm_client
        self._tool_executor_injected = tool_executor is not None
        self._checkpoint_manager_injected = checkpoint_manager is not None
        self._harness_injected = harness is not None
        self._datacenter_injected = datacenter is not None
        self._evaluation_hub_injected = evaluation_hub is not None
        self._evolver_injected = evolver is not None

        # 初始化 FlowSkill
        self._init_flow_skill(config)

        # ========== OpenTelemetry 初始化 ==========
        self._telemetry_enabled = False
        self._init_telemetry()

        # 初始化 Hooks
        self._hooks_loader = None
        self._hooks = []
        self._init_hooks()

        # 初始化 MCP 服务器
        self._mcp_manager = None
        self._init_mcp_servers()

        # Initialize components (use injected or create)
        self._harness = harness
        self._datacenter = datacenter
        self._evaluation_hub = evaluation_hub
        self._evolver = evolver

        # Data persistence directory - 默认项目本地，可通过配置修改
        import os

        # 默认使用项目本地的 .young 目录
        default_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".young"
        )
        self._data_dir = getattr(config, "data_dir", None) or default_data_dir

        # Checkpoint manager (use injected or create internally)
        self._checkpoint_manager = checkpoint_manager
        self._init_checkpoint()

        # Harness - use injected or create internally
        if not self._harness_injected:
            try:
                from src.harness import Harness
                self._harness = Harness()
            except Exception as e:
                print(f"[Warning] Harness init failed: {e}")

        # DataCenter - use injected or create internally
        if not self._datacenter_injected:
            try:
                from src.datacenter.datacenter import DataCenter
                self._datacenter = DataCenter()
            except Exception as e:
                print(f"[Warning] DataCenter init failed: {e}")

        # EvaluationHub - use injected or create internally
        if not self._evaluation_hub_injected:
            try:
                from src.evaluation.hub import EvaluationHub

                self._evaluation_hub = EvaluationHub()
                # P2: 加载历史评估记录
                eval_path = os.path.join(self._data_dir, "evaluations.json")
                if os.path.exists(eval_path):
                    try:
                        self._evaluation_hub.load_results(eval_path)
                        print(
                            f"[EvaluationHub] Loaded {len(self._evaluation_hub._results)} historical results"
                        )
                    except Exception as load_err:
                        print(f"[Warning] Failed to load historical evaluations: {load_err}")
            except Exception as e:
                print(f"[Warning] EvaluationHub init failed: {e}")

        # EvalPlanner - 评估计划生成器
        self._eval_planner = EvalPlanner()
        print("[EvalPlanner] Initialized for dynamic evaluation planning")

        # EvolEngine - use injected or create internally
        if not self._evolver_injected:
            try:
                from src.evolver.engine import EvolutionEngine

                self._evolver = EvolutionEngine()
                # 预加载一些基础 genes
                self._init_default_genes()
            except Exception as e:
                print(f"[Warning] EvolutionEngine init failed: {e}")

        self._packages = {}
        self._loaded_skills = {}
        self._tools = {}
        # ToolExecutor - use injected or create internally
        self._tool_executor = tool_executor or ToolExecutor(permission_evaluator=self._permission)

        # ========== AI Docker Sandbox 初始化 ==========
        self._sandbox = sandbox
        self._sandbox_pool = sandbox_pool
        if self._sandbox or self._sandbox_pool:
            # 配置沙箱
            self._tool_executor.set_sandbox(self._sandbox)
            self._tool_executor.set_sandbox_pool(self._sandbox_pool)
            print("[YoungAgent] AI Docker Sandbox enabled")

        # 从配置读取执行参数（支持外部配置）
        # 兼容旧 dict 格式和新 ExecutionConfig 类型
        execution_config = getattr(config, "execution", None)
        if execution_config is None:
            execution_config = {}
        elif hasattr(execution_config, 'max_tool_calls'):  # 新类型: ExecutionConfig
            self._max_tool_calls = execution_config.max_tool_calls
            self._timeout_seconds = execution_config.timeout_seconds
            self._checkpoint_enabled = execution_config.checkpoint_enabled
        else:  # 旧格式: dict
            self._max_tool_calls = execution_config.get("max_tool_calls", 10)
            self._timeout_seconds = execution_config.get("timeout_seconds", 300)
            self._checkpoint_enabled = execution_config.get("checkpoint_enabled", True)

        # 打印执行配置
        print("[YoungAgent] Execution config:")
        print(f"  - max_tool_calls: {self._max_tool_calls}")
        print(f"  - timeout_seconds: {self._timeout_seconds}")
        print(f"  - checkpoint_enabled: {self._checkpoint_enabled}")

        # 初始化 LLM 客户端 - use injected or create internally
        if self._llm is None:
            try:
                from src.llm.client_adapter import LLMClient
                self._llm = LLMClient()
            except Exception as e:
                print(f"[Warning] LLM client init failed: {e}")

        # R1-1: 初始化 EvaluationCoordinator (在 LLM 初始化之后)
        try:
            self._eval_coordinator = EvaluationCoordinator(llm_client=self._llm)
        except Exception as e:
            print(f"[Warning] EvaluationCoordinator init failed: {e}")
            self._eval_coordinator = None

        # 初始化 TaskExecutor
        self._task_executor = None

        # 初始化 SubAgents（传入 LLM 和工具执行器）
        self._init_builtin_subagents()
        self._load_skills()

        # TaskExecutor 在 skills 加载后初始化（因为依赖 flow_skill）
        self._init_task_executor()

        # RalphLoop - 自主循环执行器
        self._ralph_loop = RalphLoop(
            config=RalphLoopConfig(
                max_iterations=10,
                min_completion_rate=0.8,
                enable_parallel=True,
            ),
            executor=self._task_executor.execute if self._task_executor else None,
        )

    def _load_skills(self):
        """加载配置的 Skills - 参考 Anthropic SKILL.md 格式"""
        from pathlib import Path

        import yaml

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
        self._build_skill_prompt()

    def _build_skill_prompt(self):
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

    def _init_default_genes(self):
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
            print(f"[Warning] Default genes init failed: {e}")

    def _init_flow_skill(self, config):
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
            self._load_flow_skill_by_name(flow_name, flow_config)
        except Exception as e:
            print(f"[Warning] FlowSkill init failed: {e}")
            self._flow_skill = None

    def _load_flow_skill_by_name(self, flow_name: str, flow_config: dict = None):
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

    def switch_flow_skill(self, flow_name: str, flow_config: dict = None):
        """运行时切换 FlowSkill"""
        print(f"[FlowSkill] Switching to: {flow_name}")
        try:
            self._load_flow_skill_by_name(flow_name, flow_config)
            # 更新 TaskExecutor 的 FlowSkill
            if self._task_executor:
                self._task_executor.update_flow_skill(self._flow_skill)
            return True
        except Exception as e:
            print(f"[FlowSkill] Switch failed: {e}")
            return False

    def _init_task_executor(self):
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

    def _init_telemetry(self):
        """初始化 OpenTelemetry 遥测"""
        try:
            import os

            from src.telemetry import OPENTELEMETRY_AVAILABLE, init_telemetry

            # 检查是否启用遥测
            enabled = os.getenv("OPENYOUNG_TELEMETRY", "false").lower() == "true"

            if enabled and OPENTELEMETRY_AVAILABLE:
                service_name = f"openyoung-{self.config.name}"
                self._telemetry_enabled = init_telemetry(
                    service_name=service_name,
                    enable_console=False
                )
        except Exception:
            # 遥测初始化失败不影响主流程
            pass

    def _init_hooks(self):
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
            print(f"[Warning] Hooks init failed: {e}")
            self._hooks = []

    def _init_mcp_servers(self):
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
            print(f"[Warning] MCP init failed: {e}")
            self._mcp_manager = None

    def _init_checkpoint(self):
        """初始化 CheckpointManager"""
        # Skip if checkpoint_manager was already injected
        if self._checkpoint_manager_injected and self._checkpoint_manager is not None:
            return

        try:
            from src.memory.checkpoint import CheckpointManager

            checkpoint_dir = self._data_dir + "/checkpoints"
            self._checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)
            print(f"[Checkpoint] Initialized at {checkpoint_dir}")
        except Exception as e:
            print(f"[Warning] Checkpoint init failed: {e}")
            self._checkpoint_manager = None

    # ========== AI Docker Sandbox Methods ==========

    def enable_sandbox(
        self,
        max_memory_mb: int = 512,
        max_execution_time_seconds: int = 300,
        allow_network: bool = False,
    ) -> None:
        """启用 AI Docker 沙箱

        Args:
            max_memory_mb: 最大内存限制 (MB)
            max_execution_time_seconds: 最大执行时间 (秒)
            allow_network: 是否允许网络访问
        """
        if self._sandbox or self._sandbox_pool:
            print("[YoungAgent] Sandbox already enabled")
            return

        # 创建沙箱配置
        config = SandboxConfig(
            max_memory_mb=max_memory_mb,
            max_execution_time_seconds=max_execution_time_seconds,
            allow_network=allow_network,
        )

        # 创建沙箱
        self._sandbox = AISandbox(config)
        self._tool_executor.set_sandbox(self._sandbox)

        print(f"[YoungAgent] Sandbox enabled: memory={max_memory_mb}MB, timeout={max_execution_time_seconds}s")

    def enable_sandbox_pool(
        self,
        min_size: int = 2,
        max_size: int = 10,
        max_memory_mb: int = 512,
        max_execution_time_seconds: int = 300,
    ) -> None:
        """启用 AI Docker 沙箱池

        Args:
            min_size: 最小实例数
            max_size: 最大实例数
            max_memory_mb: 最大内存限制 (MB)
            max_execution_time_seconds: 最大执行时间 (秒)
        """
        if self._sandbox or self._sandbox_pool:
            print("[YoungAgent] Sandbox already enabled")
            return

        # 创建配置
        sandbox_config = SandboxConfig(
            max_memory_mb=max_memory_mb,
            max_execution_time_seconds=max_execution_time_seconds,
        )
        pool_config = PoolConfig(
            min_size=min_size,
            max_size=max_size,
            sandbox_config=sandbox_config,
        )

        # 创建沙箱池
        self._sandbox_pool = SandboxPool(pool_config)
        self._tool_executor.set_sandbox_pool(self._sandbox_pool)

        print(f"[YoungAgent] Sandbox pool enabled: size={min_size}-{max_size}")

    async def _save_checkpoint(self, file_path: str = None, reason: str = "task_complete"):
        """保存检查点"""
        if not self._checkpoint_manager:
            return

        try:
            # 保存任务状态
            state = {
                "session_id": self._session_id,
                "history_count": len(self._history),
                "stats": self._stats,
            }

            checkpoint_id = await self._checkpoint_manager.create_checkpoint(
                file_path=file_path or self._data_dir + "/state.json",
                reason=reason,
            )
            if checkpoint_id:
                print(f"[Checkpoint] Created: {checkpoint_id}")
        except Exception as e:
            print(f"[Warning] Checkpoint save failed: {e}")

    def _trigger_hooks(self, trigger: str, context: dict = None) -> list:
        """触发指定类型的 hooks"""
        triggered = []

        # 1. 触发内置的自学习 Hook
        if trigger == "post_task" and context:
            try:
                from src.package_manager.hooks_loader import LearningHook

                learning_hook = LearningHook()
                result = learning_hook.on_post_task(context)
                if result.get("status") == "success":
                    print(f"[LearningHook] Evolution triggered: {result.get('signals', [])}")
                    if result.get("capsule_created"):
                        print(f"[LearningHook] Capsule created: {result.get('capsule_id')}")
                triggered.append({"hook": "learning_hook", "trigger": trigger, "action": "evolve"})
            except Exception as e:
                print(f"[LearningHook] Error: {e}")

        # 2. 触发配置的 hooks
        if self._hooks_loader and self._hooks:
            try:
                hooks = self._hooks_loader.get_hooks_by_trigger(trigger)
                for hook in hooks:
                    triggered.append(
                        {
                            "hook": hook.name,
                            "trigger": trigger,
                            "action": hook.action.value if hook.action else None,
                        }
                    )
                    print(f"[Hooks] Triggered: {hook.name} ({trigger})")
            except Exception as e:
                print(f"[Warning] Hook trigger failed: {e}")

        return triggered

    def _init_builtin_subagents(self):
        """初始化 SubAgents - 从配置加载，参考 Claude Code Task 协议"""
        from src.core.types import SubAgentType

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

    async def run(self, user_input: str) -> str:
        # 启动 harness
        if self._harness:
            self._harness.start()

        # ========== Hooks: pre_task ==========
        self._trigger_hooks("pre_task", {"input": user_input})

        if not await self._permission.can_run(user_input):
            return "Permission denied"

        # ========== FlowSkill 前置处理 ==========
        context = {"session_id": self._session_id}
        if self._flow_skill:
            try:
                user_input = await self._flow_skill.pre_process(user_input, context)
            except Exception as e:
                print(f"[FlowSkill] Pre-process error: {e}")

        task = await self._parse_input(user_input)

        # ========== EvalPlanner - 生成评估计划 ==========
        eval_plan = None
        if self._eval_planner:
            try:
                eval_plan = await self._eval_planner.generate_plan(user_input)
                print(f"[EvalPlanner] Generated plan for task type: {eval_plan.task_type}")
                print(f"[EvalPlanner] Success criteria: {len(eval_plan.success_criteria)} items")
                print(f"[EvalPlanner] Validation methods: {len(eval_plan.validation_methods)} items")
            except Exception as e:
                print(f"[EvalPlanner] Failed to generate plan: {e}")

        # 记录开始时间
        start_time = datetime.now()

        # 使用 TaskExecutor 执行任务
        result = await self._task_executor.execute(task)

        # ========== FlowSkill 后置处理 ==========
        if self._flow_skill:
            try:
                result = await self._flow_skill.post_process(result, context)
            except Exception as e:
                print(f"[FlowSkill] Post-process error: {e}")

        # ========== Hooks: post_task ==========
        # 构建学习上下文
        hook_context = {
            "result": result,
            "task": task.description if task else "",
            "success": not result.startswith("Error") and not result.startswith("error"),
            "session_id": self._session_id,
            "tools_used": [m.role.value for m in self._history if m.role.value == "tool"],
            "result_summary": result[:200] if result else "",
        }
        self._trigger_hooks("post_task", hook_context)

        # 记录结束时间
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # ========== 1. DataCenter - 记录 Trace ==========
        if self._datacenter:
            try:
                from src.datacenter.datacenter import TraceRecord, TraceStatus

                status = (
                    TraceStatus.SUCCESS
                    if result and not result.startswith("Error")
                    else TraceStatus.FAILED
                )
                trace = TraceRecord(
                    session_id=self._session_id,
                    agent_name=self.config.name,
                    duration_ms=duration_ms,
                    status=status,
                    error=result[:200] if status == TraceStatus.FAILED else "",
                )
                self._datacenter.record_trace(trace)
            except Exception as e:
                print(f"[DataCenter] Error: {e}")

        # ========== 2. EvaluationCoordinator - 质量评估 ==========
        # R1-1: 使用 EvaluationCoordinator 进行评估
        quality_score = 1.0
        if self._eval_coordinator and result:
            try:
                # 创建评估上下文
                total_tokens = self._stats.get("total_tokens", 0)
                model = self._stats.get("model", "unknown")

                eval_context = EvaluationContext(
                    task_description=task.description,
                    task_result=result,
                    duration_ms=duration_ms,
                    tokens_used=total_tokens,
                    model=model,
                    session_id=self._session_id,
                )

                # 使用协调器执行评估
                eval_report = await self._eval_coordinator.evaluate(eval_context)
                quality_score = eval_report.score

                print(f"[EvaluationCoordinator] Score: {quality_score:.2f}")
                print(f"[EvaluationCoordinator] Task type: {eval_report.task_type}")
                print(f"[EvaluationCoordinator] Completion rate: {eval_report.completion_rate:.2f}")

                # 文件验证（保留在 young_agent 中因为需要文件系统访问）
                file_validation = validate_file_creation(task.description, result)
                if not file_validation["verified"]:
                    print(f"[FileValidation] {file_validation['message']}")
                    quality_score *= 0.3  # 文件未创建，大幅降低
                elif file_validation["files_found"]:
                    print(f"[FileValidation] Files verified: {file_validation['files_found']}")

                # 记录到 EvaluationHub（保持兼容性）
                if self._evaluation_hub:
                    from src.evaluation.hub import EvaluationResult

                    # 处理 judge_result 可能是 JudgeScore 对象或 dict 的情况
                    jr = eval_report.judge_result
                    if hasattr(jr, "get"):
                        # 是 dict
                        jr_input = jr.get("input", "")
                        jr_output = jr.get("output", "")
                        jr_scores = jr.get("scores", [])
                        jr_total = jr.get("total_score", 0)
                        jr_avg = jr.get("average_score", 0)
                    else:
                        # 是 JudgeScore 对象
                        jr_input = getattr(jr, "input", "")
                        jr_output = getattr(jr, "output", "")
                        jr_scores = getattr(jr, "scores", [])
                        jr_total = getattr(jr, "total_score", 0)
                        jr_avg = getattr(jr, "average_score", 0)

                    judge_result_serializable = {
                        "input": jr_input,
                        "output": jr_output,
                        "scores": [
                            {
                                "dimension": getattr(s, "dimension", ""),
                                "score": getattr(s, "score", 0),
                                "reasoning": getattr(s, "reasoning", ""),
                            }
                            for s in jr_scores
                        ],
                        "total_score": jr_total,
                        "average_score": jr_avg,
                    }

                    eval_details = {
                        "judge_result": judge_result_serializable,
                        "eval_plan": eval_report.eval_plan.to_dict()
                        if hasattr(eval_report.eval_plan, "to_dict")
                        else {},
                        "completion_rate": eval_report.completion_rate,
                        "task_type": eval_report.task_type,
                        "threshold_violations": eval_report.threshold_violations,
                        "weights_used": eval_report.weights_used,
                        "file_validation": file_validation,
                    }

                    eval_result = EvaluationResult(
                        metric="task_completion",
                        score=quality_score,
                        details=eval_details,
                        evaluator="evaluation_coordinator",
                    )
                    self._evaluation_hub._results.append(eval_result)

            except Exception as e:
                print(f"[EvaluationCoordinator] Error: {e}, using default score")
                quality_score = 0.9 if not result.startswith("Error") else 0.3

        # ========== 3. EvolutionEngine - 触发进化 ==========
        if self._evolver:
            try:
                signals = ["success"] if quality_score > 0.5 else ["failure"]
                gene = self._evolver.evolve(signals)
                if gene:
                    # 创建 capsule
                    capsule = self._evolver.create_capsule(
                        trigger=signals,
                        gene=gene,
                        summary=f"Task: {task.description[:50]}... Result: {result[:50]}...",
                    )
                    print(f"[Evolver] Created capsule: {capsule.id}")
            except Exception as e:
                print(f"[Evolver] Error: {e}")

        # ========== 4. Harness - 记录步骤 ==========
        if self._harness:
            self._harness.record_step(quality_score > 0.5)

        # 记录对话历史（带上限，防止内存泄漏）
        self._history.append(Message(role=MessageRole.USER, content=user_input))
        self._history.append(Message(role=MessageRole.ASSISTANT, content=result))

        # 限制历史记录数量
        if len(self._history) > self._max_history:
            # 保留最近的对话，移除最老的
            self._history = self._history[-self._max_history :]

        # ========== 5. Auto-save all components ==========
        self._save_all()

        # ========== 6. Checkpoint - 保存状态 ==========
        # 任务完成后自动保存 checkpoint
        await self._save_checkpoint(reason="task_complete")

        # ========== 7. 评估反馈优化 ==========
        # 根据评估结果自动优化配置
        await self._apply_evaluation_optimization(result, quality_score)

        return result

    async def _apply_evaluation_optimization(self, result: str, quality_score: float):
        """根据评估结果自动优化 agent 配置"""
        if not self._evaluation_hub:
            return

        try:
            # 获取最新的评估结果
            latest_eval = self._evaluation_hub.get_latest_result()
            if not latest_eval:
                return

            # 调用优化方法
            config_updates = self._evaluation_hub.optimize_agent_config(
                self.config.name, latest_eval
            )

            # 如果有需要更新的配置
            if any(config_updates.values()) and config_updates.get("reason"):
                print(f"[Evaluation] Optimization: {config_updates['reason']}")

                # 保存评估历史
                self._evaluation_hub.save_history(self.config.name, latest_eval)

                # 显示配置更新建议
                updates = [f"{k}={v}" for k, v in config_updates.items() if v and k != "reason"]
                if updates:
                    print(f"[Evaluation] Suggested updates: {', '.join(updates)}")
                    print(
                        f"[Evaluation] Run 'openyoung config set agent.model {config_updates.get('model', '')}' to apply"
                    )

            # ========== 执行结果回写 ==========
            # 分析执行结果，提取模式
            try:
                from src.evolver.result_analyzer import ResultAnalyzer

                # 获取任务描述
                task_desc = ""
                if self._history:
                    for msg in reversed(self._history):
                        if msg.role.value == "user":
                            task_desc = msg.content
                            break

                analyzer = ResultAnalyzer()
                analysis = analyzer.analyze(task_desc, result)

                # 如果成功，生成 FlowSkill 配置建议
                if analysis.get("success"):
                    flowskill_config = analyzer.generate_flowskill_config()
                    if flowskill_config:
                        print(
                            f"[ResultAnalyzer] Generated FlowSkill: {flowskill_config.get('name')}"
                        )
                        print(f"[ResultAnalyzer] Workflow: {flowskill_config.get('workflow', [])}")

                        # 保存分析结果
                        import os

                        os.makedirs(self._data_dir, exist_ok=True)
                        import json

                        analysis_path = os.path.join(self._data_dir, "analysis.json")
                        with open(analysis_path, "w") as f:
                            json.dump(analysis, f, indent=2, ensure_ascii=False)
                        print(f"[ResultAnalyzer] Saved to {analysis_path}")
            except Exception as e:
                print(f"[ResultAnalyzer] Error: {e}")

        except Exception as e:
            print(f"[Evaluation] Optimization error: {e}")

    def _save_all(self):
        """保存所有组件数据到磁盘"""
        import os

        os.makedirs(self._data_dir, exist_ok=True)

        # 保存 DataCenter traces
        if self._datacenter:
            try:
                path = os.path.join(self._data_dir, "traces.json")
                self._datacenter.trace_collector.save(path)
                print(f"[DataCenter] Saved traces to {path}")
            except Exception as e:
                print(f"[DataCenter] Save error: {e}")

        # 保存 EvaluationHub results
        if self._evaluation_hub:
            try:
                path = os.path.join(self._data_dir, "evaluations.json")
                self._evaluation_hub.save_results(path)
                print(f"[EvaluationHub] Saved results to {path}")
            except Exception as e:
                print(f"[EvaluationHub] Save error: {e}")

        # 保存 EvolutionEngine genes and capsules
        if self._evolver:
            try:
                genes_path = os.path.join(self._data_dir, "genes.json")
                capsules_path = os.path.join(self._data_dir, "capsules.json")
                self._evolver.save(genes_path, capsules_path)
                print(f"[Evolver] Saved to {self._data_dir}")
            except Exception as e:
                print(f"[Evolver] Save error: {e}")

        # 保存 Harness status
        if self._harness:
            try:
                path = os.path.join(self._data_dir, "harness.json")
                self._harness.save(path)
                print(f"[Harness] Saved to {path}")
            except Exception as e:
                print(f"[Harness] Save error: {e}")

    async def _parse_input(self, user_input: str) -> Task:
        """解析用户输入 - 支持 @mention 触发 SubAgent"""
        import re

        # 参考 Claude Code Task 协议: @subagent task_description
        match = re.match(r"@(\w+)\s+(.+)", user_input.strip())
        if match:
            subagent_name = match.group(1)
            description = match.group(2)

            # 查找对应的 SubAgentType
            from src.core.types import SubAgentType

            subagent_type = None

            # 首先检查是否匹配预定义类型
            for sat in SubAgentType:
                if sat.value == subagent_name:
                    subagent_type = sat
                    break

            # 如果没有匹配预定义类型，检查是否在已加载的 SubAgents 中
            if subagent_type is None and subagent_name in self._sub_agents:
                # 使用 GENERAL 类型作为占位符，实际委托时会查找具体 SubAgent
                subagent_type = SubAgentType.GENERAL

            return Task(
                id=str(uuid.uuid4()),
                description=description,
                input=description,
                subagent_type=subagent_type,
                custom_subagent=subagent_name
                if subagent_type == SubAgentType.GENERAL and subagent_name in self._sub_agents
                else None,
            )
        return Task(id=str(uuid.uuid4()), description=user_input, input=user_input)

    async def _delegate_to_subagent(self, task: Task) -> str:
        """委托任务给 SubAgent - 使用 TaskDispatcher"""
        subagent_type = task.subagent_type.value if task.subagent_type else None
        custom_name = getattr(task, "custom_subagent", None)

        # 如果有自定义 SubAgent 名称，直接从 _sub_agents 中查找
        if custom_name and custom_name in self._sub_agents:
            sub_agent = self._sub_agents[custom_name]
            print(f"[SubAgent] Direct delegation to @{custom_name}: {task.description[:50]}...")
            sub_task = Task(
                id=str(uuid.uuid4()),
                description=task.description,
                input=task.description,
            )
            context = {"parent_session": self._session_id, "summary": ""}
            result = await sub_agent.run(sub_task, context)
            return result

        # 使用 TaskDispatcher 进行任务分发
        if self._dispatcher:
            try:
                from src.core.types import TaskDispatchParams

                params = TaskDispatchParams(
                    task_description=task.description,
                    subagent_type=task.subagent_type,
                    context={"parent_session": self._session_id},
                )
                parent_context = {"session_id": self._session_id, "summary": ""}

                print(f"[Dispatcher] Delegating to @{subagent_type}: {task.description[:50]}...")
                result = await self._dispatcher.dispatch(params, parent_context)
                return result.get("result", "")
            except Exception as e:
                print(f"[Dispatcher] Error: {e}, falling back to direct delegation")

        # 降级到直接调用（兼容模式）
        sub_agent = None
        for sa in self._sub_agents.values():
            if sa.type == task.subagent_type:
                sub_agent = sa
                break

        if not sub_agent:
            return f"[Error] SubAgent not found: {subagent_type}"

        print(f"[SubAgent] Direct delegation to @{subagent_type}: {task.description[:50]}...")

        # 创建子任务
        sub_task = Task(
            id=str(uuid.uuid4()),
            description=task.description,
            input=task.description,
        )

        # 构建子上下文
        context = {
            "session_id": self._session_id,
            "parent_summary": "",
            "task": task.description,
        }

        try:
            # 执行 SubAgent
            result = await sub_agent.run(sub_task, context)
            return result
        except Exception as e:
            return f"[Error] SubAgent execution failed: {str(e)}"

    async def _execute(self, task: Task) -> str:
        """执行任务 - 支持 SubAgent 委托"""

        # ========== FlowSkill 智能路由 ==========
        if self._flow_skill:
            try:
                # 检查是否需要委托给 SubAgent
                should_delegate = await self._flow_skill.should_delegate(
                    task.description, {"session_id": self._session_id}
                )
                if should_delegate:
                    # 获取合适的 SubAgent 类型
                    subagent_type = await self._flow_skill.get_subagent_type(task.description)
                    if subagent_type and subagent_type != "general":
                        print(f"[FlowSkill] Delegating to subagent: {subagent_type}")
                        task.subagent_type = subagent_type
                        return await self._delegate_to_subagent(task)
            except Exception as e:
                print(f"[FlowSkill] Smart routing error: {e}")

        # 如果是 SubAgent 调用，委托给对应 SubAgent
        if task.subagent_type:
            return await self._delegate_to_subagent(task)

        messages = []
        system_prompt = (
            self.config.system_prompt
            or """你是一个有帮助的AI助手。你可以通过执行代码来完成任务。可用工具：bash, write, edit, read, glob, grep"""
        )
        messages.append({"role": "system", "content": system_prompt})
        for msg in self._history[-10:]:
            messages.append({"role": msg.role.value, "content": msg.content})
        messages.append({"role": "user", "content": task.description})
        tools = self._tool_executor.get_tool_schemas()

        try:
            from src.llm.client_adapter import LLMClient

            client = LLMClient()
            for i in range(self._max_tool_calls):
                response = await client.chat(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=tools,
                )
                message = response["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    await client.close()
                    return content
                for tool_call in tool_calls:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    arguments = json.loads(func["arguments"])
                    print(f"\n[执行工具] {tool_name}: {arguments}")
                    result = await self._tool_executor.execute(tool_name, arguments)
                    messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call],
                        }
                    )
                    tool_result = result.result if result.success else f"错误: {result.error}"
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"call_{i}"),
                            "content": tool_result,
                        }
                    )
                    print(f"[工具结果] {tool_result[:200]}...")
            await client.close()
            return "已达到最大工具调用次数"
        except Exception as e:
            return f"Error: {str(e)}"

    # ===== 获取各组件数据的方法 =====

    def get_harness_stats(self) -> dict[str, Any]:
        if self._harness:
            return self._harness.get_status()
        return {}

    def get_datacenter_traces(self) -> list:
        if self._datacenter:
            return self._datacenter.trace_collector._traces
        return []

    def get_evaluation_results(self) -> list:
        if self._evaluation_hub:
            return self._evaluation_hub._results
        return []

    def get_evolver_genes(self) -> list:
        if self._evolver:
            return list(self._evolver._matcher._genes.values())
        return []

    def get_evolver_capsules(self) -> list:
        if self._evolver:
            return self._evolver.get_capsules()
        return []

    def get_all_stats(self) -> dict[str, Any]:
        return {
            "harness": self.get_harness_stats(),
            "datacenter_traces_count": len(self.get_datacenter_traces()),
            "evaluation_results_count": len(self.get_evaluation_results()),
            "evolver_genes_count": len(self.get_evolver_genes()),
            "evolver_capsules_count": len(self.get_evolver_capsules()),
        }

    def get_evaluation_trend(self, limit: int = 10) -> dict[str, Any]:
        """获取评估趋势数据

        Args:
            limit: 返回最近 N 条记录

        Returns:
            趋势数据字典
        """
        if not self._evaluation_hub:
            return {"error": "EvaluationHub not initialized"}
        return self._evaluation_hub.get_trend(limit)
