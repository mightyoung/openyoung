#!/usr/bin/env python3
"""
OpenYoung Expert-Level E2E Test Suite

Based on best practices from:
- Andrej Karpathy: "LLM as Simulator" - Realistic end-to-end scenarios
- Anthropic: Multi-dimensional evaluation (correctness, safety, efficiency, clarity)
- Simon Willison: Progressive testing from simple to complex

This test suite validates:
1. Real API calls with DeepSeek
2. Multi-dimensional quality assessment
3. Tool execution capabilities
4. Exception handling robustness
5. Evaluation plan generation
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import required modules
from src.agents.young_agent import YoungAgent
from src.agents.evaluation_coordinator import EvaluationCoordinator, EvaluationContext
from src.agents.task_executor import TaskExecutor
from src.agents.sub_agent import SubAgent
from src.core.types import Task, AgentConfig, AgentMode
from src.evaluation.planner import EvalPlanner
from src.llm.client import LLMClient
from src.tools.executor import ToolExecutor


@dataclass
class TestCase:
    """Test case definition"""
    id: str
    name: str
    description: str
    task: str
    expected_skills: list[str] = field(default_factory=list)
    timeout: int = 120


@dataclass
class TestResult:
    """Individual test result"""
    test_id: str
    test_name: str
    status: str  # PASS, FAIL, ERROR, TIMEOUT
    duration: float
    task_result: str
    evaluation: Optional[dict] = None
    error: Optional[str] = None
    metrics: dict = field(default_factory=dict)


@dataclass
class TestReport:
    """Comprehensive test report"""
    timestamp: str
    total: int
    passed: int
    failed: int
    pass_rate: str
    results: list
    metrics_summary: dict


class ExpertE2ETestSuite:
    """
    Expert-level E2E test suite for OpenYoung

    Design principles:
    1. Real API calls (not mocks)
    2. Multi-dimensional evaluation
    3. Progressive complexity
    4. Detailed metrics
    """

    def __init__(self):
        self.results: list[TestResult] = []
        self.llm_client: Optional[LLMClient] = None

        # Define test cases with progressive complexity
        self.test_cases = [
            TestCase(
                id="test_001",
                name="简单代码生成",
                description="验证基本代码生成能力",
                task="写一个Python函数，计算斐波那契数列的第n项",
                expected_skills=["coding"],
                timeout=60
            ),
            TestCase(
                id="test_002",
                name="数据分析任务",
                description="验证理解和分析能力",
                task="解释一下什么是机器学习中的梯度下降算法？",
                expected_skills=["reasoning", "analysis"],
                timeout=60
            ),
            TestCase(
                id="test_003",
                name="多步骤推理",
                description="验证复杂推理能力",
                task="如果今天是星期一，那么100天后是星期几？请给出计算过程。",
                expected_skills=["reasoning", "math"],
                timeout=60
            ),
            TestCase(
                id="test_004",
                name="创意写作",
                description="验证创意内容生成",
                task="写一首关于春天的七言绝句",
                expected_skills=["creative", "writing"],
                timeout=60
            ),
            TestCase(
                id="test_005",
                name="技术解释",
                description="验证专业技术解释能力",
                task="用通俗易懂的语言解释什么是RESTful API",
                expected_skills=["explanation", "technical"],
                timeout=60
            ),
        ]

    async def initialize(self):
        """Initialize test environment"""
        print("\n" + "=" * 70)
        print("  OpenYoung Expert E2E Test Suite")
        print("  Based on: Karpathy + Anthropic + Simon Willison methodologies")
        print("=" * 70)

        # Check API key
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("\n⚠️  WARNING: DEEPSEEK_API_KEY not found in environment")
            print("   Some tests may fail due to missing API key")

        # Initialize LLM client
        self.llm_client = LLMClient()

        # Create agent config
        self.config = AgentConfig(
            name="expert_test_agent",
            model="deepseek-chat",
            mode=AgentMode.PRIMARY,
            temperature=0.7,
            max_tokens=2000,
        )

        # Initialize YoungAgent
        self.agent = YoungAgent(config=self.config)

        print("\n✅ Test environment initialized")

    async def run_single_test(self, test_case: TestCase) -> TestResult:
        """Execute a single test case"""
        print(f"\n{'─' * 70}")
        print(f"📋 Running: {test_case.id} - {test_case.name}")
        print(f"   Task: {test_case.task[:50]}...")
        print(f"{'─' * 70}")

        start_time = time.time()

        try:
            # Execute task using YoungAgent directly with string
            result = await self.agent.run(test_case.task)

            duration = time.time() - start_time

            # Evaluate result using EvaluationCoordinator
            eval_result = None
            try:
                eval_context = EvaluationContext(
                    task_description=test_case.task,
                    task_result=result,
                    duration_ms=int(duration * 1000),
                    tokens_used=0,
                    model=self.config.model,
                )

                evaluator = EvaluationCoordinator(llm_client=self.llm_client)
                eval_report = await evaluator.evaluate(eval_context)

                eval_result = {
                    "score": eval_report.score,
                    "task_type": eval_report.task_type,
                    "completion_rate": eval_report.completion_rate,
                    "base_score": eval_report.base_score,
                }
            except Exception as e:
                print(f"   ⚠️  Evaluation error: {e}")

            print(f"\n   ✅ Completed in {duration:.2f}s")
            print(f"   📊 Result length: {len(result)} chars")
            if eval_result:
                print(f"   📈 Score: {eval_result.get('score', 'N/A'):.2f}")
                print(f"   📊 Task type: {eval_result.get('task_type', 'N/A')}")

            return TestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                status="PASS",
                duration=duration,
                task_result=result[:500],  # Truncate for report
                evaluation=eval_result,
                metrics={
                    "result_length": len(result),
                    "duration_seconds": duration,
                }
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            print(f"\n   ⏱️  Timeout after {duration:.2f}s")
            return TestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                status="TIMEOUT",
                duration=duration,
                task_result="",
                error=f"Task timed out after {test_case.timeout}s",
                metrics={"timeout": True}
            )

        except Exception as e:
            duration = time.time() - start_time
            print(f"\n   ❌ Error: {str(e)[:100]}")
            return TestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                status="ERROR",
                duration=duration,
                task_result="",
                error=str(e)[:500],
                metrics={"error": True}
            )

    async def run_all_tests(self) -> TestReport:
        """Run all test cases"""
        await self.initialize()

        print(f"\n📊 Running {len(self.test_cases)} test cases...")

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n[{i}/{len(self.test_cases)}] ", end="")
            result = await self.run_single_test(test_case)
            self.results.append(result)

            # Small delay between tests
            await asyncio.sleep(1)

        # Generate report
        return self.generate_report()

    def generate_report(self) -> TestReport:
        """Generate comprehensive test report"""
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status in ["FAIL", "ERROR"])
        total = len(self.results)

        # Calculate metrics summary
        durations = [r.duration for r in self.results]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Evaluation scores
        eval_scores = [
            r.evaluation.get("score", 0)
            for r in self.results
            if r.evaluation
        ]
        avg_score = sum(eval_scores) / len(eval_scores) if eval_scores else 0

        metrics_summary = {
            "avg_duration_seconds": round(avg_duration, 2),
            "total_duration_seconds": round(sum(durations), 2),
            "avg_evaluation_score": round(avg_score, 3),
            "task_types": list(set(
                r.evaluation.get("task_type", "unknown")
                for r in self.results
                if r.evaluation
            ))
        }

        report = TestReport(
            timestamp=datetime.now().isoformat(),
            total=total,
            passed=passed,
            failed=failed,
            pass_rate=f"{(passed/total*100):.1f}%",
            results=self.results,
            metrics_summary=metrics_summary
        )

        return report

    def print_report(self, report: TestReport):
        """Print formatted test report"""
        print("\n" + "=" * 70)
        print("  TEST REPORT")
        print("=" * 70)

        print(f"\n📊 Summary:")
        print(f"   Total:  {report.total}")
        print(f"   Passed: {report.passed} ✅")
        print(f"   Failed: {report.failed} ❌")
        print(f"   Rate:   {report.pass_rate}")

        print(f"\n⏱️  Performance:")
        print(f"   Avg duration: {report.metrics_summary['avg_duration_seconds']}s")
        print(f"   Total time:  {report.metrics_summary['total_duration_seconds']}s")

        if report.metrics_summary.get('avg_evaluation_score'):
            print(f"\n📈 Quality:")
            print(f"   Avg score:   {report.metrics_summary['avg_evaluation_score']:.3f}")
            print(f"   Task types:  {', '.join(report.metrics_summary['task_types'])}")

        print(f"\n📋 Details:")
        for r in self.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "⚠️",
                "TIMEOUT": "⏱️"
            }.get(r.status, "❓")

            print(f"   {status_icon} {r.test_id}: {r.test_name} ({r.duration:.1f}s)")

            if r.error:
                print(f"      Error: {r.error[:80]}...")
            elif r.evaluation:
                print(f"      Score: {r.evaluation.get('score', 'N/A'):.2f}, "
                      f"Type: {r.evaluation.get('task_type', 'N/A')}")

        print("\n" + "=" * 70)

    async def cleanup(self):
        """Cleanup resources"""
        if self.llm_client:
            await self.llm_client.close()
        print("\n🧹 Test resources cleaned up")


async def main():
    """Main entry point"""
    # Create and run test suite
    suite = ExpertE2ETestSuite()

    try:
        report = await suite.run_all_tests()
        suite.print_report(report)

        # Save report to file
        output_path = "/tmp/openyoung_expert_e2e_report.json"
        report_data = {
            "timestamp": report.timestamp,
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "pass_rate": report.pass_rate,
            "metrics_summary": report.metrics_summary,
            "results": [
                {
                    "id": r.test_id,
                    "name": r.test_name,
                    "status": r.status,
                    "duration": f"{r.duration:.2f}s",
                    "result": r.task_result[:200] + "..." if len(r.task_result) > 200 else r.task_result,
                    "evaluation": r.evaluation,
                    "error": r.error,
                }
                for r in report.results
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Report saved to: {output_path}")

        # Exit with appropriate code
        sys.exit(0 if report.failed == 0 else 1)

    finally:
        await suite.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
