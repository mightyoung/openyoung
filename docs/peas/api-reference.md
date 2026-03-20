# PEAS API Reference

## 模块导入

```python
from src.peas import (
    # Types
    Priority,
    FeaturePoint,
    ParsedDocument,
    ContractRequirement,
    IntentSpec,
    ExecutionContract,
    VerificationStatus,
    DriftLevel,
    FeatureStatus,
    DriftReport,
    FeedbackAction,
    # Core
    MarkdownParser,
    IntentExtractor,
    ContractBuilder,
    FeatureTracker,
    DriftDetector,
    PEASHarnessIntegration,
)
```

## Data Types

### Priority

需求优先级枚举

```python
from src.peas import Priority

# Values
Priority.MUST    # 必须实现
Priority.SHOULD # 应该实现
Priority.COULD  # 可选实现

# Usage
priority = Priority.MUST
print(priority.value)  # "must"
```

### FeaturePoint

功能点数据结构

```python
from src.peas import FeaturePoint, Priority

fp = FeaturePoint(
    id="FP-001",
    title="用户注册",
    description="用户通过邮箱注册",
    priority=Priority.MUST,
    acceptance_criteria=["发送验证邮件", "验证链接24小时有效"],
    related_section="功能需求"
)
```

### ParsedDocument

解析后的文档对象

```python
from src.peas import MarkdownParser

parser = MarkdownParser()
doc = parser.parse(content)

# Properties
doc.title           # 文档标题
doc.sections        # 章节列表
doc.feature_points  # 功能点列表
doc.raw_content     # 原始内容

# Computed
doc.total_features  # 功能点总数
doc.must_features  # MUST优先级功能点
doc.should_features # SHOULD优先级功能点
```

### ContractRequirement

合约需求

```python
from src.peas import ContractRequirement, Priority

req = ContractRequirement(
    req_id="REQ-001",
    description="邮箱注册功能",
    priority=Priority.MUST,
    verification_method="llm_judge",
    verification_prompt="验证是否实现...",
    metadata={"section": "2.1"}
)
```

### IntentSpec

意图规格

```python
from src.peas import IntentSpec

intent = IntentSpec(
    primary_goals=["实现用户注册", "实现用户登录"],
    constraints=["必须使用HTTPS", "密码必须加密存储"],
    quality_bar="production",
    metadata={"version": "1.0"}
)
```

### ExecutionContract

执行合约

```python
from src.peas import ExecutionContract

contract = ExecutionContract.create(
    requirements=[req1, req2],
    intent=intent,
    version="1.0"
)

# Properties
contract.contract_id     # 合约ID
contract.version         # 版本号
contract.created_at      # 创建时间
contract.requirements    # 需求列表
contract.intent         # 意图规格
contract.metadata       # 元数据

# Methods
contract.get_requirement("REQ-001")  # 获取指定需求
contract.total_requirements           # 需求总数
```

### VerificationStatus

验证状态

```python
from src.peas import VerificationStatus

VerificationStatus.PENDING    # 待验证
VerificationStatus.VERIFIED  # 已通过
VerificationStatus.FAILED     # 已失败
VerificationStatus.SKIPPED   # 已跳过
```

### DriftLevel

偏离级别

```python
from src.peas import DriftLevel

DriftLevel.NONE      # 无偏离
DriftLevel.MINOR    # 轻微
DriftLevel.MODERATE # 中度
DriftLevel.SEVERE   # 严重
DriftLevel.CRITICAL # 关键
```

### FeatureStatus

功能点状态

```python
from src.peas import FeatureStatus, VerificationStatus

status = FeatureStatus(
    req_id="FP-001",
    status=VerificationStatus.VERIFIED,
    evidence=["匹配关键词: 用户,注册"],
    notes="验证通过"
)

# Methods
status.is_verified()  # 是否已验证
status.is_failed()    # 是否失败
```

### DriftReport

偏离报告

