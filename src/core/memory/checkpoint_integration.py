"""
Checkpoint 与 LangGraph State 集成

提供:
- AgentState <-> Checkpoint 相互转换
- 自动保存/恢复工作流
"""

import logging
from typing import Any, Optional

from src.core.agent_checkpoint import (
    AgentCheckpoint,
    AgentCheckpointManager,
    get_checkpoint_manager,
)
from src.core.langgraph_state import AgentState, TaskPhase, create_initial_state

logger = logging.getLogger(__name__)


def agent_state_to_checkpoint_state(state: AgentState) -> dict[str, Any]:
    """将 AgentState 转换为 Checkpoint 格式

    Args:
        state: LangGraph AgentState

    Returns:
        可序列化的字典
    """
    return {
        "messages": state.get("messages", []),
        "context": state.get("context", {}),
        "phase": state.get("phase", TaskPhase.IDLE).value
        if isinstance(state.get("phase"), TaskPhase)
        else state.get("phase", "idle"),
        "checkpoint_ref": state.get("checkpoint_ref"),
        "metadata": state.get("metadata", {}),
        "task_id": state.get("task_id"),
        "task_description": state.get("task_description"),
        "result": state.get("result"),
        "evaluation_score": state.get("evaluation_score"),
        "evaluation_feedback": state.get("evaluation_feedback"),
        "error": state.get("error"),
        "error_trace": state.get("error_trace"),
    }


def checkpoint_state_to_agent_state(state: dict[str, Any]) -> AgentState:
    """将 Checkpoint 状态转换为 AgentState

    Args:
        state: 从数据库加载的字典

    Returns:
        LangGraph AgentState
    """
    # 处理 phase 转换
    phase = state.get("phase", "idle")
    if isinstance(phase, str):
        try:
            phase = TaskPhase(phase)
        except ValueError:
            phase = TaskPhase.IDLE

    # 构建 AgentState
    agent_state = AgentState(
        messages=state.get("messages", []),
        context=state.get("context", {}),
        phase=phase,
        checkpoint_ref=state.get("checkpoint_ref"),
        metadata=state.get("metadata", {}),
        task_id=state.get("task_id"),
        task_description=state.get("task_description"),
        result=state.get("result"),
        evaluation_score=state.get("evaluation_score"),
        evaluation_feedback=state.get("evaluation_feedback"),
        error=state.get("error"),
        error_trace=state.get("error_trace"),
    )

    return agent_state


async def save_agent_state(
    agent_id: str,
    task_id: str,
    state: AgentState,
    event_history: Optional[list[dict]] = None,
    metadata: Optional[dict[str, Any]] = None,
    is_final: bool = False,
) -> str:
    """保存 Agent 状态到 Checkpoint

    Args:
        agent_id: Agent ID
        task_id: 任务 ID
        state: LangGraph AgentState
        event_history: 事件历史
        metadata: 元数据
        is_final: 是否为最终检查点

    Returns:
        checkpoint_id
    """
    checkpoint_mgr = await get_checkpoint_manager()

    # 转换状态
    checkpoint_state = agent_state_to_checkpoint_state(state)

    # 保存
    checkpoint_id = await checkpoint_mgr.save(
        agent_id=agent_id,
        task_id=task_id,
        state=checkpoint_state,
        event_history=event_history or [],
        metadata=metadata or {},
        is_final=is_final,
    )

    logger.info(f"Saved agent state checkpoint: {checkpoint_id}")
    return checkpoint_id


async def load_agent_state(
    checkpoint_id: str,
) -> Optional[AgentState]:
    """从 Checkpoint 加载 Agent 状态

    Args:
        checkpoint_id: Checkpoint ID

    Returns:
        AgentState 或 None
    """
    checkpoint_mgr = await get_checkpoint_manager()

    checkpoint = await checkpoint_mgr.get(checkpoint_id)
    if not checkpoint:
        logger.warning(f"Checkpoint not found: {checkpoint_id}")
        return None

    # 转换状态
    return checkpoint_state_to_agent_state(checkpoint.state)


async def restore_from_latest(
    agent_id: str,
    task_id: Optional[str] = None,
) -> Optional[AgentState]:
    """从最新检查点恢复状态

    Args:
        agent_id: Agent ID
        task_id: 任务 ID (可选)

    Returns:
        AgentState 或 None
    """
    checkpoint_mgr = await get_checkpoint_manager()

    checkpoint = await checkpoint_mgr.get_latest(agent_id, task_id)
    if not checkpoint:
        logger.warning(f"No checkpoint found for agent {agent_id}, task {task_id}")
        return None

    logger.info(f"Restored from checkpoint: {checkpoint.id}")
    return checkpoint_state_to_agent_state(checkpoint.state)


# ====================
# 工作流集成
# ====================


class CheckpointWorkflowMixin:
    """将 Checkpoint 功能集成到 LangGraph Workflow

    用法:
        class MyWorkflow(CheckpointWorkflowMixin, LangGraphWorkflow):
            pass
    """

    async def save_checkpoint(
        self,
        agent_id: str,
        task_id: str,
        state: AgentState,
    ) -> str:
        """保存检查点"""
        return await save_agent_state(agent_id, task_id, state)

    async def restore_checkpoint(
        self,
        checkpoint_id: str,
    ) -> Optional[AgentState]:
        """恢复检查点"""
        return await load_agent_state(checkpoint_id)

    async def restore_latest(
        self,
        agent_id: str,
        task_id: Optional[str] = None,
    ) -> Optional[AgentState]:
        """从最新检查点恢复"""
        return await restore_from_latest(agent_id, task_id)
