"""
统一执行记录模型 - R2-3 DataCenter 存储统一

提供 ExecutionRecord 作为统一的数据模型，替代分散的 TraceRecord, RunRecord, StepRecord
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ExecutionStatus:
    """执行状态常量"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ExecutionRecord:
    """统一的执行记录模型

    整合 TraceRecord, RunRecord, StepRecord 为单一模型
    支持层级追溯: execution → run → step
    """

    # 层级标识
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str | None = None
    step_id: str | None = None

    # 基本信息
    agent_name: str = ""
    task_description: str = ""
    session_id: str = ""

    # 时间
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_ms: int = 0

    # Token 统计
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    # 状态
    status: str = ExecutionStatus.PENDING
    error: str = ""

    # 扩展字段
    metadata: dict[str, Any] = field(default_factory=dict)

    # 子记录 (可选，用于完整记录)
    steps: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "execution_id": self.execution_id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
            "steps": self.steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionRecord":
        """从字典创建"""
        # 处理时间字段
        start_time = data.get("start_time")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)

        end_time = data.get("end_time")
        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        return cls(
            execution_id=data.get("execution_id", str(uuid.uuid4())),
            run_id=data.get("run_id"),
            step_id=data.get("step_id"),
            agent_name=data.get("agent_name", ""),
            task_description=data.get("task_description", ""),
            session_id=data.get("session_id", ""),
            start_time=start_time or datetime.now(),
            end_time=end_time,
            duration_ms=data.get("duration_ms", 0),
            prompt_tokens=data.get("prompt_tokens", 0),
            completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            cost_usd=data.get("cost_usd", 0.0),
            status=data.get("status", ExecutionStatus.PENDING),
            error=data.get("error", ""),
            metadata=data.get("metadata", {}),
            steps=data.get("steps", []),
        )

    def mark_running(self):
        """标记为运行中"""
        self.status = ExecutionStatus.RUNNING

    def mark_success(self):
        """标记为成功"""
        self.status = ExecutionStatus.SUCCESS
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

    def mark_failed(self, error: str = ""):
        """标记为失败"""
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_ms = int((self.end_time - self.start_time).total_seconds() * 1000)

    def add_step(self, step: dict[str, Any]):
        """添加步骤记录"""
        if self.steps is None:
            self.steps = []
        self.steps.append(step)


class RecordAdapter:
    """记录适配器 - 兼容现有模型"""

    @staticmethod
    def from_trace(record) -> ExecutionRecord:
        """从 TraceRecord 转换"""
        return ExecutionRecord(
            execution_id=record.session_id,
            session_id=record.session_id,
            agent_name=record.agent_name,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_ms=record.duration_ms,
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            total_tokens=record.total_tokens,
            cost_usd=record.cost_usd,
            status=record.status.value if hasattr(record.status, "value") else str(record.status),
            error=record.error,
            metadata=record.metadata,
        )

    @staticmethod
    def from_run(record) -> ExecutionRecord:
        """从 RunRecord 转换"""
        duration = record.duration or 0
        return ExecutionRecord(
            execution_id=record.run_id,
            run_id=record.run_id,
            session_id=record.agent_id,
            task_description=record.task,
            start_time=record.started_at,
            end_time=record.completed_at,
            duration_ms=int(duration * 1000) if duration else 0,
            prompt_tokens=record.input_tokens,
            completion_tokens=record.output_tokens,
            total_tokens=record.input_tokens + record.output_tokens,
            status=record.status,
            error=record.error or "",
            metadata=record.metadata,
        )

    @staticmethod
    def from_step(record) -> ExecutionRecord:
        """从 StepRecord 转换"""
        return ExecutionRecord(
            execution_id=record.run_id,
            run_id=record.run_id,
            step_id=record.step_id,
            task_description=record.step_name,
            start_time=record.created_at,
            duration_ms=record.latency_ms,
            status=record.status,
            error=record.error,
            metadata={"step_order": record.step_order, "tool_name": record.tool_name},
        )