```python
from src.peas import DriftDetector, DriftReport

detector = DriftDetector()
report = detector.detect(statuses, contract)

# Properties
report.drift_score       # 偏离分数 (0-100)
report.level             # 偏离级别
report.verified_count    # 通过数量
report.failed_count      # 失败数量
report.total_count       # 总数
report.recommendations   # 建议列表

# Computed
report.alignment_rate    # 对齐率 (%)
report.is_aligned        # 是否对齐
```

## Core Classes

### MarkdownParser

Markdown文档解析器

```python
from src.peas import MarkdownParser

parser = MarkdownParser()

# Methods
doc = parser.parse(content)              # 解析字符串
doc = parser.parse_file(path)            # 解析文件
doc = parser.parse_file(path, allowed_dir="/path")  # 安全解析
```

### ContractBuilder

合约构建器

```python
from src.peas import ContractBuilder

builder = ContractBuilder(llm_client=llm_client)

# Methods
contract = builder.build(doc)           # 构建合约
contract = builder.build(doc, intent)    # 带意图构建
```

### FeatureTracker

功能点追踪器

```python
from src.peas import FeatureTracker

tracker = FeatureTracker(contract, llm_client=None)

# Methods
statuses = tracker.verify_sync(result)     # 同步验证
statuses = await tracker.verify(result)     # 异步验证
status = tracker.get_summary()             # 获取摘要
status = tracker.get_status("FP-001")      # 获取指定状态

# Summary format
{
    "total": 10,
    "verified": 8,
    "failed": 2,
    "skipped": 0,
    "pass_rate": 0.8
}
```

### DriftDetector

偏离检测器

```python
from src.peas import DriftDetector

detector = DriftDetector()

# Methods
report = detector.detect(statuses, contract)           # 检测偏离
report = detector.detect_from_tracker(tracker)         # 从tracker检测
```

### PEASHarnessIntegration

Harness集成

```python
from src.peas import PEASHarnessIntegration

integration = PEASHarnessIntegration(
    llm_client=None,
    harness_config=None
)

# Methods
doc = integration.parse_spec(content)              # 解析规格
doc = integration.parse_spec_file(path)            # 解析文件
contract = integration.build_contract()             # 构建合约
result = await integration.execute(task, context)   # 执行
async for item in integration.execute_streaming(task, context):
    # 流式执行
    pass

# Get results
report = integration.get_drift_report()             # 获取偏离报告
summary = integration.get_feature_summary()        # 获取功能摘要
```

## Utility Functions

```python
# 从understanding模块
from src.peas.understanding import parse_markdown, parse_markdown_file

doc = parse_markdown(content)
doc = parse_markdown_file(path)

# 从contract模块
from src.peas.contract import build_contract

contract = build_contract(doc, intent=None)

# 从integration模块
from src.peas.integration import create_integration

integration = create_integration(llm_client=None)
```

## Error Handling

```python
from src.peas import MarkdownParser

parser = MarkdownParser()

# 文档过大
try:
    doc = parser.parse(large_content)
except ValueError as e:
    # Content size exceeds maximum
    pass

# 文件路径遍历
try:
    doc = parser.parse_file("../etc/passwd", allowed_dir="/safe/path")
except ValueError:
    # File path escapes allowed directory
    pass
```

## Configuration

### Content Size Limit
```python
# 最大内容大小: 10MB
MAX_CONTENT_SIZE = 10 * 1024 * 1024
```

### Priority Patterns

| Priority | Patterns |
|----------|----------|
| MUST | `must`, `必须`, `强制`, `required`, `必选`, `(M)`, `[M]` |
| SHOULD | `should`, `应该`, `建议`, `recommended`, `(S)`, `[S]` |
| COULD | `could`, `可以`, `可选`, `optional`, `(C)`, `[C]` |

### Feature Markers

支持的标记:
- `Feature: xxx`
- `功能: xxx`
- `Requirement: xxx`
- `需求: xxx`
- `REQ-xxx`
- `FR-xxx`
