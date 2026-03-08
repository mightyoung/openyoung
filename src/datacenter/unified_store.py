"""
UnifiedStore - 统一存储层

基于 BaseStorage 实现 ExecutionRecord 的统一存储
支持 CRUD 操作和跨表查询
"""

import json
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage
from .execution_record import ExecutionRecord, ExecutionStatus


class UnifiedStore(BaseStorage):
    """统一存储层 - 执行记录"""

    def __init__(self, db_path: str = ".young/unified.db"):
        self.db_path = db_path
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库表"""
        # 执行记录主表
        self._create_table(
            "executions",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "execution_id": "TEXT UNIQUE NOT NULL",
                "run_id": "TEXT",
                "step_id": "TEXT",
                "agent_name": "TEXT",
                "task_description": "TEXT",
                "session_id": "TEXT",
                "start_time": "TIMESTAMP",
                "end_time": "TIMESTAMP",
                "duration_ms": "INTEGER DEFAULT 0",
                "prompt_tokens": "INTEGER DEFAULT 0",
                "completion_tokens": "INTEGER DEFAULT 0",
                "total_tokens": "INTEGER DEFAULT 0",
                "cost_usd": "REAL DEFAULT 0.0",
                "status": "TEXT DEFAULT 'pending'",
                "error": "TEXT",
                "metadata": "TEXT",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
            indexes=[
                ("idx_execution_id", "execution_id"),
                ("idx_run_id", "run_id"),
                ("idx_session_id", "session_id"),
                ("idx_status", "status"),
                ("idx_start_time", "start_time"),
            ]
        )

    def save(self, record: ExecutionRecord) -> str:
        """保存执行记录"""
        query = """
            INSERT OR REPLACE INTO executions (
                execution_id, run_id, step_id, agent_name, task_description,
                session_id, start_time, end_time, duration_ms,
                prompt_tokens, completion_tokens, total_tokens, cost_usd,
                status, error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self._execute(query, (
            record.execution_id,
            record.run_id,
            record.step_id,
            record.agent_name,
            record.task_description,
            record.session_id,
            record.start_time.isoformat() if record.start_time else None,
            record.end_time.isoformat() if record.end_time else None,
            record.duration_ms,
            record.prompt_tokens,
            record.completion_tokens,
            record.total_tokens,
            record.cost_usd,
            record.status,
            record.error,
            json.dumps(record.metadata, ensure_ascii=False, default=str),
        ))

        return record.execution_id

    def get(self, execution_id: str) -> ExecutionRecord | None:
        """根据 ID 获取执行记录"""
        query = "SELECT * FROM executions WHERE execution_id = ?"
        rows = self._execute(query, (execution_id,), fetch=True)

        if not rows:
            return None

        return self._row_to_record(rows[0])

    def get_by_session(self, session_id: str, limit: int = 10) -> list[ExecutionRecord]:
        """根据 session_id 查询执行记录"""
        query = """
            SELECT * FROM executions
            WHERE session_id = ?
            ORDER BY start_time DESC
            LIMIT ?
        """
        rows = self._execute(query, (session_id, limit), fetch=True)
        return [self._row_to_record(row) for row in rows]

    def get_by_run(self, run_id: str) -> list[ExecutionRecord]:
        """根据 run_id 查询执行记录（包括关联的 step）"""
        query = "SELECT * FROM executions WHERE run_id = ? OR execution_id = ? ORDER BY start_time"
        rows = self._execute(query, (run_id, run_id), fetch=True)
        return [self._row_to_record(row) for row in rows]

    def list_recent(self, limit: int = 20) -> list[ExecutionRecord]:
        """列出最近的执行记录"""
        query = "SELECT * FROM executions ORDER BY start_time DESC LIMIT ?"
        rows = self._execute(query, (limit,), fetch=True)
        return [self._row_to_record(row) for row in rows]

    def list_by_status(self, status: str, limit: int = 20) -> list[ExecutionRecord]:
        """根据状态查询执行记录"""
        query = "SELECT * FROM executions WHERE status = ? ORDER BY start_time DESC LIMIT ?"
        rows = self._execute(query, (status, limit), fetch=True)
        return [self._row_to_record(row) for row in rows]

    def update_status(self, execution_id: str, status: str, error: str = "") -> bool:
        """更新执行状态"""
        end_time = datetime.now().isoformat() if status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED] else None

        query = """
            UPDATE executions
            SET status = ?, error = ?, end_time = ?,
                duration_ms = CASE
                    WHEN end_time IS NOT NULL AND start_time IS NOT NULL
                    THEN CAST((julianday(end_time) - julianday(start_time)) * 86400000 AS INTEGER)
                    ELSE duration_ms
                END
            WHERE execution_id = ?
        """

        self._execute(query, (status, error, end_time, execution_id))
        return True

    def delete(self, execution_id: str) -> bool:
        """删除执行记录"""
        query = "DELETE FROM executions WHERE execution_id = ?"
        self._execute(query, (execution_id,))
        return True

    def count(self, status: str | None = None) -> int:
        """统计执行记录数量"""
        if status:
            query = "SELECT COUNT(*) as count FROM executions WHERE status = ?"
            rows = self._execute(query, (status,), fetch=True)
        else:
            query = "SELECT COUNT(*) as count FROM executions"
            rows = self._execute(query, fetch=True)

        return rows[0]["count"] if rows else 0

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
                SUM(duration_ms) as total_duration_ms,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost
            FROM executions
        """
        rows = self._execute(query, fetch=True)
        if not rows or rows[0]["total"] == 0:
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "running": 0,
                "total_duration_ms": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }

        row = rows[0]
        return {
            "total": row["total"] or 0,
            "success": row["success"] or 0,
            "failed": row["failed"] or 0,
            "running": row["running"] or 0,
            "total_duration_ms": row["total_duration_ms"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "total_cost": row["total_cost"] or 0.0,
        }

    def _row_to_record(self, row: dict) -> ExecutionRecord:
        """将数据库行转换为 ExecutionRecord"""
        # 解析时间
        start_time = row.get("start_time")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)

        end_time = row.get("end_time")
        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)

        # 解析 metadata
        metadata = row.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {}

        return ExecutionRecord(
            execution_id=row["execution_id"],
            run_id=row.get("run_id"),
            step_id=row.get("step_id"),
            agent_name=row.get("agent_name", ""),
            task_description=row.get("task_description", ""),
            session_id=row.get("session_id", ""),
            start_time=start_time,
            end_time=end_time,
            duration_ms=row.get("duration_ms", 0),
            prompt_tokens=row.get("prompt_tokens", 0),
            completion_tokens=row.get("completion_tokens", 0),
            total_tokens=row.get("total_tokens", 0),
            cost_usd=row.get("cost_usd", 0.0),
            status=row.get("status", "pending"),
            error=row.get("error", ""),
            metadata=metadata or {},
        )


# ========== 便捷函数 ==========

def get_unified_store(db_path: str = ".young/unified.db") -> UnifiedStore:
    """获取统一存储实例"""
    return UnifiedStore(db_path)
