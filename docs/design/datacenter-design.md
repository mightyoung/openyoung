# Mightyoung DataCenter 设计 (v2.1)
> 基于 OpenCode、Claude Code、DSPy 调研
> 更新日期: 2026-03-01
> 合并 Harness 设计

---

## 1. 定位

DataCenter 是 Agent 的**统一数据中心**，整合数据存储、状态管理、评估数据获取能力。

设计原则：
- **核心零依赖**: 仅使用 Python 标准库
- **内存优先**: 默认内存存储，可扩展到数据库
- **可插拔架构**: 核心与可选扩展分离

---

## 2. 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                         DataCenter 架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Harness (数据获取方式)                                   │    │
│  │  - TraceCollector: 执行轨迹收集                          │    │
│  │  - BudgetController: 预算控制                           │    │
│  │  - PatternDetector: 失败模式检测                         │    │
│  │  - QualityChecker: 质量检查                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Memory Layer (三层记忆)                                │    │
│  │  - Episodic Memory: 对话历史、任务轨迹                  │    │
│  │  - Semantic Memory: 事实/实体、用户偏好                 │    │
│  │  - Working Memory: 当前状态、上下文                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Checkpoint Layer (状态恢复)                            │    │
│  │  - State persistence: 状态持久化                        │    │
│  │  - Session recovery: 会话恢复                          │    │
│  │  - Version tracking: 版本追踪                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Harness 核心组件 (详细实现)

### 3.1 TraceCollector

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from enum import Enum

class TraceStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TraceRecord:
    session_id: str
    agent_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: TraceStatus = TraceStatus.SUCCESS
    error: str = ""
    metadata: dict = field(default_factory=dict)

class TraceCollector:
    def __init__(self):
        self._traces: list[TraceRecord] = []

    def record(self, trace: TraceRecord) -> None:
        self._traces.append(trace)

    def get_by_session(self, session_id: str) -> list[TraceRecord]:
        return [t for t in self._traces if t.session_id == session_id]

    def get_summary(self) -> dict:
        total = len(self._traces)
        if total == 0:
            return {"total": 0, "success": 0, "failed": 0, "success_rate": 0.0}

        success = sum(1 for t in self._traces if t.status == TraceStatus.SUCCESS)
        failed = sum(1 for t in self._traces if t.status == TraceStatus.FAILED)

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": round(success / total, 4),
            "total_tokens": sum(t.total_tokens for t in self._traces),
            "total_cost": round(sum(t.cost_usd for t in self._traces), 4)
        }
```

### 3.2 BudgetController

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

@dataclass
class BudgetAllocation:
    complexity: ComplexityLevel
    allocated_budget: int
    reasoning_effort: str
    estimated_tokens: int

class BudgetController:
    BUDGET_MAP = {
        ComplexityLevel.LOW: 16000,
        ComplexityLevel.MEDIUM: 32000,
        ComplexityLevel.HIGH: 64000
    }

    def __init__(self):
        self._history: list[BudgetAllocation] = []

    def allocate(self, task_description: str, context_length: int = 0, tool_count: int = 0) -> BudgetAllocation:
        complexity = self._estimate_complexity(task_description, context_length, tool_count)

        allocation = BudgetAllocation(
            complexity=complexity,
            allocated_budget=self.BUDGET_MAP[complexity],
            reasoning_effort=complexity.value,
            estimated_tokens=int(self.BUDGET_MAP[complexity] * 0.8)
        )

        self._history.append(allocation)
        return allocation

    def _estimate_complexity(self, task: str, context_length: int, tool_count: int) -> ComplexityLevel:
        score = 0
        if len(task) > 500: score += 2
        elif len(task) > 200: score += 1
        if context_length > 10000: score += 2
        elif context_length > 5000: score += 1
        if tool_count > 5: score += 2
        elif tool_count > 2: score += 1

        if score >= 4: return ComplexityLevel.HIGH
        elif score >= 2: return ComplexityLevel.MEDIUM
        return ComplexityLevel.LOW
```

