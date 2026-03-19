# PEAS MVP - Plan-Execution Alignment System
# 规划-执行对齐系统 (精简版MVP)

**版本**: v1.0 MVP
**目标**: 验证核心假设 - 意图合约+偏离检测能否真正解决Plan-Execution不统一问题
**周期**: 6周

---

## Layer 0: 任务索引

```
Phase 1 (Week 1-2): Parser + Contract ✅
  M1.1: MarkdownParser ✅ (14 tests)
  M1.2: IntentExtractor ✅
  M1.3: ContractBuilder ✅ (11 tests)

Phase 2 (Week 3-4): Verification ✅
  M2.1: FeatureTracker ✅ (8 tests)
  M2.2: DriftDetector ✅ (8 tests)

Phase 3 (Week 5-6): Integration + Test ✅
  M3.1: Harness集成 ✅ (PEASHarnessIntegration)
  M3.2: 单元测试 ✅ (16 verification tests)
  M3.3: E2E验证 ✅ (30 E2E tests)
```

**当前任务**: PEAS MVP 完成 (71 tests)

---

## Layer 0.1: MVP完成总结

### 完成日期
2026-03-20

### 测试统计
| 测试类型 | 测试数 | 状态 |
|---------|--------|------|
| Parser Tests | 14 | ✅ PASS |
| Contract Tests | 11 | ✅ PASS |
| Verification Tests | 16 | ✅ PASS |
| E2E Tests | 30 | ✅ PASS |
| **总计** | **71** | ✅ **PASS** |

### 已修复问题
1. **优先级检测Bug** - 修复了中文优先级的正则匹配
2. **测试Fixture问题** - 修复了FeatureTracker实例化问题
3. **导入顺序问题** - 修复了contract.py中Priority导入顺序
4. **类型提示问题** - 添加了Optional类型提示
5. **安全增强** - 添加了输入大小限制(10MB)和路径遍历保护
6. **性能优化** - 预编译正则表达式提升解析性能

### 核心特性
- Markdown设计文档解析 (支持中文)
- Given-When-Then验收标准提取
- 优先级检测 (MUST/SHOULD/COULD)
- 执行合约构建
- 功能点追踪与验证
- 偏离检测与报告
- Harness引擎集成

---

## 一、核心问题定义

### 用户痛点
- 用户提供详细设计文档，但Agent执行时只实现框架没有内容
- 执行方向与规划偏离很大

### 解决方案
```
用户设计文档 (Markdown + HTML原型)
        ↓
┌─────────────────────────────┐
│  意图理解层                  │
│  1. 解析文档结构             │
│  2. 提取核心意图              │
│  3. 构建可验证合约           │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│  执行验证层                  │
│  1. 功能点追踪              │
│  2. 实时偏离检测           │
│  3. 修正循环               │
└─────────────────────────────┘
        ↓
对齐报告 + 修正建议
```

---

## 二、技术架构

### 目录结构

```
src/peas/
├── __init__.py
├── types/
│   ├── __init__.py
│   ├── document.py      # 文档解析类型
│   ├── contract.py     # 合约类型
│   └── verification.py  # 验证类型
├── understanding/
│   ├── __init__.py
│   ├── markdown_parser.py   # M1.1
│   └── intent_extractor.py  # M1.2
├── contract/
│   ├── __init__.py
│   └── builder.py           # M1.3
├── verification/
│   ├── __init__.py
│   ├── tracker.py          # M2.1
│   └── drift_detector.py   # M2.2
├── integration/
│   ├── __init__.py
│   └── harness.py          # M3.1
└── llm/
    ├── __init__.py
    └── client.py           # LLM客户端

tests/peas/
├── test_parser.py
├── test_contract.py
├── test_verification.py
└── test_e2e.py
```

---

## 三、核心类型定义

### 3.1 文档解析类型

```python
# src/peas/types/document.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

class Priority(Enum):
    MUST = "must"
    SHOULD = "should"
    COULD = "could"

@dataclass
class FeaturePoint:
    """功能点"""
    id: str  # "FP-001"
    title: str
    description: str
    priority: Priority
    acceptance_criteria: list[str] = field(default_factory=list)

@dataclass
class ParsedDocument:
    """解析后的文档"""
    title: str
    sections: list[str]
    feature_points: list[FeaturePoint]
    raw_content: str
```

