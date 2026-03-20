"""
Performance tests for PEAS core modules

These tests benchmark critical performance paths to prevent regressions.
"""
import time
import pytest
from src.peas.understanding import MarkdownParser
from src.peas.contract import ContractBuilder
from src.peas.verification import DriftDetector
from src.peas.types import Priority, FeaturePoint, FeatureStatus
from src.peas.types.contract import ExecutionContract, ContractRequirement
from src.peas.types.verification import VerificationStatus


class TestMarkdownParserPerformance:
    """MarkdownParser性能测试"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    @pytest.fixture
    def small_doc(self):
        """小文档 ~1KB"""
        return """# Test Document

## Section 1
- Feature: Feature A
- Feature: Feature B

## Section 2
- Feature: Feature C
"""

    @pytest.fixture
    def medium_doc(self):
        """中等文档 ~10KB"""
        lines = ["# Test Document\n\n"]
        for i in range(50):
            lines.append(f"## Section {i}\n")
            for j in range(10):
                lines.append(f"- Feature: Feature {i}-{j}\n")
                lines.append(f"  - Description line for feature {i}-{j}\n")
        return "".join(lines)

    @pytest.fixture
    def large_doc(self):
        """大文档 ~100KB"""
        lines = ["# Large Test Document\n\n"]
        for i in range(500):
            lines.append(f"## Section {i}\n")
            for j in range(20):
                lines.append(f"- Feature: Feature {i}-{j}\n")
                lines.append(f"  - Description line for feature {i}-{j}\n")
                lines.append(f"  - Additional detail {i}-{j}\n")
        return "".join(lines)

    def test_parse_small_doc(self, parser, small_doc):
        """解析小文档性能测试 - 目标: <50ms"""
        start = time.perf_counter()
        result = parser.parse(small_doc)
        elapsed = (time.perf_counter() - start) * 1000

        assert result.total_features == 3
        assert elapsed < 50, f"Small doc parsing took {elapsed:.2f}ms, expected <50ms"

    def test_parse_medium_doc(self, parser, medium_doc):
        """解析中等文档性能测试 - 目标: <500ms解析10KB"""
        # 验证文档大小
        doc_size = len(medium_doc.encode('utf-8'))
        assert doc_size >= 8000, f"Test doc should be ~10KB, got {doc_size} bytes"

        start = time.perf_counter()
        result = parser.parse(medium_doc)
        elapsed = (time.perf_counter() - start) * 1000

        assert result.total_features == 500
        assert elapsed < 500, f"Medium doc parsing took {elapsed:.2f}ms, expected <500ms"

    def test_parse_large_doc(self, parser, large_doc):
        """解析大文档性能测试 - 目标: <2s解析100KB"""
        start = time.perf_counter()
        result = parser.parse(large_doc)
        elapsed = (time.perf_counter() - start) * 1000

        assert result.total_features == 10000
        assert elapsed < 2000, f"Large doc parsing took {elapsed:.2f}ms, expected <2000ms"


class TestDriftDetectorPerformance:
    """DriftDetector性能测试"""

    @pytest.fixture
    def detector(self):
        return DriftDetector()

    @pytest.fixture
    def mock_contract(self):
        """创建包含100个requirements的合约"""
        requirements = []
        priorities = [Priority.MUST, Priority.SHOULD, Priority.COULD]
        for i in range(100):
            req = ContractRequirement(
                req_id=f"FP-{i:03d}",
                description=f"Feature {i}",
                priority=priorities[i % 3],
                verification_method="llm_judge",
                verification_prompt=f"Verify feature {i}"
            )
            requirements.append(req)

        return ExecutionContract.create(
            requirements=requirements,
            version="1.0",
            metadata={"test": "perf"}
        )

    @pytest.fixture
    def status_list_100(self):
        """100个feature statuses"""
        statuses = []
        for i in range(100):
            status = FeatureStatus(
                req_id=f"FP-{i:03d}",
                status=VerificationStatus.VERIFIED if i % 2 == 0 else VerificationStatus.FAILED,
                evidence=[f"evidence_{i}"]
            )
            statuses.append(status)
        return statuses

    @pytest.fixture
    def status_list_10(self):
        """10个feature statuses"""
        statuses = []
        for i in range(10):
            status = FeatureStatus(
                req_id=f"FP-{i:03d}",
                status=VerificationStatus.VERIFIED,
                evidence=["test evidence"]
            )
            statuses.append(status)
        return statuses

    def test_detect_10_features(self, detector, status_list_10):
        """检测10个feature points - 目标: <10ms"""
        start = time.perf_counter()
        report = detector.detect(status_list_10)
        elapsed = (time.perf_counter() - start) * 1000

        assert report.total_count == 10
        assert elapsed < 10, f"Detect 10 features took {elapsed:.2f}ms, expected <10ms"

    def test_detect_100_features(self, detector, status_list_100, mock_contract):
        """检测100个feature points - 目标: <100ms"""
        start = time.perf_counter()
        report = detector.detect(status_list_100, mock_contract)
        elapsed = (time.perf_counter() - start) * 1000

        assert report.total_count == 100
        assert elapsed < 100, f"Detect 100 features took {elapsed:.2f}ms, expected <100ms"

    def test_detect_1000_features(self, detector):
        """检测1000个feature points - 目标: <500ms"""
        statuses = []
        for i in range(1000):
            status = FeatureStatus(
                req_id=f"FP-{i:04d}",
                status=VerificationStatus.VERIFIED,
                evidence=["test evidence"]
            )
            statuses.append(status)

        start = time.perf_counter()
        report = detector.detect(statuses)
        elapsed = (time.perf_counter() - start) * 1000

        assert report.total_count == 1000
        assert elapsed < 500, f"Detect 1000 features took {elapsed:.2f}ms, expected <500ms"


class TestContractBuilderPerformance:
    """ContractBuilder性能测试"""

    @pytest.fixture
    def builder(self):
        return ContractBuilder()

    @pytest.fixture
    def doc_with_10_features(self):
        """包含10个功能点的文档"""
        from src.peas.types import ParsedDocument

        feature_points = []
        for i in range(10):
            fp = FeaturePoint(
                id=f"FP-{i:03d}",
                title=f"Feature {i}",
                description=f"Description for feature {i}",
                priority=Priority.MUST if i % 3 == 0 else Priority.SHOULD,
                acceptance_criteria=[f"AC {i}.1", f"AC {i}.2"]
            )
            feature_points.append(fp)

        return ParsedDocument(
            title="Test Document",
            sections=["Section 1", "Section 2"],
            feature_points=feature_points,
            raw_content="test"
        )

    @pytest.fixture
    def doc_with_50_features(self):
        """包含50个功能点的文档"""
        from src.peas.types import ParsedDocument

        feature_points = []
        priorities = [Priority.MUST, Priority.SHOULD, Priority.COULD]
        for i in range(50):
            fp = FeaturePoint(
                id=f"FP-{i:03d}",
                title=f"Feature {i}",
                description=f"Description for feature {i}",
                priority=priorities[i % 3],
                acceptance_criteria=[f"AC {i}.1", f"AC {i}.2", f"AC {i}.3"]
            )
            feature_points.append(fp)

        return ParsedDocument(
            title="Test Document",
            sections=[f"Section {i}" for i in range(10)],
            feature_points=feature_points,
            raw_content="test"
        )

    @pytest.fixture
    def doc_with_100_features(self):
        """包含100个功能点的文档"""
        from src.peas.types import ParsedDocument

        feature_points = []
        priorities = [Priority.MUST, Priority.SHOULD, Priority.COULD]
        for i in range(100):
            fp = FeaturePoint(
                id=f"FP-{i:03d}",
                title=f"Feature {i}",
                description=f"Description for feature {i}",
                priority=priorities[i % 3],
                acceptance_criteria=[f"AC {i}.1"]
            )
            feature_points.append(fp)

        return ParsedDocument(
            title="Test Document",
            sections=[f"Section {i}" for i in range(20)],
            feature_points=feature_points,
            raw_content="test"
        )

    def test_build_10_requirements(self, builder, doc_with_10_features):
        """构建10个requirements - 目标: <50ms"""
        start = time.perf_counter()
        contract = builder.build(doc_with_10_features)
        elapsed = (time.perf_counter() - start) * 1000

        assert contract.total_requirements == 10
        assert elapsed < 50, f"Build 10 requirements took {elapsed:.2f}ms, expected <50ms"

    def test_build_50_requirements(self, builder, doc_with_50_features):
        """构建50个requirements - 目标: <200ms"""
        start = time.perf_counter()
        contract = builder.build(doc_with_50_features)
        elapsed = (time.perf_counter() - start) * 1000

        assert contract.total_requirements == 50
        assert elapsed < 200, f"Build 50 requirements took {elapsed:.2f}ms, expected <200ms"

    def test_build_100_requirements(self, builder, doc_with_100_features):
        """构建100个requirements - 目标: <400ms"""
        start = time.perf_counter()
        contract = builder.build(doc_with_100_features)
        elapsed = (time.perf_counter() - start) * 1000

        assert contract.total_requirements == 100
        assert elapsed < 400, f"Build 100 requirements took {elapsed:.2f}ms, expected <400ms"


class TestIntegrationPerformance:
    """PEAS集成流程性能测试"""

    @pytest.fixture
    def sample_spec(self):
        """中等规模测试规格"""
        lines = ["# Test System PRD\n\n"]
        lines.append("## 功能需求\n\n")
        for i in range(20):
            lines.append(f"### 功能模块 {i}\n")
            for j in range(5):
                priority = "Must" if j == 0 else "Should"
                lines.append(f"- Feature: 功能 {i}-{j} ({priority})\n")
                lines.append(f"  - 描述: 这是功能 {i}-{j} 的详细描述\n")
        return "".join(lines)

    def test_parse_build_combined(self, sample_spec):
        """Parse + Build组合性能测试 - 目标: <1s"""
        parser = MarkdownParser()
        builder = ContractBuilder()

        # Parse阶段
        start = time.perf_counter()
        doc = parser.parse(sample_spec)
        parse_time = (time.perf_counter() - start) * 1000

        # Build阶段
        start = time.perf_counter()
        contract = builder.build(doc)
        build_time = (time.perf_counter() - start) * 1000

        total_time = parse_time + build_time

        assert doc.total_features == 100
        assert contract.total_requirements == 100

        # 单独验证各阶段性能
        assert parse_time < 500, f"Parse took {parse_time:.2f}ms, expected <500ms"
        assert build_time < 500, f"Build took {build_time:.2f}ms, expected <500ms"

        # 总时间 < 1s
        assert total_time < 1000, f"Total parse+build took {total_time:.2f}ms, expected <1000ms"

    def test_full_pipeline_estimate(self, sample_spec):
        """完整流程(不含执行)性能估算"""
        parser = MarkdownParser()
        builder = ContractBuilder()
        detector = DriftDetector()

        start = time.perf_counter()

        # 1. Parse
        doc = parser.parse(sample_spec)

        # 2. Build
        contract = builder.build(doc)

        # 3. 模拟验证结果
        statuses = []
        for i, req in enumerate(contract.requirements):
            status = FeatureStatus(
                req_id=req.req_id,
                status=VerificationStatus.VERIFIED if i % 2 == 0 else VerificationStatus.FAILED,
                evidence=["test evidence"]
            )
            statuses.append(status)

        # 4. Detect
        report = detector.detect(statuses, contract)

        elapsed = (time.perf_counter() - start) * 1000

        assert report.total_count == 100
        # 完整流程应该 < 2s
        assert elapsed < 2000, f"Full pipeline took {elapsed:.2f}ms, expected <2000ms"


class BenchmarkResults:
    """性能基准结果记录类

    用于记录和比较性能基准测试结果
    """

    @staticmethod
    def record_benchmark(name: str, elapsed_ms: float, threshold_ms: float) -> dict:
        """记录单个基准测试结果"""
        return {
            "name": name,
            "elapsed_ms": elapsed_ms,
            "threshold_ms": threshold_ms,
            "passed": elapsed_ms < threshold_ms,
            "margin_pct": ((threshold_ms - elapsed_ms) / threshold_ms * 100) if elapsed_ms < threshold_ms else 0
        }

    @staticmethod
    def format_report(results: list[dict]) -> str:
        """格式化基准测试报告"""
        lines = ["# PEAS Performance Benchmark Results\n"]
        lines.append("=" * 50 + "\n\n")

        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"## {r['name']}\n")
            lines.append(f"- Elapsed: {r['elapsed_ms']:.2f}ms\n")
            lines.append(f"- Threshold: {r['threshold_ms']}ms\n")
            lines.append(f"- Status: {status}\n")
            if r["passed"]:
                lines.append(f"- Margin: {r['margin_pct']:.1f}% headroom\n")
            lines.append("\n")

        return "".join(lines)
