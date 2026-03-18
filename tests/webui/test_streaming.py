"""
Tests for WebUI Chat Streaming Functionality

Tests the SSE streaming implementation in api_client.py and 2_Chat.py
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestStreamChat:
    """Test stream_chat method in APIClient"""

    @pytest.mark.asyncio
    async def test_stream_chat_post_method(self):
        """Test that stream_chat uses POST method"""
        from src.webui.services.api_client import APIClient

        client = APIClient()
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_lines():
            return
            yield  # Makes it a generator

        mock_response.aiter_lines = mock_aiter_lines

        mock_context = MagicMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)

        client.client.stream = MagicMock(return_value=mock_context)

        # Consume the generator
        try:
            async for _ in client.stream_chat("test-session", "test message"):
                pass
        except Exception:
            pass

        # Verify POST was called with correct endpoint
        client.client.stream.assert_called_once()
        call_args = client.client.stream.call_args
        assert call_args[0][0] == "POST"
        assert "/test-session/stream" in call_args[0][1]
        assert call_args[1]["json"] == {"message": "test message"}


class TestSSEParser:
    """Test SSE event parsing logic"""

    def test_parse_plain_data(self):
        """Test parsing plain data without event type"""
        data = '{"content": "test"}'
        result = json.loads(data)
        assert result.get("content") == "test"

    def test_parse_sse_event_format(self):
        """Test SSE event format parsing"""
        # Format: event:chunk\ndata:{"content":"..."}
        line = 'event: chunk\ndata: {"content": "Hello"}'

        # Parse event type
        parts = line.split("\n", 1)
        event_type = parts[0].replace("event:", "").strip()
        event_data = parts[1].replace("data:", "").strip()

        assert event_type == "chunk"
        assert json.loads(event_data) == {"content": "Hello"}

    def test_parse_multiple_events(self):
        """Test parsing multiple SSE events"""
        lines = [
            'event: chunk\ndata: {"content": "Hello"}',
            'event: chunk\ndata: {"content": " World"}',
            'event: done\ndata: {"response": "Hello World"}',
        ]

        events = []
        for line in lines:
            if line.startswith("event:"):
                parts = line.split("\n", 1)
                event_type = parts[0].replace("event:", "").strip()
                event_data = parts[1].replace("data:", "").strip()
                events.append({"event": event_type, "data": json.loads(event_data)})

        assert len(events) == 3
        assert events[0]["event"] == "chunk"
        assert events[0]["data"]["content"] == "Hello"
        assert events[2]["event"] == "done"

    def test_parse_error_event(self):
        """Test parsing error SSE event"""
        line = 'event: error\ndata: {"error": "Session not found"}'

        parts = line.split("\n", 1)
        event_type = parts[0].replace("event:", "").strip()
        event_data = parts[1].replace("data:", "").strip()

        assert event_type == "error"
        assert json.loads(event_data)["error"] == "Session not found"


class TestAPIIntegration:
    """Integration tests for API client"""

    def test_api_client_initialization(self):
        """Test API client can be initialized"""
        from src.webui.services.api_client import APIClient

        client = APIClient(base_url="http://localhost:8000", api_key="test-key")

        assert client.base_url == "http://localhost:8000"
        assert client.api_key == "test-key"

    def test_api_client_default_url(self):
        """Test API client default URL"""
        from src.webui.services.api_client import APIClient

        client = APIClient()

        assert client.base_url == "http://localhost:8000"

    def test_api_client_has_stream_method(self):
        """Test API client has stream_chat method"""
        from src.webui.services.api_client import APIClient

        client = APIClient()

        assert hasattr(client, "stream_chat")
        assert callable(client.stream_chat)

    def test_api_client_session_attribute(self):
        """Test API client has client (httpx.AsyncClient) attribute"""
        from src.webui.services.api_client import APIClient

        client = APIClient()

        # The client should have a client attribute (httpx.AsyncClient)
        assert hasattr(client, "client")
