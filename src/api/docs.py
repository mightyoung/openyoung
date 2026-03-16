"""
API Documentation Utilities - API文档工具

提供OpenAPI文档生成、SDK客户端等功能
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ====================
# OpenAPI Schema Helpers
# ====================


@dataclass
class SchemaExample:
    """Schema示例"""

    summary: str
    value: Any


def create_schema_example(model_class: type, example_data: dict[str, Any]) -> dict[str, Any]:
    """创建Schema示例"""
    return {
        "summary": f"Example {model_class.__name__}",
        "value": example_data,
    }


def create_error_schema(error_code: str, message: str) -> dict[str, Any]:
    """创建错误响应Schema"""
    return {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "example": error_code},
                    "message": {"type": "string", "example": message},
                },
            }
        },
    }


# ====================
# API Client SDK
# ====================


class APIClientBase:
    """API客户端基类

    提供通用的请求、重试、超时处理
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

    def _build_url(self, path: str) -> str:
        """构建完整URL"""
        return f"{self.base_url}/{path.lstrip('/')}"

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "OpenYoung/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get(self, path: str, **kwargs) -> dict[str, Any]:
        """GET请求"""
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> dict[str, Any]:
        """POST请求"""
        return await self._request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> dict[str, Any]:
        """PUT请求"""
        return await self._request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> dict[str, Any]:
        """DELETE请求"""
        return await self._request("DELETE", path, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        """执行请求"""
        import httpx

        url = self._build_url(path)
        headers = self._get_headers()

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method, url=url, headers=headers, **kwargs
                    )
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed, retrying: {e}")

        return {}


# ====================
# SDK Builders
# ====================


class EvaluationSDK:
    """评估SDK客户端"""

    def __init__(self, client: APIClientBase):
        self._client = client

    async def run_evaluation(self, dataset: str, agent: str = "young", **options) -> dict[str, Any]:
        """运行评估"""
        return await self._client.post(
            "/evaluations/run", json={"dataset": dataset, "agent": agent, **options}
        )

    async def get_evaluation(self, run_id: str) -> dict[str, Any]:
        """获取评估结果"""
        return await self._client.get(f"/evaluations/{run_id}")

    async def list_evaluations(self, limit: int = 10, offset: int = 0) -> dict[str, Any]:
        """列出评估"""
        return await self._client.get("/evaluations", params={"limit": limit, "offset": offset})


class AgentSDK:
    """Agent SDK客户端"""

    def __init__(self, client: APIClientBase):
        self._client = client

    async def spawn_agent(
        self, agent_type: str, name: Optional[str] = None, **config
    ) -> dict[str, Any]:
        """创建Agent"""
        return await self._client.post(
            "/agents/spawn", json={"type": agent_type, "name": name, **config}
        )

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        """获取Agent信息"""
        return await self._client.get(f"/agents/{agent_id}")

    async def kill_agent(self, agent_id: str) -> dict[str, Any]:
        """终止Agent"""
        return await self._client.post(f"/agents/{agent_id}/kill", json={})


class TaskSDK:
    """任务SDK客户端"""

    def __init__(self, client: APIClientBase):
        self._client = client

    async def submit_task(self, task: str, agent: str = "young", **options) -> dict[str, Any]:
        """提交任务"""
        return await self._client.post("/tasks", json={"task": task, "agent": agent, **options})

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """获取任务状态"""
        return await self._client.get(f"/tasks/{task_id}")

    async def cancel_task(self, task_id: str) -> dict[str, Any]:
        """取消任务"""
        return await self._client.post(f"/tasks/{task_id}/cancel", json={})


# ====================
# SDK Factory
# ====================


class OpenYoungSDK:
    """OpenYoung SDK主类

    统一访问所有API功能
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self._client = APIClientBase(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.evaluations = EvaluationSDK(self._client)
        self.agents = AgentSDK(self._client)
        self.tasks = TaskSDK(self._client)

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        return await self._client.get("/health")

    async def close(self):
        """关闭客户端"""
        # Async client cleanup if needed
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ====================
# Documentation Helpers
# ====================


def create_api_docs_config() -> dict[str, Any]:
    """创建API文档配置"""
    return {
        "title": "OpenYoung API",
        "description": """
        OpenYoung - AI Agent Orchestration Platform

        ## Features
        - Multi-agent coordination and orchestration
        - Task scheduling with DAG execution
        - Agent evaluation and metrics
        - Real-time streaming responses

        ## Authentication
        Pass your API key in the Authorization header:
        ```
        Authorization: Bearer YOUR_API_KEY
        ```
        """,
        "version": "1.0.0",
        "contact": {"name": "OpenYoung Team", "url": "https://github.com/ruvnet/openyoung"},
        "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    }


# 导出
__all__ = [
    "APIClientBase",
    "EvaluationSDK",
    "AgentSDK",
    "TaskSDK",
    "OpenYoungSDK",
    "create_api_docs_config",
    "SchemaExample",
    "create_schema_example",
    "create_error_schema",
]
