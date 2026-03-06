"""
Checkpoint - 标准 Checkpoint 接口
LangGraph 风格: SqliteSaver, CheckpointSaver Protocol
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Protocol
from datetime import datetime
from dataclasses import dataclass, field


class CheckpointSaver(Protocol):
    """标准 Checkpoint 接口 - LangGraph 风格"""

    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点"""
        ...

    def put(self, thread_id: str, state: Dict[str, Any]) -> str:
        """保存检查点"""
        ...

    def list(self, thread_id: str = None, limit: int = 10) -> List[Dict]:
        """列出检查点"""
        ...

    def delete(self, thread_id: str) -> bool:
        """删除检查点"""
        ...


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    thread_id: str
    state: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SqliteCheckpointSaver:
    """SQLite 检查点存储 - LangGraph 风格"""

    def __init__(self, db_path: str = ".young/checkpoints.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                checkpoint_id TEXT NOT NULL,
                state TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread ON checkpoints(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created ON checkpoints(created_at)")

        conn.commit()
        conn.close()

    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取最新检查点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, state, metadata, created_at
            FROM checkpoints
            WHERE thread_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (thread_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "checkpoint_id": row[0],
            "state": json.loads(row[1]),
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3]
        }

    def put(self, thread_id: str, state: Dict[str, Any], metadata: Dict = None) -> str:
        """保存检查点"""
        import uuid

        checkpoint_id = f"{thread_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO checkpoints (thread_id, checkpoint_id, state, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            thread_id,
            checkpoint_id,
            json.dumps(state, ensure_ascii=False, default=str),
            json.dumps(metadata or {}, default=str)
        ))

        conn.commit()
        conn.close()

        return checkpoint_id

    def list(self, thread_id: str = None, limit: int = 10) -> List[Dict]:
        """列出检查点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if thread_id:
            cursor.execute("""
                SELECT checkpoint_id, thread_id, state, metadata, created_at
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (thread_id, limit))
        else:
            cursor.execute("""
                SELECT checkpoint_id, thread_id, state, metadata, created_at
                FROM checkpoints
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "checkpoint_id": row[0],
                "thread_id": row[1],
                "state": json.loads(row[2]),
                "metadata": json.loads(row[3]) if row[3] else {},
                "created_at": row[4]
            }
            for row in rows
        ]

    def delete(self, thread_id: str) -> bool:
        """删除检查点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))

        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count > 0

    def get_by_id(self, checkpoint_id: str) -> Optional[Dict]:
        """根据 ID 获取检查点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT checkpoint_id, thread_id, state, metadata, created_at
            FROM checkpoints
            WHERE checkpoint_id = ?
        """, (checkpoint_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "checkpoint_id": row[0],
            "thread_id": row[1],
            "state": json.loads(row[2]),
            "metadata": json.loads(row[3]) if row[3] else {},
            "created_at": row[4]
        }

    def get_thread_count(self, thread_id: str) -> int:
        """获取线程的检查点数量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (thread_id,))
        count = cursor.fetchone()[0]
        conn.close()

        return count


# ========== 便捷函数 ==========

def get_checkpoint_saver(db_path: str = ".young/checkpoints.db") -> SqliteCheckpointSaver:
    """获取检查点存储"""
    return SqliteCheckpointSaver(db_path)
