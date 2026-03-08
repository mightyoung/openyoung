"""
Isolation - 数据隔离模块

从 enterprise.py 提取的多级别数据隔离功能。
"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class IsolationLevel(str, Enum):
    """隔离级别"""

    SESSION = "session"  # 会话级别
    USER = "user"  # 用户级别
    AGENT = "agent"  # Agent 级别
    GLOBAL = "global"  # 全局级别


@dataclass
class IsolationConfig:
    """隔离配置"""

    level: IsolationLevel = IsolationLevel.GLOBAL
    base_path: Path = field(default_factory=lambda: Path(".young"))
    session_id: str = ""
    user_id: str = ""
    agent_id: str = ""

    def get_isolation_path(self, path: Path = None) -> Path:
        """获取隔离路径"""
        path = path or self.base_path

        if self.level == IsolationLevel.GLOBAL:
            return path / "global"

        if self.level == IsolationLevel.AGENT and self.agent_id:
            return path / "agents" / self.agent_id

        if self.level == IsolationLevel.USER and self.user_id:
            return path / "users" / self.user_id

        if self.level == IsolationLevel.SESSION and self.session_id:
            return path / "sessions" / self.session_id

        return path


class IsolationManager:
    """隔离管理器 - 管理多级别数据隔离"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "isolation.db"
        self._init_db()

    def _init_db(self):
        """初始化隔离数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS isolation_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                user_id TEXT,
                agent_id TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS isolation_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isolation_level TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def create_isolation_dirs(
        self, level: IsolationLevel, session_id: str = "", user_id: str = "", agent_id: str = ""
    ) -> Path:
        """创建隔离目录"""
        config = IsolationConfig(
            level=level,
            base_path=self.data_dir,
            session_id=session_id,
            user_id=user_id,
            agent_id=agent_id,
        )
        path = config.get_isolation_path()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_isolation_path(
        self, level: IsolationLevel, session_id: str = "", user_id: str = "", agent_id: str = ""
    ) -> Path:
        """获取隔离路径"""
        return self.create_isolation_dirs(level, session_id, user_id, agent_id)

    def is_isolated(self, level: IsolationLevel) -> bool:
        """检查是否启用隔离"""
        return level != IsolationLevel.GLOBAL

    def save_data(
        self,
        key: str,
        data: str,
        level: IsolationLevel,
        session_id: str = "",
        user_id: str = "",
        agent_id: str = "",
    ) -> bool:
        """保存隔离数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        level_str = level.value if hasattr(level, "value") else str(level)

        cursor.execute(
            """
            INSERT INTO isolation_data (isolation_level, resource_type, resource_id, data)
            VALUES (?, ?, ?, ?)
        """,
            (level_str, key, session_id or user_id or agent_id or "global", json.dumps(data)),
        )

        conn.commit()
        conn.close()
        return True

    def load_data(
        self,
        key: str,
        level: IsolationLevel,
        session_id: str = "",
        user_id: str = "",
        agent_id: str = "",
        default: str = None,
    ) -> str:
        """加载隔离数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        level_str = level.value if hasattr(level, "value") else str(level)
        resource_id = session_id or user_id or agent_id or "global"

        cursor.execute(
            """
            SELECT data FROM isolation_data
            WHERE isolation_level = ? AND resource_type = ? AND resource_id = ?
            ORDER BY created_at DESC LIMIT 1
        """,
            (level_str, key, resource_id),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return default if default is not None else {}

    def query_data(self, level: IsolationLevel = None) -> list:
        """查询隔离数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if level:
            level_str = level.value if hasattr(level, "value") else str(level)
            cursor.execute(
                "SELECT * FROM isolation_data WHERE isolation_level = ?",
                (level_str,),
            )
        else:
            cursor.execute("SELECT * FROM isolation_data")

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "isolation_level": row[1],
                "resource_type": row[2],
                "resource_id": row[3],
                "data": json.loads(row[4]) if row[4] else None,
                "created_at": row[5],
            }
            for row in rows
        ]

    def delete_data(
        self,
        level: IsolationLevel,
        session_id: str = "",
        user_id: str = "",
        agent_id: str = "",
    ) -> int:
        """删除隔离数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        level_str = level.value if hasattr(level, "value") else str(level)
        resource_id = session_id or user_id or agent_id or "global"

        cursor.execute(
            """
            DELETE FROM isolation_data
            WHERE isolation_level = ? AND resource_id = ?
        """,
            (level_str, resource_id),
        )

        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    def get_stats(self) -> dict:
        """获取隔离统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM isolation_data")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT isolation_level, COUNT(*) FROM isolation_data GROUP BY isolation_level")
        by_level = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {"total_records": total, "by_level": by_level}


__all__ = ["IsolationLevel", "IsolationConfig", "IsolationManager"]
