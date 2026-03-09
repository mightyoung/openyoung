"""
StepRecorder - 步骤级别数据采集
记录每个关键步骤的数据
使用 BaseStorage 基类
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage


@dataclass
class StepRecord:
    """步骤记录"""

    step_id: str
    run_id: str
    step_name: str
    step_order: int
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    tool_name: str = ""
    latency_ms: int = 0
    status: str = "pending"  # pending / running / success / failed
    error: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class StepRecorder(BaseStorage):
    """步骤记录器"""

    def __init__(self, db_path: str = ".young/steps.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库"""
        self._create_table(
            "steps",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "step_id": "TEXT NOT NULL UNIQUE",
                "run_id": "TEXT NOT NULL",
                "step_name": "TEXT NOT NULL",
                "step_order": "INTEGER NOT NULL",
                "input_data": "TEXT",
                "output_data": "TEXT",
                "tool_name": "TEXT",
                "latency_ms": "INTEGER DEFAULT 0",
                "status": "TEXT DEFAULT 'pending'",
                "error": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
            indexes=[("idx_run", "run_id"), ("idx_order", "step_order")],
        )

    def start_step(
        self,
        run_id: str,
        step_name: str,
        step_order: int,
        tool_name: str = "",
        input_data: dict = None,
    ) -> str:
        """开始一个步骤"""
        # 输入验证
        if not run_id or not run_id.strip():
            raise ValueError("run_id cannot be empty")
        if not step_name or not step_name.strip():
            raise ValueError("step_name cannot be empty")
        if step_order < 0:
            raise ValueError("step_order must be non-negative")

        step_id = f"step_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT INTO steps (step_id, run_id, step_name, step_order, tool_name, input_data, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                step_id,
                run_id,
                step_name,
                step_order,
                tool_name,
                self._json_serialize(input_data or {}),
                "running",
            ),
        )

        return step_id

    def complete_step(
        self,
        step_id: str,
        status: str = "success",
        output_data: dict = None,
        latency_ms: int = 0,
        error: str = None,
    ) -> bool:
        """完成步骤"""
        self._execute(
            """
            UPDATE steps
            SET status = ?, output_data = ?, latency_ms = ?, error = ?
            WHERE step_id = ?
            """,
            (status, self._json_serialize(output_data or {}), latency_ms, error, step_id),
        )

        return True

    def fail_step(self, step_id: str, error: str) -> bool:
        """标记步骤失败"""
        return self.complete_step(step_id, status="failed", error=error)

    def get_step(self, step_id: str) -> dict | None:
        """获取步骤"""
        result = self._execute("SELECT * FROM steps WHERE step_id = ?", (step_id,), fetch=True)

        if not result:
            return None

        row = result[0]
        row["input_data"] = self._json_deserialize(row.get("input_data", "{}"))
        row["output_data"] = self._json_deserialize(row.get("output_data", "{}"))
        return row

    def list_steps(self, run_id: str) -> list[dict]:
        """列出运行的所有步骤"""
        result = self._execute(
            """
            SELECT * FROM steps
            WHERE run_id = ?
            ORDER BY step_order
            """,
            (run_id,),
            fetch=True,
        )

        steps = []
        for row in result:
            row["input_data"] = self._json_deserialize(row.get("input_data", "{}"))
            row["output_data"] = self._json_deserialize(row.get("output_data", "{}"))
            steps.append(row)

        return steps

    def get_run_summary(self, run_id: str) -> dict:
        """获取运行摘要"""
        steps = self.list_steps(run_id)

        total_latency = sum(s.get("latency_ms", 0) for s in steps)
        success_count = sum(1 for s in steps if s.get("status") == "success")
        failed_count = sum(1 for s in steps if s.get("status") == "failed")

        return {
            "run_id": run_id,
            "total_steps": len(steps),
            "success_steps": success_count,
            "failed_steps": failed_count,
            "total_latency_ms": total_latency,
            "steps": steps,
        }


# ========== 便捷函数 ==========


def get_step_recorder(db_path: str = ".young/steps.db") -> StepRecorder:
    """获取步骤记录器"""
    return StepRecorder(db_path)
