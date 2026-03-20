# PEAS - 规划执行对齐系统
# Plan-Execution Alignment System

[English](README_EN.md) | 中文

---

## 概述

PEAS (Plan-Execution Alignment System) 是一个用于将代理执行与用户提供的设计规范对齐的系统。它确保AI代理按照设计文档中的功能需求和验收标准执行任务。

## 核心功能

### 1. Markdown规格解析
- 支持解析Markdown格式的设计文档(PRD)
- 提取功能点、优先级、验收标准
- 支持中英文混合文档

### 2. 执行合约构建
- 从解析结果构建可执行的合约
- 自动确定验证方法(LLM/正则/手动)
- 生成验证prompt

### 3. 功能点追踪
- 追踪每个功能点的验证状态
- 支持LLM验证和正则验证
- 提供详细的验证摘要

### 4. 偏离检测
- 计算执行与合约的对齐率
- 评估偏离级别(无/轻微/中度/严重/关键)
- 提供改进建议

## 快速开始

```python
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

# 1. 解析Markdown文档
parser = MarkdownParser()
doc = parser.parse("""
# 用户管理系统 PRD

## 功能需求

### 用户注册
- Feature: 邮箱验证码注册
- 必须发送验证邮件到用户邮箱
""")

# 2. 构建执行合约
builder = ContractBuilder()
contract = builder.build(doc)

# 3. 验证执行结果
tracker = FeatureTracker(contract)
results = tracker.verify_sync("已实现邮箱验证码注册功能...")

# 4. 检测偏离
detector = DriftDetector()
report = detector.detect(results, contract)
print(f"对齐率: {report.alignment_rate}%")
```

## 系统架构

```
┌─────────────────┐
│ Markdown Spec   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ MarkdownParser  │──▶ ParsedDocument
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ContractBuilder │──▶ ExecutionContract
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ FeatureTracker  │──▶ FeatureStatus[]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DriftDetector   │──▶ DriftReport
└─────────────────┘
```

## 模块说明

| 模块 | 说明 |
|------|------|
| `types` | 数据类型定义 (Priority, FeaturePoint, Contract等) |
| `understanding` | MarkdownParser, IntentExtractor |
| `contract` | ContractBuilder |
| `verification` | FeatureTracker, DriftDetector |
| `integration` | PEASHarnessIntegration |

## 文档索引

- [API参考](API.md) - 完整的API文档
- [架构设计](ARCHITECTURE.md) - 系统架构详解
- [教程](TUTORIAL.md) - 逐步使用指南
- [快速开始](getting-started.md) - 快速入门指南
- [贡献指南](contribution.md) - 如何贡献代码

## 测试

```bash
# 运行所有测试
pytest tests/peas/ -v
```

## 许可证

MIT
