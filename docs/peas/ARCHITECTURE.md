# PEAS Architecture Design

## System Overview

PEAS (Plan-Execution Alignment System) 是一个用于确保AI代理执行与设计规范保持一致的系统。它通过解析设计文档、构建执行合约、追踪功能点状态和检测偏离来实现这一目标。

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PEAS Architecture                              │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   Markdown   │
     │     Spec     │
     └──────┬───────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Understanding Layer                              │
│  ┌──────────────────┐    ┌─────────────────────┐                      │
│  │  MarkdownParser  │    │  IntentExtractor    │                      │
│  │  • 提取标题      │    │  • 提取意图         │                      │
│  │  • 提取章节      │    │  • 约束条件         │                      │
│  │  • 提取功能点    │    │  • 质量标准         │                      │
│  │  • 验收标准      │    │                     │                      │
│  └────────┬─────────┘    └──────────┬──────────┘                      │
│           │                          │                                   │
│           └───────────┬──────────────┘                                   │
│                       ▼                                                   │
│              ┌─────────────────┐                                         │
│              │ ParsedDocument  │                                         │
│              │  • title        │                                         │
│              │  • sections     │                                         │
│              │  • features     │                                         │
│              └────────┬────────┘                                         │
└───────────────────────┼──────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Contract Layer                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       ContractBuilder                             │    │
│  │  • 从ParsedDocument构建ExecutionContract                        │    │
│  │  • 为每个功能点生成验证方法和prompt                               │    │
│  │  • 确定验证策略(LLM/正则/手动)                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     ExecutionContract                             │    │
│  │  contract_id, version, requirements[], intent                    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Verification Layer                                  │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐    │
│  │    FeatureTracker    │    │         DriftDetector              │    │
│  │  • 追踪功能点状态    │    │  • 计算偏离分数                    │    │
│  │  • LLM验证           │    │  • 评估偏离级别                    │    │
│  │  • 正则验证          │    │  • 生成建议                        │    │
│  └──────────┬───────────┘    └─────────────┬──────────────────────┘    │
│             │                                │                           │
│             ▼                                ▼                           │
│  ┌──────────────────────┐    ┌────────────────────────────────────┐      │
│  │   FeatureStatus[]    │    │         DriftReport                │      │
│  │  • req_id            │    │  • alignment_rate                  │      │
│  │  • status            │    │  • level (NONE-MINOR-MODERATE)     │      │
│  │  • evidence          │    │  • recommendations                 │      │
│  └──────────────────────┘    └────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Integration Layer                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                   PEASHarnessIntegration                          │    │
│  │  • 与HarnessEngine集成                                           │    │
│  │  • 支持流式执行                                                   │    │
│  │  • 自动验证和偏离检测                                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Types Module (`src/peas/types/`)

#### Document Types (`document.py`)
- `Priority`: 需求优先级枚举 (MUST/SHOULD/COULD)
- `FeaturePoint`: 功能点数据结构
- `ParsedDocument`: 解析后的文档对象

#### Contract Types (`contract.py`)
- `ContractRequirement`: 合约需求
- `IntentSpec`: 意图规格
- `ExecutionContract`: 执行合约

#### Verification Types (`verification.py`)
- `VerificationStatus`: 验证状态 (PENDING/VERIFIED/FAILED/SKIPPED)
- `DriftLevel`: 偏离级别 (NONE/MINOR/MODERATE/SEVERE/CRITICAL)
- `FeatureStatus`: 功能点状态
- `DriftReport`: 偏离报告

### 2. Understanding Module (`src/peas/understanding/`)

#### MarkdownParser
解析Markdown设计文档，提取：
- 文档标题
- 章节结构
- 功能点列表
- 优先级标记
- 验收标准 (Given-When-Then)

#### IntentExtractor
从文档中提取用户意图和约束条件

### 3. Contract Module (`src/peas/contract/`)

#### ContractBuilder
负责将ParsedDocument转换为ExecutionContract：
- 为每个功能点创建ContractRequirement
- 确定验证方法（LLM/正则/手动）
- 生成验证prompt
- 设置元数据

### 4. Verification Module (`src/peas/verification/`)

#### FeatureTracker
追踪功能点的验证状态：
- `verify()`: 异步验证（需要LLM）
- `verify_sync()`: 同步验证（正则匹配）
- `get_summary()`: 获取验证摘要

#### DriftDetector
计算执行与合约的对齐情况：
- `detect()`: 生成偏离报告
- `detect_from_tracker()`: 从tracker生成报告
- 评估对齐率和建议

### 5. Integration Module (`src/peas/integration/`)

#### PEASHarnessIntegration
与HarnessEngine的集成：
- `parse_spec()`: 解析规格文档
- `build_contract()`: 构建执行合约
- `execute()`: 执行并验证
- `execute_streaming()`: 流式执行

## Data Flow

```
1. Input: Markdown Specification
           │
           ▼
2. Parse: MarkdownParser.parse()
           │ 返回 ParsedDocument
           ▼
3. Build: ContractBuilder.build()
           │ 返回 ExecutionContract
           ▼
4. Execute: Agent performs task
           │ 产生执行结果
           ▼
5. Verify: FeatureTracker.verify()
           │ 返回 FeatureStatus[]
           ▼
6. Detect: DriftDetector.detect()
           │ 返回 DriftReport
           ▼
7. Output: Alignment report + feedback
```

## Priority Levels

| Level | Enum | Description |
|-------|------|-------------|
| Must | `Priority.MUST` | 必须实现，验证失败视为合约违反 |
| Should | `Priority.SHOULD` | 应该实现，验证失败降低对齐率 |
| Could | `Priority.COULD` | 可选实现，验证失败不影响合约 |

## Verification Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| `llm_judge` | 使用LLM进行语义验证 | 有验收标准的功能点 |
| `regex` | 关键词匹配验证 | 简单功能点 |
| `manual` | 手动验证 | 复杂或敏感功能点 |

## Drift Levels

| Level | Score Range | Action |
|-------|-------------|--------|
| NONE | 0% | 完美对齐 |
| MINOR | 1-25% | 轻微偏离，可接受 |
| MODERATE | 26-50% | 中度偏离，建议改进 |
| SEVERE | 51-75% | 严重偏离，需要重新规划 |
| CRITICAL | 76-100% | 关键偏离，合约失败 |

## Extension Points

### Custom Executor
```python
async def custom_executor(task: str, context: dict) -> str:
    # 实现自定义执行逻辑
    return result

integration = PEASHarnessIntegration()
result = await integration.execute(task, executor_fn=custom_executor)
```

### Custom Evaluator
```python
async def custom_evaluator(result, phase, context) -> bool:
    # 实现自定义评估逻辑
    return True
```

## Performance Considerations

- Parser使用预编译正则表达式
- 支持同步/异步验证模式
- 流式执行减少延迟
- 内容大小限制(10MB)防止恶意输入