### 3.3 PatternDetector

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class PatternType(Enum):
    REASONING_ERROR = "reasoning_error"
    MISSING_TOOL = "missing_tool"
    CONTEXT_OVERFLOW = "context_overflow"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

class PatternSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FailurePattern:
    pattern_type: PatternType
    description: str
    frequency: int = 1
    severity: PatternSeverity = PatternSeverity.MEDIUM
    suggestion: str = ""

PATTERN_RULES = [
    (["timeout", "超时"], PatternType.TIMEOUT, PatternSeverity.HIGH, "增加预算或优化执行路径"),
    (["tool", "error", "失败"], PatternType.TOOL_EXECUTION_ERROR, PatternSeverity.HIGH, "检查工具配置或权限"),
    (["context", "overflow", "溢出"], PatternType.CONTEXT_OVERFLOW, PatternSeverity.CRITICAL, "优化上下文管理"),
]

class PatternDetector:
    def __init__(self):
        self._patterns: dict[str, FailurePattern] = {}

    def detect(self, error_message: str) -> Optional[FailurePattern]:
        error_lower = error_message.lower()

        for keywords, pattern_type, severity, suggestion in PATTERN_RULES:
            if any(kw in error_lower for kw in keywords):
                key = pattern_type.value
                if key in self._patterns:
                    self._patterns[key].frequency += 1
                    return self._patterns[key]

                pattern = FailurePattern(
                    pattern_type=pattern_type,
                    description=f"检测到 {pattern_type.value}",
                    frequency=1,
                    severity=severity,
                    suggestion=suggestion
                )
                self._patterns[key] = pattern
                return pattern

        return FailurePattern(
            pattern_type=PatternType.UNKNOWN,
            description="未知错误",
            severity=PatternSeverity.LOW,
            suggestion="查看详细错误信息"
        )
```

### 3.4 QualityChecker

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class QualityScore:
    completeness: float  # 0-1
    accuracy: float     # 0-1
    overall: float      # 0-1
    issues: list[str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.overall == 0:
            self.overall = (self.completeness + self.accuracy) / 2

class QualityChecker:
    def __init__(self):
        self._rules = [
            self._check_empty_output,
            self._check_error_keywords,
            self._check_length_ratio,
        ]

    def check(self, input_text: str, output_text: str) -> QualityScore:
        issues = []

        for rule in self._rules:
            issue = rule(input_text, output_text)
            if issue:
                issues.append(issue)

        completeness = 1.0 if output_text.strip() else 0.0
        accuracy = 1.0 - (len(issues) * 0.2)
        accuracy = max(0.0, accuracy)

        return QualityScore(
            completeness=completeness,
            accuracy=accuracy,
            overall=(completeness + accuracy) / 2,
            issues=issues
        )

    def _check_empty_output(self, inp: str, out: str) -> Optional[str]:
        return "输出为空" if not out.strip() else None

    def _check_error_keywords(self, inp: str, out: str) -> Optional[str]:
        error_keywords = ["error", "failed", "exception", "错误", "失败"]
        return "输出包含错误信息" if any(kw in out.lower() for kw in error_keywords) else None

    def _check_length_ratio(self, inp: str, out: str) -> Optional[str]:
        return "输出过短，可能未完成" if len(inp) > 0 and len(out) < len(inp) * 0.1 else None
```

---

## 4. 数据模型

### 4.1 HarnessData

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class HarnessData:
    session_id: str
    task_description: str
    trace: list = field(default_factory=list)
    budget_status: dict = field(default_factory=dict)
    patterns: list = field(default_factory=list)
    evaluation: Optional[Any] = None
    evaluation_passed: bool = True

    @property
    def overall_quality(self) -> float:
        return self.evaluation.overall_score if self.evaluation else 1.0

    @property
    def should_continue(self) -> bool:
        if self.evaluation is None:
            return True
        return self.evaluation.passed
