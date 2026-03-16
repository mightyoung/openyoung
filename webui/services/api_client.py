"""
OpenYoung API Client

Based on CrewAI streamlit_ui patterns:
- https://github.com/crewAIInc/crewai_flows_streamlit_ui
- Uses httpx for async requests
- Supports SSE for streaming
"""

import asyncio
import json
from typing import AsyncGenerator, Optional

import httpx
from httpx_sse import aconnect_sse

from webui.utils.config import config


class APIClient:
    """OpenYoung API Client"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or config.API_BASE_URL
        self.api_key = api_key or config.API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    # ========== Session API ==========

    async def create_session(
        self,
        agent_name: str,
        initial_context: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Create a new session"""
        client = await self._get_client()

        payload = {
            "agent_name": agent_name,
            "initial_context": initial_context or {},
        }
        if session_id:
            payload["session_id"] = session_id

        response = await client.post("/api/sessions", json=payload)
        response.raise_for_status()
        return response.json()

    async def list_sessions(self) -> list[dict]:
        """List all sessions"""
        client = await self._get_client()
        response = await client.get("/api/sessions")
        response.raise_for_status()
        return response.json()

    async def get_session(self, session_id: str) -> dict:
        """Get session details"""
        client = await self._get_client()
        response = await client.get(f"/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    async def send_message(self, session_id: str, message: str) -> dict:
        """Send message to session"""
        client = await self._get_client()

        payload = {"message": message}
        response = await client.post(
            f"/api/sessions/{session_id}/messages",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def send_message_stream(self, session_id: str, message: str) -> AsyncGenerator[str, None]:
        """Send message and stream response (SSE)"""
        try:
            # Use POST to send message and get SSE stream
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0,
            ) as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                # Send POST request to stream endpoint
                async with client.stream(
                    "POST",
                    f"/api/sessions/{session_id}/stream",
                    json={"message": message},
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    # Read the SSE stream line by line
                    buffer = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                # Handle event format
                                if "event" in data and "data" in data:
                                    event_type = data["event"]
                                    event_data = json.loads(data["data"])
                                else:
                                    event_data = data
                                    event_type = "chunk"

                                if event_type == "chunk":
                                    content = event_data.get("content", "")
                                    if content:
                                        yield content
                                elif event_type == "done":
                                    break
                                elif event_type == "error":
                                    error = event_data.get("error", "Unknown error")
                                    yield f"\n[Error: {error}]"
                                    break
                            except json.JSONDecodeError:
                                pass

        except Exception as e:
            # Fallback: if SSE fails, use non-streaming
            result = await self.send_message(session_id, message)
            response_text = result.get("response", "")
            for char in response_text:
                yield char
                await asyncio.sleep(config.TYPING_SPEED)

    async def suspend_session(self, session_id: str) -> dict:
        """Suspend a session"""
        client = await self._get_client()
        response = await client.post(f"/api/sessions/{session_id}/suspend")
        response.raise_for_status()
        return response.json()

    async def resume_session(self, session_id: str) -> dict:
        """Resume a session"""
        client = await self._get_client()
        response = await client.post(f"/api/sessions/{session_id}/resume")
        response.raise_for_status()
        return response.json()

    async def delete_session(self, session_id: str) -> dict:
        """Delete a session"""
        client = await self._get_client()
        response = await client.delete(f"/api/sessions/{session_id}")
        response.raise_for_status()
        return response.json()

    # ========== Agent API ==========

    async def list_agents(self, search: Optional[str] = None) -> list[dict]:
        """List available agents"""
        client = await self._get_client()

        params = {}
        if search:
            params["search"] = search

        response = await client.get("/api/agents", params=params)
        response.raise_for_status()
        return response.json()

    async def get_agent(self, agent_name: str) -> dict:
        """Get agent details"""
        client = await self._get_client()
        response = await client.get(f"/api/agents/{agent_name}")
        response.raise_for_status()
        return response.json()

    # ========== Task API ==========

    async def run_task(self, agent_name: str, task: str, session_id: Optional[str] = None) -> dict:
        """Run a task"""
        client = await self._get_client()

        payload = {
            "agent_name": agent_name,
            "task": task,
        }
        if session_id:
            payload["session_id"] = session_id

        response = await client.post("/api/tasks/run", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_task_status(self, task_id: str) -> dict:
        """Get task status"""
        client = await self._get_client()
        response = await client.get(f"/api/tasks/{task_id}")
        response.raise_for_status()
        return response.json()

    async def stream_task_output(self, task_id: str) -> AsyncGenerator[str, None]:
        """Stream task output (SSE)"""
        client = await self._get_client()

        async with client.stream("GET", f"/api/stream/{task_id}") as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield data

    # ========== Health Check ==========

    async def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    # ========== Evaluation API ==========

    async def list_evaluations(
        self,
        execution_id: Optional[str] = None,
        passed: Optional[bool] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List evaluation records"""
        client = await self._get_client()

        params = {"limit": limit, "offset": offset}
        if execution_id:
            params["execution_id"] = execution_id
        if passed is not None:
            params["passed"] = passed
        if min_score is not None:
            params["min_score"] = min_score
        if max_score is not None:
            params["max_score"] = max_score

        response = await client.get("/api/evaluations", params=params)
        response.raise_for_status()
        return response.json()

    async def get_evaluation(self, evaluation_id: str) -> dict:
        """Get evaluation record details"""
        client = await self._get_client()
        response = await client.get(f"/api/evaluations/{evaluation_id}")
        response.raise_for_status()
        return response.json()

    # ========== Execution API ==========

    async def list_executions(
        self,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """List execution records"""
        client = await self._get_client()

        params = {"limit": limit, "offset": offset}
        if session_id:
            params["session_id"] = session_id
        if agent_name:
            params["agent_name"] = agent_name
        if status:
            params["status"] = status

        response = await client.get("/api/executions", params=params)
        response.raise_for_status()
        return response.json()

    async def get_execution(self, execution_id: str) -> dict:
        """Get execution record details"""
        client = await self._get_client()
        response = await client.get(f"/api/executions/{execution_id}")
        response.raise_for_status()
        return response.json()


# Singleton instance
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get API client singleton"""
    global _api_client
    if _api_client is None:
        _api_client = APIClient()
    return _api_client
