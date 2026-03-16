"""
Evaluation API - FastAPI 主应用

Phase 1 评估平台后端服务入口
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .middleware import APIKeyMiddleware, LoggingMiddleware, RateLimitMiddleware
from .routers import evaluations, executions, exports, stream

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Evaluation API...")
    yield
    # 关闭时
    logger.info("Shutting down Evaluation API...")


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="OpenYoung Evaluation API",
        description="Phase 1 评估平台 REST API",
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

    # 日志中间件
    app.add_middleware(LoggingMiddleware)

    # 速率限制中间件
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    # API Key 认证中间件（生产环境）
    api_keys = os.environ.get("EVAL_API_KEYS", "").split(",")
    api_keys = [k.strip() for k in api_keys if k.strip()]
    if api_keys:
        app.add_middleware(APIKeyMiddleware, api_keys=api_keys)

    # 注册路由
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
            "service": "evaluation-api",
            "version": "1.0.0",
        }

    @app.get("/")
    async def root():
        return {
            "message": "OpenYoung Evaluation API",
            "docs": "/docs",
            "version": "1.0.0",
        }

    return app


# 创建应用实例
app = create_app()
