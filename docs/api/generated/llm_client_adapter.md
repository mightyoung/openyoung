LLM Client 适配器

将新的 UnifiedLLMClient 适配为与现有 LLMClient 相同的接口
保持向后兼容

## Classes

### `LLMClient`

LLM 客户端适配器

统一接口，内部使用 UnifiedLLMClient
保持与原有 LLMClient 的向后兼容

**Methods:**
- `get_model`
- `get_capabilities`
- `get_profile`

## Functions

### `get_client()`

获取 LLM 客户端实例

### `get_model()`

获取当前模型

### `get_capabilities()`

获取模型能力

### `get_profile()`

获取模型配置
