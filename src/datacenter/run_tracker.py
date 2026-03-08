"""
RunTracker - Agent 运行追踪
记录 Run 级别数据采集
使用 BaseStorage 基类
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage


@dataclass
class RunRecord:
    """运行记录"""
    run_id: str
    agent_id: str
    task: str
    status: str  # running / success / failed
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration: float | None = None  # 秒
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "task": self.task,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration": self.duration,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "error": self.error,
            "metadata": self.metadata
        }


class RunTracker(BaseStorage):
    """运行追踪器"""

    def __init__(self, db_path: str = ".young/runs.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库表结构"""
        self._create_table(
            "runs",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "run_id": "TEXT NOT NULL UNIQUE",
                "agent_id": "TEXT NOT NULL",
                "task": "TEXT NOT NULL",
                "status": "TEXT NOT NULL",
                "started_at": "TEXT NOT NULL",
                "completed_at": "TEXT",
                "duration": "REAL",
                "input_tokens": "INTEGER DEFAULT 0",
                "output_tokens": "INTEGER DEFAULT 0",
                "error": "TEXT",
                "metadata": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            },
            indexes=[
                ("idx_agent", "agent_id"),
                ("idx_status", "status"),
                ("idx_started", "started_at")
            ]
        )

    def start_run(
        self,
        agent_id: str,
        task: str,
        metadata: dict = None
    ) -> str:
        """开始追踪一个运行"""
        # 输入验证
        if not agent_id or not agent_id.strip():
            raise ValueError("agent_id cannot be empty")
        if not task or not task.strip():
            raise ValueError("task cannot be empty")

        run_id = f"run_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT INTO runs (run_id, agent_id, task, status, started_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                agent_id,
                task,
                "running",
                datetime.now().isoformat(),
                self._json_serialize(metadata or {})
            )
        )

        return run_id

    def complete_run(
        self,
        run_id: str,
        status: str = "success",
        error: str = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: dict = None
    ) -> bool:
        """完成运行追踪"""
        # 计算时长
        result = self._execute(
            "SELECT started_at FROM runs WHERE run_id = ?",
            (run_id,),
            fetch=True
        )

        if not result:
            return False

        started = datetime.fromisoformat(result[0]["started_at"])
        duration = (datetime.now() - started).total_seconds()

        self._execute(
            """
            UPDATE runs
            SET status = ?, completed_at = ?, duration = ?, error = ?,
                input_tokens = ?, output_tokens = ?, metadata = ?
            WHERE run_id = ?
            """,
            (
                status,
                datetime.now().isoformat(),
                duration,
                error,
                input_tokens,
                output_tokens,
                self._json_serialize(metadata or {}),
                run_id
            )
        )

        return True

    def fail_run(self, run_id: str, error: str) -> bool:
        """标记运行失败"""
        return self.complete_run(run_id, status="failed", error=error)

    def get_run(self, run_id: str) -> dict | None:
        """获取运行记录"""
        result = self._execute(
            "SELECT * FROM runs WHERE run_id = ?",
            (run_id,),
            fetch=True
        )

        if not result:
            return None

        row = result[0]
        row["metadata"] = self._json_deserialize(row.get("metadata", "{}"))
        return row

    def list_runs(
        self,
        agent_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> list[dict]:
        """列出运行记录"""
        query = "SELECT * FROM runs"
        conditions = []
        params = []

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if status:
            conditions.append("status = ?")
            params.append(status)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        result = self._execute(query, tuple(params), fetch=True)

        runs = []
        for row in result:
            row["metadata"] = self._json_deserialize(row.get("metadata", "{}"))
            runs.append(row)

        return runs

    def get_stats(self, agent_id: str = None, days: int = 7) -> dict:
        """获取统计数据"""
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration) as avg_duration,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens
            FROM runs
            WHERE started_at >= ?
        """
        params = [start_date]

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        result = self._execute(query, tuple(params), fetch=True)

        if not result:
            return self._empty_stats()

        row = result[0]
        total = row.get("total", 0) or 0
        success = row.get("success", 0) or 0
        success_rate = success / total if total > 0 else 0

        return {
            "total_runs": total,
            "success": success,
            "failed": row.get("failed", 0) or 0,
            "success_rate": round(success_rate, 3),
            "avg_duration": round(row.get("avg_duration") or 0, 2),
            "total_input_tokens": row.get("total_input_tokens") or 0,
            "total_output_tokens": row.get("total_output_tokens") or 0
        }

    def _empty_stats(self) -> dict:
        """空统计数据"""
        return {
            "total_runs": 0,
            "success": 0,
            "failed": 0,
            "success_rate": 0.0,
            "avg_duration": 0.0,
            "total_input_tokens": 0,
            "total_output_tokens": 0
        }


# ========== 便捷函数 ==========

def get_run_tracker(db_path: str = ".young/runs.db") -> RunTracker:
    """获取运行追踪器"""
    return RunTracker(db_path)
