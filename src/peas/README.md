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
├── understanding/   # 文档理解 (MarkdownParser, HTMLParser)
├── contract/        # 合约构建 (ContractBuilder)
├── verification/    # 验证追踪 (FeatureTracker, DriftDetector, UIComparator)
├── integration/     # Harness集成 (PEASHarnessIntegration)
├── learning/       # 偏好学习 (PreferenceLearner)
├── monitoring/     # 指标监控 (MetricsCollector)
└── llm/            # LLM客户端
```

## 测试

```bash
# 运行所有测试
pytest tests/peas/ -v

# 测试统计 (247个测试)
# - Parser测试: 33个 (MarkdownParser + HTMLParser)
# - Contract测试: 11个
# - Verification测试: 30个 (FeatureTracker + DriftDetector + UIComparator)
# - Integration测试: 11个 (Harness集成)
# - Performance测试: 11个
# - Metrics测试: 18个
# - PreferenceLearner测试: 22个
# - Security测试: 35个
# - E2E测试: 36个
# - StyleProfiler测试: 17个
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

## HTML原型解析

支持从HTML设计文档中提取功能点：

```python
from peas import HTMLParser

parser = HTMLParser()
doc = parser.parse(html_content)
```

支持的格式：
- HTML注释: `<!-- Feature: 功能名 -->`
- data属性: `<div data-feature="xxx" data-priority="must">`
- HTML元素: button, input, form等

## 视觉对比

UIComparator支持UI结构对比和差异检测：

```python
from peas import UIComparator

comparator = UIComparator()
diff = comparator.compare(baseline_html, current_html)
```

## 风格分析

StyleProfiler分析文档写作风格，用于生成一致的输出：

```python
from peas import StyleProfiler

profiler = StyleProfiler()
profile = profiler.analyze(markdown_content)
# profile.tone, profile.doc_type, profile.language 等
```

支持的风格分析：
- 文档类型检测（SPEC, API, GUIDE, CHANGELOG, README）
- 语调分析（正式、随意、技术性、商业、学术）
- 语言检测（中文、英文、混合）
- 技术术语密度
- 章节深度和风格一致性

## 偏好学习

PreferenceLearner学习用户验证偏好，自动调整验证阈值：

```python
from peas import PreferenceLearner

learner = PreferenceLearner(window_size=20, learning_rate=0.1)
await learner.record_feedback("feature_1", accepted=True)
threshold = await learner.get_adjusted_threshold("feature_1")
```

## 指标监控

MetricsCollector收集和暴露Prometheus格式指标：

```python
from peas.monitoring import get_metrics_collector, record_parse_time

collector = get_metrics_collector()
record_parse_time(8.5)  # 毫秒

# 获取Prometheus格式指标
metrics = collector.get_metrics()
```

## 安全特性

PEAS实现了多层安全防护来保护系统免受恶意输入攻击：

### 输入验证

- **内容大小限制**: 所有解析器强制执行10MB输入大小限制，防止DoS攻击
- **编码检测**: 使用UTF-8编码实际字节数计算，防止Unicode编码绕过

### 路径遍历保护

- **目录隔离**: `parse_file`方法支持`allowed_dir`参数，限制文件访问范围
- **路径解析**: 使用`pathlib.Path.resolve()`解析绝对路径，防止符号链接绕过
- **相对路径验证**: 检查`../`等相对路径遍历尝试

### XSS防护

- **输出转义**: 提供`title_escaped`、`raw_content_escaped`等属性用于安全HTML显示
- **FeaturePoint转义**: `title_escaped`和`description_escaped`属性自动转义HTML特殊字符
- **使用方式**:
  ```python
  # 不安全 - 可能导致XSS
  print(doc.title)

  # 安全 - 自动转义
  print(doc.title_escaped)
  ```

### DoS防护

- **预编译正则表达式**: 所有正则表达式在模块级别预编译，避免重复编译开销
- **嵌套深度限制**: 解析器可以处理大量嵌套结构（如10000层嵌套div）
- **属性数量限制**: 单元素支持大量属性（如1000个data-*属性）

## 安全测试

```bash
# 运行安全测试
pytest tests/peas/test_security.py -v
```

安全测试覆盖：
- 路径遍历攻击（绝对路径、相对路径、Windows风格）
- 内容大小限制（刚好限制、超过限制、Unicode编码）
- DoS攻击（大量标题、深度嵌套、超长行）
- XSS payloads（script标签、事件处理器、javascript:URI）

## 许可证

MIT
