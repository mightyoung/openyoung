PackageManager Storage - 持久化存储层

## Classes

### `PackageMetadata`

包元数据

### `LLMProviderConfig`

LLM Provider 配置

### `PackageStorage`

包存储管理器 - 负责持久化

**Methods:**
- `registry_file`
- `providers_file`
- `sources_file`
- `lock_file`
- `load_registry`
- `save_registry`
- `add_package`
- `remove_package`
- `get_package`
- `list_packages`
- `load_providers`
- `save_providers`
- `add_provider`
- `remove_provider`
- `get_provider`
- `list_providers`
- `set_default_provider`
- `get_default_provider`

### `LockManager`

Lock 文件管理器

**Methods:**
- `load_lock`
- `save_lock`
- `generate_lock`

## Functions

### `registry_file()`

### `providers_file()`

### `sources_file()`

### `lock_file()`

### `load_registry()`

加载注册表

### `save_registry()`

保存注册表

### `add_package()`

添加包到注册表

### `remove_package()`

从注册表移除包

### `get_package()`

获取包

### `list_packages()`

列出包

### `load_providers()`

加载 LLM Provider 配置

### `save_providers()`

保存 LLM Provider 配置

### `add_provider()`

添加 LLM Provider

### `remove_provider()`

移除 LLM Provider

### `get_provider()`

获取 LLM Provider

### `list_providers()`

列出 LLM Providers

### `set_default_provider()`

设置默认 Provider

### `get_default_provider()`

获取默认 Provider

### `load_lock()`

加载 lock 文件

### `save_lock()`

保存 lock 文件

### `generate_lock()`

生成 lock 文件
