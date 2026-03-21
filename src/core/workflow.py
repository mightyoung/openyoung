"""
LangGraph 工作流引擎

实现 PLAN → EXECUTE → CHECK → RESULT 工作流
集成事件驱动和检查点机制

参考:
- LangGraph: https://langchain-ai.github.io/langgraph/
- 最佳实践: https://langchain-ai.github.io/langgraph/concepts/low_level/
"""

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Any, AsyncGenerator, Awaitable, Callable, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph

from src.core.events import Event, EventType, get_event_bus
from src.core.langgraph_state import (
    AgentState,
    TaskPhase,
    add_message,
    create_initial_state,
    set_error,
    set_result,
    update_phase,
)

logger = logging.getLogger(__name__)


# ====================
# Workflow Configuration
# ====================


class WorkflowConfig:
    """工作流配置"""

    def __init__(
        self,
        max_iterations: int = 10,
        max_plan_duration: float = 60.0,
        max_execute_duration: float = 300.0,
        enable_checkpoint: bool = True,
        checkpoint_interval: int = 5,
    ):
        self.max_iterations = max_iterations
        self.max_plan_duration = max_plan_duration
        self.max_execute_duration = max_execute_duration
        self.enable_checkpoint = enable_checkpoint
        self.checkpoint_interval = checkpoint_interval


