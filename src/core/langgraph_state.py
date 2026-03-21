"""
LangGraph 状态定义

符合 LangGraph v1.0 StateGraph 规范的 Agent 状态定义
参考: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from typing_extensions import TypedDict


class TaskPhase(str, Enum):
    """任务执行阶段"""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    CHECKING = "checking"
    RESULT = "result"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentState(TypedDict, total=False):
    """LangGraph 兼容的 Agent 状态

    使用 Annotated + add_messages 实现消息累加
    """

    # 消息历史 (自动累加)
    messages: Annotated[list[dict[str, Any]], "messages"]

    # 上下文信息
    context: dict[str, Any]

    # 当前阶段
    phase: TaskPhase

    # 检查点 ID (LangGraph 保留 checkpoint_id，改名为 checkpoint_ref)
    checkpoint_ref: Optional[str]

    # 元数据
    metadata: dict[str, Any]

    # 任务信息
    task_id: Optional[str]
    task_description: Optional[str]

    # 执行结果
    result: Optional[dict[str, Any]]

    # 评估信息
    evaluation_score: Optional[float]
    evaluation_feedback: Optional[str]
    benchmark_id: Optional[str]  # 关联的 BenchmarkTask ID
    ground_truth: Optional[dict[str, Any]]  # 期望输出/状态

    # 错误信息
    error: Optional[str]
    error_trace: Optional[str]


def create_initial_state(
    task_id: str,
    task_description: str,
    context: Optional[dict[str, Any]] = None,
    benchmark_id: Optional[str] = None,
    ground_truth: Optional[dict[str, Any]] = None,
) -> AgentState:
    """创建初始状态"""

    return AgentState(
        messages=[],
        context=context or {},
        phase=TaskPhase.IDLE,
        checkpoint_ref=None,
        metadata={
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        },
        task_id=task_id,
        task_description=task_description,
        result=None,
        evaluation_score=None,
        evaluation_feedback=None,
        benchmark_id=benchmark_id,
        ground_truth=ground_truth,
        error=None,
        error_trace=None,
    )


def update_phase(state: AgentState, phase: TaskPhase) -> AgentState:
    """更新阶段"""

    new_state = state.copy()
    new_state["phase"] = phase
    new_state["metadata"]["updated_at"] = datetime.now().isoformat()
    new_state["metadata"]["last_phase"] = phase.value

    return new_state


def add_message(state: AgentState, role: str, content: str) -> AgentState:
    """添加消息"""

    messages = state.get("messages", [])
    messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
    )

    new_state = state.copy()
    new_state["messages"] = messages

    return new_state


def set_result(state: AgentState, result: dict[str, Any]) -> AgentState:
    """设置结果"""

    new_state = state.copy()
    new_state["result"] = result
    new_state["phase"] = TaskPhase.RESULT
    new_state["metadata"]["updated_at"] = datetime.now().isoformat()

    return new_state


def set_error(state: AgentState, error: str, trace: Optional[str] = None) -> AgentState:
    """设置错误"""

    new_state = state.copy()
    new_state["error"] = error
    new_state["error_trace"] = trace
    new_state["phase"] = TaskPhase.FAILED
    new_state["metadata"]["updated_at"] = datetime.now().isoformat()

    return new_state
