"""
Session API - 会话API服务器

提供REST和WebSocket接口用于持久Agent会话
SSE流式输出支持

Note: 支持两种模式:
1. Router模式: 使用 create_session_router() 创建router
2. App模式: 使用 create_session_api() 直接注册到app
"""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# SSE 支持
try:
    from sse_starlette import EventSourceResponse
except ImportError:
    EventSourceResponse = None


# 创建Router
router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

# ========== 认证依赖 ==========


def get_valid_api_keys() -> set[str]:
    """获取有效的API密钥列表"""
    keys_str = os.environ.get("OPENYOUNG_API_KEYS", "")
    if not keys_str:
        return set()
    return set(k.strip() for k in keys_str.split(",") if k.strip())


def require_api_key(x_api_key: str = Header(None)) -> str:
    """
    验证API密钥的依赖函数

    从请求头 X-API-Key 获取密钥并验证
    返回密钥如果有效，否则抛出401错误
    """
    valid_keys = get_valid_api_keys()

    # 如果没有配置任何有效密钥，在生产环境拒绝访问
    if not valid_keys:
        # 检查是否在开发模式（允许无认证访问）
        debug_mode = os.environ.get("OPENYOUNG_DEBUG", "false").lower() == "true"
        if not debug_mode:
            raise HTTPException(
                status_code=401,
                detail="API authentication not configured. Set OPENYOUNG_API_KEYS environment variable."
            )
        return None  # 开发模式返回None表示跳过认证

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header"
        )

    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return x_api_key


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


# ========== SSE 事件生成器 ==========


async def chat_response_generator(
    session_id: str,
    session_manager,
    agent_executor=None,
) -> AsyncGenerator[str, None]:
    """
    生成聊天响应的SSE事件流

    基于 FastAPI SSE 最佳实践:
    - https://fastapi.tiangolo.com/tutorial/server-sent-events/
    - 发送 keep-alive ping
    - 使用 JSON 格式传输数据
    """
    if EventSourceResponse is None:
        yield "event: error\ndata: SSE not supported\n\n"
        return

    # 发送会话开始事件
    yield f"event: session_start\ndata: {json.dumps({'session_id': session_id})}\n\n"

    # 获取用户最新消息
    messages = session_manager.get_messages(session_id)
    if not messages:
        yield f"event: error\ndata: {json.dumps({'error': 'No messages'})}\n\n"
        return

    last_message = messages[-1]
    if last_message.role != "user":
        yield f"event: error\ndata: {json.dumps({'error': 'Last message is not from user'})}\n\n"
        return

    user_content = last_message.content

    # 发送正在处理事件
    yield f"event: processing\ndata: {json.dumps({'status': 'processing'})}\n\n"

    try:
        if agent_executor:
            # 使用Agent执行器（流式输出）
            full_response = ""
            async for chunk in agent_executor.execute_stream(user_content):
                full_response += chunk
                # 发送逐字响应事件
                yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"

                # 模拟打字效果（可配置）
                await asyncio.sleep(0.02)

            # 发送完成事件
            yield f"event: done\ndata: {json.dumps({'response': full_response})}\n\n"

            # 保存助手响应到会话
            session_manager.add_message(session_id, "assistant", full_response)

        else:
            # 临时实现：回显响应（带打字效果）
            response = f"Echo: {user_content}"

            # 逐字发送响应
            for char in response:
                yield f"event: chunk\ndata: {json.dumps({'content': char})}\n\n"
                await asyncio.sleep(0.03)

            # 发送完成事件
            yield f"event: done\ndata: {json.dumps({'response': response})}\n\n"

            # 保存助手响应到会话
            session_manager.add_message(session_id, "assistant", response)

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    # 发送 keep-alive ping（每15秒）
    # FastAPI 会自动处理，这里是备用


# ========== API 实现 ==========


