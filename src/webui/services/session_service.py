"""
Session Service - 会话管理服务
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class SessionService:
    """会话服务 - 本地会话状态管理"""

    def __init__(self):
        # 内存中的会话缓存
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_local_session(
        self, session_id: str, agent_name: str, initial_context: Dict = None
    ) -> Dict[str, Any]:
        """创建本地会话"""
        session = {
            "session_id": session_id,
            "agent_name": agent_name,
            "initial_context": initial_context or {},
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "idle",
        }
        self._sessions[session_id] = session
        return session

    def get_local_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取本地会话"""
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """添加消息到会话"""
        if session_id not in self._sessions:
            return

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._sessions[session_id]["messages"].append(message)
        self._sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话消息"""
        session = self._sessions.get(session_id)
        if session:
            return session.get("messages", [])
        return []

    def update_status(self, session_id: str, status: str) -> None:
        """更新会话状态"""
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = status
            self._sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def delete_local_session(self, session_id: str) -> bool:
        """删除本地会话"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_local_sessions(self) -> List[Dict[str, Any]]:
        """列出所有本地会话"""
        return list(self._sessions.values())

    def clear(self) -> None:
        """清空所有会话"""
        self._sessions.clear()


# 全局会话服务实例
session_service = SessionService()
