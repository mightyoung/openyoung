# PEAS Getting Started Guide

## 安装要求

- Python 3.10+
- 本项目依赖已安装

## 基本使用流程

### 步骤1: 解析Markdown规格文档

```python
from src.peas import MarkdownParser

# 从字符串解析
parser = MarkdownParser()
doc = parser.parse("""
# 项目名称 PRD

## 功能需求

### 用户认证
- Feature: 用户注册
- Feature: 用户登录
""")

# 或从文件解析
doc = parser.parse_file("path/to/spec.md")
```

### 步骤2: 构建执行合约

```python
from src.peas import ContractBuilder

builder = ContractBuilder()
contract = builder.build(doc)
print(f"合约ID: {contract.contract_id}")
print(f"需求数量: {contract.total_requirements}")
```

### 步骤3: 验证执行结果

```python
from src.peas import FeatureTracker

# 创建追踪器
tracker = FeatureTracker(contract)

# 同步验证（不使用LLM）
results = tracker.verify_sync("实现代码...")

# 或异步验证（使用LLM）
results = await tracker.verify("实现代码...")
```

### 步骤4: 检测偏离

```python
from src.peas import DriftDetector

detector = DriftDetector()
report = detector.detect(results, contract)

print(f"对齐率: {report.alignment_rate}%")
print(f"偏离级别: {report.level}")
print(f"通过: {report.verified_count}, 失败: {report.failed_count}")
```

## 完整示例

```python
import asyncio
from src.peas import (
    MarkdownParser,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
)

# 示例PRD内容
PRD_CONTENT = """
# 电商系统 PRD

## 1. 功能需求

### 1.1 用户注册

- Feature: 邮箱注册
- 必须发送验证邮件

### 1.2 用户登录

- Feature: 密码登录
- Should: 记住登录状态

### 1.3 购物车

- Feature: 添加商品
- Must: 支持数量修改
- Must: 支持删除商品
"""

async def main():
    # 1. 解析
    parser = MarkdownParser()
    doc = parser.parse(PRD_CONTENT)
    print(f"解析完成: {doc.title}, {doc.total_features}个功能点")

    # 2. 构建合约
    builder = ContractBuilder()
    contract = builder.build(doc)
    print(f"合约构建: {contract.total_requirements}个需求")

    # 3. 模拟执行结果
    execution_result = """
    已实现邮箱注册功能，发送验证邮件到用户邮箱。
    已实现密码登录功能，包含记住登录状态。
    已实现购物车添加商品功能，支持数量修改和删除。
    """

    # 4. 验证
    tracker = FeatureTracker(contract)
    results = tracker.verify_sync(execution_result)

    # 5. 检测偏离
    detector = DriftDetector()
    report = detector.detect(results, contract)

    print(f"\n验证结果:")
    print(f"  对齐率: {report.alignment_rate:.1f}%")
    print(f"  偏离级别: {report.level.name}")
    print(f"  通过: {report.verified_count}/{report.total_count}")
    print(f"  失败: {report.failed_count}/{report.total_count}")

asyncio.run(main())
```

## 输出示例

```
解析完成: 电商系统 PRD, 6个功能点
合约构建: 6个需求

验证结果:
  对齐率: 100.0%
  偏离级别: NONE
  通过: 6/6
  失败: 0/6
```

## 下一

- [API Reference](api-reference.md) - 详细API文档
- [Tutorial](tutorial.md) - 高级使用教程
- [Architecture](architecture.md) - 架构设计
