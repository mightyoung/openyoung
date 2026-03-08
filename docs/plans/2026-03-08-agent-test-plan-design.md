# OpenYoung AI Agent 测试计划 - 详细设计

> 日期: 2026-03-08
> 版本: 1.0

---

## 1. 概述

### 1.1 目标

为 OpenYoung AI Agent 平台设计一套全面的测试计划，重点验证：
- **输入理解**：Agent 能否准确解析用户意图和任务描述
- **输出质量**：Agent 生成的答案或执行的结果是否符合预期

### 1.2 策略

采用**预设测试集 + 真实任务采样**结合的方式：
- 预设测试集：50+ 场景，覆盖主要任务类型
- 真实采样：从生产环境获取真实用户任务

---

## 2. 架构设计

### 2.1 测试系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Test Runner                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Input Understanding                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Intent Parse │  │ Task Class  │  │Param Extract│    │   │
│  │  │   Tests     │  │   Tests     │  │   Tests    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↕                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Output Quality                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │Rule Checking│  │LLM Judge   │  │Format Valid │    │   │
│  │  │   Tests    │  │   Tests     │  │   Tests    │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        Test Data                                │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │   Preset Dataset    │    │    Production Sampling       │  │
│  │   (50+ scenarios)   │    │    (Real user tasks)        │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心模块

| 模块 | 职责 | 关键类 |
|------|------|--------|
| `TestRunner` | 测试执行编排 | `AgentTestRunner` |
| `InputTester` | 输入理解验证 | `IntentParser`, `TaskClassifier` |
| `OutputTester` | 输出质量评估 | `RuleChecker`, `LLMJudge` |
| `TestDataManager` | 测试数据管理 | `PresetDataset`, `ProductionSampler` |
| `ReportGenerator` | 测试报告生成 | `TestReport`, `MetricsReport` |

---

## 3. 测试维度

### 3.1 输入理解测试

| 测试项 | 验证内容 | 测试方式 |
|--------|----------|----------|
| **意图解析** | 能否准确理解用户意图 | 与标注数据对比，计算准确率 |
| **任务分类** | 能否正确分类任务类型 | 多分类测试集验证 |
| **参数提取** | 能否正确提取关键参数 | 结构化输出验证 |
| **歧义处理** | 能否处理模糊输入 | 边界测试用例 |

### 3.2 输出质量测试

| 测试项 | 验证内容 | 测试方式 |
|--------|----------|----------|
| **任务完成率** | 任务是否完成 | 规则检查（文件存在、状态等） |
| **输出相关性** | 输出是否与任务相关 | LLM Judge 评分 |
| **格式正确性** | 输出格式是否符合预期 | 结构化验证 |
| **内容准确性** | 输出内容是否正确 | 规则 + LLM Judge |

---

## 4. 测试数据设计

### 4.1 预设测试集（50+ 场景）

按任务类型分布：

| 任务类型 | 数量 | 示例 |
|----------|------|------|
| 代码生成 | 10 | "写一个快速排序函数" |
| 代码修改 | 8 | "修复这个函数的 bug" |
| 文本生成 | 8 | "写一篇博客关于 AI" |
| 数据处理 | 6 | "分析这个 CSV 文件" |
| 信息查询 | 6 | "查找 Python 最佳实践" |
| 任务执行 | 6 | "运行这个测试" |
| 问题解答 | 6 | "解释什么是 CQRS" |

### 4.2 测试用例结构

```python
@dataclass
class TestCase:
    id: str                          # 唯一标识
    task_description: str            # 任务描述
    task_type: TaskType              # 任务类型
    expected_intent: str             # 预期意图
    expected_params: dict            # 预期参数
    expected_output_format: str      # 预期输出格式
    expected_output_sample: str      # 预期输出示例（可选）
    difficulty: Difficulty           # 难度级别
    keywords: list[str]              # 关键词（用于任务分类测试）
```

### 4.3 真实任务采样

```python
@dataclass
class ProductionSample:
    task_id: str                     # 任务 ID
    task_description: str            # 任务描述
    result: str                      # 实际输出
    quality_score: float             # 质量评分（可选）
    user_feedback: str               # 用户反馈（可选）
    timestamp: datetime              # 时间戳
```

