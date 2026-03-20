# Plan-Execution Alignment System (PEAS)
# 规划-执行对齐系统

**核心目标**: 解决Agent执行与用户规划文档偏离的核心问题
**技术路线**: LLM驱动的意图理解 + 合约验证 + 持久用户记忆

---

## Layer 0: 任务索引 (~50 tokens)

```
Phase 1 (P1-P4): Plan Understanding - 规划理解层
  P1: Markdown文档解析器
  P2: 原型图解析器 (HTML截图)
  P3: 意图提取器
  P4: 合约构建器

Phase 2 (A1-A4): Alignment Verification - 对齐验证层
  A1: 功能点追踪器
  A2: UI设计对比器
  A3: 偏离检测器
  A4: 修正循环

Phase 3 (M1-M3): User Memory - 用户记忆层
  M1: 偏好学习器
  M2: 风格画像
  M3: 上下文持久化

Phase 4 (I1-I3): Integration - 集成层
  I1: 与Harness引擎集成
  I2: 与现有Agent系统集成
  I3: WebUI对齐面板
```

**当前任务**: P1

---

## Layer 1: 核心概念

### 1.1 问题定义

```
用户输入:
┌─────────────────────────────────────────────────┐
│ PRD文档 / 设计文档 / 原型图                        │
│ "用户需要注册登录功能，密码强度要符合要求..."       │
└─────────────────────────────────────────────────┘
                    │
                    ▼ [Plan Understanding]
┌─────────────────────────────────────────────────┐
│ SPEC = 结构化规格说明                             │
│ - 功能点列表 (feature_points)                     │
│ - 验收标准 (acceptance_criteria)                  │
│ - 约束条件 (constraints)                          │
│ - 原型引用 (prototype_refs)                      │
└─────────────────────────────────────────────────┘
                    │
                    ▼ [Execution]
        ┌───────────────────────────┐
        │   Agent 执行过程          │
        │   生成代码/UI/配置        │
        └───────────────────────────┘
                    │
                    ▼ [Alignment Verification]
┌─────────────────────────────────────────────────┐
│ DRIFT REPORT = 对齐报告                           │
│ - 符合项 (aligned)                               │
│ - 偏离项 (drifted)                               │
│ - 缺失项 (missing)                               │
│ - 偏离度分数 (drift_score: 0-100)                │
└─────────────────────────────────────────────────┘
                    │
                    ▼ [Correction Loop]
        ┌───────────────────────────┐
        │  FeedbackAction:         │
        │  RETRY / REPLAN / FIX    │
        └───────────────────────────┘
```

### 1.2 关键创新

| 特性 | 描述 | 差异化 |
|------|------|--------|
| **Intent Contract** | 自然语言 → 可验证合约 | 独有 |
| **Multi-modal Parsing** | 同时解析MD+HTML+截图 | 独有 |
| **Drift Detection** | 实时检测偏离 | 独有 |
| **Persistent Memory** | 用户偏好跨会话 | 独有 |
| **LLM Verification** | 用LLM做验收判断 | 独有 |

---

## Phase 1: Plan Understanding - 规划理解层

### P1: Markdown文档解析器

**状态**: 🔄 in_progress

**输入**:
- Markdown格式的PRD/设计文档
- 支持标题层级、列表、代码块、表格

**输出**:
```python
@dataclass
class ParsedDocument:
    title: str
    sections: list[Section]
    feature_points: list[FeaturePoint]
    constraints: list[Constraint]
    references: list[str]  # 外部链接、图片引用

@dataclass
class FeaturePoint:
    id: str  # "FP-001"
    title: str
    description: str
    priority: Priority  # must / should / could
    acceptance_criteria: list[str]
    related_section: str
```

**实现**:

```python
# src/peas/understanding/parser.py
class MarkdownParser:
    """解析Markdown文档为结构化数据"""

    def parse(self, content: str) -> ParsedDocument:
        # 1. 提取标题层级
        # 2. 识别功能点（列表、任务符号）
        # 3. 提取验收标准
        # 4. 识别约束条件
        # 5. 提取引用（图片、链接）

    def _extract_feature_points(self, lines: list[str]) -> list[FeaturePoint]:
        """从列表中提取功能点"""

    def _extract_acceptance_criteria(self, section: Section) -> list[str]:
        """提取验收标准（Given-When-Then模式）"""
```

**验证标准**:
- [ ] 正确解析层级标题
- [ ] 识别>90%的功能点
- [ ] 提取验收标准准确率>85%

---

### P2: 原型图解析器

**状态**: ⏳ pending

**输入**:
- HTML原型文件
- 截图图片（可选）

**输出**:
```python
@dataclass
class ParsedPrototype:
    pages: list[PageSpec]
    components: list[ComponentSpec]
    interactions: list[Interaction]
    layout_structure: LayoutTree

@dataclass
class ComponentSpec:
    id: str
    type: ComponentType  # button / input / card / modal
    label: str
    position: Position  # x, y, width, height
    styles: dict
    states: list[str]  # default / hover / disabled
```

**实现**:

```python
# src/peas/understanding/prototype_parser.py
class HTMLPrototypeParser:
    """解析HTML原型"""

    def parse(self, html_content: str) -> ParsedPrototype:
        # 1. 解析DOM结构
        # 2. 识别组件类型
        # 3. 提取布局信息
        # 4. 识别交互

class ScreenshotAnalyzer:
    """使用LLM分析截图"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def analyze(self, screenshot: Image) -> ComponentList:
        prompt = """
        分析这个UI截图，列出所有组件：
        - 组件类型
        - 位置（用百分比）
        - 样式特征
        - 交互状态
        """
```

**验证标准**:
- [ ] 正确解析HTML结构
- [ ] 组件识别准确率>80%
- [ ] 布局提取完整

---

### P3: 意图提取器

**状态**: ⏳ pending

**输入**:
- ParsedDocument
- ParsedPrototype

**输出**:
```python
@dataclass
class IntentSpec:
    primary_goals: list[Goal]
    user_persona: UserPersona
    constraints: list[Constraint]
    non_functional: NonFunctionalReqs
    risk_factors: list[Risk]

@dataclass
class Goal:
    id: str
    description: str
    success_indicator: str
    measurable_criteria: str  # "转化率>5%"
```

**实现**:

```python
# src/peas/understanding/intent_extractor.py
class IntentExtractor:
    """从结构化文档提取核心意图"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def extract(self, doc: ParsedDocument, proto: ParsedPrototype) -> IntentSpec:
        prompt = f"""
        从以下文档和原型中提取：
        1. 用户核心目标（不是功能，是要解决的问题）
        2. 用户画像（技能水平、使用场景）
        3. 硬性约束（技术限制、合规要求）
        4. 非功能性需求（性能、安全、兼容性）

        文档内容：
        {doc.markdown_content}

        原型描述：
        {proto.summary}
        """
        return await self.llm.generate(prompt, schema=IntentSpec)
```

**验证标准**:
- [ ] 目标提取准确率>85%
- [ ] 约束识别完整
- [ ] LLM调用延迟<3s

---

### P4: 合约构建器

**状态**: ⏳ pending

**输入**:
- IntentSpec
- ParsedDocument
- ParsedPrototype

**输出**:
```python
@dataclass
class ExecutionContract:
    contract_id: str
    version: str
    created_at: datetime
    requirements: list[ContractRequirement]
    verification_methods: dict[str, VerificationMethod]
    metadata: dict

@dataclass
class ContractRequirement:
    req_id: str  # "REQ-001"
    type: RequirementType  # functional / ui / non_functional
    description: str
    priority: Priority
    verification_method: VerificationMethod
    test_suggestions: list[str]

@dataclass
class VerificationMethod:
    type: VerificationType  # llm_judge / unit_test / manual / regex
    prompt_template: str
    expected_pattern: Optional[str]
    threshold: float  # 置信度阈值
```

**实现**:

