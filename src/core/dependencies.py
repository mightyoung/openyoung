"""
YoungAgent 依赖注册

定义 YoungAgent 需要的所有依赖项，并注册到 DI 容器

Note: EvaluationHub 已移除 — 评估功能迁移到 src/hub/evaluate/ (Harness 系统)
"""

from src.agents.permission import PermissionEvaluator
from src.core.events import EventBus, EventRegistry
from src.core.memory.impl.checkpoint import CheckpointManager
from src.datacenter.datacenter import DataCenter
from src.evolver.engine import EvolutionEngine
from src.harness import Harness
from src.package_manager.manager import PackageManager
from src.tools.executor import ToolExecutor


# 依赖 Token 常量
class DIToken:
    """DI 依赖标识符"""

    PACKAGE_MANAGER = "package_manager"
    LLM_CLIENT = "llm_client"
    TOOL_EXECUTOR = "tool_executor"
    CHECKPOINT_MANAGER = "checkpoint_manager"
    HARNESS = "harness"
    DATACENTER = "datacenter"
    EVOLVER = "evolver"
    EVENT_BUS = "event_bus"
    HOOK_REGISTRY = "hook_registry"


def register_young_agent_dependencies(container) -> None:
    """注册 YoungAgent 需要的所有依赖

    Args:
        container: DI 容器实例
    """
    # Package Manager
    container.register(
        DIToken.PACKAGE_MANAGER,
        lambda: PackageManager(),
        singleton=True,
    )

    # Tool Executor
    container.register(
        DIToken.TOOL_EXECUTOR,
        lambda: ToolExecutor(),
        singleton=False,
    )

    # Checkpoint Manager (using impl)
    container.register(
        DIToken.CHECKPOINT_MANAGER,
        lambda: CheckpointManager(),
        singleton=True,
    )

    # Harness
    container.register(
        DIToken.HARNESS,
        lambda: Harness(),
        singleton=True,
    )

    # DataCenter
    container.register(
        DIToken.DATACENTER,
        lambda: DataCenter(),
        singleton=True,
    )

    # EvolutionEngine
    container.register(
        DIToken.EVOLVER,
        lambda: EvolutionEngine(),
        singleton=True,
    )

    # EventRegistry
    container.register(
        DIToken.HOOK_REGISTRY,
        lambda: EventRegistry(),
        singleton=True,
    )

    # EventBus (depends on EventRegistry)
    container.register(
        DIToken.EVENT_BUS,
        lambda: EventBus(hook_registry=container.resolve(DIToken.HOOK_REGISTRY)),
        singleton=True,
    )
