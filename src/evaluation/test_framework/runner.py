"""
Test Runner - 测试运行器

负责执行测试、管理测试流程、生成报告
参考 OpenAI Evals 的运行器设计
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .models import (
    EvaluationDimension,
    TestCase,
    TestReport,
    TestResult,
    TestSuite,
    TestType,
)


@dataclass
class RunnerConfig:
    """运行器配置"""

    parallel: bool = True
    max_workers: int = 5
    timeout_seconds: int = 300
    continue_on_error: bool = True
    verbose: bool = False


class AgentTestRunner:
    """测试运行器

    负责：
    1. 加载测试用例
    2. 执行测试
    3. 生成报告
    """

    def __init__(
        self,
        agent,  # YoungAgent instance
        config: Optional[RunnerConfig] = None
    ):
        self.agent = agent
        self.config = config or RunnerConfig()
        self.results: list[TestResult] = []

    async def run_suite(
        self,
        suite: TestSuite,
        input_tester=None,
        output_tester=None,
    ) -> TestReport:
        """运行测试套件

        Args:
            suite: 测试套件
            input_tester: 输入理解测试器
            output_tester: 输出质量测试器

        Returns:
            TestReport: 测试报告
        """
        start_time = datetime.now()
        self.results = []

        print(f"[TestRunner] Running suite: {suite.name} ({suite.size} cases)")

        # 并行或串行执行
        if self.config.parallel and len(suite.test_cases) > 1:
            results = await self._run_parallel(suite, input_tester, output_tester)
        else:
            results = await self._run_sequential(suite, input_tester, output_tester)

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # 生成报告
        report = self._generate_report(results, duration_ms, suite.name)

        print(f"[TestRunner] Suite complete: {report.passed}/{report.total_tests} passed")

        return report

    async def run_case(
        self,
        test_case: TestCase,
        input_tester=None,
        output_tester=None,
    ) -> TestResult:
        """运行单个测试用例

        Args:
            test_case: 测试用例
            input_tester: 输入理解测试器
            output_tester: 输出质量测试器

        Returns:
            TestResult: 测试结果
        """
        # 根据测试用例类型选择测试器
        if self._is_input_test(test_case):
            if input_tester:
                return await input_tester.run(test_case)
        else:
            if output_tester:
                return await output_tester.run(test_case)

        # 默认：跳过测试
        return TestResult(
            test_id=test_case.id,
            test_type=TestType.OUTPUT_QUALITY,
            dimension=EvaluationDimension.COMPLETENESS,
            passed=False,
            score=0.0,
            details={"error": "No tester provided"},
            task_description=test_case.task_description,
        )

    async def _run_sequential(
        self,
        suite: TestSuite,
        input_tester,
        output_tester,
    ) -> list[TestResult]:
        """串行执行"""
        results = []
        for i, case in enumerate(suite.test_cases):
            if self.config.verbose:
                print(f"[TestRunner] {i+1}/{suite.size}: {case.id}")

            try:
                result = await self._run_with_timeout(
                    self.run_case(case, input_tester, output_tester),
                    suite.timeout_seconds
                )
                results.append(result)
            except Exception as e:
                if self.config.continue_on_error:
                    results.append(self._create_error_result(case, str(e)))
                else:
                    raise

        return results

    async def _run_parallel(
        self,
        suite: TestSuite,
        input_tester,
        output_tester,
    ) -> list[TestResult]:
        """并行执行"""
        tasks = []
        for case in suite.test_cases:
            task = self._run_with_timeout(
                self.run_case(case, input_tester, output_tester),
                suite.timeout_seconds
            )
            tasks.append(task)

        # 使用 asyncio.gather 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                if self.config.continue_on_error:
                    processed_results.append(
                        self._create_error_result(suite.test_cases[i], str(result))
                    )
                else:
                    raise result
            else:
                processed_results.append(result)

        return processed_results

    async def _run_with_timeout(self, coro, timeout_seconds: int):
        """带超时的执行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Test execution timed out after {timeout_seconds}s")

    def _is_input_test(self, test_case: TestCase) -> bool:
        """判断是否为输入理解测试"""
        # 输入理解测试主要关注意图解析、任务分类
        return test_case.task_type in [
            # 需要理解意图的任务类型
        ]

    def _create_error_result(self, case: TestCase, error: str) -> TestResult:
        """创建错误结果"""
        return TestResult(
            test_id=case.id,
            test_type=TestType.OUTPUT_QUALITY,
            dimension=EvaluationDimension.COMPLETENESS,
            passed=False,
            score=0.0,
            details={"error": error},
            task_description=case.task_description,
        )

    def _generate_report(
        self,
        results: list[TestResult],
        duration_ms: int,
        dataset_name: str,
    ) -> TestReport:
        """生成测试报告"""

        # 统计
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        skipped = 0  # 暂不支持

        # 按类型分组
        input_results = [r for r in results if r.test_type == TestType.INPUT_UNDERSTANDING]
        output_results = [r for r in results if r.test_type == TestType.OUTPUT_QUALITY]

        # 计算维度分数
        input_score = self._calculate_dimension_score(input_results)
        output_score = self._calculate_dimension_score(output_results)

        return TestReport(
            timestamp=datetime.now(),
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=duration_ms,
            input_understanding_score=input_score,
            output_quality_score=output_score,
            input_results=input_results,
            output_results=output_results,
            results=results,
            dataset_name=dataset_name,
            agent_name=getattr(self.agent, "config", None).__dict__.get("name", "unknown") if hasattr(self.agent, "config") else "unknown",
        )

    def _calculate_dimension_score(self, results: list[TestResult]) -> float:
        """计算维度平均分数"""
        if not results:
            return 0.0

        total = sum(r.score for r in results)
        return total / len(results)
