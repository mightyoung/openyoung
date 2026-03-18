"""
API Client - OpenYoung WebUI Backend Communication
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx


class APIClient:
    """API 客户端 - 与 OpenYoung 后端通信"""

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or "http://localhost:8000"
        self.api_key = api_key or ""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    # ========== Session API ==========

    async def create_session(
        self, agent_name: str, initial_context: Dict = None, session_id: str = None
    ) -> Dict[str, Any]:
        """创建会话"""
        data = {
            "agent_name": agent_name,
            "initial_context": initial_context or {},
        }
        if session_id:
            data["session_id"] = session_id

        response = await self.client.post("/api/sessions", json=data)
        response.raise_for_status()
        return response.json()

    async def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出所有会话"""
        response = await self.client.get(f"/api/sessions?limit={limit}")
        response.raise_for_status()
        return response.json().get("items", [])

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取会话详情"""
        response = await self.client.get(f"/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """发送消息"""
        response = await self.client.post(
            f"/api/sessions/{session_id}/messages", json={"message": message}
        )
        response.raise_for_status()
        return response.json()

    async def delete_session(self, session_id: str) -> None:
        """删除会话"""
        response = await self.client.delete(f"/api/sessions/{session_id}")
        response.raise_for_status()

    # ========== Agent API ==========

    async def list_agents(self, search: str = None) -> List[Dict[str, Any]]:
        """列出所有可用 Agent"""
        params = {}
        if search:
            params["search"] = search
        response = await self.client.get("/api/agents", params=params)
        response.raise_for_status()
        return response.json().get("items", [])

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """获取 Agent 详情"""
        response = await self.client.get(f"/api/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

    # ========== Execution API (Evaluation) ==========

    async def list_executions(
        self,
        session_id: str = None,
        agent_name: str = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """列出执行记录"""
        params = {"limit": limit, "offset": offset}
        if session_id:
            params["session_id"] = session_id
        if agent_name:
            params["agent_name"] = agent_name
        if status:
            params["status"] = status

        response = await self.client.get("/api/v1/executions", params=params)
        response.raise_for_status()
        return response.json()

    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """获取执行详情"""
        response = await self.client.get(f"/api/v1/executions/{execution_id}")
        response.raise_for_status()
        return response.json()

    # ========== Evaluation API ==========

    async def list_evaluations(self, execution_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """列出评估记录"""
        params = {"limit": limit}
        if execution_id:
            params["execution_id"] = execution_id

        response = await self.client.get("/api/v1/evaluations", params=params)
        response.raise_for_status()
        return response.json()

    async def get_evaluation(self, evaluation_id: str) -> Dict[str, Any]:
        """获取评估详情"""
        response = await self.client.get(f"/api/v1/evaluations/{evaluation_id}")
        response.raise_for_status()
        return response.json()

    # ========== Evaluation APIs ==========

    async def list_datasets(self) -> List[Dict[str, Any]]:
        """列出可用数据集"""
        response = await self.client.get("/api/v1/datasets")
        response.raise_for_status()
        return response.json().get("items", [])

    async def run_evaluation(
        self,
        agent_id: str,
        dataset_id: str,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """运行评估"""
        data = {
            "agent_id": agent_id,
            "dataset_id": dataset_id,
            **(config or {}),
        }
        response = await self.client.post("/api/v1/evaluations/run", json=data)
        response.raise_for_status()
        return response.json()

    async def stream_evaluation(
        self, evaluation_id: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取评估进度"""
        async with self.client.stream(
            "GET", f"/api/v1/evaluations/{evaluation_id}/stream"
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        data = line[5:].strip()
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        pass

    # ========== Stream API ==========

    async def stream_chat(
        self, session_id: str, message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式获取聊天响应 (POST版本)

        使用SSE协议，支持实时流式输出
        """
        async with self.client.stream(
            "POST",
            f"/api/sessions/{session_id}/stream",
            json={"message": message},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        data = line[5:].strip()
                        # 解析SSE事件格式: event:chunk\ndata:{...}
                        if data.startswith("event:"):
                            # 处理event:开头的SSE格式
                            parts = data.split("\n", 1)
                            if len(parts) > 1:
                                event_type = parts[0].replace("event:", "").strip()
                                event_data = parts[1].replace("data:", "").strip()
                                yield {"event": event_type, "data": json.loads(event_data)}
                        else:
                            yield json.loads(data)
                    except json.JSONDecodeError:
                        pass

    async def stream_execution(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取执行状态"""
        async with self.client.stream("GET", f"/api/v1/stream/{task_id}") as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    try:
                        yield json.loads(line[5:])
                    except json.JSONDecodeError:
                        pass

    # ========== Health Check ==========

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
