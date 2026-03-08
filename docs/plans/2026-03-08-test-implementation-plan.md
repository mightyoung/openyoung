# OpenYoung AI Agent 测试计划 - 详细实现计划

> 日期: 2026-03-08
> 关联设计: docs/plans/2026-03-08-agent-test-plan-design.md

---

## 一、测试系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      Test Framework                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────┐   │
│  │ Test Runner     │    │ Test Data Manager               │   │
│  │ - run_all()    │    │ - PresetDataset (50+ cases)    │   │
│  │ - run_suite()  │    │ - ProductionSampler            │   │
│  │ - run_case()   │    │ - TestDataLoader               │   │
│  └────────┬────────┘    └─────────────────────────────────┘   │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Test Suites                              │   │
│  │  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │Input Tests   │  │Output Tests  │                  │   │
│  │  │- intent      │  │- rule_check  │                  │   │
│  │  │- classify    │  │- llm_judge  │                  │   │
│  │  │- extract     │  │- format     │                  │   │
│  │  └──────────────┘  └──────────────┘                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                 │
│                              ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Report Generator                         │   │
│  │  - TestReport    - MetricsReport    - TrendReport    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心模块详细设计

### 2.1 测试数据模型

```python
# src/evaluation/test_framework/models.py

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Optional

class TaskType(Enum):
    """任务类型"""
    CODE_GENERATION = "code_generation"
    CODE_FIX = "code_fix"
    CODE_REVIEW = "code_review"
    TEXT_GENERATION = "text_generation"
    QUESTION_ANSWERING = "question_answering"
    DATA_PROCESSING = "data_processing"
    TASK_EXECUTION = "task_execution"
    INFORMATION_QUERY = "information_query"

class Difficulty(Enum):
    """难度级别"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

@dataclass
class TestCase:
    """测试用例"""
    id: str
    task_description: str
    task_type: TaskType
    expected_intent: str
    expected_params: dict = field(default_factory=dict)
    expected_output_format: str = "text"
    expected_output_sample: Optional[str] = None
    difficulty: Difficulty = Difficulty.MEDIUM
    keywords: list[str] = field(default_factory=list)
    # 用于输出质量测试
    validation_rules: Optional[dict] = None

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_type: str  # "input_understanding" | "output_quality"
    dimension: str  # 具体维度
    passed: bool
    score: float  # 0-1
    details: dict = field(default_factory=dict)
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class TestReport:
    """测试报告"""
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int
    # 维度分数
    input_understanding_score: float = 0.0
    output_quality_score: float = 0.0
    # 详细结果
    results: list[TestResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total_tests if self.total_tests > 0 else 0
```

### 2.2 测试运行器

```python
# src/evaluation/test_framework/runner.py

import asyncio
from typing import Optional
from dataclasses import dataclass

@dataclass
class RunnerConfig:
    """运行器配置"""
    parallel: bool = True
    max_workers: int = 5
    timeout_seconds: int = 300
    continue_on_error: bool = True

class AgentTestRunner:
    """测试运行器"""

    def __init__(
        self,
        agent,  # YoungAgent instance
        config: Optional[RunnerConfig] = None
    ):
        self.agent = agent
        self.config = config or RunnerConfig()
        self.input_tester = InputTester(agent)
        self.output_tester = OutputTester(agent)
        self.test_data_manager = TestDataManager()

    async def run_all_tests(
        self,
        dataset_name: str = "default"
    ) -> TestReport:
        """运行所有测试"""
        # 加载测试数据
        test_cases = await self.test_data_manager.load_dataset(dataset_name)

        results = []
        start_time = datetime.now()

        # 输入理解测试
        for case in test_cases:
            if case.task_type in INPUT_TASK_TYPES:
                result = await self.input_tester.run(case)
                results.append(result)

        # 输出质量测试
        for case in test_cases:
            if case.task_type in OUTPUT_TASK_TYPES:
                result = await self.output_tester.run(case)
                results.append(result)

        end_time = datetime.now()

        # 生成报告
        return self._generate_report(results, start_time, end_time)

    async def run_suite(
        self,
        suite_name: str,
        dataset_name: str = "default"
    ) -> TestReport:
        """运行指定测试套件"""
        test_cases = await self.test_data_manager.load_suite(suite_name, dataset_name)
        # ... 类似实现
```

