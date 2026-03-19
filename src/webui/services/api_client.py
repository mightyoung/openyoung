"""
API Client - OpenYoung WebUI Backend Communication
"""

import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

# SSE parsing regex - handles various line endings (CRLF, LF, CR)
SSE_EVENT_RE = re.compile(r"^event:([^\r\n]*)(?:\r\n|\r|\n)")
SSE_DATA_RE = re.compile(r"^data:([^\r\n]*)(?:\r\n|\r|\n)")


def parse_sse_line(line: str) -> tuple[str, str] | None:
    """
    Parse a single SSE-formatted line using regex.

    Args:
        line: A single line from SSE stream

    Returns:
        Tuple of (field_type, value) where field_type is 'event' or 'data',
        or None if the line doesn't match either pattern
    """
    if match := SSE_EVENT_RE.match(line):
        return ("event", match.group(1))
    if match := SSE_DATA_RE.match(line):
        return ("data", match.group(1))
    return None


def parse_sse_data(data_str: str) -> Any:
    """
    Parse SSE data field, handling various formats gracefully.

    Args:
        data_str: The data content after 'data:' prefix

    Returns:
        Parsed JSON or the raw string if parsing fails

    Raises:
        No exceptions - malformed data returns the raw string
    """
    data_str = data_str.strip()
    if not data_str:
        return None
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        return data_str


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
                result = parse_sse_line(line)
                if result is not None:
                    field_type, value = result
                    if field_type == "data":
                        parsed = parse_sse_data(value)
                        if parsed is not None:
                            yield parsed

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
            # Track pending event type and data across lines
            pending_event = None
            async for line in response.aiter_lines():
                result = parse_sse_line(line)
                if result is not None:
                    field_type, value = result
                    if field_type == "event":
                        pending_event = value.strip()
                    elif field_type == "data":
                        parsed = parse_sse_data(value)
                        if parsed is not None:
                            if pending_event:
                                yield {"event": pending_event, "data": parsed}
                                pending_event = None
                            else:
                                yield parsed

    async def stream_execution(self, task_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取执行状态"""
        async with self.client.stream("GET", f"/api/v1/stream/{task_id}") as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                result = parse_sse_line(line)
                if result is not None:
                    field_type, value = result
                    if field_type == "data":
                        parsed = parse_sse_data(value)
                        if parsed is not None:
                            yield parsed

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