# ====================
# Workflow Node Implementation
# ====================


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

    支持:
    - 事件发布/订阅
    - 检查点保存与恢复
    - 流式输出
    - 错误处理与恢复
    """

    def __init__(
        self,
        name: str = "agent",
        config: Optional[WorkflowConfig] = None,
    ):
        self.name = name
        self.config = config or WorkflowConfig()
        self.graph: Optional[StateGraph] = None
        self.compiled_graph = None
        self.nodes: list[WorkflowNode] = []
        self._checkpoint_manager = None
        self._iteration_count = 0

        # 事件总线
        self.event_bus = get_event_bus()

    def add_node(self, node: WorkflowNode) -> "LangGraphWorkflow":
        """添加节点"""
        self.nodes.append(node)
        return self

    def _create_event(self, event_type: EventType, state: AgentState, extra_data: dict = None) -> Event:
        """创建事件"""
        data = {
            "task_id": state.get("task_id"),
            "agent_id": self.name,
            "phase": state.get("phase", TaskPhase.IDLE).value,
            **(extra_data or {}),
        }
        return Event(
            type=event_type,
            data=data,
            metadata=state.get("metadata", {}),
        )

    async def _save_checkpoint(self, state: AgentState, is_final: bool = False) -> None:
        """保存检查点"""
        if not self.config.enable_checkpoint:
            return

        try:
            if self._checkpoint_manager is None:
                from src.core.agent_checkpoint import get_checkpoint_manager
                self._checkpoint_manager = await get_checkpoint_manager()

            await self._checkpoint_manager.save(
                agent_id=self.name,
                task_id=state.get("task_id", "unknown"),
                state=dict(state),
                metadata={
                    "phase": state.get("phase", TaskPhase.IDLE).value,
                    "iteration": self._iteration_count,
                    "is_final": is_final,
                    "timestamp": datetime.now().isoformat(),
                },
                is_final=is_final,
            )
            logger.debug(f"[{self.name}] Checkpoint saved for task {state.get('task_id')}")
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to save checkpoint: {e}")

    async def plan_node(self, state: AgentState) -> AgentState:
        """计划节点 - 分析任务，制定执行计划

        职责:
        1. 发布 TASK_STARTED 事件
        2. 分析任务描述
        3. 生成执行计划
        4. 保存检查点
        """
        task_id = state.get("task_id", "unknown")
        task_desc = state.get("task_description", "")

        logger.info(f"[{self.name}] Planning: {task_desc}")

        # 发布任务开始事件
        try:
            await self.event_bus.publish_async(self._create_event(
                EventType.TASK_STARTED,
                state,
                {"task_type": "planning"},
            ))
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to publish TASK_STARTED event: {e}")

        # 更新状态
        state = update_phase(state, TaskPhase.PLANNING)
        state = add_message(state, "system", f"Planning: analyzing '{task_desc}'")

        # 分析任务并生成计划
        try:
            plan = self._generate_plan(task_desc, state.get("context", {}))
            state["context"]["plan"] = plan
            state["context"]["plan_steps"] = plan.get("steps", [])
            state["context"]["current_step"] = 0
            state = add_message(state, "system", f"Plan generated: {plan.get('steps', [])}")
        except Exception as e:
            logger.error(f"[{self.name}] Plan generation failed: {e}")
            state = set_error(state, f"Plan generation failed: {str(e)}", traceback.format_exc())
            return state

        # 保存检查点
        await self._save_checkpoint(state)

        return state

    def _generate_plan(self, task_description: str, context: dict) -> dict:
        """生成执行计划

        基于任务描述生成结构化的执行计划。
        支持重规划场景。
        """
        # 简单启发式计划生成
        # 在实际实现中可以集成 LLM 进行更智能的规划

        steps = []
        task_lower = task_description.lower()

        # 基于关键词识别任务类型
        if any(kw in task_lower for kw in ["write", "create", "generate", "implement"]):
            steps.append({"action": "analyze", "description": "Analyze requirements"})
            steps.append({"action": "implement", "description": "Implement solution"})
            steps.append({"action": "verify", "description": "Verify implementation"})

        elif any(kw in task_lower for kw in ["fix", "bug", "error", "issue"]):
            steps.append({"action": "identify", "description": "Identify root cause"})
            steps.append({"action": "fix", "description": "Apply fix"})
            steps.append({"action": "test", "description": "Test fix"})

        elif any(kw in task_lower for kw in ["test", "testing"]):
            steps.append({"action": "prepare", "description": "Prepare test cases"})
            steps.append({"action": "run", "description": "Run tests"})
            steps.append({"action": "report", "description": "Generate test report"})

        elif any(kw in task_lower for kw in ["review", "analyze", "assess"]):
            steps.append({"action": "collect", "description": "Collect information"})
            steps.append({"action": "analyze", "description": "Perform analysis"})
            steps.append({"action": "summarize", "description": "Summarize findings"})

        else:
            # 默认计划
            steps = [
                {"action": "analyze", "description": "Analyze task"},
                {"action": "execute", "description": "Execute task"},
                {"action": "verify", "description": "Verify result"},
            ]

        # 检查是否需要重规划
        if context.get("replan_reason"):
            # 添加重规划步骤
            steps.insert(0, {"action": "replan", "description": f"Replanning: {context['replan_reason']}"})

        return {
            "steps": steps,
            "estimated_duration": len(steps) * 60,  # 假设每步1分钟
            "task_type": self._classify_task(task_description),
        }

    def _classify_task(self, task_description: str) -> str:
        """分类任务类型"""
        task_lower = task_description.lower()
        if any(kw in task_lower for kw in ["write", "create", "generate"]):
            return "code_generation"
        elif any(kw in task_lower for kw in ["fix", "bug"]):
            return "bug_fix"
        elif any(kw in task_lower for kw in ["test"]):
            return "testing"
        elif any(kw in task_lower for kw in ["review", "analyze"]):
            return "analysis"
        return "general"

    async def execute_node(self, state: AgentState) -> AgentState:
        """执行节点 - 执行计划中的步骤

        职责:
        1. 发布 TOOL_EXECUTED 事件
        2. 执行当前步骤
        3. 更新执行上下文
        4. 保存检查点
        """
        logger.info(f"[{self.name}] Executing...")

        # 发布执行开始事件
        try:
            await self.event_bus.publish_async(self._create_event(
                EventType.AGENT_STARTED,
                state,
                {"task_type": "execution"},
            ))
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to publish AGENT_STARTED event: {e}")

        # 更新状态
        state = update_phase(state, TaskPhase.EXECUTING)

        plan_steps = state.get("context", {}).get("plan_steps", [])
        current_step = state.get("context", {}).get("current_step", 0)
        executed_steps = state.get("context", {}).get("executed_steps", [])

        if current_step >= len(plan_steps):
            # 计划已完成，生成结果
            state["context"]["executed_steps"] = executed_steps
            state = add_message(state, "system", "All plan steps completed")
            state = set_result(state, {
                "status": "completed",
                "steps_executed": len(executed_steps),
                "output": f"Completed {len(executed_steps)} steps",
            })
            return state

        # 执行当前步骤
        current_step_data = plan_steps[current_step]
        step_action = current_step_data.get("action", "unknown")
        step_desc = current_step_data.get("description", "")

        logger.info(f"[{self.name}] Executing step {current_step + 1}/{len(plan_steps)}: {step_action}")

        state = add_message(state, "system", f"Executing: {step_desc}")
        executed_steps.append({
            "step": current_step,
            "action": step_action,
            "description": step_desc,
            "timestamp": datetime.now().isoformat(),
        })
        state["context"]["executed_steps"] = executed_steps
        state["context"]["current_step"] = current_step + 1
        state["context"]["last_action"] = step_action

        # 发布工具执行事件
        try:
            await self.event_bus.publish_async(self._create_event(
                EventType.TOOL_EXECUTED,
                state,
                {"tool": step_action, "step": current_step},
            ))
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to publish TOOL_EXECUTED event: {e}")

        # 迭代计数
        self._iteration_count += 1

        # 检查是否超过最大迭代次数
        if self._iteration_count >= self.config.max_iterations:
            logger.warning(f"[{self.name}] Max iterations ({self.config.max_iterations}) reached")
            state = set_error(state, f"Max iterations ({self.config.max_iterations}) reached")
            return state

        # 定期保存检查点
        if self.config.enable_checkpoint and self._iteration_count % self.config.checkpoint_interval == 0:
            await self._save_checkpoint(state)

        return state

    async def check_node(self, state: AgentState) -> AgentState:
        """检查节点 - 验证执行结果

        职责:
        1. 检查是否有错误
        2. 验证结果是否完整
        3. 决定是否继续执行或完成
        4. 发布相应事件
        """
        logger.info(f"[{self.name}] Checking...")

        # 更新状态
        state = update_phase(state, TaskPhase.CHECKING)

        # 检查是否有错误
        error = state.get("error")
        if error:
            logger.error(f"[{self.name}] Error detected: {error}")

            # 发布错误事件
            try:
                await self.event_bus.publish_async(self._create_event(
                    EventType.ERROR_OCCURRED,
                    state,
                    {"error": error, "recoverable": False},
                ))
            except Exception as e:
                logger.warning(f"[{self.name}] Failed to publish ERROR_OCCURRED event: {e}")

            state = update_phase(state, TaskPhase.FAILED)
            return state

        # 检查计划是否完成
        plan_steps = state.get("context", {}).get("plan_steps", [])
        current_step = state.get("context", {}).get("current_step", 0)

        if current_step >= len(plan_steps):
            # 所有步骤已完成，标记为完成
            state = update_phase(state, TaskPhase.COMPLETED)
            state = add_message(state, "system", "All plan steps verified successfully")

            # 设置最终结果
            executed_steps = state.get("context", {}).get("executed_steps", [])
            state = set_result(state, {
                "status": "success",
                "steps_completed": len(executed_steps),
                "all_steps": plan_steps,
            })
            logger.info(f"[{self.name}] Task completed successfully with {len(executed_steps)} steps")
        else:
            # 还有步骤未执行，继续
            state = add_message(state, "system", f"Step {current_step}/{len(plan_steps)} completed, continuing...")

        return state

    async def result_node(self, state: AgentState) -> AgentState:
        """结果节点 - 生成最终结果

        职责:
        1. 发布 TASK_COMPLETED 事件
        2. 生成最终结果
        3. 保存最终检查点
        """
        logger.info(f"[{self.name}] Generating result...")

        # 更新状态
        state = update_phase(state, TaskPhase.RESULT)

        # 确保有结果
        if not state.get("result"):
            executed_steps = state.get("context", {}).get("executed_steps", [])
            state = set_result(state, {
                "status": "completed",
                "steps_executed": len(executed_steps),
                "message": "Workflow completed",
            })

        # 发布完成事件
        try:
            await self.event_bus.publish_async(self._create_event(
                EventType.TASK_COMPLETED,
                state,
                {"result": state.get("result", {})},
            ))
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to publish TASK_COMPLETED event: {e}")

        # 保存最终检查点
        await self._save_checkpoint(state, is_final=True)

        state = add_message(state, "system", "Workflow result generated")
        logger.info(f"[{self.name}] Workflow completed, result: {state.get('result')}")

        return state

    def build(self, checkpointer: Optional[BaseCheckpointSaver] = None) -> "LangGraphWorkflow":
        """构建工作流图

        使用 LangGraph StateGraph 构建工作流。
        边定义:
        - __start__ -> plan
        - plan -> execute
        - execute -> check
        - check (conditional) -> execute 或 result
        - result -> END
        """
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
            },
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
        """决定是否继续执行

        路由逻辑:
        - 如果有错误 -> finish
        - 如果 phase 是 COMPLETED -> finish
        - 如果还有步骤未执行 -> continue
        - 否则 -> finish
        """
        error = state.get("error")
        if error:
            return "finish"

        phase = state.get("phase")
        if phase == TaskPhase.COMPLETED or phase == TaskPhase.FAILED:
            return "finish"

        # 检查是否还有步骤未执行
        plan_steps = state.get("context", {}).get("plan_steps", [])
        current_step = state.get("context", {}).get("current_step", 0)

        if current_step < len(plan_steps):
            return "continue"

        return "finish"

    async def run(
        self,
        task_id: str,
        task_description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AgentState:
        """运行工作流

        Args:
            task_id: 任务 ID
            task_description: 任务描述
            context: 可选的初始上下文

        Returns:
            最终的 AgentState
        """
        # 创建初始状态
        initial_state = create_initial_state(
            task_id=task_id,
            task_description=task_description,
            context=context,
        )

        if not self.compiled_graph:
            self.build()

        # 重置迭代计数
        self._iteration_count = 0

        # 运行工作流
        logger.info(f"[{self.name}] Starting workflow for task: {task_id}")

        try:
            final_state = await self.compiled_graph.ainvoke(initial_state)
            logger.info(f"[{self.name}] Workflow completed, phase: {final_state.get('phase')}")
            return final_state

        except Exception as e:
            logger.error(f"[{self.name}] Workflow execution failed: {e}")
            error_state = set_error(initial_state, str(e), traceback.format_exc())
            return error_state

    async def run_streaming(
        self,
        task_id: str,
        task_description: str,
        context: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[AgentState, None]:
        """流式运行工作流

        在每个阶段完成后 yield 状态更新。

        Args:
            task_id: 任务 ID
            task_description: 任务描述
            context: 可选的初始上下文

        Yields:
            每个阶段完成后的 AgentState
        """
        # 创建初始状态
        initial_state = create_initial_state(
            task_id=task_id,
            task_description=task_description,
            context=context,
        )

        if not self.compiled_graph:
            self.build()

        # 重置迭代计数
        self._iteration_count = 0

        logger.info(f"[{self.name}] Starting streaming workflow for task: {task_id}")

        # 使用 astream 方法进行流式执行
        async for state_update in self.compiled_graph.astream(initial_state):
            # yield 每个状态更新
            yield state_update

            # 检查是否是最终状态
            if isinstance(state_update, dict) and state_update.get("phase") in (
                TaskPhase.COMPLETED,
                TaskPhase.FAILED,
                TaskPhase.RESULT,
            ):
                break


# ====================
# Convenience Functions
# ====================

# 全局工作流实例
_default_workflow: Optional[LangGraphWorkflow] = None


def get_default_workflow() -> LangGraphWorkflow:
    """获取默认工作流

    线程安全地获取或创建全局默认工作流实例。
    """
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
    """运行默认 Agent 工作流

    这是一个便捷函数，用于快速运行默认工作流。

    Args:
        task_id: 任务 ID
        task_description: 任务描述
        context: 可选的初始上下文

    Returns:
        最终的 AgentState
    """
    workflow = get_default_workflow()
    return await workflow.run(task_id, task_description, context)
