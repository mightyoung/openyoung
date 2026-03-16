"""
OpenYoung Unified API Server

统一 API 服务器，整合 Session API、Evaluation API 和其他服务
支持 WebUI 的所有需求
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.session_api import create_session_api
from src.evaluation_api.routers import evaluations, executions, exports, stream

# =====================
# 简单的内存会话管理器
# =====================


class Session:
    """会话对象 - 适配 session_api.py 的属性访问"""

    def __init__(self, data: dict):
        self._data = data

    @property
    def session_id(self) -> str:
        return self._data.get("session_id", "")

    @property
    def agent_name(self) -> str:
        return self._data.get("agent_name", "")

    @property
    def status(self) -> str:
        return self._data.get("status", "idle")

    @property
    def is_persistent(self) -> bool:
        return self._data.get("is_persistent", True)

    @property
    def created_at(self) -> str:
        return self._data.get("created_at", "")

    @property
    def updated_at(self) -> str:
        return self._data.get("updated_at", "")


class SimpleSessionManager:
    """简化的会话管理器 - 内存存储"""

    def __init__(self):
        self._sessions = {}
        self._messages = {}

    def create_persistent_session(
        self, agent_name: str, initial_context: dict = None, session_id: str = None
    ):
        """创建持久会话"""
        import uuid

        if session_id is None:
            session_id = str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "agent_name": agent_name,
            "initial_context": initial_context or {},
            "status": "idle",
            "is_persistent": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        self._sessions[session_id] = session_data
        self._messages[session_id] = []
        return Session(session_data)  # 返回 Session 对象

    def get_session(self, session_id: str):
        """获取会话"""
        data = self._sessions.get(session_id)
        return Session(data) if data else None

    def list_sessions(self):
        """列出所有会话"""
        return [Session(s) for s in self._sessions.values()]

    def get_persistent_sessions(self):
        """获取持久会话列表"""
        return [Session(s) for s in self._sessions.values()]

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息"""
        if session_id not in self._messages:
            self._messages[session_id] = []

        self._messages[session_id].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
            }
        )

        if session_id in self._sessions:
            self._sessions[session_id]["updated_at"] = datetime.now().isoformat()

    def get_messages(self, session_id: str):
        """获取消息"""
        return self._messages.get(session_id, [])

    def delete_session(self, session_id: str):
        """删除会话"""
        self._sessions.pop(session_id, None)
        self._messages.pop(session_id, None)

    def suspend_session(self, session_id: str):
        """暂停会话"""
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = "suspended"
            return Session(self._sessions[session_id])
        return None

    def resume_session(self, session_id: str):
        """恢复会话"""
        if session_id in self._sessions:
            self._sessions[session_id]["status"] = "idle"
            return Session(self._sessions[session_id])
        return None


# 全局会话管理器
session_manager = SimpleSessionManager()


# =====================
# FastAPI 应用
# =====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("Starting OpenYoung Unified API Server...")
    yield
    # 关闭时
    print("Shutting down OpenYoung Unified API Server...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="OpenYoung API",
        description="OpenYoung Unified API - Session + Evaluation",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册 Session API
    create_session_api(app, session_manager)

    # 注册 Evaluation API
    app.include_router(executions.router, prefix="/api/v1", tags=["Executions"])
    app.include_router(evaluations.router, prefix="/api/v1", tags=["Evaluations"])
    app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
    app.include_router(stream.router, prefix="/api/v1", tags=["Stream"])

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "openyoung-api",
            "version": "1.0.0",
        }

    @app.get("/")
    async def root():
        return {
            "message": "OpenYoung Unified API",
            "docs": "/docs",
            "version": "1.0.0",
        }

    # 简单的 Agent 列表端点 (模拟)
    @app.get("/api/agents")
    async def list_agents():
        """列出可用 Agents"""
        return {
            "items": [
                {
                    "id": "default",
                    "name": "default",
                    "description": "Default AI Agent",
                    "tags": ["general"],
                    "verified": True,
                },
                {
                    "id": "coder",
                    "name": "coder",
                    "description": "Coding Assistant",
                    "tags": ["coding", "development"],
                    "verified": True,
                },
                {
                    "id": "researcher",
                    "name": "researcher",
                    "description": "Research Assistant",
                    "tags": ["research", "analysis"],
                    "verified": False,
                },
            ]
        }

    @app.get("/api/agents/{agent_id}")
    async def get_agent(agent_id: str):
        """获取 Agent 详情"""
        agents = {
            "default": {
                "id": "default",
                "name": "default",
                "description": "Default AI Agent",
                "tags": ["general"],
                "verified": True,
            },
            "coder": {
                "id": "coder",
                "name": "coder",
                "description": "Coding Assistant",
                "tags": ["coding", "development"],
                "verified": True,
            },
            "researcher": {
                "id": "researcher",
                "name": "researcher",
                "description": "Research Assistant",
                "tags": ["research", "analysis"],
                "verified": False,
            },
        }
        return agents.get(agent_id, {"error": "Agent not found"})

    return app


# 创建应用实例
app = create_app()


# =====================
# 运行服务器
# =====================


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行服务器"""
    import uvicorn

    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    run_server()