### 2.3 输入理解测试

```python
# src/evaluation/test_framework/input_tester.py

class InputTester:
    """输入理解测试"""

    def __init__(self, agent):
        self.agent = agent

    async def run(self, test_case: TestCase) -> TestResult:
        """运行单个测试"""
        start_time = datetime.now()

        # 1. 获取 Agent 的解析结果
        # 通过观察 Agent 的行为来推断其理解
        parsed_result = await self._parse_input(test_case.task_description)

        # 2. 计算匹配度
        score = self._calculate_match(parsed_result, test_case)

        # 3. 判断是否通过
        passed = score >= 0.7

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return TestResult(
            test_id=test_case.id,
            test_type="input_understanding",
            dimension="intent_parsing",
            passed=passed,
            score=score,
            details={
                "parsed": parsed_result,
                "expected": test_case.expected_intent,
            },
            duration_ms=duration_ms,
        )

    async def _parse_input(self, task_description: str) -> dict:
        """解析输入 - 通过 Agent 行为推断"""
        # 方法1: 使用 Agent 的任务分类能力
        # 方法2: 分析 Agent 的响应模式
        # 方法3: 添加探测性问题
        pass

    def _calculate_match(self, parsed: dict, expected: TestCase) -> float:
        """计算匹配度"""
        # 意图匹配
        intent_match = 1.0 if parsed.get("intent") == expected.expected_intent else 0.0

        # 参数匹配
        param_match = self._calculate_param_match(
            parsed.get("params", {}),
            expected.expected_params
        )

        return (intent_match * 0.7) + (param_match * 0.3)
```

### 2.4 输出质量测试

```python
# src/evaluation/test_framework/output_tester.py

class OutputTester:
    """输出质量测试"""

    def __init__(self, agent):
        self.agent = agent
        self.rule_checker = RuleChecker()
        self.llm_judge = None  # 延迟初始化

    async def run(self, test_case: TestCase) -> TestResult:
        """运行输出质量测试"""
        start_time = datetime.now()

        # 1. 执行任务获取输出
        output = await self._execute_task(test_case.task_description)

        # 2. 规则检查
        rule_score = await self.rule_checker.check(
            test_case.task_description,
            output,
            test_case.validation_rules or {}
        )

        # 3. LLM Judge 评估（可选，用于高质量评估）
        llm_score = 0.0
        if self.llm_judge:
            llm_score = await self.llm_judge.evaluate(
                test_case.task_description,
                output,
                test_case.expected_output_sample
            )

        # 4. 综合评分
        score = (rule_score * 0.5) + (llm_score * 0.5)
        passed = score >= 0.6

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return TestResult(
            test_id=test_case.id,
            test_type="output_quality",
            dimension="completeness",
            passed=passed,
            score=score,
            details={
                "output": output[:200],  # 截断
                "rule_score": rule_score,
                "llm_score": llm_score,
            },
            duration_ms=duration_ms,
        )

    async def _execute_task(self, task_description: str) -> str:
        """执行任务获取输出"""
        # 调用 Agent 执行任务
        return await self.agent.run(task_description)
```

### 2.5 规则检查器

```python
# src/evaluation/test_framework/rule_checker.py

import re
import json
from pathlib import Path

class RuleChecker:
    """规则检查器"""

    def __init__(self):
        self.check_registry = {
            "file_exists": self._check_file_exists,
            "json_format": self._check_json_format,
            "code_syntax": self._check_code_syntax,
            "output_contains": self._check_output_contains,
            "output_length": self._check_output_length,
        }

    async def check(
        self,
        task_description: str,
        output: str,
        rules: dict
    ) -> float:
        """执行规则检查"""
        if not rules:
            # 默认：检查是否有输出
            return 1.0 if output and len(output) > 0 else 0.0

        results = []
        for rule_name, rule_params in rules.items():
            checker = self.check_registry.get(rule_name)
            if checker:
                result = await checker(task_description, output, rule_params)
                results.append(result)

        return sum(results) / len(results) if results else 0.0

    async def _check_file_exists(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查文件是否存在"""
        file_path = params.get("path")
        if not file_path:
            # 从输出中提取路径
            match = re.search(r'(?:保存|输出|写入|创建)\s+(.+\.(?:json|txt|csv|py))', output)
            if match:
                file_path = match.group(1)

        if not file_path:
            return 0.0

        exists = Path(file_path).exists()
        return 1.0 if exists else 0.0

    async def _check_json_format(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查 JSON 格式"""
        try:
            # 尝试从输出中提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                json.loads(json_match.group())
                return 1.0
        except:
            pass
        return 0.0

    async def _check_output_contains(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查输出是否包含关键内容"""
        required = params.get("required", [])
        if not required:
            return 1.0

        found = sum(1 for kw in required if kw.lower() in output.lower())
        return found / len(required)
```