```

---

## 5. 与 EvaluationCenter 集成

DataCenter 作为**数据提供方**，为 EvaluationCenter 提供数据：

```
┌─────────────────────────────────────────────────────────────────┐
│              DataCenter → EvaluationCenter                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DataCenter                                                     │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │  Harness (数据获取)                                      │    │
│   │  - TraceLog → 评估输入                                  │    │
│   │  - Metrics → 质量评分                                  │    │
│   │  - FailurePattern → 错误模式                           │    │
│   └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼ (数据流)                            │
│   EvaluationCenter                                               │
│   - 多类型评估 (正确性/效率/安全/体验)                          │    │
│   - 多层级评估 (单元/集成/系统/E2E)                           │    │
│   - Pull Model: Agent/DataCenter 主动调用                       │    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**并行执行**: Agent 和 DataCenter 都可以独立调用 EvaluationCenter，实现并行评估。

---

## 6. 与 Package Manager 关系

DataCenter 存储的数据不受 Package Manager 管控：
- DataCenter 存储**运行时数据** (traces, memory, checkpoints)
- Package Manager 管控**包/技能/数据集**

---

## 7. 配置

```yaml
# mightyoung.yaml
datacenter:
  # Harness 配置
  harness:
    enabled: true
    trace:
      enabled: true
    budget:
      enabled: true
      dynamic: true
    pattern_detection:
      enabled: true
    quality_check:
      enabled: true

  # Memory 配置
  memory:
    episodic:
      enabled: true
      max_sessions: 100
    semantic:
      enabled: true
      vector_store: memory
    working:
      enabled: true
      max_context: 64000

  # Checkpoint 配置
  checkpoint:
    enabled: true
    backend: memory
    auto_save: true
```

---

## 8. 核心代码结构

```
src/
├── datacenter/
│   ├── __init__.py
│   ├── harness/
│   │   ├── collector.py      # TraceCollector
│   │   ├── budget.py         # BudgetController
│   │   ├── detector.py       # PatternDetector
│   │   └── checker.py        # QualityChecker
│   ├── memory/
│   │   ├── episodic.py       # EpisodicMemory
│   │   ├── semantic.py       # SemanticMemory
│   │   └── working.py       # WorkingMemory
│   ├── checkpoint/
│   │   ├── saver.py          # CheckpointSaver
│   │   └── memory.py        # MemoryCheckpointer
│   └── storage/
│       ├── __init__.py
│       └── store.py         # DataStore
```

---

## 9. 与其他系统对比

| 特性 | OpenCode | Claude Code | Codex | **Mightyoung** |
|------|----------|-------------|-------|----------------|
| Trace 收集 | ❌ | ✅ OTel | ✅ | ✅ 内存 |
| 预算控制 | ❌ | ❌ | ❌ | ✅ 动态 |
| 模式检测 | ❌ | ❌ | ❌ | ✅ 规则 |
| 质量检查 | ❌ | ❌ | ❌ | ✅ 插件 |
| 零依赖核心 | ✅ | N/A | N/A | ✅ |

---

*本文档基于 OpenCode、Claude Code、DSPy 调研设计*

> 基于 OpenCode、Claude Code、DSPy 调研
> 更新日期: 2026-02-28

---

## 1. 定位

DataCenter 是 Agent 的**统一数据中心**，整合数据存储、状态管理、评估数据获取能力。

设计原则：
- **核心零依赖**: 仅使用 Python 标准库
- **内存优先**: 默认内存存储，可扩展到数据库
- **可插拔架构**: 核心与可选扩展分离

---

## 2. 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                         DataCenter 架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Harness (数据获取方式)                                   │    │
│  │  - TraceCollector: 执行轨迹收集                          │    │
│  │  - BudgetController: 预算控制                           │    │
│  │  - PatternDetector: 失败模式检测                         │    │
│  │  - QualityChecker: 质量检查                             │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Memory Layer (三层记忆)                                │    │
│  │  - Episodic Memory: 对话历史、任务轨迹                  │    │
│  │  - Semantic Memory: 事实/实体、用户偏好                 │    │
│  │  - Working Memory: 当前状态、上下文                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Checkpoint Layer (状态恢复)                            │    │
│  │  - State persistence: 状态持久化                        │    │
│  │  - Session recovery: 会话恢复                          │    │
│  │  - Version tracking: 版本追踪                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型

