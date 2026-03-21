"""
Reward Calculator - 奖励计算器

多维度奖励信号计算。
"""

from dataclasses import dataclass

from .models import Experience


@dataclass
class RewardResult:
    """奖励计算结果"""

    task_completion: float  # 任务完成奖励
    evaluation: float  # 评估分数奖励
    efficiency: float  # 效率奖励
    error_penalty: float  # 错误惩罚
    token_efficiency: float  # Token 效率奖励
    total: float  # 总奖励


class RewardCalculator:
    """奖励计算器"""

    # 奖励权重配置
    TASK_COMPLETION_POSITIVE = 1.0
    TASK_COMPLETION_NEGATIVE = -0.5
    EVALUATION_WEIGHT = 0.3
    EFFICIENCY_WEIGHT = 0.2
    ERROR_PENALTY = -0.1
    TOKEN_EFFICIENCY_WEIGHT = 0.1

    # 基准值
    MAX_REASONABLE_STEPS = 20
    MAX_REASONABLE_TOKENS = 1000

    @classmethod
    def compute(cls, experience: Experience) -> RewardResult:
        """计算多维度奖励"""
        # 1. 任务完成奖励 (主奖励)
        task_completion = (
            cls.TASK_COMPLETION_POSITIVE if experience.success else cls.TASK_COMPLETION_NEGATIVE
        )

        # 2. 评估分数奖励 (0-1 -> 0-0.3)
        evaluation = experience.evaluation_score * cls.EVALUATION_WEIGHT

        # 3. 效率奖励 (步骤数惩罚)
        step_efficiency = max(0, 1 - experience.tool_call_count / cls.MAX_REASONABLE_STEPS)
        efficiency = step_efficiency * cls.EFFICIENCY_WEIGHT

        # 4. 错误惩罚
        error_penalty = cls.ERROR_PENALTY * experience.error_count

        # 5. Token 效率
        if experience.token_count > 0:
            token_efficiency = max(0, 1 - experience.token_count / cls.MAX_REASONABLE_TOKENS)
            token_efficiency = token_efficiency * cls.TOKEN_EFFICIENCY_WEIGHT
        else:
            token_efficiency = 0.0

        # 总奖励
        total = task_completion + evaluation + efficiency + error_penalty + token_efficiency

        return RewardResult(
            task_completion=task_completion,
            evaluation=evaluation,
            efficiency=efficiency,
            error_penalty=error_penalty,
            token_efficiency=token_efficiency,
            total=total,
        )

    @classmethod
    def compute_simple(cls, success: bool, score: float = 0.0) -> float:
        """简单奖励计算（仅任务完成+评估分数）"""
        reward = cls.TASK_COMPLETION_POSITIVE if success else cls.TASK_COMPLETION_NEGATIVE
        reward += score * cls.EVALUATION_WEIGHT
        return reward

    @classmethod
    def compute_batch(cls, experiences: list[Experience]) -> list[RewardResult]:
        """批量计算奖励"""
        return [cls.compute(exp) for exp in experiences]

    @classmethod
    def get_weighted_score(cls, reward: RewardResult) -> float:
        """获取加权分数（用于排序）"""
        return reward.total

    @classmethod
    def is_good_experience(cls, reward: RewardResult, threshold: float = 0.5) -> bool:
        """判断经验是否为正向经验"""
        return reward.total >= threshold

    @classmethod
    def analyze_reward_distribution(cls, experiences: list[Experience]) -> dict:
        """分析奖励分布"""
        rewards = cls.compute_batch(experiences)
        totals = [r.total for r in rewards]

        if not totals:
            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "positive_ratio": 0.0,
            }

        import statistics

        positive_count = sum(1 for t in totals if t > 0)

        return {
            "count": len(totals),
            "mean": statistics.mean(totals),
            "std": statistics.stdev(totals) if len(totals) > 1 else 0.0,
            "min": min(totals),
            "max": max(totals),
            "positive_ratio": positive_count / len(totals),
        }
