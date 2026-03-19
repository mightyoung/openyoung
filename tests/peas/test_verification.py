"""
Tests for Verification module (FeatureTracker + DriftDetector)
"""
import pytest
from src.peas import (
    MarkdownParser, ContractBuilder, FeatureTracker, DriftDetector,
    Priority, VerificationStatus, DriftLevel
)


class TestFeatureTracker:
    """FeatureTracker测试"""

    @pytest.fixture
    def contract(self):
        parser = MarkdownParser()
        doc = parser.parse("""
# Test PRD

## 功能
- Feature: 用户注册
- 必须发送验证邮件

- Feature: 用户登录
- Should: 密码强度检查
""")
        builder = ContractBuilder()
        return builder.build(doc)

    def test_tracker_initialization(self, contract):
        """测试追踪器初始化"""
        tracker = FeatureTracker(contract)

        assert tracker.contract is contract
        assert tracker.statuses == {}

    def test_verify_sync_returns_list(self, contract):
        """测试同步验证返回列表"""
        tracker = FeatureTracker(contract)
        result = tracker.verify_sync("执行了用户注册功能")

        assert isinstance(result, list)
        assert len(result) == 2

    def test_verify_sync_sets_statuses(self, contract):
        """测试验证设置状态"""
        tracker = FeatureTracker(contract)
        tracker.verify_sync("执行了用户注册功能")

        assert "FP-001" in tracker.statuses
        assert "FP-002" in tracker.statuses

    def test_get_status(self, contract):
        """测试获取指定状态"""
        tracker = FeatureTracker(contract)
        tracker.verify_sync("执行了用户注册功能")

        status = tracker.get_status("FP-001")
        assert status is not None
        assert status.req_id == "FP-001"

    def test_get_status_not_found(self, contract):
        """测试获取不存在状态"""
        tracker = FeatureTracker(contract)
        status = tracker.get_status("FP-999")
        assert status is None

    def test_get_summary(self, contract):
        """测试获取摘要"""
        tracker = FeatureTracker(contract)
        tracker.verify_sync("实现了用户注册")

        summary = tracker.get_summary()
        assert "total" in summary
        assert "verified" in summary
        assert "failed" in summary
        assert summary["total"] == 2

    def test_regex_verification_keyword_match(self, contract):
        """测试正则验证关键词匹配"""
        tracker = FeatureTracker(contract)

        # 直接包含关键词的文本
        result = tracker.verify_sync("用户注册功能已实现，发送了验证邮件")

        # 找到邮箱验证功能点
        email_status = tracker.get_status("FP-001")
        assert email_status.status == VerificationStatus.VERIFIED


class TestDriftDetector:
    """DriftDetector测试"""

    def test_detect_empty_statuses(self):
        """测试空状态检测"""
        detector = DriftDetector()
        report = detector.detect([])

        assert report.drift_score == 0
        assert report.level == DriftLevel.NONE

    def test_detect_all_verified(self):
        """测试全部通过检测"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.VERIFIED, evidence=[]),
        ]

        report = detector.detect(statuses)

        assert report.drift_score == 0
        assert report.level == DriftLevel.NONE
        assert report.verified_count == 2
        assert report.failed_count == 0

    def test_detect_all_failed(self):
        """测试全部失败检测"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.FAILED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.FAILED, evidence=[]),
        ]

        report = detector.detect(statuses)

        assert report.drift_score == 100
        assert report.level == DriftLevel.CRITICAL
        assert report.failed_count == 2

    def test_detect_partial_failure(self):
        """测试部分失败检测"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.FAILED, evidence=[]),
        ]

        report = detector.detect(statuses)

        assert report.drift_score == 50
        assert report.level == DriftLevel.CRITICAL

    def test_detect_with_priority_threshold(self):
        """测试优先级阈值检测"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.FAILED, evidence=[]),
            FeatureStatus(req_id="FP-003", status=VerificationStatus.FAILED, evidence=[]),
        ]

        report = detector.detect(statuses)

        # 2/3 failed = 66.7%
        assert report.drift_score > 60

    def test_recommendations_generation(self):
        """测试建议生成"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.FAILED, evidence=[]),
        ]

        report = detector.detect(statuses)

        assert len(report.recommendations) > 0

    def test_detect_from_tracker(self):
        """测试从tracker检测"""
        parser = MarkdownParser()
        doc = parser.parse("# Test\n- Feature: Test")
        contract = ContractBuilder().build(doc)

        tracker = FeatureTracker(contract)
        tracker.verify_sync("实现了功能")

        detector = DriftDetector()
        report = detector.detect_from_tracker(tracker)

        assert report is not None
        assert report.total_count == 1


class TestDriftLevels:
    """DriftLevel边界测试"""

    def test_level_boundaries(self):
        """测试级别边界"""
        from src.peas.types import FeatureStatus

        detector = DriftDetector()

        # 0% -> NONE
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
        ]
        report = detector.detect(statuses)
        assert report.level == DriftLevel.NONE

        # 5% -> MINOR
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.VERIFIED, evidence=[]),
            FeatureStatus(req_id="FP-002", status=VerificationStatus.FAILED, evidence=[]),
        ]
        # 50% failed... wait that's wrong
        # Let's do 1 out of 20 = 5%
        statuses = [FeatureStatus(req_id=f"FP-{i:03d}", status=VerificationStatus.VERIFIED if i < 19 else VerificationStatus.FAILED, evidence=[]) for i in range(20)]
        report = detector.detect(statuses)
        assert report.level == DriftLevel.MINOR

    def test_must_failure_is_critical(self):
        """测试must级别失败是严重级别"""
        from src.peas.types import FeatureStatus

        parser = MarkdownParser()
        doc = parser.parse("""
# Test
- Feature: 必须的功能
""")
        builder = ContractBuilder()
        contract = builder.build(doc)

        detector = DriftDetector()
        statuses = [
            FeatureStatus(req_id="FP-001", status=VerificationStatus.FAILED, evidence=[]),
        ]

        report = detector.detect(statuses, contract)

        assert report.level == DriftLevel.CRITICAL
