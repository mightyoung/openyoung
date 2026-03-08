PackageManager Provider - LLM Provider 管理

## Classes

### `ProviderManager`

LLM Provider 管理器

**Methods:**
- `available_providers`
- `get_provider_info`
- `get_models_for_provider`
- `detect_provider_type`
- `get_api_key_from_env`
- `get_base_url`
- `validate_provider_config`
- `create_provider_from_env`
- `load_all_from_env`
- `get_provider_for_model`

## Functions

### `available_providers()`

获取可用的 Provider 类型

### `get_provider_info()`

获取 Provider 配置信息

### `get_models_for_provider()`

获取 Provider 支持的模型列表

### `detect_provider_type()`

根据模型名检测 Provider 类型

### `get_api_key_from_env()`

从环境变量获取 API Key

### `get_base_url()`

获取 Provider 的 Base URL

### `validate_provider_config()`

验证 Provider 配置是否有效

### `create_provider_from_env()`

从环境变量创建 Provider 配置

### `load_all_from_env()`

从环境变量加载所有已配置的 Providers

### `get_provider_for_model()`

根据模型获取 Provider 配置
