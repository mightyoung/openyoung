# LLM Provider 抽象层实现计划

> 创建日期: 2026-03-05

## 目标

实现统一的 LLM Provider 抽象层，支持不同模型的 thinking 模式差异

## 架构设计

```
┌─────────────────────────────────────────────┐
│           UnifiedLLMClient (Facade)         │
│  - chat()                                   │
│  - chat_with_reasoning()                    │
│  - get_capabilities()                       │
└─────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐    ┌─────────────────────┐
│   ModelProfile     │    │  ProviderFactory    │
│ - capabilities     │    │  - detect_provider  │
│ - thinking_config  │    │  - create_client   │
│ - context_limit    │    └─────────────────────┘
└─────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│          Provider Implementations            │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐   │
│  │ OpenAI  │ │Anthropic │ │ DeepSeek  │   │
│  └─────────┘ └─────────┘ └──────────┘   │
└─────────────────────────────────────────────┘
```

## 实现步骤

### Phase 1: 创建核心类型定义 ✅
- [x] 1.1 创建 `Capability` 枚举
- [x] 1.2 创建 `ModelProfile` 数据类
- [x] 1.3 创建 `LLMResponse` 统一响应
- [x] 1.4 添加主流模型能力配置

### Phase 2: 实现 Provider 抽象 ✅
- [x] 2.1 创建 `BaseLLMProvider` 抽象类
- [x] 2.2 创建 `ProviderFactory` 工厂类

### Phase 3: 实现 Provider ✅
- [x] 3.1 实现 `OpenAIProvider`
- [x] 3.2 实现 `AnthropicProvider`
- [x] 3.3 实现 `DeepSeekProvider`

### Phase 4: 实现 UnifiedLLMClient ✅
- [x] 4.1 创建统一客户端
- [x] 4.2 实现 thinking 模式支持
- [x] 4.3 实现响应归一化

### Phase 5: 集成到现有代码 ✅
- [x] 5.1 创建适配器 (client_adapter.py)
- [x] 5.2 保持向后兼容

## 进度

### 2026-03-05

| 步骤 | 状态 |
|------|------|
| 计划创建 | ✅ |
| | |

## 决策记录

- 架构选择: 分层抽象 + Model Profile
- 实现策略: 渐进式，保持向后兼容
