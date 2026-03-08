LLM Provider 抽象层

提供统一的 LLM 调用接口，支持不同 Provider 的差异

## Classes

### `BaseLLMProvider`

LLM Provider 抽象基类

**Methods:**
- `get_profile`

### `OpenAIProvider`

OpenAI Provider

### `AnthropicProvider`

Anthropic Provider

### `DeepSeekProvider`

DeepSeek Provider

### `ProviderFactory`

Provider 工厂类

**Methods:**
- `create`
- `create_from_model`

## Functions

### `get_profile()`

获取模型能力配置

### `create()`

创建 Provider 实例

### `create_from_model()`

从模型名创建 Provider
