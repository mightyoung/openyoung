LLM Provider 核心类型定义

统一抽象层，支持不同 LLM Provider 的差异

## Classes

### `Capability`

LLM 能力枚举

### `Provider`

支持的 LLM Provider

### `ModelProfile`

模型能力描述

### `LLMResponse`

统一的 LLM 响应格式

### `Message`

统一的消息格式

## Functions

### `get_model_profile()`

获取模型能力配置

### `detect_provider()`

从模型名检测 Provider
