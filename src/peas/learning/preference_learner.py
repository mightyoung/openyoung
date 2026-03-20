"""
PreferenceLearner - 用户偏好学习系统

M3.3: 学习用户验证偏好，自动调整验证阈值
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from ..types.document import Priority
from ..types.verification import VerificationStatus

logger = logging.getLogger(__name__)


@dataclass
class FeedbackRecord:
    """反馈记录"""

    feature_id: str
    accepted: bool
    timestamp: datetime
    context: dict = field(default_factory=dict)


@dataclass
class ThresholdConfig:
    """阈值配置"""

    priority: Priority
    default_threshold: float
    min_threshold: float = 0.0
    max_threshold: float = 100.0


class PreferenceLearner:
    """学习用户验证偏好，自动调整验证阈值

    功能:
    - 记录用户对验证结果的反馈
    - 基于滑动窗口计算用户接受率
    - 动态调整 MUST/SHOULD/COULD 阈值
    - 学习用户偏好的输出格式
    """

    # 默认阈值配置
    DEFAULT_THRESHOLDS = {
        Priority.MUST: ThresholdConfig(Priority.MUST, 0.0),  # must项不允许失败
        Priority.SHOULD: ThresholdConfig(Priority.SHOULD, 30.0),
        Priority.COULD: ThresholdConfig(Priority.COULD, 50.0),
    }

    def __init__(
        self,
        window_size: int = 20,
        learning_rate: float = 0.1,
        min_feedback_count: int = 5,
    ):
        """初始化偏好学习器

        Args:
            window_size: 滑动窗口大小（用于计算接受率）
            learning_rate: 学习率（用于阈值调整）
            min_feedback_count: 最小反馈数量（用于触发学习）
        """
        self.window_size = window_size
        self.learning_rate = learning_rate
        self.min_feedback_count = min_feedback_count

        # 反馈记录: feature_id -> deque of FeedbackRecord
        self._feedback_history: dict[str, deque[FeedbackRecord]] = {}

        # 动态阈值: Priority -> current threshold
        self._thresholds: dict[Priority, float] = {
            Priority.MUST: 0.0,
            Priority.SHOULD: 30.0,
            Priority.COULD: 50.0,
        }

        # 风格偏好记录
        self._style_preferences: dict[str, int] = {}
        self._accepted_patterns: list[dict] = []
        self._rejected_patterns: list[dict] = []

        # 默认阈值配置（用于重置）
        self._default_thresholds = self._thresholds.copy()

    async def record_feedback(
        self,
        feature_id: str,
        accepted: bool,
        context: Optional[dict] = None,
    ) -> None:
        """记录用户对某个feature验证结果的反馈

        Args:
            feature_id: 功能点ID
            accepted: 是否接受（True=接受/通过，False=拒绝/失败）
            context: 额外的上下文信息（如优先级、验证状态等）
        """
        # 初始化该feature的反馈队列
        if feature_id not in self._feedback_history:
            self._feedback_history[feature_id] = deque(maxlen=self.window_size)

        # 创建反馈记录
        record = FeedbackRecord(
            feature_id=feature_id,
            accepted=accepted,
            timestamp=datetime.now(),
            context=context or {},
        )

        # 添加到队列（自动移除最旧的）
        self._feedback_history[feature_id].append(record)

        # 如果有优先级上下文，同时记录到对应优先级的统计中
        priority = context.get("priority") if context else None
        if priority and isinstance(priority, Priority):
            await self._record_priority_feedback(priority, accepted)

        logger.debug(
            f"Recorded feedback for {feature_id}: accepted={accepted}, "
            f"total feedback: {len(self._feedback_history[feature_id])}"
        )

    async def _record_priority_feedback(
        self,
        priority: Priority,
        accepted: bool,
    ) -> None:
        """记录优先级维度的反馈

        Args:
            priority: 优先级
            accepted: 是否接受
        """
        # 创建虚拟的feature_id用于优先级统计
        priority_key = f"_priority_{priority.value}"

        if priority_key not in self._feedback_history:
            self._feedback_history[priority_key] = deque(maxlen=self.window_size)

        record = FeedbackRecord(
            feature_id=priority_key,
            accepted=accepted,
            timestamp=datetime.now(),
            context={"priority": priority.value},
        )

        self._feedback_history[priority_key].append(record)

    async def get_adjusted_threshold(self, feature_id: str) -> float:
        """根据用户偏好返回调整后的阈值

        Args:
            feature_id: 功能点ID

        Returns:
            float: 调整后的阈值（0-100表示失败容忍百分比）
        """
        # 获取该feature对应的优先级
        priority = await self._get_feature_priority(feature_id)

        # 获取基础阈值
        base_threshold = self._thresholds.get(priority, 30.0)

        # 如果反馈不足，返回基础阈值
        if feature_id not in self._feedback_history:
            return base_threshold

        feedback_queue = self._feedback_history[feature_id]
        if len(feedback_queue) < self.min_feedback_count:
            return base_threshold

        # 计算用户接受率
        accepted_count = sum(1 for r in feedback_queue if r.accepted)
        total_count = len(feedback_queue)
        acceptance_rate = accepted_count / total_count if total_count > 0 else 1.0

        # 计算错误率
        error_rate = 1.0 - acceptance_rate

        # 应用阈值调整公式: new_threshold = old_threshold * (1 - learning_rate * error_rate)
        adjusted = base_threshold * (1 - self.learning_rate * error_rate)

        # 限制在合理范围内
        config = self.DEFAULT_THRESHOLDS.get(priority)
        if config:
            adjusted = max(config.min_threshold, min(config.max_threshold, adjusted))

        logger.debug(
            f"Adjusted threshold for {feature_id}: {base_threshold:.1f} -> {adjusted:.1f} "
            f"(acceptance_rate={acceptance_rate:.2%}, error_rate={error_rate:.2%})"
        )

        return adjusted

    async def _get_feature_priority(self, feature_id: str) -> Priority:
        """获取功能点的优先级

        Args:
            feature_id: 功能点ID

        Returns:
            Priority: 优先级（默认SHOULD）
        """
        if feature_id not in self._feedback_history:
            return Priority.SHOULD

        # 查找最近的带有优先级上下文的反馈
        feedback_queue = self._feedback_history[feature_id]
        for record in reversed(list(feedback_queue)):
            if record.context.get("priority"):
                try:
                    return Priority(record.context["priority"])
                except ValueError:
                    continue

        return Priority.SHOULD

    async def learn_style_preference(self, result: str) -> dict:
        """学习用户的输出风格偏好

        Args:
            result: 验证结果内容

        Returns:
            dict: 学习到的风格偏好
        """
        # 提取基本的格式特征
        style_features = {
            "has_bullet_points": "•" in result or "-" in result,
            "has_numbered_list": any(c.isdigit() for c in result[:100]),
            "has_headers": "#" in result or result.isupper(),
            "has_code_blocks": "```" in result or "`" in result,
            "length_category": self._categorize_length(result),
            "has_emoji": any(ord(c) > 127000 for c in result),
        }

        # 更新统计
        for feature, value in style_features.items():
            if value:
                self._style_preferences[feature] = self._style_preferences.get(feature, 0) + 1

        # 返回学习到的偏好
        learned_preferences = {
            feature: count / max(sum(self._style_preferences.values()), 1)
            for feature, count in self._style_preferences.items()
        }

        return {
            "features": style_features,
            "preferences": learned_preferences,
            "preferred_format": self._get_preferred_format(learned_preferences),
        }

    def _categorize_length(self, text: str) -> str:
        """分类文本长度

        Args:
            text: 文本内容

        Returns:
            str: 长度类别
        """
        length = len(text)
        if length < 100:
            return "short"
        elif length < 500:
            return "medium"
        elif length < 2000:
            return "long"
        return "very_long"

    def _get_preferred_format(self, preferences: dict) -> str:
        """获取用户偏好的格式

        Args:
            preferences: 偏好统计

        Returns:
            str: 偏好格式描述
        """
        if not preferences:
            return "balanced"

        # 找出最突出的偏好
        max_preference = max(preferences.values()) if preferences else 0

        if preferences.get("has_bullet_points", 0) > 0.5:
            return "bullet_points"
        elif preferences.get("has_numbered_list", 0) > 0.5:
            return "numbered_list"
        elif preferences.get("has_code_blocks", 0) > 0.5:
            return "code_focused"
        elif preferences.get("length_category.short", 0) > 0.5:
            return "concise"
        elif preferences.get("length_category.long", 0) > 0.5:
            return "detailed"

        return "balanced"

    def record_result_pattern(
        self,
        result: str,
        accepted: bool,
        verification_status: Optional[VerificationStatus] = None,
    ) -> None:
        """记录验证结果模式

        Args:
            result: 验证结果内容
            accepted: 用户是否接受
            verification_status: 验证状态
        """
        pattern = {
            "content": result[:500],  # 截断以节省空间
            "length": len(result),
            "status": verification_status.value if verification_status else None,
            "accepted": accepted,
            "timestamp": datetime.now().isoformat(),
        }

        if accepted:
            self._accepted_patterns.append(pattern)
            # 保持最多100个模式
            if len(self._accepted_patterns) > 100:
                self._accepted_patterns = self._accepted_patterns[-100:]
        else:
            self._rejected_patterns.append(pattern)
            if len(self._rejected_patterns) > 100:
                self._rejected_patterns = self._rejected_patterns[-100:]

    def get_acceptance_stats(self, feature_id: Optional[str] = None) -> dict:
        """获取接受率统计

        Args:
            feature_id: 功能点ID（可选）

        Returns:
            dict: 接受率统计
        """
        if feature_id:
            return self._get_feature_stats(feature_id)

        # 返回全局统计
        total_accepted = len(self._accepted_patterns)
        total_rejected = len(self._rejected_patterns)
        total = total_accepted + total_rejected

        return {
            "total_feedback": total,
            "accepted": total_accepted,
            "rejected": total_rejected,
            "acceptance_rate": total_accepted / total if total > 0 else 0.0,
        }

    def _get_feature_stats(self, feature_id: str) -> dict:
        """获取特定功能的统计

        Args:
            feature_id: 功能点ID

        Returns:
            dict: 功能点统计
        """
        if feature_id not in self._feedback_history:
            return {"total": 0, "accepted": 0, "rejected": 0, "rate": 0.0}

        queue = self._feedback_history[feature_id]
        accepted = sum(1 for r in queue if r.accepted)
        total = len(queue)

        return {
            "total": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "rate": accepted / total if total > 0 else 0.0,
        }

    def get_current_thresholds(self) -> dict[str, float]:
        """获取当前阈值配置

        Returns:
            dict: 优先级到阈值的映射
        """
        return {priority.value: threshold for priority, threshold in self._thresholds.items()}

    def reset_thresholds(self) -> None:
        """重置阈值到默认值"""
        self._thresholds = self._default_thresholds.copy()
        logger.info("Thresholds reset to defaults")

    def get_learned_patterns(self) -> dict:
        """获取学习到的模式

        Returns:
            dict: 接受和拒绝的模式统计
        """
        return {
            "accepted_count": len(self._accepted_patterns),
            "rejected_count": len(self._rejected_patterns),
            "style_preferences": self._style_preferences,
            "preferred_format": self._get_preferred_format(
                {
                    k: v / max(sum(self._style_preferences.values()), 1)
                    for k, v in self._style_preferences.items()
                }
            ),
        }


def create_preference_learner(
    window_size: int = 20,
    learning_rate: float = 0.1,
) -> PreferenceLearner:
    """创建偏好学习器的便捷函数

    Args:
        window_size: 滑动窗口大小
        learning_rate: 学习率

    Returns:
        PreferenceLearner: 偏好学习器实例
    """
    return PreferenceLearner(
        window_size=window_size,
        learning_rate=learning_rate,
    )
