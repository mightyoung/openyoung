"""
Session Manager - 会话管理
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Session:
    """任务会话"""

    session_id: str
    task_id: str | None
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    result: str | None = None
    parent_session_id: str | None = None


class SessionManager:
    """会话管理器 - 管理任务会话生命周期"""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(
        self,
        task_id: str | None,
        parent_session_id: str | None,
        description: str,
        initial_context: dict[str, Any] = None,
    ) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())

        session = Session(
            session_id=session_id,
            task_id=task_id,
            description=description,
            parent_session_id=parent_session_id,
            context=initial_context or {},
        )

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """获取会话"""
        return self._sessions.get(session_id)

    def get_or_create(
        self,
        task_id: str | None,
        parent_session_id: str | None,
        description: str,
        context: dict[str, Any] = None,
    ) -> Session:
        """获取或创建会话"""
        # 尝试通过 task_id 查找现有会话
        if task_id:
            for session in self._sessions.values():
                if session.task_id == task_id:
                    return session

        # 创建新会话
        return self.create_session(task_id, parent_session_id, description, context)

    def update_session(
        self,
        session_id: str,
        status: str | None = None,
        result: str | None = None,
        context_update: dict[str, Any] = None,
    ) -> bool:
        """更新会话"""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if status:
            session.status = status
        if result:
            session.result = result
        if context_update:
            session.context.update(context_update)

        session.updated_at = datetime.now()
        return True

    def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        return self.update_session(session_id, status="completed")

    def get_active_sessions(self) -> list:
        """获取活跃会话"""
        return [s for s in self._sessions.values() if s.status in ("pending", "running")]

    def cleanup_old_sessions(self, max_age_seconds: int = 3600):
        """清理旧会话"""
        now = datetime.now()
        to_remove = []

        for session_id, session in self._sessions.items():
            age = (now - session.updated_at).total_seconds()
            if age > max_age_seconds and session.status != "running":
                to_remove.append(session_id)

        for session_id in to_remove:
            del self._sessions[session_id]

        return len(to_remove)
