"""
YoungAgent - Main Agent Class with full system integration
"""

import uuid
from typing import Any, AsyncGenerator

from src.agents.dispatcher import TaskDispatcher
from src.agents.eval_store import EvalStore
from src.agents.permission import PermissionEvaluator

# Core 模块 - EventBus, Heartbeat, Knowledge (已迁移到 _init_methods.py)
from src.core.logger import get_logger
from src.core.types import (
    Task,
)

# 模块级 logger
logger = get_logger(__name__)
# Extracted methods from _checkpoint_methods.py

# Extracted methods from _init_methods.py
from src.agents._init_methods import (
    _load_flow_skill_by_name,
    init_builtin_subagents,
    init_checkpoint,
    init_core_runtime,
    init_default_genes,
    init_execution_config,
    init_flow_skill,
    init_hooks,
    init_llm_and_evaluation,
    init_mcp_servers,
    init_memory_facade,
    init_ralph_loop,
    init_task_executor,
    init_telemetry,
    load_skills,
)

# Extracted methods from _run_methods.py
from src.agents._run_methods import (
    _apply_result_analysis,
    _parse_input,
    _save_all,
    run,
    run_streaming,
)

# Extracted methods from _sandbox_methods.py
from src.package_manager.manager import PackageManager

# AI Docker - Runtime
from src.tools.executor import ToolExecutor


