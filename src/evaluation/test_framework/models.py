"""
Test Framework Data Models

定义测试框架的核心数据模型
参考 OpenAI Evals 设计理念
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TaskType(Enum):
    """任务类型 - 覆盖 Agent 主要能力"""

    CODE_GENERATION = "code_generation"  # 代码生成
    CODE_FIX = "code_fix"  # 代码修复
    CODE_REVIEW = "code_review"  # 代码审查
    TEXT_GENERATION = "text_generation"  # 文本生成
    QUESTION_ANSWERING = "question_answering"  # 问答
    DATA_PROCESSING = "data_processing"  # 数据处理
    TASK_EXECUTION = "task_execution"  # 任务执行
    INFORMATION_QUERY = "information_query"  # 信息查询
    WEB_SCRAPING = "web_scraping"  # Web 爬取


class Difficulty(Enum):
    """难度级别"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestType(Enum):
    """测试类型"""

    INPUT_UNDERSTANDING = "input_understanding"  # 输入理解
    OUTPUT_QUALITY = "output_quality"  # 输出质量


class EvaluationDimension(Enum):
    """评估维度"""

    # 输入理解
    INTENT_PARSING = "intent_parsing"  # 意图解析
    TASK_CLASSIFICATION = "task_classification"  # 任务分类
    PARAM_EXTRACTION = "param_extraction"  # 参数提取

    # 输出质量
    COMPLETENESS = "completeness"  # 完整性
    ACCURACY = "accuracy"  # 准确性
    RELEVANCE = "relevance"  # 相关性
    FORMAT = "format"  # 格式正确性


@dataclass
class TestCase:
    """测试用例

    参考 OpenAI Evals 的测试用例设计：
    - 明确的输入/预期输出
    - 支持多种验证方式
    """

    id: str
    task_description: str
    task_type: TaskType
    expected_intent: str

    # 可选字段
    expected_params: dict = field(default_factory=dict)
    expected_output_format: str = "text"
    expected_output_sample: Optional[str] = None
    difficulty: Difficulty = Difficulty.MEDIUM
    keywords: list[str] = field(default_factory=list)

    # 验证规则（用于输出质量测试）
    validation_rules: Optional[dict] = None

    # 元数据
    tags: list[str] = field(default_factory=list)
    source: str = "preset"  # "preset" | "production"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_description": self.task_description,
            "task_type": self.task_type.value,
            "expected_intent": self.expected_intent,
            "difficulty": self.difficulty.value,
        }


@dataclass
class TestResult:
    """测试结果

    记录单个测试的执行结果
    """

    test_id: str
    test_type: TestType
    dimension: EvaluationDimension
    passed: bool
    score: float  # 0-1

    # 详细信息
    details: dict = field(default_factory=dict)

    # 性能指标
    duration_ms: int = 0

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)

    # 关联数据
    task_description: str = ""
    actual_output: str = ""

    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "test_type": self.test_type.value,
            "dimension": self.dimension.value,
            "passed": self.passed,
            "score": self.score,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class TestReport:
    """测试报告

    聚合测试结果，生成可读报告
    参考 Google HELM 的报告格式
    """

    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration_ms: int

    # 维度分数（加权平均）
    input_understanding_score: float = 0.0
    output_quality_score: float = 0.0

    # 按测试类型分组
    input_results: list[TestResult] = field(default_factory=list)
    output_results: list[TestResult] = field(default_factory=list)

    # 所有结果
    results: list[TestResult] = field(default_factory=list)

    # 元数据
    dataset_name: str = "default"
    agent_name: str = "unknown"

    @property
    def pass_rate(self) -> float:
        """通过率"""
        if self.total_tests == 0:
            return 0.0
        return self.passed / self.total_tests

    @property
    def success(self) -> bool:
        """是否成功（通过率 >= 80%）"""
        return self.pass_rate >= 0.8

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "summary": {
                "total": self.total_tests,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "pass_rate": self.pass_rate,
                "success": self.success,
            },
            "scores": {
                "input_understanding": self.input_understanding_score,
                "output_quality": self.output_quality_score,
            },
            "duration_ms": self.duration_ms,
        }


@dataclass
class TestSuite:
    """测试套件

    组合多个相关测试用例
    """

    name: str
    description: str
    test_cases: list[TestCase]

    # 配置
    required_score: float = 0.7  # 套件通过所需最低分数
    parallel: bool = True
    timeout_seconds: int = 300

    @property
    def size(self) -> int:
        return len(self.test_cases)

    def filter_by_type(self, task_type: TaskType) -> "TestSuite":
        """按任务类型筛选"""
        filtered = [tc for tc in self.test_cases if tc.task_type == task_type]
        return TestSuite(
            name=f"{self.name}_{task_type.value}",
            description=self.description,
            test_cases=filtered,
        )

    def filter_by_difficulty(self, difficulty: Difficulty) -> "TestSuite":
        """按难度筛选"""
        filtered = [tc for tc in self.test_cases if tc.difficulty == difficulty]
        return TestSuite(
            name=f"{self.name}_{difficulty.value}",
            description=self.description,
            test_cases=filtered,
        )
