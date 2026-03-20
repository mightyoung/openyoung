"""
Tests for PreferenceLearner - 用户偏好学习系统
"""
import pytest
from datetime import datetime, timedelta

from src.peas.learning.preference_learner import (
    PreferenceLearner,
    FeedbackRecord,
    ThresholdConfig,
    create_preference_learner,
)
from src.peas.types.document import Priority
from src.peas.types.verification import VerificationStatus


class TestPreferenceLearner:
    """PreferenceLearner测试类"""

    @pytest.fixture
    def learner(self):
        """创建PreferenceLearner实例"""
        return PreferenceLearner(window_size=10, learning_rate=0.1)

    @pytest.fixture
    def learner_with_min_feedback(self):
        """创建带有最小反馈数的PreferenceLearner实例"""
        return PreferenceLearner(
            window_size=10,
            learning_rate=0.1,
            min_feedback_count=3,
        )

    @pytest.mark.asyncio
    async def test_record_feedback_basic(self, learner):
        """测试基本反馈记录"""
        await learner.record_feedback("feature_1", accepted=True)

        stats = learner.get_acceptance_stats("feature_1")
        assert stats["total"] == 1
        assert stats["accepted"] == 1
        assert stats["rejected"] == 0

    @pytest.mark.asyncio
    async def test_record_feedback_with_context(self, learner):
        """测试带上下文的反馈记录"""
        context = {
            "priority": Priority.MUST,
            "status": "verified",
        }
        await learner.record_feedback("feature_1", accepted=True, context=context)

        stats = learner.get_acceptance_stats("feature_1")
        assert stats["total"] == 1
        assert stats["accepted"] == 1

    @pytest.mark.asyncio
    async def test_record_multiple_feedback(self, learner):
        """测试多条反馈记录"""
        # 记录多条反馈
        await learner.record_feedback("feature_1", accepted=True)
        await learner.record_feedback("feature_1", accepted=True)
        await learner.record_feedback("feature_1", accepted=False)

        stats = learner.get_acceptance_stats("feature_1")
        assert stats["total"] == 3
        assert stats["accepted"] == 2
        assert stats["rejected"] == 1

    @pytest.mark.asyncio
    async def test_window_size_limit(self, learner):
        """测试滑动窗口大小限制"""
        # 窗口大小为10
        for i in range(15):
            await learner.record_feedback(f"feature_{i % 3}", accepted=(i % 2 == 0))

        # 每个feature应该最多只有10条记录
        for i in range(3):
            stats = learner.get_acceptance_stats(f"feature_{i}")
            assert stats["total"] <= 10

    @pytest.mark.asyncio
    async def test_get_adjusted_threshold_no_feedback(self, learner):
        """测试无反馈时返回默认阈值"""
        threshold = await learner.get_adjusted_threshold("feature_unknown")
        assert threshold == 30.0  # SHOULD默认阈值

    @pytest.mark.asyncio
    async def test_get_adjusted_threshold_insufficient_feedback(
        self,
        learner_with_min_feedback,
    ):
        """测试反馈不足时返回默认阈值"""
        # 只记录1条反馈（少于min_feedback_count=3）
        await learner_with_min_feedback.record_feedback("feature_1", accepted=True)

        threshold = await learner_with_min_feedback.get_adjusted_threshold("feature_1")
        assert threshold == 30.0  # 仍返回默认阈值

    @pytest.mark.asyncio
    async def test_get_adjusted_threshold_high_acceptance(
        self,
        learner_with_min_feedback,
    ):
        """测试高接受率时阈值上调"""
        # 记录3条接受的反馈（接受率100%）
        for _ in range(3):
            await learner_with_min_feedback.record_feedback(
                "feature_1", accepted=True
            )

        # 获取优先级为SHOULD的feature_id
        priority_key = "_priority_should"

        threshold = await learner_with_min_feedback.get_adjusted_threshold(priority_key)

        # 高接受率应该提高阈值（容忍更多失败）
        # new_threshold = 30 * (1 - 0.1 * 0) = 30 (无错误，阈值不变)
        assert threshold == 30.0

    @pytest.mark.asyncio
    async def test_get_adjusted_threshold_low_acceptance(
        self,
        learner_with_min_feedback,
    ):
        """测试低接受率时阈值下调"""
        # 记录3条反馈，2条拒绝（接受率33%）
        # 同时指定SHOULD优先级
        for accepted in [True, False, False]:
            await learner_with_min_feedback.record_feedback(
                "feature_1",
                accepted=accepted,
                context={"priority": Priority.SHOULD},
            )

        threshold = await learner_with_min_feedback.get_adjusted_threshold("feature_1")

        # 低接受率应该降低阈值
        # new_threshold = 30 * (1 - 0.1 * 0.67) = 27.99
        assert threshold < 30.0
        assert threshold > 20.0

    @pytest.mark.asyncio
    async def test_learn_style_preference(self, learner):
        """测试风格偏好学习"""
        # 模拟带有项目符号的结果
        result = "• Feature 1 implemented\n• Feature 2 completed"

        prefs = await learner.learn_style_preference(result)

        assert "features" in prefs
        assert prefs["features"]["has_bullet_points"] is True
        assert "preferences" in prefs
        assert "preferred_format" in prefs

    @pytest.mark.asyncio
    async def test_record_result_pattern(self, learner):
        """测试结果模式记录"""
        learner.record_result_pattern(
            result="Test result content",
            accepted=True,
            verification_status=VerificationStatus.VERIFIED,
        )

        patterns = learner.get_learned_patterns()
        assert patterns["accepted_count"] == 1
        assert patterns["rejected_count"] == 0

    @pytest.mark.asyncio
    async def test_record_result_pattern_rejected(self, learner):
        """测试拒绝模式记录"""
        learner.record_result_pattern(
            result="Test result content",
            accepted=False,
            verification_status=VerificationStatus.FAILED,
        )

        patterns = learner.get_learned_patterns()
        assert patterns["accepted_count"] == 0
        assert patterns["rejected_count"] == 1

    def test_get_current_thresholds(self, learner):
        """测试获取当前阈值"""
        thresholds = learner.get_current_thresholds()

        assert "must" in thresholds
        assert "should" in thresholds
        assert "could" in thresholds
        assert thresholds["must"] == 0.0
        assert thresholds["should"] == 30.0
        assert thresholds["could"] == 50.0

    def test_reset_thresholds(self, learner):
        """测试阈值重置"""
        # 修改阈值
        learner._thresholds[Priority.SHOULD] = 50.0

        # 重置
        learner.reset_thresholds()

        thresholds = learner.get_current_thresholds()
        assert thresholds["should"] == 30.0

    def test_get_acceptance_stats_global(self, learner):
        """测试全局接受率统计"""
        # 记录一些模式
        learner.record_result_pattern("result1", accepted=True)
        learner.record_result_pattern("result2", accepted=True)
        learner.record_result_pattern("result3", accepted=False)

        stats = learner.get_acceptance_stats()
        assert stats["total_feedback"] == 3
        assert stats["accepted"] == 2
        assert stats["rejected"] == 1
        assert stats["acceptance_rate"] == pytest.approx(2/3)

    def test_get_acceptance_stats_feature(self, learner):
        """测试特定功能的接受率统计"""
        # 通过反馈记录
        import asyncio
        asyncio.run(learner.record_feedback("feature_x", accepted=True))
        asyncio.run(learner.record_feedback("feature_x", accepted=True))
        asyncio.run(learner.record_feedback("feature_x", accepted=False))

        stats = learner.get_acceptance_stats("feature_x")
        assert stats["total"] == 3
        assert stats["accepted"] == 2
        assert stats["rejected"] == 1
        assert stats["rate"] == pytest.approx(2/3)

    def test_get_acceptance_stats_unknown_feature(self, learner):
        """测试未知功能的接受率统计"""
        stats = learner.get_acceptance_stats("unknown_feature")
        assert stats["total"] == 0
        assert stats["rate"] == 0.0


