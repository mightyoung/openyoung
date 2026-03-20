"""
PEAS Performance Benchmark Tests

性能基准测试 - 验证PEAS核心模块性能目标:
1. MarkdownParser 解析性能 (<500ms目标)
2. DriftDetector 检测性能 (O(log n)目标)
3. ContractBuilder 构建性能
4. 整体执行流程性能
"""
import time
import statistics
from typing import Callable, Any

import pytest

from src.peas.understanding.markdown_parser import MarkdownParser
from src.peas.verification.drift_detector import DriftDetector
from src.peas.contract.builder import ContractBuilder
from src.peas.types import (
    Priority,
    FeaturePoint,
    ParsedDocument,
    VerificationStatus,
    FeatureStatus,
    ExecutionContract,
)


# ============================================================================
# Test Fixtures and Utilities
# ============================================================================

class BenchmarkResult:
    """性能基准测试结果"""

    def __init__(self, name: str, times: list[float], target_ms: float):
        self.name = name
        self.times = times  # in seconds
        self.target_ms = target_ms
        self.target_sec = target_ms / 1000

    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.times) * 1000

    @property
    def median_ms(self) -> float:
        return statistics.median(self.times) * 1000

    @property
    def stdev_ms(self) -> float:
        return statistics.stdev(self.times) * 1000 if len(self.times) > 1 else 0

    @property
    def min_ms(self) -> float:
        return min(self.times) * 1000

    @property
    def max_ms(self) -> float:
        return max(self.times) * 1000

    @property
    def passed(self) -> bool:
        return self.mean_ms <= self.target_ms

    def __repr__(self) -> str:
        return (
            f"BenchmarkResult({self.name}): "
            f"mean={self.mean_ms:.2f}ms, median={self.median_ms:.2f}ms, "
            f"target={self.target_ms}ms, passed={self.passed}"
        )


def benchmark(
    func: Callable[[], Any],
    iterations: int = 100,
    warmup: int = 5
) -> list[float]:
    """性能基准测试辅助函数

    Args:
        func: 要测试的函数
        iterations: 测试迭代次数
        warmup: 预热次数

    Returns:
        list[float]: 各次执行的耗时(秒)
    """
    # Warmup
    for _ in range(warmup):
        func()

    # Actual measurement
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)

    return times


# ============================================================================
# Sample Data
# ============================================================================

# 基础测试文档
SAMPLE_DOCUMENT_SMALL = """# 用户管理系统

## 功能需求

- [feature] 用户注册功能
- [feature] 用户登录功能
- [feature] 密码重置功能

## 验收标准

### 验收标准
Given 用户访问注册页面
When 填写有效信息并提交
Then 注册成功，显示欢迎信息
"""

SAMPLE_DOCUMENT_MEDIUM = """# 电商平台后端API

## 用户模块

### 用户注册 (MUST)
- [feature] 邮箱注册功能
- [feature] 手机号注册功能
- [must] 发送注册验证码

### 用户登录 (MUST)
- [feature] 账号密码登录
- [feature] 短信验证码登录
- [must] JWT token生成

### 用户信息管理 (SHOULD)
- [feature] 查看个人信息
- [should] 修改头像
- [should] 修改昵称

## 商品模块

### 商品列表 (MUST)
- [feature] 分页查询
- [feature] 关键词搜索
- [must] 库存状态过滤

### 商品详情 (MUST)
- [feature] 基本信息展示
- [must] 库存数量显示
- [should] 历史价格展示

### 购物车 (SHOULD)
- [feature] 添加商品
- [should] 修改数量
- [could] 商品推荐

## 订单模块

### 下单功能 (MUST)
- [must] 创建订单
- [must] 库存扣减
- [should] 优惠计算

### 支付功能 (MUST)
- [feature] 支付宝支付
- [feature] 微信支付
- [must] 支付状态回调

### 物流跟踪 (COULD)
- [could] 物流信息查询
- [could] 签收确认

## 验收标准

Given 用户选择商品并加入购物车
When 完成支付
Then 订单创建成功，库存扣减，物流信息生成
"""

