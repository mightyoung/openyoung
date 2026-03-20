"""
OpenYoung Unified API Server

统一 API 服务器，整合 Session API、Evaluation API 和其他服务
支持 WebUI 的所有需求
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import get_all_routers
from src.api.session_api import create_session_api

# 直接导入 (方案B - 分散注册，保留兼容)
# from src.evaluation_api.routers import evaluations, executions, exports, stream

logger = logging.getLogger(__name__)

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
    """简化的会话管理器 - 内存存储，支持可选 Redis 降级"""

    def __init__(self, redis_url: str = None):
        self._redis = None
        if redis_url:
            try:
                from redis import Redis

                self._redis = Redis.from_url(redis_url)
                self._redis.ping()
                logger.info("SimpleSessionManager initialized with Redis")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}), using in-memory fallback")
                self._redis = None
        self._memory: dict = {}  # 内存回退
        self._messages: dict = {}  # 内存回退

    def _get_session_data(self, session_id: str) -> Optional[dict]:
        """从 Redis 或内存获取会话数据"""
        if self._redis:
            try:
                data = self._redis.hgetall(f"session:{session_id}")
                if data:
                    return {k.decode(): v.decode() for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Redis error getting session {session_id}: {e}")
        return self._memory.get(session_id)

    def _save_session_data(self, session_id: str, data: dict) -> None:
        """保存会话数据到 Redis 或内存"""
        if self._redis:
            try:
                self._redis.hset(
                    f"session:{session_id}", mapping={k: str(v) for k, v in data.items()}
                )
                self._redis.expire(f"session:{session_id}", 86400)  # 24h TTL
                return
            except Exception as e:
                logger.warning(f"Redis error saving session {session_id}: {e}")
        self._memory[session_id] = data

    def _get_messages(self, session_id: str) -> list:
        """获取消息列表"""
        if self._redis:
            try:
                msgs = self._redis.lrange(f"messages:{session_id}", 0, -1)
                return [json.loads(m.decode()) for m in msgs]
            except Exception as e:
                logger.warning(f"Redis error getting messages for {session_id}: {e}")
        return self._messages.get(session_id, [])

    def _append_message(self, session_id: str, message: dict) -> None:
        """追加消息"""
        if self._redis:
            try:
                self._redis.rpush(f"messages:{session_id}", json.dumps(message))
                self._redis.expire(f"messages:{session_id}", 86400)
                return
            except Exception as e:
                logger.warning(f"Redis error appending message to {session_id}: {e}")
        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(message)

    def _delete_session_data(self, session_id: str) -> None:
        """删除会话数据"""
        if self._redis:
            try:
                self._redis.delete(f"session:{session_id}", f"messages:{session_id}")
            except Exception as e:
                logger.warning(f"Redis error deleting session {session_id}: {e}")
        self._memory.pop(session_id, None)
        self._messages.pop(session_id, None)

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
        self._save_session_data(session_id, session_data)
        return Session(session_data)

    def get_session(self, session_id: str):
        """获取会话"""
        data = self._get_session_data(session_id)
        return Session(data) if data else None

    def list_sessions(self):
        """列出所有会话"""
        if self._redis:
            try:
                keys = self._redis.keys("session:*")
                return [self.get_session(k.decode().split(":")[1]) for k in keys]
            except Exception:
                pass
        return [Session(s) for s in self._memory.values()]

    def get_persistent_sessions(self):
        """获取持久会话列表"""
        return self.list_sessions()

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        self._append_message(session_id, message)
        # 更新会话时间
        data = self._get_session_data(session_id)
        if data:
            data["updated_at"] = datetime.now().isoformat()
            self._save_session_data(session_id, data)

    def get_messages(self, session_id: str):
        """获取消息"""
        return self._get_messages(session_id)

    def delete_session(self, session_id: str):
        """删除会话"""
        self._delete_session_data(session_id)

    def suspend_session(self, session_id: str):
        """暂停会话"""
        data = self._get_session_data(session_id)
        if data:
            data["status"] = "suspended"
            self._save_session_data(session_id, data)
            return Session(data)
        return None

    def resume_session(self, session_id: str):
        """恢复会话"""
        data = self._get_session_data(session_id)
        if data:
            data["status"] = "idle"
            self._save_session_data(session_id, data)
            return Session(data)
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

    # CORS 中间件 - 安全配置
    # 从环境变量读取允许的源，默认仅允许 localhost:3000
    cors_origins_env = os.environ.get("CORS_ORIGINS", "")
    if cors_origins_env:
        allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    else:
        allowed_origins = ["http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # 注册 Session API
    create_session_api(app, session_manager)

    # 统一路由注册 (方案A - 使用 get_all_routers())
    for router, prefix, tags in get_all_routers():
        app.include_router(router, prefix=prefix, tags=tags)

    # 方式1: 分散注册 (已弃用)
    # app.include_router(executions.router, prefix="/api/v1", tags=["Executions"])
    # app.include_router(evaluations.router, prefix="/api/v1", tags=["Evaluations"])
    # app.include_router(exports.router, prefix="/api/v1", tags=["Exports"])
    # app.include_router(stream.router, prefix="/api/v1", tags=["Stream"])

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