---

## 5. 输入理解测试设计

### 5.1 意图解析测试

**测试目标**：验证 Agent 能否准确理解用户意图

**测试方法**：
1. 准备标注数据集（输入 → 预期意图）
2. 运行 Agent 解析输入
3. 对比结果，计算准确率

**评估指标**：
- 准确率（Accuracy）
- 精确率（Precision）
- 召回率（Recall）
- F1 分数

**示例测试用例**：
```python
test_cases = [
    {
        "input": "帮我写一个 Python 函数来计算斐波那契数列",
        "expected_intent": "code_generation",
    },
    {
        "input": "这个代码有 bug，帮我修一下",
        "expected_intent": "code_fix",
    },
    {
        "input": "什么是 REST API?",
        "expected_intent": "question_answering",
    },
]
```

### 5.2 任务分类测试

**测试目标**：验证 Agent 能否正确分类任务类型

**任务类型定义**：
```python
class TaskType(Enum):
    CODE_GENERATION = "code_generation"    # 代码生成
    CODE_FIX = "code_fix"                   # 代码修复
    CODE_REVIEW = "code_review"             # 代码审查
    TEXT_GENERATION = "text_generation"     # 文本生成
    QUESTION_ANSWERING = "question_answering"  # 问答
    DATA_PROCESSING = "data_processing"     # 数据处理
    TASK_EXECUTION = "task_execution"       # 任务执行
    INFORMATION_QUERY = "information_query"   # 信息查询
```

**测试方法**：
1. 准备多分类测试集
2. 运行任务分类
3. 计算分类准确率

---

## 6. 输出质量测试设计

### 6.1 规则检查测试

**适用场景**：可明确验证的任务

**示例**：
- 文件创建任务 → 检查文件是否存在
- 数据处理任务 → 检查输出格式
- 代码生成任务 → 检查语法正确性

```python
class RuleChecker:
    def check_file_creation(self, task: str, result: str) -> bool:
        """检查文件创建任务"""
        # 提取文件路径
        # 检查文件是否存在
        # 检查内容是否为空
        pass

    def check_format_validity(self, task: str, result: str, format: str) -> bool:
        """检查格式有效性"""
        pass
```

### 6.2 LLM Judge 评估

**设计参考**：OpenAI、Anthropic 评估框架

**架构**：
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent    │────▶│   Output   │────▶│  LLM Judge  │
│   Output   │     │   Store    │     │   Evaluator │
└─────────────┘     └─────────────┘     └─────────────┘
                                               ↕
                                        ┌─────────────┐
                                        │ Quality     │
                                        │ Score       │
                                        └─────────────┘
```

**评分维度**：
```python
class JudgeDimension(Enum):
    COMPLETENESS = "completeness"       # 完整性：是否完成所有要求
    ACCURACY = "accuracy"               # 准确性：内容是否正确
    RELEVANCE = "relevance"             # 相关性：是否切题
    COHERENCE = "coherence"             # 连贯性：逻辑是否清晰
    SAFETY = "safety"                   # 安全性：是否包含有害内容
```

**评分 Prompt 示例**：
```
你是一个专业的代码评审专家。请根据以下维度评估 Agent 的输出质量：

任务：{task_description}
输出：{output}

请给出 0-1 的评分，并解释理由。
```

### 6.3 格式验证测试

**验证类型**：
- JSON 格式验证
- Markdown 格式验证
- 代码语法验证
- 自定义格式验证

---

## 7. 测试执行

### 7.1 测试运行器

```python
class AgentTestRunner:
    def __init__(self, agent: YoungAgent):
        self.agent = agent
        self.input_tester = InputTester()
        self.output_tester = OutputTester()

    async def run_all_tests(self) -> TestReport:
        """运行所有测试"""
        results = []

        # 输入理解测试
        input_results = await self.input_tester.run_all()
        results.extend(input_results)

        # 输出质量测试
        output_results = await self.output_tester.run_all()
        results.extend(output_results)

        return TestReport(results=results)

    async def run_suite(self, suite_name: str) -> TestReport:
        """运行指定测试套件"""
        pass
