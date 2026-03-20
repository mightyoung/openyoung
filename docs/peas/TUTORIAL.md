# PEAS Tutorial

## 概述

本教程将指导您从基础到高级使用PEAS系统。我们将涵盖：
1. 基本使用流程
2. 高级验证策略
3. 与Harness集成
4. 自定义扩展

## 教程1: 基础使用

### 目标
学习如何使用PEAS解析Markdown文档并验证执行结果。

### 步骤1: 准备Markdown规格文档

```markdown
# 电商系统 PRD

## 功能需求

### 用户模块

- Feature: 用户注册
  - 用户通过邮箱注册账户
  - Must: 发送验证邮件
  - Should: 记录注册时间

- Feature: 用户登录
  - 支持邮箱+密码登录
  - Must: 验证密码正确性
```

### 步骤2: 解析和构建合约

```python
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

# 1. 解析文档
parser = MarkdownParser()
doc = parser.parse(markdown_content)

print(f"标题: {doc.title}")
print(f"功能点: {doc.total_features}")
print(f"必须实现: {len(doc.must_features)}")

# 2. 构建合约
builder = ContractBuilder()
contract = builder.build(doc)

print(f"需求数: {contract.total_requirements}")
for req in contract.requirements:
    print(f"  {req.req_id}: {req.priority.value} - {req.verification_method}")
```

### 步骤3: 验证执行结果

```python
# 模拟实现代码
implementation = """
已实现用户注册功能：
- 创建用户表存储用户信息
- 实现注册API接口
- 集成邮件服务发送验证邮件
- 验证链接有效期24小时

已实现用户登录功能：
- 实现登录API接口
- 密码使用bcrypt加密存储
- 验证密码正确性后返回JWT
"""

# 验证
tracker = FeatureTracker(contract)
results = tracker.verify_sync(implementation)

# 查看结果
for status in results:
    symbol = "✓" if status.is_verified() else "✗"
    print(f"{symbol} {status.req_id}: {status.status.value}")
```

## 教程2: LLM验证

### 目标
使用LLM进行更准确的语义验证。

### 配置LLM客户端

```python
# 方式1: 使用项目LLM客户端
from src.llm import get_llm_client

llm_client = get_llm_client()

# 方式2: 自定义客户端
class MyLLMClient:
    async def generate(self, prompt: str) -> str:
        # 调用你的LLM API
        return "PASS - 实现了所需功能"
```

### 使用LLM验证

```python
import asyncio

async def verify_with_llm():
    # 创建带LLM的追踪器
    tracker = FeatureTracker(contract, llm_client=llm_client)

    # 异步验证
    results = await tracker.verify(implementation)

    for status in results:
        print(f"{status.req_id}: {status.status.value}")
        if status.evidence:
            print(f"  证据: {status.evidence[0]}")

asyncio.run(verify_with_llm())
```

## 教程3: 偏离检测

### 目标
学习如何检测和分析执行与合约的偏离。

### 完整流程

```python
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

# 解析
parser = MarkdownParser()
doc = parser.parse(prd_content)

# 构建
builder = ContractBuilder()
contract = builder.build(doc)

# 不完整的实现
partial_implementation = """
只实现了用户注册功能，但还没做登录功能。
"""

# 验证
tracker = FeatureTracker(contract)
results = tracker.verify_sync(partial_implementation)

# 检测偏离
detector = DriftDetector()
report = detector.detect(results, contract)

print(f"对齐率: {report.alignment_rate:.1f}%")
print(f"偏离级别: {report.level.name}")
print(f"通过: {report.verified_count}/{report.total_count}")
print(f"失败: {report.failed_count}/{report.total_count}")

# 建议
if report.recommendations:
    print("\n建议:")
    for rec in report.recommendations:
        print(f"  - {rec}")
```

### 偏离级别判断

| 级别 | 对齐率 | 处理建议 |
|------|--------|----------|
| NONE | 100% | 完美，继续 |
| MINOR | 75-99% | 轻微问题，可接受 |
| MODERATE | 50-74% | 需要改进 |
| SEVERE | 25-49% | 需要重新规划 |
| CRITICAL | 0-24% | 合约失败 |

## 教程4: Harness集成