### 3.2 合约类型

```python
# src/peas/types/contract.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable

@dataclass
class ContractRequirement:
    """合约需求"""
    req_id: str  # "REQ-001"
    description: str
    priority: Priority
    verification_method: str  # "llm_judge" / "regex" / "manual"
    verification_prompt: Optional[str] = None

@dataclass
class ExecutionContract:
    """执行合约"""
    contract_id: str
    version: str
    created_at: datetime
    requirements: list[ContractRequirement]
    metadata: dict = field(default_factory=dict)
```

### 3.3 验证类型

```python
# src/peas/types/verification.py

from dataclasses import dataclass, field
from enum import Enum

class VerificationStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"

class DriftLevel(Enum):
    NONE = 0
    MINOR = 1
    MODERATE = 2
    SEVERE = 3
    CRITICAL = 4

@dataclass
class FeatureStatus:
    """功能点状态"""
    req_id: str
    status: VerificationStatus
    evidence: list[str] = field(default_factory=list)
    notes: Optional[str] = None

@dataclass
class DriftReport:
    """偏离报告"""
    drift_score: float  # 0-100
    level: DriftLevel
    verified_count: int
    failed_count: int
    total_count: int
    recommendations: list[str] = field(default_factory=list)
```

---

## 四、模块详细设计

### M1.1: MarkdownParser

**职责**: 解析Markdown设计文档，提取功能点

**输入**: Markdown格式的设计文档
**输出**: ParsedDocument

```python
# src/peas/understanding/markdown_parser.py

class MarkdownParser:
    """Markdown文档解析器"""

    def parse(self, content: str) -> ParsedDocument:
        """解析Markdown文档"""
        lines = content.split('\n')

        # 1. 提取标题
        title = self._extract_title(lines)

        # 2. 提取章节
        sections = self._extract_sections(lines)

        # 3. 提取功能点
        feature_points = self._extract_feature_points(lines)

        return ParsedDocument(
            title=title,
            sections=sections,
            feature_points=feature_points,
            raw_content=content
        )

    def _extract_title(self, lines: list[str]) -> str:
        """提取文档标题"""

    def _extract_sections(self, lines: list[str]) -> list[str]:
        """提取章节标题"""

    def _extract_feature_points(self, lines: list[str]) -> list[FeaturePoint]:
        """提取功能点列表"""
```

**验证标准**:
- [ ] 正确识别Markdown标题层级
- [ ] 提取>90%的功能点
- [ ] 识别Given-When-Then验收标准

---

### M1.2: IntentExtractor

**职责**: 从ParsedDocument提取核心意图

**输入**: ParsedDocument
**输出**: IntentSpec (简化版)

```python
# src/peas/understanding/intent_extractor.py

@dataclass
class IntentSpec:
    """意图规格"""
    primary_goals: list[str]
    constraints: list[str]
    quality_bar: str  # "must pass tests"

class IntentExtractor:
    """意图提取器"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def extract(self, doc: ParsedDocument) -> IntentSpec:
        """从文档提取核心意图"""
        prompt = f"""
从以下设计文档提取核心意图：

标题: {doc.title}
功能点:
{self._format_feature_points(doc.feature_points)}

输出格式:
- primary_goals: 主要目标列表
- constraints: 约束条件列表
- quality_bar: 质量标准
"""
        return await self.llm.generate(prompt, schema=IntentSpec)
```

---

### M1.3: ContractBuilder

**职责**: 构建可执行合约

**输入**: ParsedDocument + IntentSpec
**输出**: ExecutionContract

```python
# src/peas/contract/builder.py

class ContractBuilder:
    """合约构建器"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def build(
        self,
        doc: ParsedDocument,
        intent: IntentSpec
    ) -> ExecutionContract:
        """构建执行合约"""

        requirements = []

        for fp in doc.feature_points:
            req = ContractRequirement(
                req_id=fp.id,
                description=fp.title,
                priority=fp.priority,
                verification_method=self._determine_verification_method(fp),
                verification_prompt=self._generate_prompt(fp)
            )
            requirements.append(req)

        return ExecutionContract(
            contract_id=str(uuid.uuid4()),
            version="1.0",
            created_at=datetime.now(),
            requirements=requirements,
            metadata={
                "title": doc.title,
                "intent": intent.__dict__
            }
        )

    def _determine_verification_method(self, fp: FeaturePoint) -> str:
        """确定验证方法"""
        if len(fp.acceptance_criteria) > 0:
            return "llm_judge"
        return "regex"
```