```python
# src/peas/understanding/contract_builder.py
class ContractBuilder:
    """构建可执行合约"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def build(
        self,
        intent: IntentSpec,
        doc: ParsedDocument,
        proto: ParsedPrototype
    ) -> ExecutionContract:
        # 1. 为每个功能点生成验收方法
        requirements = await self._generate_requirements(intent, doc, proto)

        # 2. 为每个需求设计验证方法
        verification_methods = {}
        for req in requirements:
            verification_methods[req.req_id] = await self._design_verification(req)

        return ExecutionContract(
            contract_id=str(uuid.uuid4()),
            version="1.0",
            requirements=requirements,
            verification_methods=verification_methods
        )

    async def _design_verification(self, req: ContractRequirement) -> VerificationMethod:
        """设计单个需求的验证方法"""
        prompt = f"""
        为以下需求设计验证方法：
        需求: {req.description}
        类型: {req.type}
        优先级: {req.priority}

        选择验证类型：
        - llm_judge: 用LLM判断是否满足
        - unit_test: 建议单元测试
        - manual: 需要人工验收
        - regex: 模式匹配验证
        """
```

**验证标准**:
- [ ] 合约覆盖所有功能点
- [ ] 验证方法准确率>90%
- [ ] 合约可序列化/存储

---

## Phase 2: Alignment Verification - 对齐验证层

### A1: 功能点追踪器

**状态**: ⏳ pending

**输入**:
- ExecutionContract
- Agent执行结果

**输出**:
```python
@dataclass
class FeaturePointStatus:
    req_id: str
    status: FeatureStatus  # pending / in_progress / verified / failed
    evidence: list[str]
    verification_result: VerificationResult

@dataclass
class VerificationResult:
    passed: bool
    confidence: float
    details: str
    llm_judgment: Optional[str]
```

**实现**:

```python
# src/peas/verification/feature_tracker.py
class FeaturePointTracker:
    """追踪功能点执行状态"""

    def __init__(self, contract: ExecutionContract, llm_client):
        self.contract = contract
        self.llm = llm_client
        self.status: dict[str, FeaturePointStatus] = {}

    async def verify_feature(self, req_id: str, execution_result: Any) -> VerificationResult:
        req = self.contract.get_requirement(req_id)
        method = self.contract.verification_methods[req_id]

        if method.type == VerificationType.LLM_JUDGE:
            return await self._llm_verify(req, execution_result, method)
        elif method.type == VerificationType.REGEX:
            return self._regex_verify(req, execution_result, method)
        # ...

    async def _llm_verify(
        self,
        req: ContractRequirement,
        execution: Any,
        method: VerificationMethod
    ) -> VerificationResult:
        prompt = method.prompt_template.format(
            requirement=req.description,
            execution_result=str(execution)
        )
        response = await self.llm.generate(prompt)

        return VerificationResult(
            passed=self._parse_passed(response),
            confidence=self._parse_confidence(response),
            details=self._parse_details(response),
            llm_judgment=response
        )
```

---

### A2: UI设计对比器

**状态**: ⏳ pending

**输入**:
- ParsedPrototype (目标UI)
- 实际生成的UI

**输出**:
```python
@dataclass
class UIDriftReport:
    drift_score: float  # 0-100, 100=完全对齐
    component_match: list[ComponentMatch]
    layout_score: float
    style_drift: list[StyleDrift]
    missing_components: list[str]
    extra_components: list[str]

@dataclass
class ComponentMatch:
    expected: ComponentSpec
    actual: Optional[ComponentSpec]
    match_score: float
    drift_description: str
```

**实现**:

```python
# src/peas/verification/ui_comparator.py
class UIComparator:
    """对比UI实现与设计"""

    def __init__(self, llm_client):
        self.llm = llm_client

    async def compare(
        self,
        target: ParsedPrototype,
        actual_ui: Union[str, Image]
    ) -> UIDriftReport:
        # 1. 如果actual是截图，用LLM提取组件
        if isinstance(actual_ui, Image):
            actual_components = await self._extract_components_from_image(actual_ui)
        else:
            actual_components = self._parse_html_components(actual_ui)

        # 2. 逐个组件对比
        matches = []
        for target_comp in target.components:
            match = self._find_best_match(target_comp, actual_components)
            matches.append(match)

        # 3. 计算偏离度
        drift_score = self._calculate_drift_score(matches)

        return UIDriftReport(
            drift_score=drift_score,
            component_match=matches,
            layout_score=self._calculate_layout_score(target, actual_components),
            missing_components=[m.expected.id for m in matches if m.actual is None],
            extra_components=[m.actual.id for m in matches if m.expected is None]
        )

    async def _extract_components_from_image(self, screenshot: Image) -> list[ComponentSpec]:
        prompt = """
        分析这个UI截图，提取所有UI组件：
        输出JSON格式：
        {
            "components": [
                {
                    "id": "comp-1",
                    "type": "button/input/card...",
                    "label": "按钮文字或输入框placeholder",
                    "position": {"x": "10%", "y": "20%"},
                    "styles": {"color": "blue", "size": "large"}
                }
            ]
        }
        """
```

---

### A3: 偏离检测器

**状态**: ⏳ pending

**输入**:
- FeaturePointStatus列表
- UIDriftReport

**输出**:
```python
@dataclass
class DriftReport:
    overall_drift_score: float  # 0-100
    severity: DriftSeverity  # none / minor / moderate / severe / critical
    drifted_requirements: list[DriftedRequirement]
    recommendations: list[str]
    feedback_action: FeedbackAction

@dataclass
class DriftedRequirement:
    req_id: str
    drift_type: DriftType  # missing / wrong / incomplete / extra
    description: str
    expected: str
    actual: str
    fix_suggestion: str
```

**实现**:

```python
# src/peas/verification/drift_detector.py
class DriftDetector:
    """检测执行与规划的偏离"""

    def __init__(self, threshold_map: dict[Priority, float]):
        # 不同优先级有不同的偏离阈值
        self.threshold_map = threshold_map  # must=10, should=30, could=50

    def detect(
        self,
        feature_status: list[FeaturePointStatus],
        ui_report: UIDriftReport
    ) -> DriftReport:
        # 1. 收集失败的功能点
        failed = [f for f in feature_status if f.status == FeatureStatus.FAILED]

        # 2. 收集偏离的UI组件
        drifted_ui = [c for c in ui_report.component_match if c.match_score < 0.8]

        # 3. 计算整体偏离度
        # 加权平均：must需求权重最高
        overall_score = self._calculate_weighted_drift(
            failed, drifted_ui, feature_status, ui_report
        )

        # 4. 确定严重程度
        severity = self._determine_severity(overall_score, failed, drifted_ui)

        # 5. 生成建议
        recommendations = self._generate_recommendations(failed, drifted_ui)

        # 6. 决定反馈动作
        action = self._determine_action(severity, overall_score)

        return DriftReport(
            overall_drift_score=overall_score,
            severity=severity,
            drifted_requirements=self._build_drifted_list(failed, drifted_ui),
            recommendations=recommendations,
            feedback_action=action
        )

    def _determine_action(
        self,
        severity: DriftSeverity,
        score: float
    ) -> FeedbackAction:
        if severity in (DriftSeverity.NONE, DriftSeverity.MINOR):
            return FeedbackAction.COMPLETE
        elif severity == DriftSeverity.MODERATE:
            return FeedbackAction.RETRY
        elif severity == DriftSeverity.SEVERE:
            return FeedbackAction.REPLAN
        else:  # CRITICAL
            return FeedbackAction.ESCALATE
```

---

### A4: 修正循环

**状态**: ⏳ pending

**输入**:
- DriftReport
- Original IntentSpec

**输出**:
```python
@dataclass
class CorrectionResult:
    action: FeedbackAction
    replanned_tasks: list[Task]
    retry_count: int
    explanation: str
```

**实现**:

```python
# src/peas/verification/correction_loop.py
class CorrectionLoop:
    """执行修正循环"""

    def __init__(self, llm_client, max_retries: int = 3):
        self.llm = llm_client
        self.max_retries = max_retries

    async def correct(
        self,
        drift_report: DriftReport,
        original_plan: IntentSpec,
        execution_history: list[ExecutionAttempt]
    ) -> CorrectionResult:
        if drift_report.feedback_action == FeedbackAction.COMPLETE:
            return CorrectionResult(
                action=FeedbackAction.COMPLETE,
                replanned_tasks=[],
                retry_count=0,
                explanation="对齐度达标，无需修正"
            )

        if drift_report.feedback_action == FeedbackAction.RETRY:
            return await self._handle_retry(drift_report, original_plan)

        elif drift_report.feedback_action == FeedbackAction.REPLAN:
            return await self._handle_replan(drift_report, original_plan, execution_history)

        else:  # ESCALATE
            return CorrectionResult(
                action=FeedbackAction.ESCALATE,
                replanned_tasks=[],
                retry_count=0,
                explanation="偏离度过大，需要人工介入"
            )

    async def _handle_replan(
        self,
        drift_report: DriftReport,
        original_plan: IntentSpec,
        history: list[ExecutionAttempt]
    ) -> CorrectionResult:
        prompt = f"""
        用户原始规划：
        {original_plan.summary}

        执行偏离报告：
        {drift_report.summary}

        执行历史：
        {self._format_history(history)}

        请重新规划执行任务，确保：
        1. 解决所有偏离问题
        2. 不引入新的偏离
        3. 保持与原始规划的一致性

        输出格式：
        - 需要重试的任务列表
        - 修正策略
        - 预期结果
        """
        response = await self.llm.generate(prompt)

        return CorrectionResult(
            action=FeedbackAction.REPLAN,
            replanned_tasks=self._parse_replanned_tasks(response),
            retry_count=len(history) + 1,
            explanation=response
        )
```

---

## Phase 3: User Memory - 用户记忆层

### M1: 偏好学习器

**状态**: ⏳ pending

**输入**:
- 用户反馈（每次执行后）
- 用户手动设置

**输出**:
```python
@dataclass
class UserPreference:
    user_id: str
    coding_style: CodingStyle
    stack_preferences: StackPreferences
    quality_bar: QualityBar
    communication_style: CommunicationStyle
    updated_at: datetime

@dataclass
class CodingStyle:
    naming_convention: str  # snake_case / camelCase / PascalCase
    comment_style: str  # minimal / moderate / detailed
    architecture: str  # monolithic / modular / microservices
    testing_preference: str  # TDD / after / minimal

@dataclass
class QualityBar:
    min_coverage: float  # 0-100
    max_critical_bugs: int
    min_documentation_score: float
```

**实现**:

```python
# src/peas/memory/preference_learner.py
class PreferenceLearner:
    """从用户反馈中学习偏好"""

    def __init__(self, storage: PreferenceStorage):
        self.storage = storage

    async def learn_from_feedback(
        self,
        user_id: str,
        feedback: UserFeedback
    ) -> UserPreference:
        # 1. 获取当前偏好
        current = await self.storage.get(user_id) or UserPreference.default(user_id)

        # 2. 分析反馈
        if feedback.type == FeedbackType.LIKE:
            # 强化正向行为
            current = self._reinforce_positive(current, feedback)
        elif feedback.type == FeedbackType.DISLIKE:
            # 修正负向行为
            current = self._correct_negative(current, feedback)
        elif feedback.type == FeedbackType.MANUAL:
            # 直接更新
            current = self._apply_manual(current, feedback)

        # 3. 保存
        current.updated_at = datetime.now()
        await self.storage.save(current)

        return current

    def _reinforce_positive(
        self,
        pref: UserPreference,
        feedback: UserFeedback
    ) -> UserPreference:
        """强化正向模式"""
        # 例如：用户说"代码风格很好"
        # → 增加当前编码风格的权重
        return pref  # 返回更新后的偏好
```

---

### M2: 风格画像

**状态**: ⏳ pending

**输入**:
- 历史代码产出
- 用户偏好