---

## 三、预设测试数据集

### 3.1 数据结构

```python
# tests/fixtures/test_dataset.py

TEST_DATASET = {
    "default": [
        # 代码生成 (10 cases)
        {
            "id": "code_gen_001",
            "task_description": "用 Python 写一个函数，计算列表的平均值",
            "task_type": "code_generation",
            "expected_intent": "code_generation",
            "expected_output_format": "python_code",
            "difficulty": "easy",
            "keywords": ["python", "函数", "平均"],
            "validation_rules": {
                "output_contains": {"required": ["def", "return", "sum"]}
            }
        },
        {
            "id": "code_gen_002",
            "task_description": "实现一个快速排序算法",
            "task_type": "code_generation",
            "expected_intent": "code_generation",
            "expected_output_format": "python_code",
            "difficulty": "medium",
            "keywords": ["快速排序", "算法"],
            "validation_rules": {
                "output_contains": {"required": ["def", "quick"]}
            }
        },
        # ... 8 more code generation cases

        # 代码修复 (8 cases)
        {
            "id": "code_fix_001",
            "task_description": "这个函数有 bug，帮我修一下",
            "task_type": "code_fix",
            "expected_intent": "code_fix",
            "expected_output_format": "python_code",
            "difficulty": "medium",
            "keywords": ["bug", "修复", "错误"],
        },
        # ... 7 more code fix cases

        # 文本生成 (8 cases)
        {
            "id": "text_gen_001",
            "task_description": "写一篇关于 AI 发展的博客文章",
            "task_type": "text_generation",
            "expected_intent": "text_generation",
            "expected_output_format": "markdown",
            "difficulty": "medium",
            "keywords": ["AI", "发展", "文章"],
        },
        # ... 7 more text generation cases

        # 数据处理 (6 cases)
        {
            "id": "data_001",
            "task_description": "分析这个 CSV 文件并给出统计摘要",
            "task_type": "data_processing",
            "expected_intent": "data_processing",
            "expected_output_format": "text",
            "difficulty": "medium",
            "keywords": ["CSV", "分析", "统计"],
            "validation_rules": {
                "output_contains": {"required": ["总计", "平均", "count"]}
            }
        },
        # ... 5 more data processing cases

        # 信息查询 (6 cases)
        {
            "id": "query_001",
            "task_description": "Python 异步编程的最佳实践是什么?",
            "task_type": "information_query",
            "expected_intent": "question_answering",
            "expected_output_format": "text",
            "difficulty": "medium",
            "keywords": ["Python", "异步", "最佳实践"],
        },
        # ... 5 more query cases

        # 任务执行 (6 cases)
        {
            "id": "exec_001",
            "task_description": "运行项目中的所有测试",
            "task_type": "task_execution",
            "expected_intent": "task_execution",
            "expected_output_format": "text",
            "difficulty": "easy",
            "keywords": ["运行", "测试", "execute"],
        },
        # ... 5 more execution cases

        # 问题解答 (6 cases)
        {
            "id": "qa_001",
            "task_description": "什么是 CQRS 模式?",
            "task_type": "question_answering",
            "expected_intent": "question_answering",
            "expected_output_format": "text",
            "difficulty": "medium",
            "keywords": ["CQRS", "模式", "架构"],
        },
        # ... 5 more QA cases
    ]
}
```

---

## 四、实现计划

