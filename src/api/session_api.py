"""
Session API - 会话API服务器

提供REST和WebSocket接口用于持久Agent会话
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


# ========== 请求模型 ==========

class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    agent_name: str
    initial_context: dict = {}
    session_id: Optional[str] = None


class MessageRequest(BaseModel):
    """消息请求"""
    message: str


# ========== 响应模型 ==========

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    status: str
    agent_name: str
    is_persistent: bool


class MessageResponse(BaseModel):
    """消息响应"""
    session_id: str
    response: str
    status: str


# ========== API 实现 ==========

def create_session_api(app: FastAPI, session_manager):
    """创建会话API"""

    @app.post("/api/sessions", response_model=SessionResponse)
    async def create_session(req: CreateSessionRequest):
        """创建持久会话"""
        session = session_manager.create_persistent_session(
            agent_name=req.agent_name,
            initial_context=req.initial_context,
            session_id=req.session_id,
        )
        return SessionResponse(
            session_id=session.session_id,
            status=session.status,
            agent_name=session.agent_name or "",
            is_persistent=session.is_persistent,
        )

    @app.get("/api/sessions")
    async def list_sessions():
        """列出会话"""
        sessions = session_manager.get_persistent_sessions()
        return [
            SessionResponse(
                session_id=s.session_id,
                status=s.status,
                agent_name=s.agent_name or "",
                is_persistent=s.is_persistent,
            )
            for s in sessions
        ]

    @app.get("/api/sessions/{session_id}")
    async def get_session(session_id: str):
        """获取会话"""
        session = session_manager.get_persistent_session(session_id)
        if not session:
            return {"error": "Session not found"}, 404

        return SessionResponse(
            session_id=session.session_id,
            status=session.status,
            agent_name=session.agent_name or "",
            is_persistent=session.is_persistent,
        )

    @app.post("/api/sessions/{session_id}/messages", response_model=MessageResponse)
    async def send_message(session_id: str, req: MessageRequest):
        """发送消息到会话"""
        session = session_manager.get_persistent_session(session_id)
        if not session:
            return {"error": "Session not found"}, 404

        # 添加用户消息
        session_manager.add_message(session_id, "user", req.message)

        # TODO: 调用Agent执行
        # response = await agent.execute(session, req.message)

        response = f"Echo: {req.message}"  # 临时实现

        # 添加助手消息
        session_manager.add_message(session_id, "assistant", response)

        return MessageResponse(
            session_id=session_id,
            response=response,
            status=session.status,
        )

    @app.get("/api/sessions/{session_id}/history")
    async def get_history(session_id: str):
        """获取历史消息"""
        messages = session_manager.get_messages(session_id)
        return {
            "session_id": session_id,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in messages
            ],
        }

    @app.post("/api/sessions/{session_id}/suspend")
    async def suspend_session(session_id: str):
        """暂停会话"""
        success = session_manager.suspend_session(session_id)
        return {"success": success, "session_id": session_id}

    @app.post("/api/sessions/{session_id}/resume")
    async def resume_session(session_id: str):
        """恢复会话"""
        success = session_manager.resume_session(session_id)
        return {"success": success, "session_id": session_id}

    @app.post("/api/sessions/{session_id}/terminate")
    async def terminate_session(session_id: str):
        """终止会话"""
        success = session_manager.terminate_session(session_id)
        return {"success": success, "session_id": session_id}

    @app.websocket("/api/ws/{session_id}")
    async def websocket_session(websocket: WebSocket, session_id: str):
        """WebSocket实时交互"""
        await websocket.accept()

        try:
            while True:
                # 接收消息
                message = await websocket.receive_text()

                # 添加用户消息
                session_manager.add_message(session_id, "user", message)

                # TODO: 调用Agent执行
                # response = await agent.execute(session, message)
                response = f"Echo: {message}"  # 临时实现

                # 添加助手消息
                session_manager.add_message(session_id, "assistant", response)

                # 发送响应
                await websocket.send_text(response)

        except WebSocketDisconnect:
            pass


def create_session_app(session_manager):
    """创建会话应用"""
    app = FastAPI(title="OpenYoung Session API")
    create_session_api(app, session_manager)
    return app
