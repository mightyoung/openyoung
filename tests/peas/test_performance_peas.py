"""
PEAS Performance Benchmark Tests

性能基准测试 - 针对 PEAS 核心模块:
1. MarkdownParser 解析性能
2. DriftDetector 检测性能
3. 性能回归检测

目标阈值:
- MarkdownParser: 小型<10ms, 中型<50ms, 大型<200ms
- DriftDetector: 10功能<5ms, 50功能<20ms
"""
import time
import statistics
import pytest

from src.peas.understanding.markdown_parser import MarkdownParser
from src.peas.verification.drift_detector import DriftDetector
from src.peas.types import FeatureStatus, VerificationStatus


# ============================================================================
# Sample Documents
# ============================================================================

def _generate_small_doc() -> str:
    """生成小型文档 (<100行)"""
    return """# 用户管理系统

## 功能需求

### 用户注册
- Feature: 邮箱注册功能
- Feature: 手机号注册功能

### 用户登录
- Feature: 账号密码登录
- Feature: 短信验证码登录

### 用户信息
- Feature: 查看个人信息
- Feature: 修改头像
- Feature: 修改昵称

## 验收标准

Given 用户访问注册页面
When 填写有效信息并提交
Then 注册成功，显示欢迎信息
"""


def _generate_medium_doc() -> str:
    """生成中型文档 (100-500行)"""
    lines = ["# 电商平台后端API\n\n"]

    modules = ["用户模块", "商品模块", "订单模块", "支付模块", "物流模块"]
    for m_idx, module in enumerate(modules):
        lines.append(f"## {module}\n\n")
        for i in range(10):
            priority = "MUST" if i < 3 else "SHOULD" if i < 7 else "COULD"
            lines.append(f"### {module}功能{i+1} ({priority})\n")
            lines.append(f"- Feature: 核心功能{m_idx}-{i}\n")
            lines.append(f"  - 详细描述：这是功能的具体说明\n")
            lines.append(f"  - 验收标准： Given... When... Then...\n")
            lines.append(f"- Feature: 辅助功能{m_idx}-{i}\n")
            lines.append(f"  - 详细描述：辅助功能的说明\n")

    lines.append("\n## 验收标准\n\n")
    for i in range(20):
        lines.append(f"Given 用户执行操作{i}\n")
        lines.append(f"When 满足条件{i}\n")
        lines.append(f"Then 预期结果{i}\n\n")

    return "".join(lines)


def _generate_large_doc() -> str:
    """生成大型文档 (>500行)"""
    lines = ["# 大型企业管理系统\n\n"]

    for module_idx in range(20):
        lines.append(f"## 模块{module_idx + 1}\n\n")

        for func_idx in range(15):
            priority = ["MUST", "SHOULD", "COULD"][func_idx % 3]
            lines.append(f"### 功能{module_idx + 1}.{func_idx + 1} ({priority})\n")

            for feat_idx in range(3):
                lines.append(f"- Feature: 功能点{module_idx}-{func_idx}-{feat_idx}\n")
                lines.append(f"  - 描述：这是功能点的详细描述\n")
                lines.append(f"  - Given 用户访问页面\n")
                lines.append(f"  - When 点击按钮\n")
                lines.append(f"  - Then 显示结果\n")

        lines.append("\n")

    lines.append("## 验收标准\n\n")
    for i in range(50):
        lines.append(f"### 验收场景{i + 1}\n")
        lines.append(f"Given 系统处于正常状态\n")
        lines.append(f"When 用户执行操作\n")
        lines.append(f"Then 预期结果正确\n\n")

    return "".join(lines)


SMALL_DOC = _generate_small_doc()
MEDIUM_DOC = _generate_medium_doc()
LARGE_DOC = _generate_large_doc()


# ============================================================================
# Performance Test Classes
# ============================================================================