**输出**:
```python
@dataclass
class UserStyleProfile:
    user_id: str
    patterns: list[CodePattern]  # 常用的代码模式
    anti_patterns: list[str]  # 用户不喜欢的模式
    tech_stack: list[str]  # 偏好技术栈
    architecture_taste: ArchitectureTaste

@dataclass
class CodePattern:
    name: str
    frequency: float
    example: str
    context: str  # 在什么场景使用
```

**实现**:

```python
# src/peas/memory/style_profiler.py
class StyleProfiler:
    """构建用户风格画像"""

    def __init__(self, llm_client, storage: StyleStorage):
        self.llm = llm_client
        self.storage = storage

    async def build_profile(
        self,
        user_id: str,
        code_samples: list[str]
    ) -> UserStyleProfile:
        # 1. LLM分析代码样本
        prompt = f"""
        分析以下代码样本，总结用户的编码风格：

        代码样本：
        {code_samples[:5]}  # 限制数量避免token溢出

        分析维度：
        1. 命名规范
        2. 代码组织
        3. 注释风格
        4. 架构偏好
        5. 常用的设计模式
        6. 不喜欢的模式
        """
        analysis = await self.llm.generate(prompt)

        # 2. 存储画像
        profile = self._parse_profile(analysis)
        await self.storage.save(profile)

        return profile

    async def match_style(
        self,
        template_code: str,
        user_id: str
    ) -> str:
        """根据用户风格调整代码模板"""
        profile = await self.storage.get(user_id)
        if not profile:
            return template_code  # 没有画像，返回原始模板

        prompt = f"""
        调整以下代码模板以匹配用户风格：

        用户风格：
        - 命名规范: {profile.coding_style.naming_convention}
        - 注释风格: {profile.coding_style.comment_style}
        - 架构偏好: {profile.coding_style.architecture}

        代码模板：
        {template_code}

        输出调整后的代码。
        """
        return await self.llm.generate(prompt)
```

---

### M3: 上下文持久化

**状态**: ⏳ pending

**输入**:
- 跨会话的上下文信息
- 项目知识

**输出**:
```python
@dataclass
class PersistentContext:
    user_id: str
    project_context: list[ProjectMemory]
    conversation_history: list[SessionSummary]
    learned_facts: list[LearnedFact]

@dataclass
class ProjectMemory:
    project_id: str
    domain_knowledge: str
    key_decisions: list[Decision]
    glossary: dict[str, str]  # 业务术语解释
```

**实现**:

```python
# src/peas/memory/context_persistence.py
class ContextPersistence:
    """持久化跨会话上下文"""

    def __init__(self, storage: ContextStorage):
        self.storage = storage

    async def save_context(
        self,
        user_id: str,
        session_data: SessionData
    ) -> None:
        # 1. 提取项目知识
        project_memory = await self._extract_project_knowledge(session_data)

        # 2. 总结会话
        summary = self._summarize_session(session_data)

        # 3. 提取学到的facts
        facts = await self._extract_learned_facts(session_data)

        # 4. 存储
        context = await self.storage.get(user_id) or PersistentContext(user_id)
        context.project_context.append(project_memory)
        context.conversation_history.append(summary)
        context.learned_facts.extend(facts)

        await self.storage.save(context)

    async def get_relevant_context(
        self,
        user_id: str,
        current_task: str
    ) -> PersistentContext:
        """获取与当前任务相关的上下文"""
        full_context = await self.storage.get(user_id)

        # 过滤相关项目
        relevant_projects = [
            p for p in full_context.project_context
            if self._is_relevant(p, current_task)
        ]

        return PersistentContext(
            user_id=user_id,
            project_context=relevant_projects,
            conversation_history=full_context.conversation_history[-5:],  # 最近5个会话
            learned_facts=self._filter_facts(full_context.learned_facts, current_task)
        )
```

---

## Phase 4: Integration - 集成层

### I1: 与Harness引擎集成

**状态**: ⏳ pending

**集成点**:

```python
# src/peas/integration/harness_integration.py

class PEASHarnessIntegration:
    """将PEAS集成到Harness执行引擎"""

    def __init__(
        self,
        harness: HarnessEngine,
        plan_understanding: PlanUnderstandingLayer,
        alignment_verification: AlignmentVerificationLayer,
        user_memory: UserMemoryLayer
    ):
        self.harness = harness
        self.plan_layer = plan_understanding
        self.verify_layer = alignment_verification
        self.memory = user_memory

    async def execute_with_alignment(
        self,
        user_spec: UserSpec,  # Markdown + 原型
        context: dict
    ) -> AlignmentExecutionResult:
        # 1. Plan Understanding
        contract = await self.plan_layer.build_contract(user_spec)

        # 2. 获取用户偏好
        user_pref = await self.memory.get_preference(context.user_id)

        # 3. 注入偏好到执行上下文
        enhanced_context = {
            **context,
            "user_preference": user_pref,
            "execution_contract": contract
        }

        # 4. 执行 Harness
        # 在每个阶段后进行对齐检查
        for phase in [ExecutionPhase.UNIT, ExecutionPhase.INTEGRATION, ExecutionPhase.E2E]:
            phase_result = await self.harness.execute_phase(phase, enhanced_context)

            # 对齐检查
            drift_report = await self.verify_layer.check_alignment(
                contract, phase_result
            )

            if drift_report.feedback_action == FeedbackAction.REPLAN:
                # 重新规划后继续
                enhanced_context = await self._replan_and_continue(
                    drift_report, enhanced_context
                )

        # 5. 最终验证
        final_report = await self.verify_layer.generate_final_report(contract, enhanced_context)

        # 6. 学习用户偏好
        await self.memory.learn_from_execution(context.user_id, final_report)

        return AlignmentExecutionResult(
            contract=contract,
            execution_result=enhanced_context,
            alignment_report=final_report
        )
```

---

### I2: WebUI对齐面板

**状态**: ⏳ pending

**页面**: `webui/pages/alignment_dashboard.py`

**功能**:
1. 显示执行合约
2. 实时显示对齐状态
3. 偏离告警
4. 用户反馈输入

```python
# webui/pages/alignment_dashboard.py

def render_alignment_dashboard():
    st.title("📋 Plan-Execution Alignment")

    # 1. 当前合约
    contract = st.session_state.current_contract

    # 2. 对齐状态
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Drift Score", f"{contract.drift_score}%")

    with col2:
        st.metric("Features Verified",
            f"{contract.verified_count}/{contract.total_count}")

    with col3:
        st.metric("User Preference Match",
            f"{contract.preference_match}%")

    # 3. 功能点列表
    st.subheader("Feature Status")
    for req in contract.requirements:
        status_icon = {
            'verified': '✅',
            'failed': '❌',
            'pending': '⏳'
        }[req.status]
        st.markdown(f"{status_icon} **{req.id}**: {req.description}")

    # 4. 偏离详情
    if contract.drift_report:
        st.subheader("Drift Details")
        for drift in contract.drift_report.drifted_requirements:
            with st.expander(f"❌ {drift.req_id}: {drift.drift_type}"):
                st.write(f"**Expected**: {drift.expected}")
                st.write(f"**Actual**: {drift.actual}")
                st.write(f"**Suggestion**: {drift.fix_suggestion}")

    # 5. 用户反馈
    st.subheader("Feedback")
    feedback = st.selectbox(
        "Was this execution aligned with your intent?",
        ["👍 Good", "👎 Not aligned", "🤔 Partial"]
    )
    if st.button("Submit Feedback"):
        await submit_feedback(feedback)
```

---

## Layer 2: 实施计划

### Sprint 1: 核心抽象和Parser (1周)

| 任务 | 描述 | 文件 |
|------|------|------|
| P1.1 | 创建PEAS目录结构 | src/peas/ |
| P1.2 | 实现MarkdownParser基础 | src/peas/understanding/markdown_parser.py |
| P1.3 | 实现HTMLPrototypeParser | src/peas/understanding/prototype_parser.py |
| P1.4 | 基础单元测试 | tests/peas/test_parser.py |