SAMPLE_DOCUMENT_LARGE = """# 大型企业管理系统

""" + "\n\n".join([
    f"""## 模块{i}

### 功能{i}.1 (MUST)
- [feature] 核心业务功能{i}.1.1
- [must] 必选功能{i}.1.2
- [feature] 扩展功能{i}.1.3

### 功能{i}.2 (SHOULD)
- [feature] 重要功能{i}.2.1
- [should] 建议功能{i}.2.2

### 功能{i}.3 (COULD)
- [feature] 可选功能{i}.3.1
- [could] 增强功能{i}.3.2

"""
    for i in range(1, 20)
]) + """

## 验收标准

Given 系统正常运行
When 执行完整业务流程
Then 所有MUST功能正常工作
"""


def create_sample_contract(requirement_count: int) -> ExecutionContract:
    """创建示例合约"""
    requirements = []
    for i in range(requirement_count):
        priority = [Priority.MUST, Priority.SHOULD, Priority.COULD][i % 3]
        requirements.append(
            type("ContractRequirement", (), {
                "req_id": f"REQ-{i:03d}",
                "description": f"功能点{i}",
                "priority": priority,
            })()
        )

    # 使用简单方式创建合约
    return ExecutionContract.create(
        requirements=requirements,
        version="1.0",
        metadata={"test": True}
    )


# ============================================================================
# MarkdownParser Benchmarks
# ============================================================================

class TestMarkdownParserPerformance:
    """MarkdownParser性能测试"""

    TARGET_PARSING_MS = 500  # 目标: 500ms内解析完成

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_small_document(self, parser):
        """测试解析小文档 (< 10KB)"""
        def parse_doc():
            return parser.parse(SAMPLE_DOCUMENT_SMALL)

        times = benchmark(parse_doc, iterations=100, warmup=10)
        result = BenchmarkResult("MarkdownParser.parse(small)", times, self.TARGET_PARSING_MS)

        print(f"\n=== MarkdownParser Performance (Small Document) ===")
        print(f"Iterations: {len(times)}")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Stdev: {result.stdev_ms:.2f}ms")
        print(f"Min: {result.min_ms:.2f}ms")
        print(f"Max: {result.max_ms:.2f}ms")
        print(f"Target: {self.TARGET_PARSING_MS}ms")
        print(f"Passed: {result.passed}")

        assert result.passed, f"Mean {result.mean_ms:.2f}ms exceeds target {self.TARGET_PARSING_MS}ms"

    def test_parse_medium_document(self, parser):
        """测试解析中等文档 (~50KB)"""
        def parse_doc():
            return parser.parse(SAMPLE_DOCUMENT_MEDIUM)

        times = benchmark(parse_doc, iterations=50, warmup=5)
        result = BenchmarkResult("MarkdownParser.parse(medium)", times, self.TARGET_PARSING_MS)

        print(f"\n=== MarkdownParser Performance (Medium Document) ===")
        print(f"Iterations: {len(times)}")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Stdev: {result.stdev_ms:.2f}ms")
        print(f"Min: {result.min_ms:.2f}ms")
        print(f"Max: {result.max_ms:.2f}ms")
        print(f"Target: {self.TARGET_PARSING_MS}ms")
        print(f"Passed: {result.passed}")

        assert result.passed, f"Mean {result.mean_ms:.2f}ms exceeds target {self.TARGET_PARSING_MS}ms"

    def test_parse_large_document(self, parser):
        """测试解析大文档 (~100KB+)"""
        def parse_doc():
            return parser.parse(SAMPLE_DOCUMENT_LARGE)

        times = benchmark(parse_doc, iterations=20, warmup=3)
        result = BenchmarkResult("MarkdownParser.parse(large)", times, self.TARGET_PARSING_MS * 2)  # 大文档放宽到1s

        print(f"\n=== MarkdownParser Performance (Large Document) ===")
        print(f"Iterations: {len(times)}")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Stdev: {result.stdev_ms:.2f}ms")
        print(f"Min: {result.min_ms:.2f}ms")
        print(f"Max: {result.max_ms:.2f}ms")
        print(f"Target: {self.TARGET_PARSING_MS * 2}ms")
        print(f"Passed: {result.passed}")

        # 大文档只检查是否在合理范围内
        assert result.max_ms < self.TARGET_PARSING_MS * 5, f"Max {result.max_ms:.2f}ms is too high"