---

### M2.1: FeatureTracker

**职责**: 追踪功能点执行状态

**输入**: ExecutionContract, 执行结果
**输出**: list[FeatureStatus]

```python
# src/peas/verification/tracker.py

class FeatureTracker:
    """功能点追踪器"""

    def __init__(self, contract: ExecutionContract, llm_client):
        self.contract = contract
        self.llm = llm_client
        self.status: dict[str, FeatureStatus] = {}

    async def verify(self, execution_result: str) -> list[FeatureStatus]:
        """验证执行结果"""
        results = []

        for req in self.contract.requirements:
            if req.verification_method == "llm_judge":
                result = await self._llm_verify(req, execution_result)
            else:
                result = await self._regex_verify(req, execution_result)

            results.append(result)
            self.status[req.req_id] = result

        return results

    async def _llm_verify(
        self,
        req: ContractRequirement,
        execution: str
    ) -> FeatureStatus:
        """LLM验证"""
        prompt = f"""
验证以下需求是否被正确实现：

需求: {req.description}
验收标准: {req.verification_prompt}

执行结果:
{execution}

判断: 是否满足需求？给出简短理由。
"""
        response = await self.llm.generate(prompt)

        passed = self._parse_verdict(response)

        return FeatureStatus(
            req_id=req.req_id,
            status=VerificationStatus.VERIFIED if passed else VerificationStatus.FAILED,
            evidence=[response]
        )
```

---

### M2.2: DriftDetector

**职责**: 检测执行与规划的偏离

**输入**: list[FeatureStatus]
**输出**: DriftReport

```python
# src/peas/verification/drift_detector.py

class DriftDetector:
    """偏离检测器"""

    def __init__(self, threshold_map: dict = None):
        self.threshold_map = threshold_map or {
            Priority.MUST: 10,   # must项偏离容忍度0
            Priority.SHOULD: 30,
            Priority.COULD: 50
        }

    def detect(self, statuses: list[FeatureStatus]) -> DriftReport:
        """检测偏离"""

        total = len(statuses)
        verified = sum(1 for s in statuses if s.status == VerificationStatus.VERIFIED)
        failed = sum(1 for s in statuses if s.status == VerificationStatus.FAILED)

        # 计算偏离度
        drift_score = (failed / total * 100) if total > 0 else 0

        # 确定严重程度
        level = self._determine_level(drift_score, statuses)

        # 生成建议
        recommendations = self._generate_recommendations(statuses)

        return DriftReport(
            drift_score=drift_score,
            level=level,
            verified_count=verified,
            failed_count=failed,
            total_count=total,
            recommendations=recommendations
        )

    def _determine_level(
        self,
        score: float,
        statuses: list[FeatureStatus]
    ) -> DriftLevel:
        """确定偏离级别"""
        # 检查must级别是否有失败
        must_failed = any(
            s.status == VerificationStatus.FAILED
            for s in statuses
            if self._get_priority(s.req_id) == Priority.MUST
        )

        if must_failed or score >= 50:
            return DriftLevel.CRITICAL
        elif score >= 30:
            return DriftLevel.SEVERE
        elif score >= 15:
            return DriftLevel.MODERATE
        elif score >= 5:
            return DriftLevel.MINOR
        return DriftLevel.NONE
```

---

### M3.1: Harness集成

**职责**: 与Harness引擎集成

