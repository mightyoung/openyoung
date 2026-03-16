"""
Testing Utilities - Agent Testing Infrastructure

提供测试用的 Mock、Fixture 和工具类
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MessageRole(Enum):
    """消息角色"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class MockMessage:
    """模拟消息"""

    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_calls: Optional[list] = None


@dataclass
class MockChoice:
    """模拟选择"""

    message: MockMessage
    finish_reason: str = "stop"


@dataclass
class MockUsage:
    """模拟使用统计"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class MockResponse:
    """模拟LLM响应"""

    choices: list[MockChoice]
    usage: MockUsage = field(default_factory=MockUsage)
    model: str = "mock-model"
    id: str = "mock-id"


class FakeLLMClient:
    """Fake LLM 客户端 - 用于测试

    特性:
    - 可配置响应
    - 支持异步
    - 记录调用历史
    """

    def __init__(
        self,
        response: str = "Mocked response",
        delay: float = 0.0,
        should_fail: bool = False,
        error_message: str = "Mock error",
    ):
        self.response = response
        self.delay = delay
        self.should_fail = should_fail
        self.error_message = error_message
        self._call_history: list[dict[str, Any]] = []

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> MockResponse:
        """模拟聊天完成调用"""
        # 记录调用
        self._call_history.append(
            {
                "messages": messages,
                "kwargs": kwargs,
            }
        )

        # 模拟延迟
        if self.delay > 0:
            await asyncio.sleep(self.delay)

        # 模拟错误
        if self.should_fail:
            raise RuntimeError(self.error_message)

        # 返回模拟响应
        return MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        role=MessageRole.ASSISTANT,
                        content=self.response,
                    )
                )
            ],
            usage=MockUsage(
                prompt_tokens=sum(len(m.get("content", "")) for m in messages) // 4,
                completion_tokens=len(self.response) // 4,
                total_tokens=sum(len(m.get("content", "")) for m in messages) // 4
                + len(self.response) // 4,
            ),
        )

    def get_call_history(self) -> list[dict[str, Any]]:
        """获取调用历史"""
        return self._call_history.copy()

    def clear_history(self):
        """清除调用历史"""
        self._call_history.clear()


class StreamingFakeLLMClient(FakeLLMClient):
    """流式 Fake LLM 客户端"""

    async def create(self, messages: list[dict[str, str]], **kwargs):
        """创建响应 - 统一接口"""
        stream = kwargs.get("stream", False)
        if stream:
            return self._stream_response(messages)
        return await self.chat(messages, **kwargs)

    async def _stream_response(self, messages: list[dict[str, str]]):
        """内部流式响应生成器"""
        words = self.response.split()
        for i, word in enumerate(words):
            yield MockResponse(
                choices=[
                    MockChoice(
                        message=MockMessage(
                            role=MessageRole.ASSISTANT,
                            content=word + (" " if i < len(words) - 1 else ""),
                        )
                    )
                ],
            )
            await asyncio.sleep(0.01)


class MockAgentConfig:
    """模拟 Agent 配置"""

    def __init__(
        self,
        name: str = "test-agent",
        model: str = "mock-model",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs,
    ):
        self.name = name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.extra = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return getattr(self, key, default) or self.extra.get(key, default)


# ====================
# Pytest Fixtures
# ====================

import pytest


@pytest.fixture
def fake_llm_client():
    """Fake LLM 客户端 Fixture"""
    return FakeLLMClient()


@pytest.fixture
def streaming_llm_client():
    """流式 LLM 客户端 Fixture"""
    return StreamingFakeLLMClient()


@pytest.fixture
def mock_agent_config():
    """模拟 Agent 配置 Fixture"""
    return MockAgentConfig()


@pytest.fixture
def event_loop():
    """事件循环 Fixture - 用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ====================
# 测试辅助函数
# ====================


def create_test_message(
    role: MessageRole = MessageRole.USER,
    content: str = "Test message",
    name: Optional[str] = None,
) -> dict[str, str]:
    """创建测试消息字典"""
    msg = {"role": role.value, "content": content}
    if name:
        msg["name"] = name
    return msg


def assert_response_valid(response: MockResponse) -> bool:
    """验证响应有效性"""
    assert response is not None
    assert hasattr(response, "choices")
    assert len(response.choices) > 0
    assert response.choices[0].message is not None
    return True
