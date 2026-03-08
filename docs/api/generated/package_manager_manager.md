PackageManager - 包管理系统

## Classes

### `PackageManager`

包管理器 - 安装和管理依赖包

**Methods:**
- `list_packages`
- `get_package`
- `regenerate_lock`
- `add_provider`
- `remove_provider`
- `get_provider`
- `list_providers`
- `set_default_provider`
- `get_default_provider`
- `get_provider_for_model`
- `load_sources`
- `save_sources`
- `load_lock`
- `save_lock`

## Functions

### `list_packages()`

列出已安装的包

### `get_package()`

获取包信息

### `regenerate_lock()`

重新生成 lock 文件

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

### `get_provider_for_model()`

根据模型获取 Provider 配置

### `load_sources()`

加载 Source 配置

### `save_sources()`

保存 Source 配置

### `load_lock()`

加载 lock 文件

### `save_lock()`

保存 lock 文件
