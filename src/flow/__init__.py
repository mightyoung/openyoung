"""
Flow Package - 工作流编排
"""

from .base import FlowSkill
from .composite import (
    ChainFlowSkill,
    CompositeFlowSkill,
    ConditionalFlowSkill,
    ParallelFlowSkill,
    compose_conditional,
    compose_parallel,
    compose_skills,
)
from .conditional import ConditionalFlow
from .development import DevelopmentFlow, create_development_flow
from .loop import LoopFlow
from .parallel import ParallelFlow
from .pipeline import Pipeline, PipelineContext, PipelineExecutor, Stage
from .sequential import SequentialFlow

# LangGraph 适配器
try:
    from .langgraph_adapter import (
        LANGGRAPH_AVAILABLE,
        AgentState,
        FlowEdge,
        FlowNode,
        LangGraphAdapter,
        NodeType,
        ReActAgentFactory,
        StateGraphConverter,
        create_simple_agent,
    )
except ImportError:
    LangGraphAdapter = None
    StateGraphConverter = None
    ReActAgentFactory = None
    FlowNode = None
    FlowEdge = None
    AgentState = None
    NodeType = None
    create_simple_agent = None
    LANGGRAPH_AVAILABLE = False

# Agent Graph Builder
try:
    from .agent_graph import (
        ActionType,
        AgentGraphBuilder,
        AgentGraphState,
        create_agent_graph,
    )
except ImportError:
    AgentGraphBuilder = None
    AgentGraphState = None
    ActionType = None
    create_agent_graph = None

__all__ = [
    # Base
    "FlowSkill",
    # Pipeline
    "Pipeline",
    "Stage",
    "PipelineContext",
    "PipelineExecutor",
    # Composite
    "CompositeFlowSkill",
    "ChainFlowSkill",
    "ParallelFlowSkill",
    "ConditionalFlowSkill",
    "compose_skills",
    "compose_parallel",
    "compose_conditional",
    # Flows
    "SequentialFlow",
    "ParallelFlow",
    "ConditionalFlow",
    "LoopFlow",
    "DevelopmentFlow",
    "create_development_flow",
    # LangGraph
    "LangGraphAdapter",
    "StateGraphConverter",
    "ReActAgentFactory",
    "FlowNode",
    "FlowEdge",
    "AgentState",
    "NodeType",
    "create_simple_agent",
    "LANGGRAPH_AVAILABLE",
    # Agent Graph
    "AgentGraphBuilder",
    "AgentGraphState",
    "ActionType",
    "create_agent_graph",
]
