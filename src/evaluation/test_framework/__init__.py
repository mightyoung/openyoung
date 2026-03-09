"""
Test Framework - Agent 测试框架

基于 OpenAI Evals 和 Google HELM 设计理念

核心模块：
- models: 数据模型
- runner: 测试运行器
- input_tester: 输入理解测试
- output_tester: 输出质量测试
- data_manager: 测试数据管理
- reporter: 报告生成
"""

from .data_manager import TestDataManager
from .input_tester import InputTester, IntentParser
from .models import (
    Difficulty,
    EvaluationDimension,
    TaskType,
    TestCase,
    TestReport,
    TestResult,
    TestSuite,
    TestType,
)
from .output_tester import OutputTester, RuleChecker
from .reporter import MetricsCalculator, TestReporter
from .runner import AgentTestRunner, RunnerConfig

__all__ = [
    # Models
    "TaskType",
    "Difficulty",
    "TestType",
    "EvaluationDimension",
    "TestCase",
    "TestResult",
    "TestReport",
    "TestSuite",
    # Runner
    "AgentTestRunner",
    "RunnerConfig",
    # Testers
    "InputTester",
    "IntentParser",
    "OutputTester",
    "RuleChecker",
    # Data
    "TestDataManager",
    # Reporter
    "TestReporter",
    "MetricsCalculator",
]
