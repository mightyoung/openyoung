"""
Isolation Manager - 多级别数据隔离控制
支持：Session / User / Agent / Global 隔离级别
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .models import IsolationLevel


@dataclass
class IsolationConfig:
    """隔离配置"""
    level: IsolationLevel = IsolationLevel.SESSION

    # 路径配置
    base_path: Path = field(default_factory=lambda: Path(".young"))

    # 隔离标识
    session_id: str = ""
    user_id: str = ""
    agent_id: str = ""

    def get_isolation_path(self) -> Path:
        """获取隔离路径"""
        path = self.base_path

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

        # SQLite 数据库路径
        self.db_path = self.data_dir / "isolation.db"
        self._init_db()

    def _init_db(self):
        """初始化隔离数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 隔离策略表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS isolation_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                user_id TEXT,
                agent_id TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)

        # 隔离数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS isolation_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isolation_key TEXT NOT NULL,
                level TEXT NOT NULL,
                user_id TEXT,
                agent_id TEXT,
                session_id TEXT,
                data_type TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iso_key ON isolation_data(isolation_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iso_level ON isolation_data(level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iso_user ON isolation_data(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iso_agent ON isolation_data(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iso_session ON isolation_data(session_id)")

        conn.commit()
        conn.close()

    def get_isolation_key(
        self,
        level: IsolationLevel,
        user_id: str = "",
        agent_id: str = "",
        session_id: str = ""
    ) -> str:
        """生成隔离键"""
        if level == IsolationLevel.GLOBAL:
            return "global"

        if level == IsolationLevel.AGENT:
            return f"agent:{agent_id}"

        if level == IsolationLevel.USER:
            return f"user:{user_id}"

        if level == IsolationLevel.SESSION:
            return f"session:{session_id}"

        return "global"

    def save_data(
        self,
        key: str,
        data: Any,
        level: IsolationLevel,
        data_type: str = "json",
        user_id: str = "",
        agent_id: str = "",
        session_id: str = ""
    ):
        """保存隔离数据"""
        isolation_key = self.get_isolation_key(level, user_id, agent_id, session_id)

        # 序列化数据
        if data_type == "json":
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            data_str = str(data)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO isolation_data (
                isolation_key, level, user_id, agent_id, session_id, data_type, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (isolation_key, level.value, user_id, agent_id, session_id, data_type, data_str))

        conn.commit()
        conn.close()

    def load_data(
        self,
        key: str,
        level: IsolationLevel,
        user_id: str = "",
        agent_id: str = "",
        session_id: str = "",
        default: Any = None
    ) -> Any:
        """加载隔离数据"""
        isolation_key = self.get_isolation_key(level, user_id, agent_id, session_id)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data_type, data FROM isolation_data
            WHERE isolation_key = ? AND level = ?
            ORDER BY created_at DESC LIMIT 1
        """, (isolation_key, level.value))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return default

        data_type, data_str = row

        if data_type == "json":
            try:
                return json.loads(data_str)
            except:
                return default
        else:
            return data_str

    def query_data(
        self,
        level: IsolationLevel = None,
        user_id: str = None,
        agent_id: str = None,
        session_id: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """查询隔离数据"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = "SELECT * FROM isolation_data WHERE 1=1"
        params = []

        if level:
            sql += " AND level = ?"
            params.append(level.value)

        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)

        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)

        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def delete_data(
        self,
        level: IsolationLevel,
        user_id: str = "",
        agent_id: str = "",
        session_id: str = ""
    ) -> int:
        """删除隔离数据"""
        isolation_key = self.get_isolation_key(level, user_id, agent_id, session_id)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM isolation_data WHERE isolation_key = ? AND level = ?
        """, (isolation_key, level.value))

        count = cursor.rowcount
        conn.commit()
        conn.close()

        return count

    def get_isolation_path(
        self,
        level: IsolationLevel,
        user_id: str = "",
        agent_id: str = "",
        session_id: str = ""
    ) -> Path:
        """获取隔离目录路径"""
        base = self.data_dir

        if level == IsolationLevel.GLOBAL:
            return base / "global"

        if level == IsolationLevel.AGENT and agent_id:
            return base / "agents" / agent_id

        if level == IsolationLevel.USER and user_id:
            return base / "users" / user_id

        if level == IsolationLevel.SESSION and session_id:
            return base / "sessions" / session_id

        return base

    def create_isolation_dirs(
        self,
        level: IsolationLevel,
        user_id: str = "",
        agent_id: str = "",
        session_id: str = ""
    ) -> Path:
        """创建隔离目录结构"""
        base = self.get_isolation_path(level, user_id, agent_id, session_id)

        # 创建子目录
        (base / "memory").mkdir(parents=True, exist_ok=True)
        (base / "checkpoints").mkdir(parents=True, exist_ok=True)
        (base / "traces").mkdir(parents=True, exist_ok=True)
        (base / "output").mkdir(parents=True, exist_ok=True)
        (base / "config").mkdir(parents=True, exist_ok=True)

        return base

    def get_stats(self) -> Dict[str, Any]:
        """获取隔离统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 按级别统计
        cursor.execute("""
            SELECT level, COUNT(*) as count
            FROM isolation_data
            GROUP BY level
        """)
        by_level = {row[0]: row[1] for row in cursor.fetchall()}

        # 按 user 统计
        cursor.execute("""
            SELECT user_id, COUNT(*) as count
            FROM isolation_data
            WHERE user_id IS NOT NULL AND user_id != ''
            GROUP BY user_id
        """)
        by_user = {row[0]: row[1] for row in cursor.fetchall()}

        # 按 agent 统计
        cursor.execute("""
            SELECT agent_id, COUNT(*) as count
            FROM isolation_data
            WHERE agent_id IS NOT NULL AND agent_id != ''
            GROUP BY agent_id
        """)
        by_agent = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM isolation_data")
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "total_records": total,
            "by_level": by_level,
            "by_user": by_user,
            "by_agent": by_agent,
        }


# ========== 便捷函数 ==========

def get_isolation_manager(data_dir: str = ".young") -> IsolationManager:
    """获取隔离管理器实例"""
    return IsolationManager(data_dir)
