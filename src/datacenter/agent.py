"""
Agent - Agent 角色系统与消息总线
借鉴 Anthropic (角色定义) + AutoGen (消息通信)
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    """Agent 角色 - 借鉴 Anthropic"""
    INITIALIZER = "initializer"      # 环境初始化
    CODER = "coder"                # 代码生成
    REVIEWER = "reviewer"          # 代码审查
    EXECUTOR = "executor"          # 任务执行
    ORCHESTRATOR = "orchestrator"  # 编排协调
    RESEARCHER = "researcher"       # 调研分析


@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_id: str
    name: str
    role: AgentRole

    # 能力
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

    # 工作区
    workspace: str = ""  # 独立工作区路径
    shared_state: str = ""  # 共享状态文件

    # 元数据
    version: str = "1.0.0"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


# ========== 消息总线 ==========

class MessageType(str, Enum):
    """消息类型"""
    REQUEST = "request"      # 请求
    RESPONSE = "response"  # 响应
    NOTIFICATION = "notify"  # 通知
    BROADCAST = "broadcast"  # 广播


@dataclass
class AgentMessage:
    """Agent 消息"""
    message_id: str
    sender_id: str
    receiver_id: str  # 空表示广播
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


class MessageBus:
    """Agent 消息总线 - AutoGen 黑板模式"""

    def __init__(self, db_path: str = ".young/message_bus.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                receiver_id TEXT,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender_id)")

        conn.commit()
        conn.close()

    def publish(self, message: AgentMessage):
        """发布消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages (message_id, sender_id, receiver_id, message_type, content)
            VALUES (?, ?, ?, ?, ?)
        """, (
            message.message_id,
            message.sender_id,
            message.receiver_id,
            message.message_type.value,
            json.dumps(message.content, ensure_ascii=False)
        ))

        conn.commit()
        conn.close()

    def get_messages(
        self,
        agent_id: str,
        unread_only: bool = True,
        limit: int = 50
    ) -> List[Dict]:
        """获取消息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = """
            SELECT * FROM messages
            WHERE receiver_id = ? OR receiver_id = ''
        """
        params = [agent_id]

        if unread_only:
            sql += " AND is_read = 0"

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "message_id": row["message_id"],
                "sender_id": row["sender_id"],
                "receiver_id": row["receiver_id"],
                "message_type": row["message_type"],
                "content": json.loads(row["content"]),
                "is_read": bool(row["is_read"]),
                "created_at": row["created_at"]
            }
            for row in rows
        ]

    def mark_read(self, message_id: str):
        """标记已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE messages SET is_read = 1 WHERE message_id = ?", (message_id,))

        conn.commit()
        conn.close()

    def mark_all_read(self, agent_id: str):
        """标记所有消息已读"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("UPDATE messages SET is_read = 1 WHERE receiver_id = ?", (agent_id,))

        conn.commit()
        conn.close()

    def get_unread_count(self, agent_id: str) -> int:
        """获取未读消息数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM messages
            WHERE (receiver_id = ? OR receiver_id = '') AND is_read = 0
        """, (agent_id,))

        count = cursor.fetchone()[0]
        conn.close()

        return count


# ========== Agent 注册表 ==========

class AgentRegistry:
    """Agent 注册表 - 支持角色"""

    def __init__(self, db_path: str = ".young/agents.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                capabilities TEXT,
                skills TEXT,
                workspace TEXT,
                shared_state TEXT,
                version TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def register(self, config: AgentConfig):
        """注册 Agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO agents (
                agent_id, name, role, capabilities, skills,
                workspace, shared_state, version, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.agent_id,
            config.name,
            config.role.value,
            json.dumps(config.capabilities),
            json.dumps(config.skills),
            config.workspace,
            config.shared_state,
            config.version,
            config.description,
            config.created_at.isoformat()
        ))

        conn.commit()
        conn.close()

    def get(self, agent_id: str) -> Optional[AgentConfig]:
        """获取 Agent"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return AgentConfig(
            agent_id=row["agent_id"],
            name=row["name"],
            role=AgentRole(row["role"]),
            capabilities=json.loads(row["capabilities"]),
            skills=json.loads(row["skills"]),
            workspace=row["workspace"] or "",
            shared_state=row["shared_state"] or "",
            version=row["version"] or "1.0.0",
            description=row["description"] or ""
        )

    def list_by_role(self, role: AgentRole) -> List[AgentConfig]:
        """按角色列出 Agent"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents WHERE role = ?", (role.value,))
        rows = cursor.fetchall()
        conn.close()

        return [
            AgentConfig(
                agent_id=row["agent_id"],
                name=row["name"],
                role=AgentRole(row["role"]),
                capabilities=json.loads(row["capabilities"]),
                skills=json.loads(row["skills"]),
                workspace=row["workspace"] or "",
                shared_state=row["shared_state"] or "",
                version=row["version"] or "1.0.0",
                description=row["description"] or ""
            )
            for row in rows
        ]

    def list_all(self) -> List[AgentConfig]:
        """列出所有 Agent"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agents")
        rows = cursor.fetchall()
        conn.close()

        return [
            AgentConfig(
                agent_id=row["agent_id"],
                name=row["name"],
                role=AgentRole(row["role"]),
                capabilities=json.loads(row["capabilities"]),
                skills=json.loads(row["skills"]),
                workspace=row["workspace"] or "",
                shared_state=row["shared_state"] or "",
                version=row["version"] or "1.0.0",
                description=row["description"] or ""
            )
            for row in rows
        ]


# ========== 便捷函数 ==========

def get_message_bus(db_path: str = ".young/message_bus.db") -> MessageBus:
    """获取消息总线"""
    return MessageBus(db_path)


def get_agent_registry(db_path: str = ".young/agents.db") -> AgentRegistry:
    """获取 Agent 注册表"""
    return AgentRegistry(db_path)
