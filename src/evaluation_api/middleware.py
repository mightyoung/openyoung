"""
Evaluation API Middleware

提供认证、日志等中间件
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # 记录请求
        logger.info(f"Request: {request.method} {request.url.path}")

        # 处理请求
        response = await call_next(request)

        # 记录响应
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件

    注意: 生产环境应使用 Redis 等分布式存储
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._request_counts: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # 清理过期记录
        if client_ip in self._request_counts:
            self._request_counts[client_ip] = [
                t for t in self._request_counts[client_ip] if current_time - t < 60
            ]
        else:
            self._request_counts[client_ip] = []

        # 检查速率限制
        if len(self._request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"},
            )

        # 记录请求
        self._request_counts[client_ip].append(current_time)

        return await call_next(request)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """API Key 认证中间件"""

    def __init__(self, app, api_keys: list[str] = None):
        super().__init__(app)
        self.api_keys = set(api_keys or [])
        # 开发环境跳过认证
        self.skip_auth = not self.api_keys

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查和开发环境
        if request.url.path in ["/health", "/"] or self.skip_auth:
            return await call_next(request)

        # 检查 API Key
        api_key = request.headers.get("X-API-Key")
        if not api_key or api_key not in self.api_keys:
            logger.warning(f"Invalid or missing API key from {request.client.host}")
            return Response(
                content="Invalid or missing API key",
                status_code=401,
            )

        return await call_next(request)