```python
# src/peas/integration/harness.py

class PEASHarnessIntegration:
    """PEAS与Harness集成"""

    def __init__(
        self,
        harness,
        parser: MarkdownParser,
        extractor: IntentExtractor,
        builder: ContractBuilder,
        tracker: FeatureTracker,
        detector: DriftDetector
    ):
        self.harness = harness
        self.parser = parser
        self.extractor = extractor
        self.builder = builder
        self.tracker = tracker
        self.detector = detector

    async def execute_with_alignment(
        self,
        user_spec: str,  # Markdown文档
        task_context: dict
    ) -> dict:
        """带对齐检查的执行"""

        # 1. 解析文档
        doc = self.parser.parse(user_spec)

        # 2. 提取意图
        intent = await self.extractor.extract(doc)

        # 3. 构建合约
        contract = await self.builder.build(doc, intent)

        # 4. 执行Harness
        result = await self.harness.execute(task_context)

        # 5. 验证结果
        statuses = await self.tracker.verify(str(result))

        # 6. 检测偏离
        drift_report = self.detector.detect(statuses)

        return {
            "result": result,
            "contract": contract,
            "drift_report": drift_report
        }
```

---

## 五、用户交互流程

```
┌─────────────────────────────────────────────────────┐
│  1. 用户上传设计文档 (Markdown)                       │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  2. PEAS解析 → 生成Contract草案                      │
│     - 显示功能点列表                                 │
│     - 显示验收标准                                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  3. 用户确认/修改Contract                           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  4. Harness执行任务                                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  5. PEAS验证 → 生成DriftReport                    │
│     - 显示符合项 ✅                                 │
│     - 显示偏离项 ❌                                 │
│     - 显示修正建议                                 │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  6. 用户反馈 → 学习偏好                             │
└─────────────────────────────────────────────────────┘
```

---

## 六、验证标准

### 功能验证

| 指标 | 目标 |
|------|------|
| Markdown解析准确率 | >90% |
| 功能点识别率 | >90% |
| 偏离检测召回率 | >85% |
| 合约覆盖率 | >95% |

### 性能验证

| 指标 | 目标 |
|------|------|
| 解析延迟 | <2s |
| 单功能点验证 | <1s |
| 总验证延迟 | <10s |

### 用户价值验证

| 指标 | 目标 |
|------|------|
| 用户对齐满意率 | >80% |
| 修正建议采纳率 | >60% |

---

## 七、实施计划

### Week 1: Parser核心

| Day | 任务 |
|-----|------|
| 1-2 | 创建src/peas/目录结构 |
| 3-4 | 实现MarkdownParser基础 |
| 5 | 单元测试 |

### Week 2: Contract构建

| Day | 任务 |
|-----|------|
| 1-2 | 实现IntentExtractor |
| 3-4 | 实现ContractBuilder |
| 5 | 集成测试 |

### Week 3: Verification基础

| Day | 任务 |
|-----|------|
| 1-2 | 实现FeatureTracker |
| 3-4 | 实现DriftDetector |
| 5 | 验证逻辑测试 |

### Week 4: LLM集成

| Day | 任务 |
|-----|------|
| 1-2 | LLM客户端抽象 |
| 3-4 | LLM验证集成 |
| 5 | 端到端测试 |

### Week 5: Harness集成

| Day | 任务 |
|-----|------|
| 1-3 | PEASHarnessIntegration |
| 4-5 | 集成测试 |

### Week 6: 验证优化

| Day | 任务 |
|-----|------|
| 1-2 | E2E验证 |
| 3-4 | 性能优化 |
| 5 | MVP评审 |

---

## 八、关键决策

### 决策1: MVP不包含

以下功能延后到验证MVP后：
- HTML原型解析 (Phase 2)
- UIComparator (Phase 2)
- PreferenceLearner (Phase 3)
- StyleProfiler (Phase 3)

### 决策2: 验证方法

MVP只使用LLM验证，不做正则匹配初筛（复杂度高）

### 决策3: LLM选择

使用项目的LLM客户端，支持多Provider切换

---

## 九、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| LLM验证成本高 | 中 | 中 | 限制验证次数，缓存结果 |
| 解析准确率不足 | 中 | 高 | 人工确认Contract |
| 用户不接受流程 | 低 | 高 | 快速迭代反馈 |

---

## 版本历史

| 版本 | 日期 | 修改 |
|------|------|------|
| v1.0 | 2026-03-20 | MVP初始版本 |

---

**文档状态**: 待实施
**下次更新**: 开始M1.1时