def create_session_api(app: FastAPI, session_manager, agent_executor=None):
    """创建会话API"""

    @app.post("/api/sessions", response_model=SessionResponse, dependencies=[Depends(require_api_key)])
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

    @app.get("/api/sessions", dependencies=[Depends(require_api_key)])
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

    @app.get("/api/sessions/{session_id}", dependencies=[Depends(require_api_key)])
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

    @app.post("/api/sessions/{session_id}/messages", response_model=MessageResponse, dependencies=[Depends(require_api_key)])
    async def send_message(session_id: str, req: MessageRequest):
        """发送消息到会话（非流式）"""
        session = session_manager.get_persistent_session(session_id)
        if not session:
            return {"error": "Session not found"}, 404

        # 添加用户消息
        session_manager.add_message(session_id, "user", req.message)

        # 调用Agent执行
        if agent_executor:
            response = await agent_executor.execute(req.message)
        else:
            response = f"Echo: {req.message}"  # 临时实现

        # 添加助手消息
        session_manager.add_message(session_id, "assistant", response)

        return MessageResponse(
            session_id=session_id,
            response=response,
            status=session.status,
        )

    @app.get("/api/sessions/{session_id}/stream", dependencies=[Depends(require_api_key)])
    async def stream_message(session_id: str, message: str = ""):
        """
        流式发送消息到会话（SSE）

        使用 Server-Sent Events 实现实时流式响应

        Query Parameters:
        - message: 要发送的消息内容（可选，如果不提供则使用最后一条用户消息）

        Event Types:
        - session_start: 会话开始
        - processing: 正在处理
        - chunk: 响应片段
        - done: 完成
        - error: 错误
        """
        if EventSourceResponse is None:
            return StreamingResponse(
                iter(["SSE not supported"]),
                media_type="text/plain",
                status_code=500,
            )

        session = session_manager.get_persistent_session(session_id)
        if not session:
            return EventSourceResponse(
                iter([f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"])
            )

        # 如果提供了消息，先保存用户消息
        if message:
            session_manager.add_message(session_id, "user", message)

        return EventSourceResponse(
            chat_response_generator(session_id, session_manager, agent_executor),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    @app.post("/api/sessions/{session_id}/stream", dependencies=[Depends(require_api_key)])
    async def stream_message_post(session_id: str, req: MessageRequest):
        """
        POST版本的流式消息接口

        使用 Server-Sent Events 实现实时流式响应
        """
        if EventSourceResponse is None:
            return StreamingResponse(
                iter(["SSE not supported"]),
                media_type="text/plain",
                status_code=500,
            )

        session = session_manager.get_persistent_session(session_id)
        if not session:
            return EventSourceResponse(
                iter([f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"])
            )

        # 保存用户消息
        session_manager.add_message(session_id, "user", req.message)

        return EventSourceResponse(
            chat_response_generator(session_id, session_manager, agent_executor),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    @app.get("/api/sessions/{session_id}/history", dependencies=[Depends(require_api_key)])
    async def get_history(session_id: str):
        """获取历史消息"""
        messages = session_manager.get_messages(session_id)
        return {
            "session_id": session_id,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages
            ],
        }

    @app.post("/api/sessions/{session_id}/suspend", dependencies=[Depends(require_api_key)])
    async def suspend_session(session_id: str):
        """暂停会话"""
        success = session_manager.suspend_session(session_id)
        return {"success": success, "session_id": session_id}

    @app.post("/api/sessions/{session_id}/resume", dependencies=[Depends(require_api_key)])
    async def resume_session(session_id: str):
        """恢复会话"""
        success = session_manager.resume_session(session_id)
        return {"success": success, "session_id": session_id}

    @app.post("/api/sessions/{session_id}/terminate", dependencies=[Depends(require_api_key)])
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

                # 调用Agent执行
                if agent_executor:
                    response = await agent_executor.execute(message)
                else:
                    response = f"Echo: {message}"

                # 添加助手消息
                session_manager.add_message(session_id, "assistant", response)

                # 发送响应
                await websocket.send_text(response)

        except WebSocketDisconnect:
            pass


def create_session_app(session_manager, agent_executor=None):
    """创建会话应用"""
    app = FastAPI(title="OpenYoung Session API")
    create_session_api(app, session_manager, agent_executor)
    return app