class YoungAgent:
    def __init__(
        self,
        config,
        package_manager=None,
        llm_client=None,
        tool_executor=None,
        checkpoint_manager=None,
        memory_facade=None,
        harness=None,
        datacenter=None,
        evolver=None,
        sandbox=None,
        sandbox_pool=None,
        container=None,
    ):
        """Initialize YoungAgent with optional dependency injection."""
        self.config = config
        self.mode = config.mode
        self._session_id = str(uuid.uuid4())
        self._history = []
        self._max_history = 100  # 限制历史记录数量，防止内存泄漏
        self._sub_agents = {}
        self._stats = {"total_tokens": 0, "tool_calls": 0, "errors": 0}
        self._permission = PermissionEvaluator(config.permission)
        self._dispatcher = TaskDispatcher(self._sub_agents)
        self._container = container
        self._flow_skill = None
        self._package_manager = package_manager or PackageManager()
        self._llm = llm_client

        # 初始化 FlowSkill
        init_flow_skill(self, config)

        # OpenTelemetry 初始化
        init_telemetry(self)

        # Hooks 初始化
        self._hooks_loader = None
        self._hooks = []
        init_hooks(self)

        # MCP 服务器初始化
        self._mcp_manager = None
        init_mcp_servers(self)

        # Initialize components
        self._harness = harness
        self._datacenter = datacenter
        self._eval_store = EvalStore()
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
        self._checkpoint_manager_injected = checkpoint_manager is not None
        init_checkpoint(self)

        # Memory Facade (use injected or create internally)
        self._memory_facade = memory_facade
        self._memory_facade_injected = memory_facade is not None
        init_memory_facade(self)

        # Harness - use injected > container > create
        if self._harness is None:
            try:
                from src.harness import Harness

                self._harness = Harness()
            except Exception as e:
                logger.warning(f"Harness init failed: {e}")

        # DataCenter - use injected > container > create
        if self._datacenter is None:
            try:
                from src.datacenter.datacenter import DataCenter

                self._datacenter = DataCenter()
            except Exception as e:
                logger.warning(f"DataCenter init failed: {e}")

        # EvolEngine - use injected > create
        if self._evolver is None:
            try:
                from src.evolver.engine import EvolutionEngine

                self._evolver = EvolutionEngine()
                init_default_genes(self)
            except Exception as e:
                logger.warning(f"EvolutionEngine init failed: {e}")

        self._packages = {}
        self._loaded_skills = {}
        self._tools = {}
        self._tool_executor = tool_executor or ToolExecutor(permission_evaluator=self._permission)

        # AI Docker Sandbox
        self._sandbox = sandbox
        self._sandbox_pool = sandbox_pool
        if self._sandbox or self._sandbox_pool:
            self._tool_executor.set_sandbox(self._sandbox)
            self._tool_executor.set_sandbox_pool(self._sandbox_pool)
            print("[YoungAgent] AI Docker Sandbox enabled")

        # Core Runtime: EventBus, Heartbeat, KnowledgeManager
        init_core_runtime(self, config)

        # Execution config
        init_execution_config(self, config)

        # LLM client and EvaluationCoordinator
        init_llm_and_evaluation(self)

        # 初始化 TaskExecutor
        self._task_executor = None

        # 初始化 SubAgents（传入 LLM 和工具执行器）
        init_builtin_subagents(self)
        load_skills(self)

        # TaskExecutor 在 skills 加载后初始化（因为依赖 flow_skill）
        init_task_executor(self)

        # RalphLoop - 自主循环执行器
        init_ralph_loop(self)

    def switch_flow_skill(self, flow_name: str, flow_config: dict = None):
        """运行时切换 FlowSkill"""
        print(f"[FlowSkill] Switching to: {flow_name}")
        try:
            _load_flow_skill_by_name(self, flow_name, flow_config)
            # 更新 TaskExecutor 的 FlowSkill
            if self._task_executor:
                self._task_executor.update_flow_skill(self._flow_skill)
            return True
        except Exception as e:
            print(f"[FlowSkill] Switch failed: {e}")
            return False

    async def run(self, user_input: str) -> str:
        """Main execution method - delegates to _run_methods.run()."""
        return await run(self, user_input)

    async def run_streaming(self, user_input: str) -> AsyncGenerator[dict, None]:
        """Streaming execution method - yields partial results.

        Args:
            user_input: User input string

        Yields:
            dict with partial result data
        """
        async for partial in run_streaming(self, user_input):
            yield partial

    async def _apply_result_analysis(self, result: str) -> None:
        """Analyze execution result - delegates to _run_methods._apply_result_analysis()."""
        return await _apply_result_analysis(self, result)

    def _save_all(self):
        """Save all components - delegates to _run_methods._save_all()."""
        return _save_all(self)

    async def _parse_input(self, user_input: str) -> "Task":
        """Parse user input - delegates to _run_methods._parse_input()."""
        return await _parse_input(self, user_input)

    # ===== Stats getters =====

    def get_harness_stats(self) -> dict[str, Any]:
        if self._harness:
            return self._harness.get_status()
        return {}

    def get_memory_facade(self):
        """获取 MemoryFacade 实例"""
        return self._memory_facade

    def get_datacenter_traces(self) -> list:
        if self._datacenter:
            return self._datacenter.trace_collector._traces
        return []

    def get_evaluation_results(self) -> list:
        if self._eval_store:
            return self._eval_store._results
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
            "memory_enabled": self._memory_facade is not None,
        }

    async def store_knowledge(self, content: str, layer: str = "semantic", **kwargs) -> bool:
        """存储知识到分层记忆系统

        Args:
            content: 知识内容
            layer: 存储层 (working/semantic/checkpoint)
            **kwargs: 额外参数

        Returns:
            是否存储成功
        """
        if not self._memory_facade:
            return False
        try:
            await self._memory_facade.store(content=content, layer=layer, **kwargs)
            return True
        except Exception as e:
            logger.warning(f"store_knowledge failed: {e}")
            return False

    async def retrieve_knowledge(self, query: str, limit: int = 5, **kwargs) -> list:
        """从分层记忆系统检索知识

        Args:
            query: 查询内容
            limit: 返回结果数量
            **kwargs: 额外参数

        Returns:
            检索结果列表
        """
        if not self._memory_facade:
            return []
        try:
            return await self._memory_facade.retrieve(query=query, limit=limit, **kwargs)
        except Exception as e:
            logger.warning(f"retrieve_knowledge failed: {e}")
            return []

    def get_evaluation_trend(self, limit: int = 10) -> dict[str, Any]:
        """获取评估趋势数据

        Args:
            limit: 返回最近 N 条记录

        Returns:
            趋势数据字典
        """
        # Evaluation now uses Harness system (src/hub/evaluate/)
        # Return simple trend from _eval_store
        results = self._eval_store._results[-limit:] if self._eval_store._results else []
        if not results:
            return {"error": "No evaluation results yet"}
        return {
            "trend": [r.get("score", 0) for r in results],
            "task_types": [r.get("task_type", "unknown") for r in results],
            "count": len(results),
        }