```

### 7.2 测试套件

| 套件名称 | 测试内容 | 运行频率 |
|----------|----------|----------|
| `unit` | 单元测试 | 每次提交 |
| `integration` | 集成测试 | 每日 |
| `e2e` | 端到端测试 | 每周 |
| `regression` | 回归测试 | 发布前 |
| `performance` | 性能测试 | 每周 |

---

## 8. 测试报告

### 8.1 报告结构

```python
@dataclass
class TestReport:
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int

    # 维度分数
    input_understanding_score: float    # 输入理解得分
    output_quality_score: float        # 输出质量得分

    # 详细结果
    results: list[TestResult]

@dataclass
class TestResult:
    test_id: str
    test_type: str                     # "input_understanding" | "output_quality"
    dimension: str                     # 具体维度
    passed: bool
    score: float                       # 0-1
    details: dict                      # 详细信息
```

### 8.2 可视化指标

| 指标 | 描述 | 目标值 |
|------|------|--------|
| 意图解析准确率 | 正确理解用户意图的比例 | ≥ 85% |
| 任务分类准确率 | 正确分类任务类型的比例 | ≥ 90% |
| 任务完成率 | 成功完成任务的的比例 | ≥ 80% |
| 输出质量评分 | LLM Judge 平均评分 | ≥ 0.8 |
| 平均响应时间 | 端到端响应时间 | < 30s |

---

## 9. 实现计划

### Phase 1: 基础设施（1 周）

- [ ] 创建测试框架基础结构
- [ ] 实现 TestRunner 核心类
- [ ] 设计测试数据模型
- [ ] 搭建测试报告系统

### Phase 2: 预设测试集（2 周）

- [ ] 设计 50+ 测试用例
- [ ] 实现任务分类测试
- [ ] 实现意图解析测试
- [ ] 实现格式验证测试

### Phase 3: 输出评估（2 周）

- [ ] 集成 LLM Judge
- [ ] 实现规则检查器
- [ ] 实现多维度评分
- [ ] 优化评估 Prompt

### Phase 4: 真实采样（1 周）

- [ ] 实现生产数据采样器
- [ ] 建立持续测试流程
- [ ] 集成监控告警

---

## 10. 附录

### A. 测试用例示例

```python
# 代码生成任务测试用例
{
    "id": "code_gen_001",
    "task_description": "用 Python 写一个函数，计算列表的平均值",
    "task_type": TaskType.CODE_GENERATION,
    "expected_intent": "code_generation",
    "expected_output_format": "python_code",
    "difficulty": Difficulty.EASY,
}

# 问答任务测试用例
{
    "id": "qa_001",
    "task_description": "什么是 CQRS 模式?",
    "task_type": TaskType.QUESTION_ANSWERING,
    "expected_intent": "question_answering",
    "expected_output_format": "text",
    "difficulty": Difficulty.MEDIUM,
}
```

### B. 评估 Prompt 模板

```python
EVALUATION_PROMPT = """
你是一个专业的 AI Agent 评估专家。请根据以下维度评估 Agent 的输出质量。

## 任务信息
任务描述：{task_description}
任务类型：{task_type}
预期输出格式：{expected_format}

## Agent 输出
{output}

## 评估维度
1. 完整性（Completeness）：是否完成了任务的所有要求？
2. 准确性（Accuracy）：输出内容是否正确？
3. 相关性（Relevance）：输出是否切题？
4. 格式正确性（Format）：输出格式是否符合要求？

## 输出格式
请按以下 JSON 格式返回评估结果：
{{
    "scores": {{
        "completeness": 0.0-1.0,
        "accuracy": 0.0-1.0,
        "relevance": 0.0-1.0,
        "format": 0.0-1.0
    }},
    "overall_score": 0.0-1.0,
    "feedback": "评估反馈"
}}
"""
```

---

## 参考资料

- OpenAI Evals 框架
- Anthropic 评估最佳实践
- Google ML Engineering Guide
- Martin Fowler 测试策略
