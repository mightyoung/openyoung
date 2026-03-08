"""
Agent Graph Builder - 基于 LangGraph 的 Agent 工作流构建器

使用 LangGraph 构建 Agent 工作流:
- DecisionNode: 决策下一步操作
- ToolNode: 工具执行
- LLMNode: LLM 调用
- EvalNode: 评估节点

参考 LangChain Agents 和 AutoGen 架构
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from src.flow.langgraph_adapter import (
    AgentState as BaseAgentState,
    FlowNode,
    FlowEdge,
    NodeType,
    LANGGRAPH_AVAILABLE,
)

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """动作类型"""
    LLM = "llm"  # 调用 LLM
    TOOL = "tool"  # 执行工具
    EVAL = "eval"  # 执行评估
    END = "end"  # 结束


@dataclass
class AgentGraphState(BaseAgentState):
    """Agent 工作流状态"""
    current_action: ActionType = ActionType.LLM
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    eval_result: Optional[Dict[str, Any]] = None
    loop_count: int = 0
    max_loops: int = 10


class NodeHandler(ABC):
    """节点处理器基类"""

    @abstractmethod
    async def process(self, state: AgentGraphState) -> AgentGraphState:
        """处理状态"""
        pass


class DecisionNodeHandler(NodeHandler):
    """决策节点处理器

    使用 LLM 决定下一步操作:
    - 调用 LLM
    - 执行工具
    - 执行评估
    - 结束
    """

    def __init__(self, llm: Any, tools: List[Any], eval_plugins: List[Any] = None):
        self.llm = llm
        self.tools = tools
        self.eval_plugins = eval_plugins or []
        self._tool_map = {t.name: t for t in tools}

    async def process(self, state: AgentGraphState) -> AgentGraphState:
        """决策下一步操作"""
        # 检查循环次数
        if state.loop_count >= state.max_loops:
            logger.warning(f"Max loops reached: {state.max_loops}")
            state.current_action = ActionType.END
            return state

        # 简单决策逻辑 (实际应该用 LLM)
        messages = state.messages

        # 检查是否需要工具调用
        if messages and hasattr(messages[-1], "tool_calls"):
            state.current_action = ActionType.TOOL
            # 获取工具调用信息
            if hasattr(messages[-1], "tool_calls"):
                tool_call = messages[-1].tool_calls[0]
                state.tool_name = tool_call.get("name")
                state.tool_input = tool_call.get("input", {})
        elif self._needs_evaluation(state):
            state.current_action = ActionType.EVAL
        else:
            state.current_action = ActionType.LLM

        state.loop_count += 1
        return state

    def _needs_evaluation(self, state: AgentGraphState) -> bool:
        """检查是否需要评估"""
        # 如果有评估插件且任务完成，则评估
        return bool(self.eval_plugins and state.result is not None)


class ToolNodeHandler(NodeHandler):
    """工具节点处理器"""

    def __init__(self, tools: List[Any]):
        self.tools = tools
        self._tool_map = {t.name: t for t in tools}

    async def process(self, state: AgentGraphState) -> AgentGraphState:
        """执行工具"""
        if not state.tool_name:
            return state

        tool = self._tool_map.get(state.tool_name)
        if not tool:
            logger.warning(f"Tool not found: {state.tool_name}")
            state.current_action = ActionType.LLM
            return state

        try:
            # 执行工具
            result = await self._execute_tool(tool, state.tool_input or {})
            state.result = result
            # 添加结果到消息
            from langchain_core.messages import ToolMessage
            state.messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=state.tool_name
                )
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            state.result = {"error": str(e)}

        # 重置工具状态，准备下一步
        state.tool_name = None
        state.tool_input = None

        return state

    async def _execute_tool(self, tool: Any, input_data: Dict[str, Any]) -> Any:
        """执行单个工具"""
        if hasattr(tool, "ainvoke"):
            return await tool.ainvoke(input_data)
        elif hasattr(tool, "invoke"):
            return tool.invoke(input_data)
        else:
            return tool(**input_data)


class LLMNodeHandler(NodeHandler):
    """LLM 调用节点处理器"""

    def __init__(self, llm: Any):
        self.llm = llm

    async def process(self, state: AgentGraphState) -> AgentGraphState:
        """调用 LLM"""
        try:
            if hasattr(self.llm, "ainvoke"):
                response = await self.ainvoke(state.messages)
            else:
                response = self.llm.invoke(state.messages)

            state.messages.append(response)
            state.result = response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            state.result = {"error": str(e)}

        return state

    async def ainvoke(self, messages: List[Any]) -> Any:
        """异步调用 LLM"""
        if hasattr(self.llm, "ainvoke"):
            return await self.llm.ainvoke(messages)
        return self.llm.invoke(messages)


class EvalNodeHandler(NodeHandler):
    """评估节点处理器"""

    def __init__(self, eval_plugins: List[Any]):
        self.eval_plugins = eval_plugins
        self._plugin_map = {p.name: p for p in eval_plugins}

    async def process(self, state: AgentGraphState) -> AgentGraphState:
        """执行评估"""
        from src.evaluation.plugins import EvalContext

        # 创建评估上下文
        context = EvalContext(
            task_description=state.context.get("task", ""),
            task_type=state.context.get("task_type", "general"),
            output_data=state.result,
        )

        # 运行所有插件
        results = []
        for plugin in self.eval_plugins:
            try:
                result = plugin.evaluate(context)
                results.append(result.to_dict())
            except Exception as e:
                logger.error(f"Plugin {plugin.name} failed: {e}")

        state.eval_result = {"results": results}
        return state


class AgentGraphBuilder:
    """Agent 工作流图构建器

    使用 LangGraph 构建可配置的 Agent 工作流。

    示例:
    ```python
    builder = AgentGraphBuilder(llm=llm, tools=tools)
    graph = builder.build()

    # 运行
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="Hello")]
    })
    ```
    """

    def __init__(
        self,
        llm: Any = None,
        tools: Optional[List[Any]] = None,
        eval_plugins: Optional[List[Any]] = None,
        max_loops: int = 10,
    ):
        self.llm = llm
        self.tools = tools or []
        self.eval_plugins = eval_plugins or []
        self.max_loops = max_loops
        self._graph = None
        self._compiled = None

        # 节点处理器
        self._decision_handler: Optional[DecisionNodeHandler] = None
        self._tool_handler: Optional[ToolNodeHandler] = None
        self._llm_handler: Optional[LLMNodeHandler] = None
        self._eval_handler: Optional[EvalNodeHandler] = None

    def build(self):
        """构建工作流图

        Returns:
            Self for chaining
        """
        if not LANGGRAPH_AVAILABLE:
            raise RuntimeError("LangGraph not available. Install langgraph package.")

        from langgraph.graph import StateGraph, END

        # 创建状态图
        self._graph = StateGraph(AgentGraphState)

        # 初始化处理器
        self._init_handlers()

        # 添加节点
        self._graph.add_node("decision", self._decision_wrapper)
        self._graph.add_node("tool", self._tool_wrapper)
        self._graph.add_node("llm", self._llm_wrapper)
        self._graph.add_node("eval", self._eval_wrapper)

        # 设置入口
        self._graph.set_entry_point("decision")

        # 条件边 - 根据决策结果路由
        self._graph.add_conditional_edges(
            "decision",
            self._route_decision,
            {
                ActionType.LLM.value: "llm",
                ActionType.TOOL.value: "tool",
                ActionType.EVAL.value: "eval",
                ActionType.END.value: END,
            }
        )

        # 边 - 执行完成后回到决策
        self._graph.add_edge("llm", "decision")
        self._graph.add_edge("tool", "decision")
        self._graph.add_edge("eval", "decision")

        return self

    def _init_handlers(self):
        """初始化节点处理器"""
        self._decision_handler = DecisionNodeHandler(
            self.llm, self.tools, self.eval_plugins
        )
        self._tool_handler = ToolNodeHandler(self.tools)
        self._llm_handler = LLMNodeHandler(self.llm)
        self._eval_handler = EvalNodeHandler(self.eval_plugins)

    def _route_decision(self, state: AgentGraphState) -> str:
        """路由决策"""
        return state.current_action.value

    async def _decision_wrapper(self, state: Dict) -> Dict:
        """决策节点包装"""
        agent_state = self._to_agent_state(state)
        result = await self._decision_handler.process(agent_state)
        return self._to_dict(result)

    async def _tool_wrapper(self, state: Dict) -> Dict:
        """工具节点包装"""
        agent_state = self._to_agent_state(state)
        result = await self._tool_handler.process(agent_state)
        return self._to_dict(result)

    async def _llm_wrapper(self, state: Dict) -> Dict:
        """LLM 节点包装"""
        agent_state = self._to_agent_state(state)
        result = await self._llm_handler.process(agent_state)
        return self._to_dict(result)

    async def _eval_wrapper(self, state: Dict) -> Dict:
        """评估节点包装"""
        agent_state = self._to_agent_state(state)
        result = await self._eval_handler.process(agent_state)
        return self._to_dict(result)

    def _to_agent_state(self, data: Dict) -> AgentGraphState:
        """转换为 AgentGraphState"""
        return AgentGraphState(
            messages=data.get("messages", []),
            context=data.get("context", {}),
            current_action=ActionType(data.get("current_action", ActionType.LLM.value)),
            tool_name=data.get("tool_name"),
            tool_input=data.get("tool_input"),
            eval_result=data.get("eval_result"),
            loop_count=data.get("loop_count", 0),
            max_loops=data.get("max_loops", self.max_loops),
        )

    def _to_dict(self, state: AgentGraphState) -> Dict:
        """转换为字典"""
        return {
            "messages": state.messages,
            "context": state.context,
            "current_action": state.current_action.value,
            "tool_name": state.tool_name,
            "tool_input": state.tool_input,
            "eval_result": state.eval_result,
            "result": state.result,
            "loop_count": state.loop_count,
            "max_loops": state.max_loops,
        }

    def compile(self):
        """编译图"""
        if not self._graph:
            self.build()
        self._compiled = self._graph.compile()
        return self._compiled

    async def ainvoke(self, input_data: Dict) -> Dict:
        """异步调用"""
        if not self._compiled:
            self.compile()

        # 确保有 max_loops
        if "max_loops" not in input_data:
            input_data["max_loops"] = self.max_loops

        return await self._compiled.ainvoke(input_data)

    def invoke(self, input_data: Dict) -> Dict:
        """同步调用"""
        if not self._compiled:
            self.compile()

        if "max_loops" not in input_data:
            input_data["max_loops"] = self.max_loops

        return self._compiled.invoke(input_data)


# 便捷函数
def create_agent_graph(
    llm: Any,
    tools: Optional[List[Any]] = None,
    eval_plugins: Optional[List[Any]] = None,
    max_loops: int = 10,
) -> AgentGraphBuilder:
    """创建 Agent 工作流图

    Args:
        llm: LLM 实例
        tools: 工具列表
        eval_plugins: 评估插件列表
        max_loops: 最大循环次数

    Returns:
        AgentGraphBuilder 实例
    """
    builder = AgentGraphBuilder(
        llm=llm,
        tools=tools,
        eval_plugins=eval_plugins,
        max_loops=max_loops,
    )
    return builder


__all__ = [
    "AgentGraphBuilder",
    "AgentGraphState",
    "ActionType",
    "NodeHandler",
    "DecisionNodeHandler",
    "ToolNodeHandler",
    "LLMNodeHandler",
    "EvalNodeHandler",
    "create_agent_graph",
]