### 目标
学习如何将PEAS与HarnessEngine集成。

### 基础集成

```python
from src.peas import PEASHarnessIntegration

# 创建集成
integration = PEASHarnessIntegration(
    llm_client=None,  # 可选LLM客户端
    harness_config=None  # 可选Harness配置
)

# 1. 解析规格
doc = integration.parse_spec(spec_content)

# 2. 构建合约
contract = integration.build_contract()

# 3. 执行并验证
result = await integration.execute(
    task_description="实现用户管理系统",
    context={"user_id": "123"}
)

# 4. 获取结果
print(f"对齐率: {result['alignment_rate']:.1f}%")
print(f"偏离报告: {result['drift_report']}")
```

### 自定义执行器

```python
from src.peas import PEASHarnessIntegration

async def my_executor(task: str, context: dict) -> str:
    # 调用你的AI代理执行任务
    result = await my_agent.execute(task)
    return result

integration = PEASHarnessIntegration()
doc = integration.parse_spec(spec_content)
contract = integration.build_contract()

result = await integration.execute(
    task_description="实现...",
    executor_fn=my_executor
)
```

### 流式执行

```python
async def streaming_example():
    integration = PEASHarnessIntegration()
    doc = integration.parse_spec(spec_content)
    contract = integration.build_contract()

    async for event in integration.execute_streaming("实现用户管理"):
        print(f"阶段: {event['phase']}")
        print(f"迭代: {event['iteration']}")
        print(f"状态: {event['status']}")
        print("---")
```

## 教程5: 高级用法

### 自定义验证策略

```python
from src.peas import (
    ContractBuilder,
    ContractRequirement,
    Priority,
)

builder = ContractBuilder()

# 手动创建特定需求
requirements = [
    ContractRequirement(
        req_id="REQ-001",
        description="必须使用HTTPS",
        priority=Priority.MUST,
        verification_method="regex",
        verification_prompt=None,
        metadata={"pattern": r"https://"}
    ),
    ContractRequirement(
        req_id="REQ-002",
        description="密码加密",
        priority=Priority.MUST,
        verification_method="llm_judge",
        verification_prompt="验证密码是否加密存储"
    ),
]

# 构建合约
from src.peas.types import ExecutionContract
from datetime import datetime

contract = ExecutionContract(
    contract_id="custom-001",
    version="1.0",
    created_at=datetime.now(),
    requirements=requirements
)
```

### 批量验证

```python
from src.peas import FeatureTracker

# 验证多个实现版本
versions = [
    ("v1.0", implementation_v1),
    ("v1.1", implementation_v1_1),
    ("v2.0", implementation_v2),
]

tracker = FeatureTracker(contract)

for version_name, code in versions:
    results = tracker.verify_sync(code)
    detector = DriftDetector()
    report = detector.detect(results, contract)
    print(f"{version_name}: {report.alignment_rate:.1f}%")
```

### 生成报告

```python
from src.peas import DriftReport
import json

def generate_report(tracker: FeatureTracker, contract, detector):
    statuses = list(tracker.statuses.values())
    report = detector.detect(statuses, contract)

    return {
        "contract_id": contract.contract_id,
        "version": contract.version,
        "summary": tracker.get_summary(),
        "alignment_rate": report.alignment_rate,
        "drift_level": report.level.name,
        "details": [
            {
                "req_id": s.req_id,
                "status": s.status.value,
                "evidence": s.evidence
            }
            for s in statuses
        ]
    }

report = generate_report(tracker, contract, detector)
print(json.dumps(report, indent=2, ensure_ascii=False))
```

## 最佳实践

### 1. 规格文档格式

```markdown
# 功能名称

## 功能描述

- Feature: 功能点名称
- Must: 必须实现的要求
- Should: 应该实现的要求
- Could: 可选实现

### 验收标准

Given [前提]
When [操作]
Then [预期结果]
```

### 2. 验证时机

- **开发阶段**: 使用正则验证快速反馈
- **测试阶段**: 使用LLM验证准确性
- **生产阶段**: 结合两种方式

### 3. 偏离阈值

建议根据项目阶段设置不同阈值：
- 开发阶段: >70% 可接受
- 测试阶段: >85% 可接受
- 发布阶段: >95% 可接受
