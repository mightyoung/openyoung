#!/usr/bin/env python3
"""
Performance Regression Check for PEAS

This script runs performance benchmarks and checks for regressions.
It can be integrated into CI/CD pipelines.
"""
import time
import sys
from dataclasses import dataclass
from typing import Callable, Optional

from src.peas.understanding import MarkdownParser
from src.peas.contract import ContractBuilder
from src.peas.verification import DriftDetector
from src.peas.types import Priority, FeaturePoint, ParsedDocument
from src.peas.types.contract import ExecutionContract, ContractRequirement
from src.peas.types.verification import VerificationStatus, FeatureStatus


@dataclass
class BenchmarkResult:
    """单个基准测试结果"""
    name: str
    actual_ms: float
    threshold_ms: float

    @property
    def passed(self) -> bool:
        return self.actual_ms <= self.threshold_ms

    @property
    def margin_pct(self) -> float:
        if self.actual_ms <= self.threshold_ms:
            return ((self.threshold_ms - self.actual_ms) / self.threshold_ms) * 100
        return 0

    @property
    def regression_pct(self) -> float:
        if self.actual_ms > self.threshold_ms:
            return ((self.actual_ms - self.threshold_ms) / self.threshold_ms) * 100
        return 0


class PerformanceRegressionChecker:
    """性能回归检测器"""

    # 基准阈值定义
    THRESHOLDS = {
        "parser_10kb": 500,
        "parser_100kb": 2000,
        "detector_100": 100,
        "detector_1000": 500,
        "builder_50": 200,
        "builder_100": 400,
        "parse_build": 1000,
    }

    def __init__(self):
        self.parser = MarkdownParser()
        self.builder = ContractBuilder()
        self.detector = DriftDetector()
        self.results: list[BenchmarkResult] = []

    def create_test_doc(self, num_features: int) -> str:
        """创建测试文档"""
        lines = ["# Test Document\n\n"]
        for i in range(num_features // 10):
            lines.append(f"## Section {i}\n")
            for j in range(10):
                lines.append(f"- Feature: Feature {i}-{j}\n")
                lines.append(f"  - Description for feature {i}-{j}\n")
        return "".join(lines)

    def create_test_features(self, num: int) -> list[FeaturePoint]:
        """创建测试功能点"""
        features = []
        priorities = [Priority.MUST, Priority.SHOULD, Priority.COULD]
        for i in range(num):
            fp = FeaturePoint(
                id=f"FP-{i:03d}",
                title=f"Feature {i}",
                description=f"Description {i}",
                priority=priorities[i % 3],
                acceptance_criteria=[f"AC {i}.1"]
            )
            features.append(fp)
        return features

    def run_benchmark(
        self,
        name: str,
        fn: Callable[[], float],
        threshold: float
    ) -> BenchmarkResult:
        """运行单个基准测试

        Args:
            name: 测试名称
            fn: 要测试的函数，返回耗时(ms)
            threshold: 阈值(ms)

        Returns:
            BenchmarkResult: 测试结果
        """
        # 预热
        fn()

        # 实际测试 - 运行多次取平均
        runs = 5
        times = []
        for _ in range(runs):
            elapsed = fn()
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        result = BenchmarkResult(name, avg_time, threshold)
        self.results.append(result)

        return result

    def benchmark_parser_10kb(self) -> BenchmarkResult:
        """MarkdownParser 10KB 文档测试"""
        doc = self.create_test_doc(500)  # ~10KB

        def run():
            start = time.perf_counter()
            self.parser.parse(doc)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("parser_10kb", run, self.THRESHOLDS["parser_10kb"])

    def benchmark_parser_100kb(self) -> BenchmarkResult:
        """MarkdownParser 100KB 文档测试"""
        doc = self.create_test_doc(5000)  # ~100KB

        def run():
            start = time.perf_counter()
            self.parser.parse(doc)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("parser_100kb", run, self.THRESHOLDS["parser_100kb"])

    def benchmark_detector_100(self) -> BenchmarkResult:
        """DriftDetector 100 features 测试"""
        # 创建合约
        requirements = []
        priorities = [Priority.MUST, Priority.SHOULD, Priority.COULD]
        for i in range(100):
            req = ContractRequirement(
                req_id=f"FP-{i:03d}",
                description=f"Feature {i}",
                priority=priorities[i % 3],
                verification_method="llm_judge",
                verification_prompt=f"Verify {i}"
            )
            requirements.append(req)
        contract = ExecutionContract.create(
            requirements=requirements,
            version="1.0",
            metadata={}
        )

        statuses = []
        for i in range(100):
            status = FeatureStatus(
                req_id=f"FP-{i:03d}",
                status=VerificationStatus.VERIFIED,
                evidence=["test"]
            )
            statuses.append(status)

        def run():
            start = time.perf_counter()
            self.detector.detect(statuses, contract)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("detector_100", run, self.THRESHOLDS["detector_100"])

    def benchmark_detector_1000(self) -> BenchmarkResult:
        """DriftDetector 1000 features 测试"""
        requirements = []
        for i in range(1000):
            req = ContractRequirement(
                req_id=f"FP-{i:04d}",
                description=f"Feature {i}",
                priority=Priority.SHOULD,
                verification_method="llm_judge",
                verification_prompt=f"Verify {i}"
            )
            requirements.append(req)
        contract = ExecutionContract.create(
            requirements=requirements,
            version="1.0",
            metadata={}
        )

        statuses = []
        for i in range(1000):
            status = FeatureStatus(
                req_id=f"FP-{i:04d}",
                status=VerificationStatus.VERIFIED,
                evidence=["test"]
            )
            statuses.append(status)

        def run():
            start = time.perf_counter()
            self.detector.detect(statuses, contract)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("detector_1000", run, self.THRESHOLDS["detector_1000"])

    def benchmark_builder_50(self) -> BenchmarkResult:
        """ContractBuilder 50 requirements 测试"""
        features = self.create_test_features(50)
        doc = ParsedDocument(
            title="Test",
            sections=["S1", "S2"],
            feature_points=features,
            raw_content="test"
        )

        def run():
            start = time.perf_counter()
            self.builder.build(doc)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("builder_50", run, self.THRESHOLDS["builder_50"])

    def benchmark_builder_100(self) -> BenchmarkResult:
        """ContractBuilder 100 requirements 测试"""
        features = self.create_test_features(100)
        doc = ParsedDocument(
            title="Test",
            sections=[f"S{i}" for i in range(10)],
            feature_points=features,
            raw_content="test"
        )

        def run():
            start = time.perf_counter()
            self.builder.build(doc)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("builder_100", run, self.THRESHOLDS["builder_100"])

    def benchmark_parse_build(self) -> BenchmarkResult:
        """Parse + Build 集成测试"""
        doc_content = self.create_test_doc(100)  # 100 features

        def run():
            start = time.perf_counter()
            doc = self.parser.parse(doc_content)
            self.builder.build(doc)
            return (time.perf_counter() - start) * 1000

        return self.run_benchmark("parse_build", run, self.THRESHOLDS["parse_build"])

    def run_all(self) -> list[BenchmarkResult]:
        """运行所有基准测试"""
        print("Running PEAS Performance Benchmarks...")
        print("=" * 50)

        self.benchmark_parser_10kb()
        self.benchmark_parser_100kb()
        self.benchmark_detector_100()
        self.benchmark_detector_1000()
        self.benchmark_builder_50()
        self.benchmark_builder_100()
        self.benchmark_parse_build()

        return self.results

    def print_report(self) -> bool:
        """打印基准测试报告

        Returns:
            bool: 所有测试是否通过
        """
        print("\n" + "=" * 50)
        print("PERFORMANCE BENCHMARK REPORT")
        print("=" * 50)

        all_passed = True
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            if not result.passed:
                all_passed = False

            print(f"\n{result.name}")
            print(f"  Actual:   {result.actual_ms:>8.2f} ms")
            print(f"  Threshold:{result.threshold_ms:>8.2f} ms")
            print(f"  Status:   {status}", end="")
            if result.passed:
                print(f" (margin: {result.margin_pct:.1f}%)")
            else:
                print(f" (REGRESSION: +{result.regression_pct:.1f}%)")

        print("\n" + "=" * 50)
        if all_passed:
            print("RESULT: ALL TESTS PASSED")
        else:
            print("RESULT: REGRESSION DETECTED!")
        print("=" * 50)

        return all_passed


def main():
    """主函数"""
    checker = PerformanceRegressionChecker()
    results = checker.run_all()
    passed = checker.print_report()

    # 返回退出码
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
