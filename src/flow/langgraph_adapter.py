"""
LangGraph 适配器模块

提供与 LangGraph 的集成能力:
- StateGraph 转换器
- ReAct Agent 工厂
- 与现有 flow 模块的兼容层

依赖: langgraph >= 0.0.20
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)

# LangGraph 依赖检查
try:
    from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
    from langchain_core.tools import BaseTool
    from langgraph.graph import END, StateGraph
    from langgraph.prebuilt import create_react_agent
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available. LangGraphAdapter will be disabled.")


class NodeType(Enum):
    """节点类型"""
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    ACTION = "action"


@dataclass
class FlowNode:
    """Flow 节点定义"""
    id: str
    name: str
    node_type: NodeType
    handler: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowEdge:
    """Flow 边定义"""
    source: str
    target: str
    condition: Optional[Callable[[Any], bool]] = None


@dataclass
class AgentState:
    """Agent 状态定义"""
    messages: List[BaseMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    next_step: Optional[str] = None
    result: Optional[Any] = None


class StateGraphConverter:
    """将现有 Flow 节点转换为 LangGraph StateGraph"""

    def __init__(self, state_schema: Optional[type] = None):
        self.graph: Optional[StateGraph] = None
        self.nodes: Dict[str, FlowNode] = {}
        self.edges: List[FlowEdge] = []
        self.state_schema = state_schema or AgentState
        self._initialized = False

    def add_node(self, node: FlowNode) -> StateGraphConverter:
        """添加节点"""
        self.nodes[node.id] = node
        return self

    def add_edge(self, edge: FlowEdge) -> StateGraphConverter:
        """添加边"""
        self.edges.append(edge)
        return self

    def build(self) -> StateGraphConverter:
        """构建 StateGraph"""
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not available")

        self.graph = StateGraph(self.state_schema)

        # 添加节点
        for node_id, node in self.nodes.items():
            if node.handler:
                self.graph.add_node(node_id, node.handler)

        # 添加边
        for edge in self.edges:
            if edge.condition:
                self.graph.add_conditional_edges(
                    edge.source,
                    edge.condition,
                    {True: edge.target, False: END}
                )
            else:
                self.graph.add_edge(edge.source, edge.target)

        # 设置入口点
        if self.edges:
            self.graph.set_entry_point(self.edges[0].source)

        self.graph.set_finish_point(END)
        self._initialized = True
        return self

    def compile(self):
        """编译图"""
        if not self._initialized:
            self.build()
        return self.graph.compile()


class ReActAgentFactory:
    """ReAct Agent 工厂"""

    def __init__(self, llm: Any = None, tools: Optional[List[BaseTool]] = None):
        self.llm = llm
        self.tools = tools or []
        self.agent = None

    def create_react_agent(
        self,
        llm: Any,
        tools: Sequence[BaseTool],
        state_modifier: Optional[Callable[[dict], dict]] = None
    ) -> Any:
        """创建 ReAct Agent"""
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not available")

        self.llm = llm
        self.tools = list(tools)

        # 创建 agent
        self.agent = create_react_agent(llm, tools, state_modifier=state_modifier)
        return self.agent

    def run(self, input_data: str | Dict | List[BaseMessage]) -> Dict[str, Any]:
        """运行 Agent"""
        if not self.agent:
            raise RuntimeError("Agent not created. Call create_react_agent first.")

        # 转换输入
        if isinstance(input_data, str):
            input_data = {"messages": [HumanMessage(content=input_data)]}
        elif isinstance(input_data, list):
            input_data = {"messages": input_data}

        # 运行
        result = self.agent.invoke(input_data)
        return result


class LangGraphAdapter:
    """LangGraph 主适配器

    提供与 LangGraph 的无缝集成:
    - 从现有 Flow 创建 LangGraph
    - ReAct Agent 支持
    - 状态管理
    """

    def __init__(self):
        self.graph: Optional[StateGraph] = None
        self._converter = StateGraphConverter()
        self._react_factory = ReActAgentFactory()

    def create_from_flow(
        self,
        nodes: List[FlowNode],
        edges: List[FlowEdge],
        state_schema: Optional[type] = None
    ) -> StateGraph:
        """从现有 Flow 节点创建 LangGraph

        Args:
            nodes: Flow 节点列表
            edges: Flow 边列表
            state_schema: 状态模式

        Returns:
            编译后的 StateGraph
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not available")

        converter = StateGraphConverter(state_schema)

        # 添加节点
        for node in nodes:
            converter.add_node(node)

        # 添加边
        for edge in edges:
            converter.add_edge(edge)

        # 构建并编译
        converter.build()
        self.graph = converter.compile()
        return self.graph

    def create_react_agent(
        self,
        llm: Any,
        tools: List[BaseTool],
        state_modifier: Optional[Callable[[dict], dict]] = None
    ) -> Any:
        """创建 ReAct Agent

        Args:
            llm: LLM 实例
            tools: 工具列表
            state_modifier: 状态修改器

        Returns:
            ReAct Agent
        """
        return self._react_factory.create_react_agent(llm, tools, state_modifier)

    def run_agent(
        self,
        agent: Any,
        input_data: str | Dict | List[BaseMessage]
    ) -> Dict[str, Any]:
        """运行 Agent

        Args:
            agent: Agent 实例
            input_data: 输入数据

        Returns:
            运行结果
        """
        return self._react_factory.run(input_data)

    def get_graph(self) -> Optional[StateGraph]:
        """获取当前的图"""
        return self.graph


def create_simple_agent(
    llm: Any,
    tools: List[BaseTool],
    system_message: Optional[str] = None
) -> Any:
    """创建简单的 ReAct Agent

    便捷函数，用于快速创建 ReAct Agent。

    Args:
        llm: LLM 实例
        tools: 工具列表
        system_message: 系统消息

    Returns:
        ReAct Agent
    """
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph not available")

    from langgraph.prebuilt import create_react_agent

    # 构建状态修改器
    def state_modifier(state: dict) -> dict:
        if system_message:
            return {"messages": [system_message] + state.get("messages", [])}
        return state

    return create_react_agent(llm, tools, state_modifier=state_modifier)


# 向后兼容导出
__all__ = [
    "LangGraphAdapter",
    "StateGraphConverter",
    "ReActAgentFactory",
    "FlowNode",
    "FlowEdge",
    "AgentState",
    "NodeType",
    "create_simple_agent",
    "LANGGRAPH_AVAILABLE",
]
