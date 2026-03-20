# PEAS API Reference

## Table of Contents

- [Types](#types)
  - [Priority](#priority)
  - [FeaturePoint](#featurepoint)
  - [ParsedDocument](#parseddocument)
  - [ContractRequirement](#contractrequirement)
  - [IntentSpec](#intentspec)
  - [ExecutionContract](#executioncontract)
  - [VerificationStatus](#verificationstatus)
  - [DriftLevel](#driftlevel)
  - [FeatureStatus](#featurestatus)
  - [DriftReport](#driftreport)
  - [FeedbackAction](#feedbackaction)
- [Core Modules](#core-modules)
  - [MarkdownParser](#markdownparser)
  - [IntentExtractor](#intentextractor)
  - [ContractBuilder](#contractbuilder)
  - [FeatureTracker](#featuretracker)
  - [DriftDetector](#driftdetector)
  - [PEASHarnessIntegration](#peasharnessintegration)

---

## Types

### Priority

```python
from peas import Priority
```

需求优先级枚举。

| Value | Description |
|-------|-------------|
| `MUST` | 必须实现 (must) |
| `SHOULD` | 应该实现 (should) |
| `COULD` | 可以实现 (could) |

**Usage:**
```python
priority = Priority.MUST
print(priority.value)  # "must"
```

---

### FeaturePoint

```python
from peas import FeaturePoint, Priority
```

功能点数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | 功能点唯一标识符 (如 "FP-001") |
| `title` | `str` | 功能点标题 |
| `description` | `str` | 功能点描述 |
| `priority` | `Priority` | 优先级 |
| `acceptance_criteria` | `list[str]` | 验收标准列表 |
| `related_section` | `Optional[str]` | 关联章节 |

**Usage:**
```python
fp = FeaturePoint(
    id="FP-001",
    title="用户认证",
    description="实现基于JWT的用户认证",
    priority=Priority.MUST,
    acceptance_criteria=["given...when...then..."],
    related_section="功能需求"
)
```

---

### ParsedDocument

```python
from peas import ParsedDocument
```

解析后的文档数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `title` | `str` | 文档标题 |
| `sections` | `list[str]` | 章节列表 |
| `feature_points` | `list[FeaturePoint]` | 功能点列表 |
| `raw_content` | `str` | 原始内容 |
| `metadata` | `dict` | 元数据 |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `total_features` | `int` | 功能点总数 |
| `must_features` | `list[FeaturePoint]` | MUST级别功能点 |
| `should_features` | `list[FeaturePoint]` | SHOULD级别功能点 |

**Usage:**
```python
parser = MarkdownParser()
doc = parser.parse(markdown_content)

print(doc.title)
print(doc.total_features)
print(doc.must_features)
```

---

### ContractRequirement

```python
from peas import ContractRequirement
```

合约需求数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `req_id` | `str` | 需求ID (如 "REQ-001") |
| `description` | `str` | 需求描述 |
| `priority` | `Priority` | 优先级 |
| `verification_method` | `str` | 验证方法 ("llm_judge", "regex", "manual") |
| `verification_prompt` | `Optional[str]` | 验证prompt |
| `metadata` | `dict` | 元数据 |

---

### IntentSpec

```python
from peas import IntentSpec
```

意图规格数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `primary_goals` | `list[str]` | 主要目标列表 |
| `constraints` | `list[str]` | 约束条件列表 |
| `quality_bar` | `str` | 质量标准 |
| `metadata` | `dict` | 元数据 |

**Usage:**
```python
intent = IntentSpec(
    primary_goals=["实现用户认证", "实现权限管理"],
    constraints=["必须在2周内完成", "必须符合安全标准"],
    quality_bar="功能完整且通过验收测试"
)
```

---

### ExecutionContract

```python
from peas import ExecutionContract
```

执行合约数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `contract_id` | `str` | 合约唯一ID |
| `version` | `str` | 合约版本 |
| `created_at` | `datetime` | 创建时间 |
| `requirements` | `list[ContractRequirement]` | 需求列表 |
| `metadata` | `dict` | 元数据 |
| `intent` | `Optional[IntentSpec]` | 意图规格 |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create()` | `ExecutionContract` | 工厂方法创建合约 |
| `get_requirement(req_id)` | `ContractRequirement` | 获取指定需求 |
| `total_requirements` | `int` | 需求总数属性 |

**Usage:**
```python
contract = ExecutionContract.create(
    requirements=[...],
    intent=intent,
    version="1.0"
)

# 获取需求
req = contract.get_requirement("REQ-001")

# 获取总数
print(contract.total_requirements)
```

---

### VerificationStatus

```python
from peas import VerificationStatus
```

验证状态枚举。

| Value | Description |
|-------|-------------|
| `PENDING` | 待验证 |
| `VERIFIED` | 已验证通过 |
| `FAILED` | 验证失败 |
| `SKIPPED` | 已跳过 |

---

### DriftLevel

```python
from peas import DriftLevel
```

偏离级别枚举。

| Value | Description |
|-------|-------------|
| `NONE` | 无偏离 (0%) |
| `MINOR` | 轻微偏离 (1-5%) |
| `MODERATE` | 中度偏离 (15-30%) |
| `SEVERE` | 严重偏离 (30-50%) |
| `CRITICAL` | 关键偏离 (>50% 或MUST项失败) |

---

### FeatureStatus

```python
from peas import FeatureStatus
```

功能点状态数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `req_id` | `str` | 需求ID |
| `status` | `VerificationStatus` | 验证状态 |
| `evidence` | `list[str]` | 验证证据 |
| `notes` | `Optional[str]` | 备注 |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `is_verified()` | `bool` | 是否通过验证 |
| `is_failed()` | `bool` | 是否失败 |

---

### DriftReport

```python
from peas import DriftReport
```

偏离报告数据类。

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `drift_score` | `float` | 偏离分数 (0-100) |
| `level` | `DriftLevel` | 偏离级别 |
| `verified_count` | `int` | 通过数量 |
| `failed_count` | `int` | 失败数量 |
| `total_count` | `int` | 总数量 |
| `recommendations` | `list[str]` | 改进建议 |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `alignment_rate` | `float` | 对齐率 (0-100%) |
| `is_aligned` | `bool` | 是否对齐 |

**Usage:**
```python
report = DriftReport(
    drift_score=15.5,
    level=DriftLevel.MINOR,
    verified_count=8,
    failed_count=1,
    total_count=9,
    recommendations=["建议添加会话超时处理"]
)

print(report.alignment_rate)  # 88.9
print(report.is_aligned)      # True
```

---

### FeedbackAction

```python
from peas import FeedbackAction
```

反馈动作枚举。

| Value | Description |
|-------|-------------|
| `COMPLETE` | 完成 |
| `RETRY` | 重试 |
| `REPLAN` | 重新规划 |
| `ESCALATE` | 升级处理 |

---

## Core Modules

### MarkdownParser

```python
from peas import MarkdownParser

parser = MarkdownParser()
```

Markdown文档解析器。

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `parse(content)` | `ParsedDocument` | 解析Markdown字符串 |
| `parse_file(file_path, allowed_dir=None)` | `ParsedDocument` | 从文件解析Markdown |

**Class Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `HEADING_PATTERN` | `re.Pattern` | Markdown标题正则 |
| `FEATURE_MARKERS` | `list[re.Pattern]` | 功能点标记模式 |
| `PRIORITY_PATTERNS` | `dict` | 优先级检测模式 |
| `GWT_PATTERN` | `re.Pattern` | Given-When-Then模式 |

**Usage:**
```python
# 解析字符串
doc = parser.parse("""
# 项目PRD

## 功能需求
- Feature: 用户注册
- Feature: 用户登录 (Must)
""")

# 解析文件 (带路径安全保护)
doc = parser.parse_file("path/to/spec.md", allowed_dir="/safe/dir")
```

**Security Features:**
- 输入大小限制: 10MB
- 路径遍历保护 (通过 `allowed_dir` 参数)

**Convenience Functions:**
```python
from peas import parse_markdown, parse_markdown_file

doc = parse_markdown(content)
doc = parse_markdown_file("path/to/spec.md")
```

---

### IntentExtractor

```python
from peas import IntentExtractor

extractor = IntentExtractor(llm_client)
```

意图提取器。

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `extract(doc)` | `IntentSpec` | 同步提取意图 |
| `extract_with_llm(doc)` | `Async[IntentSpec]` | 使用LLM提取意图 |

**Usage:**
```python
# 同步提取
intent = extractor.extract(doc)

# 使用LLM提取
intent = await extractor.extract_with_llm(doc)
```

---

### ContractBuilder

```python
from peas import ContractBuilder

builder = ContractBuilder(llm_client)
```

合约构建器。

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `build(doc, intent=None)` | `ExecutionContract` | 构建执行合约 |

**Usage:**
```python
builder = ContractBuilder()
contract = builder.build(doc, intent)

# 或使用便捷函数
from peas import build_contract
contract = build_contract(doc, intent)
```

---

### FeatureTracker

```python
from peas import FeatureTracker

tracker = FeatureTracker(contract, llm_client)
```

功能点追踪器。

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `verify(execution_result)` | `Async[list[FeatureStatus]]` | 异步验证执行结果 |
| `verify_sync(execution_result)` | `list[FeatureStatus]` | 同步验证执行结果 |
| `get_status(req_id)` | `FeatureStatus` | 获取指定功能点状态 |
| `get_summary()` | `dict` | 获取验证摘要 |

**Usage:**
```python
# 同步验证 (不使用LLM)
results = tracker.verify_sync(execution_result)

# 异步验证 (使用LLM)
results = await tracker.verify(execution_result)

# 获取状态
status = tracker.get_status("FP-001")

# 获取摘要
summary = tracker.get_summary()
# {
#     "total": 10,
#     "verified": 8,
#     "failed": 1,
#     "skipped": 1,
#     "pass_rate": 0.8
# }
```

---

### DriftDetector

```python
from peas import DriftDetector

detector = DriftDetector(threshold_map)
```

偏离检测器。

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold_map` | `dict` | `None` | 优先级阈值映射 |

**Default Threshold Map:**
```python
{
    Priority.MUST: 0,    # must项不允许失败
    Priority.SHOULD: 30, # should项容忍30%失败
    Priority.COULD: 50   # could项容忍50%失败
}
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `detect(statuses, contract)` | `DriftReport` | 检测偏离 |
| `detect_from_tracker(tracker)` | `DriftReport` | 从tracker检测偏离 |

**Usage:**
```python
detector = DriftDetector()

# 检测偏离
report = detector.detect(statuses, contract)

# 从tracker检测
report = detector.detect_from_tracker(tracker)

# 使用便捷函数
from peas import detect_drift
report = detect_drift(statuses, contract)
```

---

### PEASHarnessIntegration

```python
from peas import PEASHarnessIntegration

integration = PEASHarnessIntegration(llm_client, harness_config)
```

PEAS与Harness引擎的集成类。

**Constructor Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm_client` | `Any` | `None` | LLM客户端 |
| `HarnessConfig` | `Optional[HarnessConfig]` | `None` | Harness配置 |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `parse_spec(spec_content)` | `ParsedDocument` | 解析规格文档 |
| `parse_spec_file(file_path)` | `ParsedDocument` | 从文件解析规格 |
| `build_contract()` | `ExecutionContract` | 构建执行合约 |
| `execute(task_description, executor_fn, context)` | `Async[dict]` | 执行并验证 |
| `execute_streaming(...)` | `AsyncGenerator[dict]` | 流式执行 |
| `get_drift_report()` | `Optional[DriftReport]` | 获取偏离报告 |
| `get_feature_summary()` | `dict` | 获取功能点摘要 |

**Usage:**
```python
integration = PEASHarnessIntegration(llm_client=llm_client)

# 1. 解析规格
doc = integration.parse_spec(markdown_content)

# 2. 构建合约
contract = integration.build_contract()

# 3. 执行并验证
result = await integration.execute(
    task_description="实现用户认证功能",
    executor_fn=my_executor,
    context={"project": "my-app"}
)

# 4. 获取结果
print(result["alignment_rate"])
print(result["drift_report"].level)
```

---

## Convenience Functions

PEAS provides convenient shortcut functions for common operations:

| Function | Module | Description |
|----------|--------|-------------|
| `parse_markdown()` | `peas.understanding` | 解析Markdown字符串 |
| `parse_markdown_file()` | `peas.understanding` | 从文件解析Markdown |
| `extract_intent()` | `peas.understanding` | 提取意图 |
| `build_contract()` | `peas.contract` | 构建合约 |
| `detect_drift()` | `peas.verification` | 检测偏离 |
| `create_integration()` | `peas.integration` | 创建集成实例 |

---

## Error Handling

PEAS may raise the following exceptions:

| Exception | Description |
|-----------|-------------|
| `ValueError` | Invalid input (e.g., content too large, path traversal attempt) |
| `RuntimeError` | Invalid state (e.g., calling execute before build_contract) |

**Example:**
```python
try:
    doc = parser.parse(content)
except ValueError as e:
    if "exceeds maximum" in str(e):
        print("Content too large")
    elif "escapes allowed directory" in str(e):
        print("Path traversal detected")
    else:
        raise
```
