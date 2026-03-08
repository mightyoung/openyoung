"""
LLM Provider 核心类型定义

统一抽象层，支持不同 LLM Provider 的差异
"""

from dataclasses import dataclass, field
from enum import Enum


class Capability(Enum):
    """LLM 能力枚举"""
    VISION = "vision"
    THINKING = "thinking"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    JSON_MODE = "json_mode"
    TOOL_USE = "tool_use"


class Provider(Enum):
    """支持的 LLM Provider"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass
class ModelProfile:
    """模型能力描述"""
    model: str
    provider: Provider
    capabilities: list[Capability] = field(default_factory=list)
    supports_thinking: bool = False
    thinking_budget_max: int | None = None
    context_window: int = 4096
    max_output_tokens: int | None = None
    unsupported_params: list[str] = field(default_factory=list)
    thinking_param_name: str | None = None  # Provider 特定的 thinking 参数名


@dataclass
class LLMResponse:
    """统一的 LLM 响应格式"""
    content: str
    reasoning: str | None = None  # 统一的 reasoning 字段
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    provider: str = ""
    finish_reason: str | None = None


@dataclass
class Message:
    """统一的消息格式"""
    role: str  # "system", "user", "assistant"
    content: str
    name: str | None = None
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None


# ========== 模型能力配置 ==========

MODEL_PROFILES: dict[str, ModelProfile] = {
    # OpenAI
    "o1": ModelProfile(
        model="o1",
        provider=Provider.OPENAI,
        capabilities=[Capability.THINKING],
        supports_thinking=True,
        thinking_budget_max=100000,
        context_window=200000,
        max_output_tokens=100000,
        unsupported_params=["temperature", "top_p", "logprobs", "frequency_penalty", "presence_penalty"],
    ),
    "o1-mini": ModelProfile(
        model="o1-mini",
        provider=Provider.OPENAI,
        capabilities=[Capability.THINKING],
        supports_thinking=True,
        thinking_budget_max=65000,
        context_window=128000,
        max_output_tokens=65000,
        unsupported_params=["temperature", "top_p", "logprobs", "frequency_penalty", "presence_penalty"],
    ),
    "o3": ModelProfile(
        model="o3",
        provider=Provider.OPENAI,
        capabilities=[Capability.THINKING],
        supports_thinking=True,
        thinking_budget_max=200000,
        context_window=200000,
        max_output_tokens=100000,
        unsupported_params=["temperature", "top_p", "logprobs", "frequency_penalty", "presence_penalty"],
    ),
    "gpt-4o": ModelProfile(
        model="gpt-4o",
        provider=Provider.OPENAI,
        capabilities=[Capability.VISION, Capability.FUNCTION_CALLING, Capability.STREAMING],
        supports_thinking=False,
        context_window=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelProfile(
        model="gpt-4o-mini",
        provider=Provider.OPENAI,
        capabilities=[Capability.VISION, Capability.FUNCTION_CALLING, Capability.STREAMING],
        supports_thinking=False,
        context_window=128000,
        max_output_tokens=16384,
    ),

    # Anthropic
    "claude-sonnet-4-20250514": ModelProfile(
        model="claude-sonnet-4-20250514",
        provider=Provider.ANTHROPIC,
        capabilities=[Capability.THINKING, Capability.VISION],
        supports_thinking=True,
        thinking_budget_max=32000,
        context_window=200000,
        max_output_tokens=8192,
        thinking_param_name="thinking",
    ),
    "claude-3-5-sonnet-20241022": ModelProfile(
        model="claude-3-5-sonnet-20241022",
        provider=Provider.ANTHROPIC,
        capabilities=[Capability.THINKING, Capability.VISION],
        supports_thinking=True,
        thinking_budget_max=32000,
        context_window=200000,
        max_output_tokens=8192,
        thinking_param_name="thinking",
    ),
    "claude-3-opus-20240229": ModelProfile(
        model="claude-3-opus-20240229",
        provider=Provider.ANTHROPIC,
        capabilities=[Capability.VISION],
        supports_thinking=False,
        context_window=200000,
        max_output_tokens=4096,
    ),
    "claude-3-haiku-20240307": ModelProfile(
        model="claude-3-haiku-20240307",
        provider=Provider.ANTHROPIC,
        capabilities=[Capability.VISION],
        supports_thinking=False,
        context_window=200000,
        max_output_tokens=4096,
    ),

    # DeepSeek
    "deepseek-chat": ModelProfile(
        model="deepseek-chat",
        provider=Provider.DEEPSEEK,
        capabilities=[Capability.FUNCTION_CALLING],
        supports_thinking=False,
        context_window=64000,
        max_output_tokens=4096,
    ),
    "deepseek-reasoner": ModelProfile(
        model="deepseek-reasoner",
        provider=Provider.DEEPSEEK,
        capabilities=[Capability.THINKING],
        supports_thinking=True,
        thinking_budget_max=32000,
        context_window=64000,
        max_output_tokens=4096,
        thinking_param_name="thinking",
        unsupported_params=["temperature", "top_p", "logprobs"],
    ),

    # Google
    "gemini-2.0-flash": ModelProfile(
        model="gemini-2.0-flash",
        provider=Provider.GOOGLE,
        capabilities=[Capability.THINKING, Capability.VISION],
        supports_thinking=True,
        thinking_budget_max=1024,
        context_window=1000000,
    ),
    "gemini-1.5-pro": ModelProfile(
        model="gemini-1.5-pro",
        provider=Provider.GOOGLE,
        capabilities=[Capability.VISION, Capability.FUNCTION_CALLING],
        supports_thinking=False,
        context_window=2000000,
        max_output_tokens=8192,
    ),

    # Ollama
    "llama3": ModelProfile(
        model="llama3",
        provider=Provider.OLLAMA,
        capabilities=[],
        supports_thinking=False,
        context_window=8192,
        max_output_tokens=4096,
    ),
    "qwen2.5": ModelProfile(
        model="qwen2.5",
        provider=Provider.OLLAMA,
        capabilities=[],
        supports_thinking=False,
        context_window=32768,
        max_output_tokens=4096,
    ),
}


def get_model_profile(model: str) -> ModelProfile:
    """获取模型能力配置"""
    # 精确匹配
    if model in MODEL_PROFILES:
        return MODEL_PROFILES[model]

    # 前缀匹配
    for profile_model, profile in MODEL_PROFILES.items():
        if model.startswith(profile_model) or profile_model in model:
            return profile

    # 默认配置
    return ModelProfile(
        model=model,
        provider=Provider.CUSTOM,
        capabilities=[],
        supports_thinking=False,
        context_window=4096,
    )


def detect_provider(model: str) -> Provider:
    """从模型名检测 Provider"""
    model_lower = model.lower()

    if model_lower.startswith("gpt") or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return Provider.OPENAI
    if "claude" in model_lower:
        return Provider.ANTHROPIC
    if "deepseek" in model_lower:
        return Provider.DEEPSEEK
    if "gemini" in model_lower:
        return Provider.GOOGLE
    if model_lower in ["llama", "qwen", "mistral", "phi"]:
        return Provider.OLLAMA

    return Provider.CUSTOM
