"""
Experience Store - 经验存储

使用 SQLite 持久化经验数据。
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Experience, TaskCategory


class ExperienceStore:
    """经验存储"""

    def __init__(self, db_path: str = "data/experiences.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._lock = asyncio.Lock()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 经验表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                task_category TEXT NOT NULL,
                task_description TEXT NOT NULL,
                states_json TEXT,
                actions_json TEXT,
                success INTEGER NOT NULL,
                evaluation_score REAL,
                completion_rate REAL,
                duration_ms INTEGER,
                token_count INTEGER,
                tool_call_count INTEGER,
                error_count INTEGER,
                rewards_json TEXT,
                embedding_json TEXT,
                created_at TEXT NOT NULL
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_category ON experiences(task_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_success ON experiences(success)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON experiences(created_at)")

        # 统计表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_tasks INTEGER,
                success_count INTEGER,
                avg_score REAL,
                avg_reward REAL,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    async def save(self, experience: Experience):
        """保存经验"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT OR REPLACE INTO experiences (
                    id, task_id, task_category, task_description,
                    states_json, actions_json, success,
                    evaluation_score, completion_rate, duration_ms,
                    token_count, tool_call_count, error_count,
                    rewards_json, embedding_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    experience.id,
                    experience.task_id,
                    experience.task_category.value,
                    experience.task_description,
                    json.dumps([s.to_dict() for s in experience.states]),
                    json.dumps([a.to_dict() for a in experience.actions]),
                    1 if experience.success else 0,
                    experience.evaluation_score,
                    experience.completion_rate,
                    experience.duration_ms,
                    experience.token_count,
                    experience.tool_call_count,
                    experience.error_count,
                    json.dumps(experience.rewards),
                    json.dumps(experience.embedding) if experience.embedding else None,
                    experience.created_at.isoformat(),
                ),
            )

            conn.commit()
            conn.close()

    async def get(self, experience_id: str) -> Optional[Experience]:
        """获取单条经验"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM experiences WHERE id = ?", (experience_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_experience(row)

    async def query(
        self,
        task_category: Optional[TaskCategory] = None,
        success: Optional[bool] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
    ) -> List[Experience]:
        """查询经验"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM experiences WHERE 1=1"
        params = []

        if task_category:
            query += " AND task_category = ?"
            params.append(task_category.value)

        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)

        if min_score is not None:
            query += " AND evaluation_score >= ?"
            params.append(min_score)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_experience(row) for row in rows]

    async def get_recent_failures(self, limit: int = 10) -> List[Experience]:
        """获取最近的失败经验"""
        return await self.query(success=False, limit=limit)

    async def get_successful_patterns(
        self, task_category: TaskCategory, limit: int = 10
    ) -> List[Experience]:
        """获取成功模式"""
        return await self.query(task_category=task_category, success=True, limit=limit)

    async def update_stats(self):
        """更新统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            """
            INSERT INTO learning_stats (
                date, total_tasks, success_count, avg_score, avg_reward, created_at
            )
            SELECT
                ?,
                COUNT(*),
                SUM(success),
                AVG(evaluation_score),
                AVG(json_extract(rewards_json, '$.total')),
                ?
            FROM experiences
            WHERE date(created_at) = ?
        """,
            (today, datetime.now().isoformat(), today),
        )

        conn.commit()
        conn.close()

    def _row_to_experience(self, row) -> Experience:
        """行转经验对象"""
        return Experience(
            id=row["id"],
            task_id=row["task_id"],
            task_category=TaskCategory(row["task_category"]),
            task_description=row["task_description"],
            states=[],  # 简化处理
            actions=[],  # 简化处理
            success=bool(row["success"]),
            evaluation_score=row["evaluation_score"] or 0.0,
            completion_rate=row["completion_rate"] or 0.0,
            duration_ms=row["duration_ms"] or 0,
            token_count=row["token_count"] or 0,
            tool_call_count=row["tool_call_count"] or 0,
            error_count=row["error_count"] or 0,
            rewards=json.loads(row["rewards_json"]) if row["rewards_json"] else {},
            embedding=json.loads(row["embedding_json"]) if row["embedding_json"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
