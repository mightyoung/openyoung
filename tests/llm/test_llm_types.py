"""
LLM Types Tests
"""

import pytest

from src.llm.types import (
    MODEL_PROFILES,
    Capability,
    LLMResponse,
    Message,
    ModelProfile,
    Provider,
    detect_provider,
    get_model_profile,
)


class TestCapability:
    def test_capability_values(self):
        assert Capability.VISION.value == "vision"
        assert Capability.THINKING.value == "thinking"
        assert Capability.FUNCTION_CALLING.value == "function_calling"
        assert Capability.STREAMING.value == "streaming"


class TestProvider:
    def test_provider_values(self):
        assert Provider.OPENAI.value == "openai"
        assert Provider.ANTHROPIC.value == "anthropic"
        assert Provider.DEEPSEEK.value == "deepseek"


class TestModelProfile:
    def test_deepseek_chat_profile(self):
        profile = get_model_profile("deepseek-chat")
        assert profile.model == "deepseek-chat"
        assert profile.provider == Provider.DEEPSEEK
        assert profile.supports_thinking is False

    def test_deepseek_reasoner_profile(self):
        profile = get_model_profile("deepseek-reasoner")
        assert profile.model == "deepseek-reasoner"
        assert profile.provider == Provider.DEEPSEEK
        assert profile.supports_thinking is True

    def test_o1_profile(self):
        profile = get_model_profile("o1")
        assert profile.model == "o1"
        assert profile.provider == Provider.OPENAI
        assert profile.supports_thinking is True

    def test_claude_profile(self):
        profile = get_model_profile("claude-sonnet-4-20250514")
        assert profile.model == "claude-sonnet-4-20250514"
        assert profile.provider == Provider.ANTHROPIC


class TestDetectProvider:
    def test_detect_openai_models(self):
        assert detect_provider("gpt-4o") == Provider.OPENAI
        assert detect_provider("o1") == Provider.OPENAI
        assert detect_provider("gpt-3.5-turbo") == Provider.OPENAI

    def test_detect_deepseek_models(self):
        assert detect_provider("deepseek-chat") == Provider.DEEPSEEK
        assert detect_provider("deepseek-reasoner") == Provider.DEEPSEEK

    def test_detect_anthropic_models(self):
        assert detect_provider("claude-3-opus") == Provider.ANTHROPIC
        assert detect_provider("claude-sonnet-4-20250514") == Provider.ANTHROPIC


class TestMessage:
    def test_message_creation(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_with_name(self):
        msg = Message(role="system", content="You are helpful", name="system")
        assert msg.name == "system"


class TestLLMResponse:
    def test_response_creation(self):
        resp = LLMResponse(
            content="Hello world",
            model="gpt-4o",
            provider="openai",
        )
        assert resp.content == "Hello world"
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"

    def test_response_with_reasoning(self):
        resp = LLMResponse(
            content="Answer",
            reasoning="Thinking process",
            model="deepseek-reasoner",
            provider="deepseek",
        )
        assert resp.reasoning == "Thinking process"