### Phase 1: 基础设施（1 周）

| 任务 | 描述 | 预估时间 | 优先级 |
|------|------|----------|--------|
| T1.1 | 创建测试框架目录结构 `src/evaluation/test_framework/` | 1h | P0 |
| T1.2 | 实现数据模型 (TestCase, TestResult, TestReport) | 2h | P0 |
| T1.3 | 实现 TestDataManager 数据加载器 | 2h | P0 |
| T1.4 | 实现 AgentTestRunner 测试运行器 | 3h | P0 |
| T1.5 | 创建测试报告生成器 | 2h | P1 |

### Phase 2: 输入理解测试（1.5 周）

| 任务 | 描述 | 预估时间 | 优先级 |
|------|------|----------|--------|
| T2.1 | 实现 InputTester 基础类 | 2h | P0 |
| T2.2 | 实现意图解析测试 | 3h | P0 |
| T2.3 | 实现任务分类测试 | 3h | P0 |
| T2.4 | 实现参数提取测试 | 2h | P1 |
| T2.5 | 创建预设测试数据集 (50+ cases) | 4h | P0 |

### Phase 3: 输出质量测试（1.5 周）

| 任务 | 描述 | 预估时间 | 优先级 |
|------|------|----------|--------|
| T3.1 | 实现 OutputTester 基础类 | 2h | P0 |
| T3.2 | 实现 RuleChecker 规则检查器 | 3h | P0 |
| T3.3 | 集成 LLM Judge 评估 | 3h | P0 |
| T3.4 | 实现格式验证测试 | 2h | P1 |
| T3.5 | 实现多维度评分 (完整性、准确性、相关性) | 3h | P1 |

### Phase 4: 测试执行与集成（1 周）

| 任务 | 描述 | 预估时间 | 优先级 |
|------|------|----------|--------|
| T4.1 | 实现测试套件管理 (unit, integration, e2e) | 2h | P0 |
| T4.2 | 集成到 CI/CD 流程 | 3h | P0 |
| T4.3 | 实现测试报告可视化 | 2h | P1 |
| T4.4 | 创建真实任务采样器 | 3h | P2 |

### Phase 5: 持续测试（持续）

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T5.1 | 定期更新测试数据集 | P1 |
| T5.2 | 监控测试指标趋势 | P1 |
| T5.3 | 根据反馈添加边界用例 | P2 |

---

## 五、CLI 命令集成

```python
# src/cli/test/__init__.py

@click.group("test")
def test_group():
    """Manage agent tests"""
    pass

@test_group.command("run")
@click.option("--suite", "-s", default="unit", help="Test suite to run")
@click.option("--dataset", "-d", default="default", help="Test dataset")
def run_tests(suite, dataset):
    """Run agent tests"""
    from src.evaluation.test_framework import AgentTestRunner
    # ...

@test_group.command("list")
def list_tests():
    """List available tests"""
    # ...

@test_group.command("report")
@click.option("--format", "-f", type=click.Choice(["text", "json", "html"]))
def show_report(format):
    """Show test report"""
    # ...
```

---

## 六、验收标准

| 指标 | 目标值 | 测量方式 |
|------|--------|----------|
| 意图解析准确率 | ≥ 85% | 对比预期意图 |
| 任务分类准确率 | ≥ 90% | 多分类测试集 |
| 任务完成率 | ≥ 80% | 规则检查 |
| 输出质量评分 | ≥ 0.8 | LLM Judge |
| 测试覆盖率 | ≥ 80% | 主要任务类型 |
| 平均测试时间 | < 30s | 计时 |

---

## 七、文件清单

```
src/evaluation/test_framework/
├── __init__.py
├── models.py          # 数据模型
├── runner.py         # 测试运行器
├── input_tester.py  # 输入理解测试
├── output_tester.py # 输出质量测试
├── rule_checker.py  # 规则检查器
├── data_manager.py  # 测试数据管理
└── reporter.py      # 报告生成器

tests/
├── test_framework/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_runner.py
│   ├── test_input_tester.py
│   ├── test_output_tester.py
│   └── fixtures/
│       └── test_dataset.py

tests/fixtures/
└── test_dataset.py   # 预设测试数据
```
