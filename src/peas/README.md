# PEAS - 规划执行对齐系统
# Plan-Execution Alignment System

[English](README_EN.md) | 中文

---

## 概述

PEAS (Plan-Execution Alignment System) 是一个用于将Agent执行与用户提供的设计规格对齐的系统。它通过解析Markdown设计文档、构建可执行合约、追踪功能点执行状态并检测偏离来确保规划与执行的一致性。

## 核心功能

- **Markdown解析** - 解析设计文档，提取功能点、验收标准和优先级
- **意图提取** - 从文档中提取核心意图和约束条件
- **合约构建** - 构建可执行的验证合约
- **功能追踪** - 追踪功能点的执行状态
- **偏离检测** - 检测执行与规划的偏离程度

## 快速开始

```python
from peas import MarkdownParser, ContractBuilder, FeatureTracker, DriftDetector

# 1. 解析Markdown文档
parser = MarkdownParser()
doc = parser.parse(markdown_content)

# 2. 构建合约
builder = ContractBuilder(llm_client)
contract = builder.build(doc)

# 3. 验证执行结果
tracker = FeatureTracker(contract, llm_client)
statuses = await tracker.verify(execution_result)

# 4. 检测偏离
detector = DriftDetector()
report = detector.detect(statuses, contract)
```

## 目录结构

```
src/peas/
├── types/           # 类型定义
├── understanding/   # 文档理解 (MarkdownParser, IntentExtractor)
├── contract/        # 合约构建 (ContractBuilder)
├── verification/    # 验证追踪 (FeatureTracker, DriftDetector)
├── integration/     # Harness集成 (PEASHarnessIntegration)
└── llm/            # LLM客户端
```

## 测试

```bash
# 运行所有测试
pytest tests/peas/ -v

# 测试统计
# - Parser测试: 14个
# - Contract测试: 11个
# - Verification测试: 16个
# - E2E测试: 30个
# 总计: 71个测试
```

## 核心类型

### Priority (优先级)
```python
from peas import Priority

MUST = "must"    # 必须实现
SHOULD = "should" # 应该实现
COULD = "could"  # 可以实现
```

### FeaturePoint (功能点)
```python
from peas import FeaturePoint

fp = FeaturePoint(
    id="FP-001",
    title="用户认证",
    description="实现基于JWT的用户认证",
    priority=Priority.MUST,
    acceptance_criteria=["given...when...then..."]
)
```

### DriftReport (偏离报告)
```python
from peas import DriftReport

report = DriftReport(
    drift_score=15.5,
    level=DriftLevel.MINOR,
    verified_count=8,
    failed_count=1,
    total_count=9,
    recommendations=["建议添加会话超时处理"]
)
```

## 与Harness集成

PEAS可以与Harness引擎集成，实现带对齐检查的执行：

```python
from peas import PEASHarnessIntegration

integration = PEASHarnessIntegration(
    llm_client=llm_client,
    harness_config=HarnessConfig()
)

# 解析规格文档
integration.parse_spec(markdown_content)

# 构建合约
contract = integration.build_contract()

# 执行并验证
result = await integration.execute(task_description)
```

## 安全特性

- 输入大小限制: 10MB
- 路径遍历保护
- 预编译正则表达式

## 许可证

MIT