### Sprint 2: Intent和Contract (1周)

| 任务 | 描述 | 文件 |
|------|------|------|
| P3.1 | 实现IntentExtractor | src/peas/understanding/intent_extractor.py |
| P4.1 | 实现ContractBuilder | src/peas/understanding/contract_builder.py |
| P4.2 | 实现Contract Storage | src/peas/storage/contract_store.py |
| P2.1 | 集成LLM Client | src/peas/llm/ |

### Sprint 3: Verification (1周)

| 任务 | 描述 | 文件 |
|------|------|------|
| A1.1 | 实现FeaturePointTracker | src/peas/verification/feature_tracker.py |
| A2.1 | 实现UIComparator | src/peas/verification/ui_comparator.py |
| A3.1 | 实现DriftDetector | src/peas/verification/drift_detector.py |
| A4.1 | 实现CorrectionLoop | src/peas/verification/correction_loop.py |

### Sprint 4: Memory (1周)

| 任务 | 描述 | 文件 |
|------|------|------|
| M1.1 | 实现PreferenceLearner | src/peas/memory/preference_learner.py |
| M2.1 | 实现StyleProfiler | src/peas/memory/style_profiler.py |
| M3.1 | 实现ContextPersistence | src/peas/memory/context_persistence.py |

### Sprint 5: Integration (1周)

| 任务 | 描述 | 文件 |
|------|------|------|
| I1.1 | Harness集成 | src/peas/integration/harness_integration.py |
| I2.1 | WebUI对齐面板 | webui/pages/alignment_dashboard.py |
| I3.1 | 端到端测试 | tests/peas/test_e2e.py |

---

## Layer 3: 验证标准

### 功能验证

- [ ] Markdown解析准确率 > 90%
- [ ] HTML原型解析完整
- [ ] 意图提取一致性 > 85%
- [ ] 合约覆盖率 > 95%
- [ ] 偏离检测召回率 > 90%
- [ ] 修正循环有效率 > 80%

### 性能验证

- [ ] Plan Understanding 延迟 < 10s
- [ ] Verification 延迟 < 5s/feature
- [ ] Memory 查询延迟 < 100ms

### 用户价值验证

- [ ] 用户反馈"对齐"率 > 80%
- [ ] 偏好学习准确率 > 75%
- [ ] 跨会话上下文保持率 > 90%

---

## Layer 4: 关键文件索引

```
src/peas/
├── __init__.py
├── understanding/
│   ├── __init__.py
│   ├── markdown_parser.py      # P1
│   ├── prototype_parser.py     # P2
│   ├── intent_extractor.py     # P3
│   └── contract_builder.py      # P4
├── verification/
│   ├── __init__.py
│   ├── feature_tracker.py       # A1
│   ├── ui_comparator.py        # A2
│   ├── drift_detector.py        # A3
│   └── correction_loop.py      # A4
├── memory/
│   ├── __init__.py
│   ├── preference_learner.py    # M1
│   ├── style_profiler.py       # M2
│   └── context_persistence.py   # M3
├── integration/
│   ├── __init__.py
│   ├── harness_integration.py  # I1
│   └── agent_integration.py    # I2
├── llm/
│   ├── __init__.py
│   └── client.py
├── storage/
│   ├── __init__.py
│   ├── contract_store.py
│   ├── preference_store.py
│   └── context_store.py
└── types/
    ├── __init__.py
    ├── document.py
    ├── contract.py
    └── verification.py

webui/pages/
└── alignment_dashboard.py      # I2

tests/peas/
├── test_parser.py
├── test_verification.py
├── test_memory.py
└── test_e2e.py
```

---

## 下一步

1. **确认计划** - 用户确认后开始实施
2. **创建目录结构** - Sprint 1第一步
3. **实现核心Parser** - 最小可运行版本
4. **集成测试** - 确保各层配合正确

---

**文档版本**: v1.0
**创建日期**: 2026-03-19
**状态**: 待用户确认
