"""
LLM 模块 - 统一 LLM Provider 抽象层

支持多种 LLM Provider，统一的接口处理不同模型的差异
"""

from .client_adapter import (
    LLMClient,
    get_client,
)
from .providers import (
    AnthropicProvider,
    BaseLLMProvider,
    DeepSeekProvider,
    OpenAIProvider,
    ProviderFactory,
)
from .types import (
    MODEL_PROFILES,
    Capability,
    LLMResponse,
    Message,
    ModelProfile,
    Provider,
    detect_provider,
    get_model_profile,
)
from .unified_client import (
    UnifiedLLMClient,
    create_client,
)

__all__ = [
    # 类型
    "Capability",
    "Provider",
    "ModelProfile",
    "LLMResponse",
    "Message",
    # 函数
    "get_model_profile",
    "detect_provider",
    "MODEL_PROFILES",
    # Provider
    "BaseLLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "DeepSeekProvider",
    "ProviderFactory",
    # 客户端
    "UnifiedLLMClient",
    "create_client",
    # 适配器（向后兼容）
    "LLMClient",
    "get_client",
]
