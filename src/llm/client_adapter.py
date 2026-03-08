"""
LLM Client 适配器

将新的 UnifiedLLMClient 适配为与现有 LLMClient 相同的接口
保持向后兼容
"""

import os
from typing import Any

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.llm.types import Message as UnifiedMessage
from src.llm.unified_client import UnifiedLLMClient


class LLMClient:
    """LLM 客户端适配器

    统一接口，内部使用 UnifiedLLMClient
    保持与原有 LLMClient 的向后兼容
    """

    def __init__(self, model: str | None = None):
        # 优先使用环境变量中的 API Key
        api_key = (
            os.getenv("OPENAI_API_KEY") or
            os.getenv("DEEPSEEK_API_KEY") or
            os.getenv("ANTHROPIC_API_KEY")
        )

        # 默认模型
        default_model = model or os.getenv("OPENYOUNG_MODEL", "deepseek-chat")

        # 创建统一客户端
        self._client = UnifiedLLMClient(
            api_key=api_key,
            default_model=default_model,
        )

        # 保持与旧接口兼容的属性
        self.model = default_model
        self._last_response = None

    def get_model(self) -> str:
        """获取当前模型"""
        return self.model

    async def chat(  # type: ignore[override]
        self,
        messages_or_model: any = None,
        model_or_messages: any = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        model: str | None = None,  # 新接口专用
        messages: list[dict[str, str]] | None = None,  # 支持 keyword argument
        **kwargs
    ) -> dict[str, Any]:
        """发送聊天请求 - 支持两种接口:

        新接口: chat(messages, model=model)
        旧接口: chat(model, messages)
        keyword: chat(model=..., messages=...)

        Args:
            messages_or_model: 消息列表或模型名称
            model_or_messages: 模型名称或消息列表
            temperature: 温度
            max_tokens: 最大 token 数
            model: 模型名称（新接口专用）
            messages: 消息列表（keyword argument）
        """
        # 支持 keyword argument 传入 messages
        if messages is not None:
            # 直接使用 keyword argument
            actual_messages = messages
        elif isinstance(messages_or_model, str):
            # 旧接口: chat(model, messages)
            model = messages_or_model
            actual_messages = model_or_messages
        else:
            # 新接口: chat(messages, model=model)
            actual_messages = messages_or_model
            if model is None:
                model = model_or_messages

        return await self._chat_impl(actual_messages, model, temperature, max_tokens, **kwargs)

    async def _chat_impl(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """内部实现"""
        model = model or self.model

        # 转换消息格式
        unified_messages = [
            UnifiedMessage(role=m["role"], content=m["content"])
            for m in messages
        ]

        # 调用统一客户端
        response = await self._client.chat(
            model=model,
            messages=unified_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # 转换为旧接口格式
        self._last_response = response
        return self._to_old_format(response)

    async def chat_with_thinking(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        thinking_budget: int | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """发送带 Thinking 的请求"""
        model = model or self.model

        unified_messages = [
            UnifiedMessage(role=m["role"], content=m["content"])
            for m in messages
        ]

        response = await self._client.chat_with_thinking(
            model=model,
            messages=unified_messages,
            thinking_budget=thinking_budget,
            **kwargs
        )

        self._last_response = response
        return self._to_old_format(response)

    def _to_old_format(self, response) -> dict[str, Any]:
        """转换为旧接口格式 - 保持与原 client.py 兼容

        旧格式: {"choices": [{"message": {"content": ..., "tool_calls": ...}}], "usage": {...}}
        """
        # 构建 message 结构（兼容旧格式）
        message = {
            "content": response.content or "",
        }

        # 如果有 tool_calls，也包含在内（从 reasoning 或其他字段解析）
        if hasattr(response, 'tool_calls') and response.tool_calls:
            message["tool_calls"] = response.tool_calls

        return {
            "choices": [{"message": message}],
            "usage": response.usage or {},
            "model": response.model,
            "finish_reason": response.finish_reason,
        }

    def get_capabilities(self, model: str | None = None) -> dict[str, bool]:
        """获取模型能力"""
        return self._client.get_capabilities(model or self.model)

    def get_profile(self, model: str | None = None):
        """获取模型配置"""
        return self._client.get_profile(model or self.model)

    async def close(self):
        """关闭客户端连接"""
        if hasattr(self._client, 'close'):
            await self._client.close()


# 便捷函数：创建客户端
def get_client(model: str | None = None) -> LLMClient:
    """获取 LLM 客户端实例"""
    return LLMClient(model=model)
