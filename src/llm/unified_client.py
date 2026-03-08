"""
UnifiedLLMClient - 统一 LLM 客户端

整合所有 Provider，提供统一的接口
"""

import os
from collections.abc import AsyncIterator

from .providers import (
    BaseLLMProvider,
    ProviderFactory,
)
from .types import (
    LLMResponse,
    Message,
    ModelProfile,
    Provider,
    detect_provider,
    get_model_profile,
)


class UnifiedLLMClient:
    """统一 LLM 客户端

    用法示例:
    ```python
    client = UnifiedLLMClient()

    # 普通聊天
    response = await client.chat(
        model="gpt-4o",
        messages=[Message(role="user", content="Hello")]
    )

    # Thinking 模式
    response = await client.chat_with_thinking(
        model="o1",
        messages=[Message(role="user", content="Solve this problem...")]
    )

    # 流式输出
    async for chunk in client.stream_chat(
        model="gpt-4o",
        messages=[Message(role="user", content="Tell me a story")]
    ):
        print(chunk, end="")
    ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str = "deepseek-chat",
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self._provider_cache: dict[Provider, BaseLLMProvider] = {}

    def _get_provider(self, model: str) -> BaseLLMProvider:
        """获取或创建 Provider 实例"""
        provider = detect_provider(model)

        if provider not in self._provider_cache:
            self._provider_cache[provider] = ProviderFactory.create(
                provider,
                api_key=self.api_key,
                base_url=self.base_url,
            )

        return self._provider_cache[provider]

    def get_profile(self, model: str = None) -> ModelProfile:
        """获取模型能力配置"""
        model = model or self.default_model
        return get_model_profile(model)

    def get_capabilities(self, model: str = None) -> dict[str, bool]:
        """获取模型能力"""
        profile = self.get_profile(model)
        cap_values = [c.value for c in profile.capabilities]
        return {
            "vision": "vision" in cap_values,
            "thinking": profile.supports_thinking,
            "function_calling": "function_calling" in cap_values,
            "streaming": "streaming" in cap_values,
        }

    async def chat(
        self,
        model: str | None = None,
        messages: list[Message] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求

        Args:
            model: 模型名，默认使用 default_model
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大输出 token
            **kwargs: 其他参数

        Returns:
            LLMResponse: 统一的响应格式
        """
        model = model or self.default_model
        messages = messages or []

        provider = self._get_provider(model)
        return await provider.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def chat_with_thinking(
        self,
        model: str | None = None,
        messages: list[Message] | None = None,
        thinking_budget: int | None = None,
        **kwargs
    ) -> LLMResponse:
        """发送带 Thinking 的请求

        Args:
            model: 模型名
            messages: 消息列表
            thinking_budget: thinking token 预算

        Returns:
            LLMResponse: 包含 reasoning 字段的响应
        """
        model = model or self.default_model
        messages = messages or []

        provider = self._get_provider(model)
        return await provider.chat_with_thinking(
            messages=messages,
            model=model,
            thinking_budget=thinking_budget,
            **kwargs
        )

    async def stream_chat(
        self,
        model: str | None = None,
        messages: list[Message] | None = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式聊天"""
        model = model or self.default_model
        messages = messages or []

        provider = self._get_provider(model)
        async for chunk in provider.stream_chat(messages=messages, model=model, **kwargs):
            yield chunk

    async def validate_connection(self, model: str | None = None) -> bool:
        """验证连接是否有效"""
        try:
            model = model or self.default_model
            # 发送最简单的请求验证
            response = await self.chat(
                model=model,
                messages=[Message(role="user", content="ping")],
                max_tokens=1,
            )
            return response.content is not None
        except Exception:
            return False


# ========== 便捷函数 ==========

def create_client(
    model: str | None = None,
    api_key: str | None = None,
    **kwargs
) -> UnifiedLLMClient:
    """创建统一客户端的便捷函数"""
    # 从环境变量获取 API Key
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")

    return UnifiedLLMClient(
        api_key=api_key,
        default_model=model or "deepseek-chat",
        **kwargs
    )