@pytest.mark.performance
class TestMarkdownParserPerformance:
    """MarkdownParser 性能测试"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_small_doc(self, parser):
        """解析小型文档 (<100行) 目标: <10ms"""
        start = time.perf_counter()
        result = parser.parse(SMALL_DOC)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n=== MarkdownParser Small Doc ===")
        print(f"Lines: {len(SMALL_DOC.splitlines())}")
        print(f"Time: {elapsed_ms:.2f}ms (target: <10ms)")
        print(f"Features found: {len(result.feature_points)}")

        assert elapsed_ms < 10, f"Small doc parsing took {elapsed_ms:.2f}ms, expected <10ms"

    def test_parse_medium_doc(self, parser):
        """解析中型文档 (100-500行) 目标: <50ms"""
        start = time.perf_counter()
        result = parser.parse(MEDIUM_DOC)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n=== MarkdownParser Medium Doc ===")
        print(f"Lines: {len(MEDIUM_DOC.splitlines())}")
        print(f"Time: {elapsed_ms:.2f}ms (target: <50ms)")
        print(f"Features found: {len(result.feature_points)}")

        assert elapsed_ms < 50, f"Medium doc parsing took {elapsed_ms:.2f}ms, expected <50ms"

    def test_parse_large_doc(self, parser):
        """解析大型文档 (>500行) 目标: <200ms"""
        start = time.perf_counter()
        result = parser.parse(LARGE_DOC)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n=== MarkdownParser Large Doc ===")
        print(f"Lines: {len(LARGE_DOC.splitlines())}")
        print(f"Time: {elapsed_ms:.2f}ms (target: <200ms)")
        print(f"Features found: {len(result.feature_points)}")

        assert elapsed_ms < 200, f"Large doc parsing took {elapsed_ms:.2f}ms, expected <200ms"


@pytest.mark.performance
class TestDriftDetectorPerformance:
    """DriftDetector 性能测试"""

    @pytest.fixture
    def detector(self):
        return DriftDetector()

    def _create_statuses(self, count: int) -> list[FeatureStatus]:
        """创建指定数量的 FeatureStatus 列表"""
        statuses = []
        statuses_to_create = count if count <= 100 else 100  # Cap at 100 for realistic testing
        for i in range(statuses_to_create):
            status_value = [
                VerificationStatus.VERIFIED,
                VerificationStatus.FAILED,
                VerificationStatus.SKIPPED
            ][i % 3]
            statuses.append(FeatureStatus(
                req_id=f"REQ-{i:03d}",
                status=status_value,
                evidence=[f"evidence_{i}"],
                notes=f"Status {i}"
            ))
        return statuses

    def test_detect_with_10_features(self, detector):
        """10个功能点检测 目标: <5ms"""
        statuses = self._create_statuses(10)

        start = time.perf_counter()
        report = detector.detect(statuses)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n=== DriftDetector (10 features) ===")
        print(f"Time: {elapsed_ms:.2f}ms (target: <5ms)")
        print(f"Total: {report.total_count}, Verified: {report.verified_count}, Failed: {report.failed_count}")

        assert elapsed_ms < 5, f"Detect 10 features took {elapsed_ms:.2f}ms, expected <5ms"

    def test_detect_with_50_features(self, detector):
        """50个功能点检测 目标: <20ms"""
        statuses = self._create_statuses(50)

        start = time.perf_counter()
        report = detector.detect(statuses)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"\n=== DriftDetector (50 features) ===")
        print(f"Time: {elapsed_ms:.2f}ms (target: <20ms)")
        print(f"Total: {report.total_count}, Verified: {report.verified_count}, Failed: {report.failed_count}")

        assert elapsed_ms < 20, f"Detect 50 features took {elapsed_ms:.2f}ms, expected <20ms"


@pytest.mark.performance
class TestPerformanceRegression:
    """性能回归测试"""

    # 性能基准数据 (基于首次运行建立)
    BASELINE = {
        "parse_small": {"mean_ms": 1.0, "median_ms": 0.9, "threshold_ms": 10},
        "parse_medium": {"mean_ms": 5.0, "median_ms": 4.5, "threshold_ms": 50},
        "parse_large": {"mean_ms": 20.0, "median_ms": 18.0, "threshold_ms": 200},
        "detect_10": {"mean_ms": 0.3, "median_ms": 0.25, "threshold_ms": 5},
        "detect_50": {"mean_ms": 1.5, "median_ms": 1.2, "threshold_ms": 20},
    }

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    @pytest.fixture
    def detector(self):
        return DriftDetector()

    def _create_statuses(self, count: int) -> list[FeatureStatus]:
        statuses = []
        for i in range(count):
            statuses.append(FeatureStatus(
                req_id=f"REQ-{i:03d}",
                status=VerificationStatus.VERIFIED if i % 2 == 0 else VerificationStatus.FAILED,
                evidence=["test"]
            ))
        return statuses

    def test_parse_time_baseline(self, parser):
        """建立解析时间基准

        运行多次取平均值，建立性能基准
        """
        iterations = 20

        # Small doc baseline
        small_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.parse(SMALL_DOC)
            small_times.append((time.perf_counter() - start) * 1000)

        # Medium doc baseline
        medium_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.parse(MEDIUM_DOC)
            medium_times.append((time.perf_counter() - start) * 1000)

        # Large doc baseline
        large_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            parser.parse(LARGE_DOC)
            large_times.append((time.perf_counter() - start) * 1000)

        current_baseline = {
            "parse_small": {
                "mean_ms": statistics.mean(small_times),
                "median_ms": statistics.median(small_times),
                "threshold_ms": 10
            },
            "parse_medium": {
                "mean_ms": statistics.mean(medium_times),
                "median_ms": statistics.median(medium_times),
                "threshold_ms": 50
            },
            "parse_large": {
                "mean_ms": statistics.mean(large_times),
                "median_ms": statistics.median(large_times),
                "threshold_ms": 200
            },
        }

        print(f"\n=== Parse Time Baseline ===")
        print(f"Small:  mean={current_baseline['parse_small']['mean_ms']:.2f}ms, "
              f"median={current_baseline['parse_small']['median_ms']:.2f}ms")
        print(f"Medium: mean={current_baseline['parse_medium']['mean_ms']:.2f}ms, "
              f"median={current_baseline['parse_medium']['median_ms']:.2f}ms")
        print(f"Large:  mean={current_baseline['parse_large']['mean_ms']:.2f}ms, "
              f"median={current_baseline['parse_large']['median_ms']:.2f}ms")

        # Verify we have reasonable baseline values
        assert current_baseline["parse_small"]["mean_ms"] < 10
        assert current_baseline["parse_medium"]["mean_ms"] < 50
        assert current_baseline["parse_large"]["mean_ms"] < 200

    def test_detect_time_baseline(self, detector):
        """建立检测时间基准"""
        iterations = 20

        # 10 features baseline
        statuses_10 = self._create_statuses(10)
        detect_10_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            detector.detect(statuses_10)
            detect_10_times.append((time.perf_counter() - start) * 1000)

        # 50 features baseline
        statuses_50 = self._create_statuses(50)
        detect_50_times = []
        for _ in range(iterations):
            start = time.perf_counter()
            detector.detect(statuses_50)
            detect_50_times.append((time.perf_counter() - start) * 1000)

        current_baseline = {
            "detect_10": {
                "mean_ms": statistics.mean(detect_10_times),
                "median_ms": statistics.median(detect_10_times),
                "threshold_ms": 5
            },
            "detect_50": {
                "mean_ms": statistics.mean(detect_50_times),
                "median_ms": statistics.median(detect_50_times),
                "threshold_ms": 20
            },
        }

        print(f"\n=== Detect Time Baseline ===")
        print(f"10 features: mean={current_baseline['detect_10']['mean_ms']:.2f}ms, "
              f"median={current_baseline['detect_10']['median_ms']:.2f}ms")
        print(f"50 features: mean={current_baseline['detect_50']['mean_ms']:.2f}ms, "
              f"median={current_baseline['detect_50']['median_ms']:.2f}ms")

        # Verify we have reasonable baseline values
        assert current_baseline["detect_10"]["mean_ms"] < 5
        assert current_baseline["detect_50"]["mean_ms"] < 20

    def test_no_regression(self, parser, detector):
        """检测性能不退步

        将当前性能与基准比较，确保没有明显退步 (>50%)
        """
        regression_threshold = 1.5  # 允许50%的性能波动

        print(f"\n=== Performance Regression Check ===")
        print(f"Baseline vs Current (allow 50% regression tolerance)")
        print("-" * 50)

        # Parse checks
        start = time.perf_counter()
        parser.parse(SMALL_DOC)
        small_ms = (time.perf_counter() - start) * 1000

        baseline = self.BASELINE["parse_small"]["mean_ms"]
        ratio = small_ms / baseline if baseline > 0 else 0
        passed = ratio <= regression_threshold
        print(f"parse_small: baseline={baseline:.2f}ms, current={small_ms:.2f}ms, "
              f"ratio={ratio:.2f}x, passed={passed}")
        assert passed, f"parse_small regression: {ratio:.2f}x slower than baseline"

        # Medium
        start = time.perf_counter()
        parser.parse(MEDIUM_DOC)
        medium_ms = (time.perf_counter() - start) * 1000

        baseline = self.BASELINE["parse_medium"]["mean_ms"]
        ratio = medium_ms / baseline if baseline > 0 else 0
        passed = ratio <= regression_threshold
        print(f"parse_medium: baseline={baseline:.2f}ms, current={medium_ms:.2f}ms, "
              f"ratio={ratio:.2f}x, passed={passed}")
        assert passed, f"parse_medium regression: {ratio:.2f}x slower than baseline"

        # Detect checks
        statuses_10 = self._create_statuses(10)
        start = time.perf_counter()
        detector.detect(statuses_10)
        detect_10_ms = (time.perf_counter() - start) * 1000

        baseline = self.BASELINE["detect_10"]["mean_ms"]
        ratio = detect_10_ms / baseline if baseline > 0 else 0
        passed = ratio <= regression_threshold
        print(f"detect_10: baseline={baseline:.2f}ms, current={detect_10_ms:.2f}ms, "
              f"ratio={ratio:.2f}x, passed={passed}")
        assert passed, f"detect_10 regression: {ratio:.2f}x slower than baseline"

        print("-" * 50)
        print("All regression checks passed!")
