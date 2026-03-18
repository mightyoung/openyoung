"""
LangGraph 工作流引擎

实现 PLAN → EXECUTE → CHECK → RESULT 工作流
集成事件驱动和检查点机制
"""

import logging
from typing import Any, Optional, Callable, Awaitable

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.core.langgraph_state import (
    AgentState,
    TaskPhase,
    create_initial_state,
    update_phase,
    add_message,
    set_result,
    set_error,
)
from src.core.events import Event, EventType, get_event_bus

logger = logging.getLogger(__name__)


class WorkflowNode:
    """工作流节点定义"""

    def __init__(
        self,
        name: str,
        handler: Callable[[AgentState], Awaitable[AgentState]],
        phase: TaskPhase,
    ):
        self.name = name
        self.handler = handler
        self.phase = phase


class LangGraphWorkflow:
    """LangGraph 工作流引擎

    实现标准的工作流: PLAN → EXECUTE → CHECK → RESULT
    集成事件驱动和检查点机制
    """

    def __init__(self, name: str = "agent"):
        self.name = name
        self.graph: Optional[StateGraph] = None
        self.compiled_graph = None
        self.nodes: list[WorkflowNode] = []

        # 事件总线
        self.event_bus = get_event_bus()

    def add_node(self, node: WorkflowNode) -> "LangGraphWorkflow":
        """添加节点"""
        self.nodes.append(node)
        return self

    async def plan_node(self, state: AgentState) -> AgentState:
        """计划节点 - 分析任务，制定执行计划"""
        logger.info(f"[{self.name}] Planning: {state.get('task_description', '')}")

        # 发布事件
        await self.event_bus.publish_async(Event(
            type=EventType.TASK_STARTED,
            data={
                "task_id": state.get("task_id"),
                "task_type": "planning",
                "agent_id": self.name,
            },
            metadata=state.get("metadata", {}),
        ))

        # 更新状态
        state = update_phase(state, TaskPhase.PLANNING)
        state = add_message(state, "system", "Task planning in progress...")

        # TODO: 实现实际的计划逻辑
        state["context"]["plan"] = {
            "steps": ["analyze", "execute", "verify"],
            "estimated_duration": 60,
        }

        return state

    async def execute_node(self, state: AgentState) -> AgentState:
        """执行节点 - 执行计划"""
        logger.info(f"[{self.name}] Executing...")

        # 更新状态
        state = update_phase(state, TaskPhase.EXECUTING)
        state = add_message(state, "system", "Task execution in progress...")

        # TODO: 实现实际的执行逻辑
        state["context"]["executed_steps"] = ["analyze"]

        return state

    async def check_node(self, state: AgentState) -> AgentState:
        """检查节点 - 验证执行结果"""
        logger.info(f"[{self.name}] Checking...")

        # 更新状态
        state = update_phase(state, TaskPhase.CHECKING)

        # 检查是否有错误
        if state.get("error"):
            state = update_phase(state, TaskPhase.FAILED)
            return state

        # 检查结果是否完整
        result = state.get("result", {})
        if not result:
            # 结果不完整，继续执行
            state = update_phase(state, TaskPhase.EXECUTING)

        return state

    async def result_node(self, state: AgentState) -> AgentState:
        """结果节点 - 生成最终结果"""
        logger.info(f"[{self.name}] Generating result...")

        # 更新状态
        state = update_phase(state, TaskPhase.RESULT)

        # 发布完成事件
        await self.event_bus.publish_async(Event(
            type=EventType.TASK_COMPLETED,
            data={
                "task_id": state.get("task_id"),
                "result": state.get("result", {}),
                "agent_id": self.name,
            },
            metadata=state.get("metadata", {}),
        ))

        return state

    def build(self, checkpointer: Optional[BaseCheckpointSaver] = None) -> "LangGraphWorkflow":
        """构建工作流图"""

        # 创建状态图
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("plan", self.plan_node)
        workflow.add_node("execute", self.execute_node)
        workflow.add_node("check", self.check_node)
        workflow.add_node("result", self.result_node)

        # 定义边
        workflow.add_edge("__start__", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "check")

        # 条件边: check -> execute 或 result
        workflow.add_conditional_edges(
            "check",
            self._should_continue,
            {
                "continue": "execute",
                "finish": "result",
            }
        )

        workflow.add_edge("result", END)

        # 编译图
        if checkpointer:
            self.compiled_graph = workflow.compile(checkpointer=checkpointer)
        else:
            self.compiled_graph = workflow.compile()

        self.graph = workflow

        logger.info(f"[{self.name}] Workflow graph built successfully")
        return self

    def _should_continue(self, state: AgentState) -> str:
        """决定是否继续执行"""

        phase = state.get("phase")
        error = state.get("error")

        # 如果有错误，结束
        if error:
            return "finish"

        # 如果检查阶段发现需要继续执行
        if phase == TaskPhase.CHECKING:
            result = state.get("result")
            if not result:
                return "continue"

        return "finish"

    async def run(
        self,
        task_id: str,
        task_description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentState:
        """运行工作流"""

        # 创建初始状态
        initial_state = create_initial_state(
            task_id=task_id,
            task_description=task_description,
            context=context,
        )

        if not self.compiled_graph:
            self.build()

        # 运行工作流
        logger.info(f"[{self.name}] Starting workflow for task: {task_id}")

        final_state = await self.compiled_graph.ainvoke(initial_state)

        logger.info(f"[{self.name}] Workflow completed, phase: {final_state.get('phase')}")

        return final_state


# 全局工作流实例
_default_workflow: Optional[LangGraphWorkflow] = None


def get_default_workflow() -> LangGraphWorkflow:
    """获取默认工作流"""
    global _default_workflow

    if _default_workflow is None:
        _default_workflow = LangGraphWorkflow(name="default")
        _default_workflow.build()

    return _default_workflow


async def run_agent_workflow(
    task_id: str,
    task_description: str,
    context: Optional[dict[str, Any]] = None,
) -> AgentState:
    """运行默认 Agent 工作流"""

    workflow = get_default_workflow()
    return await workflow.run(task_id, task_description, context)
