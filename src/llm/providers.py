"""
LLM Provider 抽象层

提供统一的 LLM 调用接口，支持不同 Provider 的差异
"""

import json
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

import httpx

from .types import (
    LLMResponse,
    Message,
    ModelProfile,
    Provider,
    detect_provider,
    get_model_profile,
)

# 全局共享的 HTTP 客户端，支持连接池复用
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """获取全局共享的 HTTP 客户端（懒加载单例）"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            timeout=60.0,
        )
    return _http_client


async def close_http_client() -> None:
    """关闭全局 HTTP 客户端，释放连接池资源"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


class BaseLLMProvider(ABC):
    """LLM Provider 抽象基类"""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def chat_with_thinking(
        self, messages: list[Message], model: str, thinking_budget: int | None = None, **kwargs
    ) -> LLMResponse:
        """发送带 thinking 的请求"""
        pass

    @abstractmethod
    async def stream_chat(
        self, messages: list[Message], model: str, **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天"""
        pass

    async def close(self) -> None:
        """关闭 provider，释放资源（子类可重写）"""
        pass

    def get_profile(self, model: str) -> ModelProfile:
        """获取模型能力配置"""
        return get_model_profile(model)

    def _filter_unsupported_params(self, model: str, params: dict) -> dict:
        """过滤不支持的参数"""
        profile = self.get_profile(model)
        if not profile.unsupported_params:
            return params

        return {k: v for k, v in params.items() if k not in profile.unsupported_params}


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider"""

    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        profile = get_model_profile(model)

        # 构建请求
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **self._filter_unsupported_params(
                model,
                {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            ),
        }

        # 添加工具调用
        if kwargs.get("tools"):
            payload["tools"] = kwargs["tools"]

        # 调用 API
        headers = {"Authorization": f"Bearer {self.api_key}"}
        base = self.base_url or "https://api.openai.com/v1"

        client = get_http_client()
        response = await client.post(
            f"{base}/chat/completions", json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # 解析响应
        msg = data["choices"][0]["message"]
        return LLMResponse(
            content=msg.get("content", ""),
            reasoning=msg.get("reasoning_content"),  # o1/o3 特有
            usage=data.get("usage", {}),
            model=model,
            provider="openai",
            finish_reason=data["choices"][0].get("finish_reason"),
        )

    async def chat_with_thinking(
        self, messages: list[Message], model: str, thinking_budget: int | None = None, **kwargs
    ) -> LLMResponse:
        # o1/o3 系列通过模型名启用 thinking，无需额外参数
        return await self.chat(messages, model, **kwargs)

    async def stream_chat(
        self, messages: list[Message], model: str, **kwargs
    ) -> AsyncIterator[str]:
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        base = self.base_url or "https://api.openai.com/v1"

        client = get_http_client()
        async with client.stream(
            "POST", f"{base}/chat/completions", json=payload, headers=headers
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                    yield content


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Provider"""

    async def chat(
        self,
        messages: list[Message],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        # 构建消息格式
        claude_messages = []
        for m in messages:
            if m.role == "system":
                claude_messages.append({"role": "user", "content": f"\n\nSystem: {m.content}"})
            else:
                claude_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": model,
            "messages": claude_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
        }

        # 添加 thinking
        if kwargs.get("thinking"):
            payload["thinking"] = kwargs["thinking"]
            if kwargs.get("thinking_budget"):
                payload["thinking"]["budget"] = kwargs["thinking_budget"]

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        base = self.base_url or "https://api.anthropic.com"

        client = get_http_client()
        response = await client.post(
            f"{base}/v1/messages", json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # 解析响应
        thinking_content = ""
        text_content = ""

        for block in data.get("content", []):
            if block.get("type") == "thinking":
                thinking_content = block.get("thinking", "")
            elif block.get("type") == "text":
                text_content = block.get("text", "")

        return LLMResponse(
            content=text_content,
            reasoning=thinking_content,
            usage={
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            model=model,
            provider="anthropic",
        )

    async def chat_with_thinking(
        self, messages: list[Message], model: str, thinking_budget: int | None = None, **kwargs
    ) -> LLMResponse:
        thinking = {"type": "enabled", "budget": thinking_budget or 1024}
        return await self.chat(
            messages, model, thinking=thinking, thinking_budget=thinking_budget, **kwargs
        )

    async def stream_chat(
        self, messages: list[Message], model: str, **kwargs
    ) -> AsyncIterator[str]:
        # Anthropic 支持流式但实现较复杂，暂时返回空
        response = await self.chat(messages, model, **kwargs)
        yield response.content


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek Provider"""

    async def chat(
        self,
        messages: list[Message],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        profile = get_model_profile(model)

        # 构建请求
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **self._filter_unsupported_params(
                model,
                {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            ),
        }

        # deepseek-reasoner 需要 extra_body
        if profile.supports_thinking and kwargs.get("thinking"):
            payload["extra_body"] = {
                "thinking": {"type": "enabled", "max_tokens": kwargs.get("thinking_budget", 32000)}
            }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        base = self.base_url or "https://api.deepseek.com/v1"

        client = get_http_client()
        response = await client.post(
            f"{base}/chat/completions", json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()

        # 解析响应
        msg = data["choices"][0]["message"]
        return LLMResponse(
            content=msg.get("content", ""),
            reasoning=msg.get("reasoning_content"),
            usage=data.get("usage", {}),
            model=model,
            provider="deepseek",
        )

    async def chat_with_thinking(
        self,
        messages: list[Message],
        model: str = "deepseek-reasoner",
        thinking_budget: int | None = None,
        **kwargs,
    ) -> LLMResponse:
        return await self.chat(
            messages, model, thinking=True, thinking_budget=thinking_budget, **kwargs
        )

    async def stream_chat(
        self, messages: list[Message], model: str, **kwargs
    ) -> AsyncIterator[str]:
        # 类似 OpenAI 的流式实现
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        base = self.base_url or "https://api.deepseek.com/v1"

        client = get_http_client()
        async with client.stream(
            "POST", f"{base}/chat/completions", json=payload, headers=headers
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        yield content


class ProviderFactory:
    """Provider 工厂类"""

    _providers = {
        Provider.OPENAI: OpenAIProvider,
        Provider.ANTHROPIC: AnthropicProvider,
        Provider.DEEPSEEK: DeepSeekProvider,
    }

    @classmethod
    def create(cls, provider: Provider, **kwargs) -> BaseLLMProvider:
        """创建 Provider 实例"""
        provider_class = cls._providers.get(provider)
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider}")

        # 从环境变量获取 API Key
        api_key = kwargs.get("api_key")
        if not api_key:
            env_keys = {
                Provider.OPENAI: "OPENAI_API_KEY",
                Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
                Provider.DEEPSEEK: "DEEPSEEK_API_KEY",
            }
            api_key = os.getenv(env_keys.get(provider, ""))

        return provider_class(api_key=api_key, base_url=kwargs.get("base_url"))

    @classmethod
    def create_from_model(cls, model: str, **kwargs) -> BaseLLMProvider:
        """从模型名创建 Provider"""
        provider = detect_provider(model)
        return cls.create(provider, **kwargs)