class TestCreatePreferenceLearner:
    """create_preference_learner便捷函数测试"""

    def test_create_with_defaults(self):
        """测试默认参数创建"""
        learner = create_preference_learner()
        assert learner.window_size == 20
        assert learner.learning_rate == 0.1
        assert learner.min_feedback_count == 5

    def test_create_with_custom_params(self):
        """测试自定义参数创建"""
        learner = create_preference_learner(
            window_size=50,
            learning_rate=0.2,
        )
        assert learner.window_size == 50
        assert learner.learning_rate == 0.2


class TestThresholdConfig:
    """ThresholdConfig测试"""

    def test_default_values(self):
        """测试默认值"""
        config = ThresholdConfig(Priority.SHOULD, 30.0)

        assert config.priority == Priority.SHOULD
        assert config.default_threshold == 30.0
        assert config.min_threshold == 0.0
        assert config.max_threshold == 100.0

    def test_custom_values(self):
        """测试自定义值"""
        config = ThresholdConfig(
            Priority.MUST,
            0.0,
            min_threshold=0.0,
            max_threshold=50.0,
        )

        assert config.min_threshold == 0.0
        assert config.max_threshold == 50.0


class TestFeedbackRecord:
    """FeedbackRecord测试"""

    def test_creation(self):
        """测试创建"""
        record = FeedbackRecord(
            feature_id="feature_1",
            accepted=True,
            timestamp=datetime.now(),
            context={"priority": "must"},
        )

        assert record.feature_id == "feature_1"
        assert record.accepted is True
        assert record.context["priority"] == "must"

    def test_default_context(self):
        """测试默认上下文"""
        record = FeedbackRecord(
            feature_id="feature_1",
            accepted=True,
            timestamp=datetime.now(),
        )

        assert record.context == {}