### 3.1 TraceLog

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class TraceStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class TraceRecord:
    """执行轨迹记录"""
    session_id: str
    agent_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = None
    duration_ms: int = 0
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    status: TraceStatus = TraceStatus.SUCCESS
    error: str = ""
    metadata: dict = field(default_factory=dict)
```

### 3.2 FailurePattern

```python
from enum import Enum

class PatternType(Enum):
    REASONING_ERROR = "reasoning_error"
    MISSING_TOOL = "missing_tool"
    CONTEXT_OVERFLOW = "context_overflow"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    TIMEOUT = "timeout"

class PatternSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FailurePattern:
    pattern_type: PatternType
    description: str
    frequency: int = 1
    severity: PatternSeverity = PatternSeverity.MEDIUM
    suggestion: str = ""
```

### 3.3 HarnessData

```python
@dataclass
class HarnessData:
    """Harness 数据存储 - 包含评估结果"""
    session_id: str
    task_description: str
    trace: list  # TraceEvent list
    budget_status: dict
    patterns: list[FailurePattern]
    evaluation: EvaluationReport = None

    @property
    def overall_quality(self) -> float:
        return self.evaluation.overall_score if self.evaluation else 1.0
```

---

## 4. 与 Evaluation Hub 集成

DataCenter 作为**数据提供方**，为 Evaluation Hub 提供数据：

```
┌─────────────────────────────────────────────────────────────────┐
│              DataCenter → Evaluation Hub                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DataCenter                                                     │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │  Harness (数据获取)                                      │    │
│   │  - TraceLog → 评估输入                                  │    │
│   │  - Metrics → 质量评分                                  │    │
│   │  - FailurePattern → 错误模式                           │    │
│   └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼ (数据流)                            │
│   Evaluation Hub                                                 │
│   - 多类型评估 (正确性/效率/安全/体验)                          │
│   - 多层级评估 (单元/集成/系统/E2E)                           │
│   - 评估注入 (按场景选择评估器)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 与 Package Manager 关系

DataCenter 存储的数据不受 Package Manager 管控：
- DataCenter 存储**运行时数据** (traces, memory, checkpoints)
- Package Manager 管控**包/技能/数据集**

---

## 6. 配置

```yaml
# mightyoung.yaml
datacenter:
  # Harness 配置
  harness:
    enabled: true
    trace:
      enabled: true
    budget:
      enabled: true
      dynamic: true
    pattern_detection:
      enabled: true
    quality_check:
      enabled: true

  # Memory 配置
  memory:
    episodic:
      enabled: true
      max_sessions: 100
    semantic:
      enabled: true
      vector_store: memory  # memory | chroma | qdrant
    working:
      enabled: true
      max_context: 64000

  # Checkpoint 配置
  checkpoint:
    enabled: true
    backend: memory  # memory | sqlite | postgres
    auto_save: true
```

---

## 7. 核心代码结构

```
src/
├── datacenter/
│   ├── __init__.py
│   ├── harness/
│   │   ├── collector.py      # TraceCollector
│   │   ├── budget.py        # BudgetController
│   │   ├── detector.py      # PatternDetector
│   │   └── checker.py       # QualityChecker
│   ├── memory/
│   │   ├── episodic.py      # EpisodicMemory
│   │   ├── semantic.py     # SemanticMemory
│   │   └── working.py      # WorkingMemory
│   ├── checkpoint/
│   │   ├── saver.py         # CheckpointSaver
│   │   └── memory.py       # MemoryCheckpointer
│   └── storage/
│       ├── __init__.py
│       └── store.py         # DataStore
```

---

*本文档基于 OpenCode、Claude Code、DSPy 调研设计*