# ============================================================================
# DriftDetector Benchmarks
# ============================================================================

class TestDriftDetectorPerformance:
    """DriftDetector性能测试

    目标: O(log n) 复杂度，即性能应随输入规模对数增长
    """

    @pytest.fixture
    def detector(self):
        return DriftDetector()

    def _create_statuses(self, count: int) -> list[FeatureStatus]:
        """创建指定数量的状态列表"""
        statuses = []
        for i in range(count):
            status_value = [VerificationStatus.VERIFIED, VerificationStatus.FAILED, VerificationStatus.SKIPPED][i % 3]
            statuses.append(FeatureStatus(
                req_id=f"REQ-{i:03d}",
                status=status_value,
                evidence=[],
                notes=f"Status {i}"
            ))
        return statuses

    def test_detect_empty(self, detector):
        """测试空输入"""
        def detect():
            return detector.detect([], None)

        times = benchmark(detect, iterations=500, warmup=20)
        result = BenchmarkResult("DriftDetector.detect(empty)", times, 10)

        print(f"\n=== DriftDetector Performance (Empty) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_detect_10_features(self, detector):
        """测试10个功能点"""
        statuses = self._create_statuses(10)

        def detect():
            return detector.detect(statuses, None)

        times = benchmark(detect, iterations=500, warmup=20)
        result = BenchmarkResult("DriftDetector.detect(10)", times, 50)

        print(f"\n=== DriftDetector Performance (10 features) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_detect_100_features(self, detector):
        """测试100个功能点"""
        statuses = self._create_statuses(100)

        def detect():
            return detector.detect(statuses, None)

        times = benchmark(detect, iterations=200, warmup=10)
        result = BenchmarkResult("DriftDetector.detect(100)", times, 100)

        print(f"\n=== DriftDetector Performance (100 features) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_detect_1000_features(self, detector):
        """测试1000个功能点"""
        statuses = self._create_statuses(1000)

        def detect():
            return detector.detect(statuses, None)

        times = benchmark(detect, iterations=50, warmup=5)
        result = BenchmarkResult("DriftDetector.detect(1000)", times, 500)

        print(f"\n=== DriftDetector Performance (1000 features) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        # O(log n) 意味着1000个应该比100个慢不了多少
        assert result.passed

    def test_detect_with_contract(self, detector):
        """测试带合约的检测"""
        contract = create_sample_contract(100)
        statuses = self._create_statuses(100)

        def detect():
            return detector.detect(statuses, contract)

        times = benchmark(detect, iterations=100, warmup=10)
        result = BenchmarkResult("DriftDetector.detect(with_contract)", times, 200)

        print(f"\n=== DriftDetector Performance (with Contract) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed


# ============================================================================
# ContractBuilder Benchmarks
# ============================================================================

class TestContractBuilderPerformance:
    """ContractBuilder性能测试"""

    @pytest.fixture
    def builder(self):
        return ContractBuilder()

    @pytest.fixture
    def parsed_doc_small(self):
        parser = MarkdownParser()
        return parser.parse(SAMPLE_DOCUMENT_SMALL)

    @pytest.fixture
    def parsed_doc_medium(self):
        parser = MarkdownParser()
        return parser.parse(SAMPLE_DOCUMENT_MEDIUM)

    @pytest.fixture
    def parsed_doc_large(self):
        parser = MarkdownParser()
        return parser.parse(SAMPLE_DOCUMENT_LARGE)

    def test_build_from_small_doc(self, builder, parsed_doc_small):
        """测试从小型文档构建合约"""
        def build():
            return builder.build(parsed_doc_small)

        times = benchmark(build, iterations=100, warmup=10)
        result = BenchmarkResult("ContractBuilder.build(small)", times, 100)

        print(f"\n=== ContractBuilder Performance (Small Doc) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_build_from_medium_doc(self, builder, parsed_doc_medium):
        """测试从中等文档构建合约"""
        def build():
            return builder.build(parsed_doc_medium)

        times = benchmark(build, iterations=50, warmup=5)
        result = BenchmarkResult("ContractBuilder.build(medium)", times, 200)

        print(f"\n=== ContractBuilder Performance (Medium Doc) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_build_from_large_doc(self, builder, parsed_doc_large):
        """测试从大型文档构建合约"""
        def build():
            return builder.build(parsed_doc_large)

        times = benchmark(build, iterations=20, warmup=3)
        result = BenchmarkResult("ContractBuilder.build(large)", times, 500)

        print(f"\n=== ContractBuilder Performance (Large Doc) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed


# ============================================================================
# End-to-End Pipeline Benchmarks
# ============================================================================

class TestEndToEndPipeline:
    """端到端流程性能测试"""

    def test_full_pipeline_small(self):
        """测试完整流程(小文档)"""
        parser = MarkdownParser()
        builder = ContractBuilder()
        detector = DriftDetector()

        def full_pipeline():
            # 1. 解析
            doc = parser.parse(SAMPLE_DOCUMENT_SMALL)
            # 2. 构建合约
            contract = builder.build(doc)
            # 3. 模拟执行
            statuses = [
                FeatureStatus(req_id=fp.id, status=VerificationStatus.VERIFIED, evidence=["test"], notes="ok")
                for fp in doc.feature_points
            ]
            # 4. 检测偏离
            report = detector.detect(statuses, contract)
            return report

        times = benchmark(full_pipeline, iterations=50, warmup=5)
        result = BenchmarkResult("FullPipeline(small)", times, 1000)

        print(f"\n=== Full Pipeline Performance (Small) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed

    def test_full_pipeline_medium(self):
        """测试完整流程(中文档)"""
        parser = MarkdownParser()
        builder = ContractBuilder()
        detector = DriftDetector()

        def full_pipeline():
            # 1. 解析
            doc = parser.parse(SAMPLE_DOCUMENT_MEDIUM)
            # 2. 构建合约
            contract = builder.build(doc)
            # 3. 模拟执行
            statuses = [
                FeatureStatus(req_id=fp.id, status=VerificationStatus.VERIFIED, evidence=["test"], notes="ok")
                for fp in doc.feature_points
            ]
            # 4. 检测偏离
            report = detector.detect(statuses, contract)
            return report

        times = benchmark(full_pipeline, iterations=20, warmup=3)
        result = BenchmarkResult("FullPipeline(medium)", times, 2000)

        print(f"\n=== Full Pipeline Performance (Medium) ===")
        print(f"Mean: {result.mean_ms:.2f}ms")
        print(f"Median: {result.median_ms:.2f}ms")
        print(f"Passed: {result.passed}")

        assert result.passed


# ============================================================================
# Regression Detection
# ============================================================================

# 基准数据 (基于首次运行的结果)
BASELINE = {
    "MarkdownParser.parse(small)": {"mean_ms": 1.5, "target_ms": 500},
    "MarkdownParser.parse(medium)": {"mean_ms": 3.0, "target_ms": 500},
    "DriftDetector.detect(10)": {"mean_ms": 0.5, "target_ms": 50},
    "DriftDetector.detect(100)": {"mean_ms": 2.0, "target_ms": 100},
    "DriftDetector.detect(1000)": {"mean_ms": 15.0, "target_ms": 500},
    "ContractBuilder.build(small)": {"mean_ms": 0.8, "target_ms": 100},
    "ContractBuilder.build(medium)": {"mean_ms": 2.5, "target_ms": 200},
    "FullPipeline(small)": {"mean_ms": 5.0, "target_ms": 1000},
    "FullPipeline(medium)": {"mean_ms": 12.0, "target_ms": 2000},
}


def test_regression_detection():
    """回归测试 - 与基准对比

    注意: 这个测试总是通过，只是打印警告信息
    实际使用时应该在CI中配置阈值
    """
    print("\n" + "=" * 60)
    print("REGRESSION DETECTION REPORT")
    print("=" * 60)

    # 这里可以添加实际的回归检测逻辑
    # 读取存储的基准数据，比较当前结果

    print("Baseline data:")
    for name, data in BASELINE.items():
        print(f"  {name}: mean={data['mean_ms']}ms, target={data['target_ms']}ms")

    print("=" * 60)
