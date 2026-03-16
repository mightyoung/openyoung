"""
Experience Data Models - 经验数据模型

定义经验收集所需的核心数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class TaskCategory(Enum):
    """任务类别"""

    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"


class ActionType(Enum):
    """动作类型"""

    TOOL_CALL = "tool_call"
    REASONING = "reasoning"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class State:
    """状态（推理过程）"""

    timestamp: datetime
    content: str
    category: str = "reasoning"

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "category": self.category,
        }


@dataclass
class Action:
    """动作（工具调用/响应）"""

    timestamp: datetime
    action_type: ActionType
    name: str  # 工具名或响应类型
    input_data: dict = field(default_factory=dict)
    output_data: Any = None
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "name": self.name,
            "input_data": self.input_data,
            "success": self.success,
        }


@dataclass
class Experience:
    """经验条目"""

    id: str
    task_id: str
    task_category: TaskCategory
    task_description: str

    # 轨迹
    states: list[State] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)

    # 结果
    success: bool = False
    evaluation_score: float = 0.0
    completion_rate: float = 0.0

    # 元数据
    duration_ms: int = 0
    token_count: int = 0
    tool_call_count: int = 0
    error_count: int = 0

    # 奖励信号（多维度）
    rewards: dict = field(default_factory=dict)

    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)

    # 向量嵌入（延迟生成）
    embedding: Optional[list[float]] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_category": self.task_category.value,
            "task_description": self.task_description,
            "success": self.success,
            "evaluation_score": self.evaluation_score,
            "completion_rate": self.completion_rate,
            "duration_ms": self.duration_ms,
            "token_count": self.token_count,
            "tool_call_count": self.tool_call_count,
            "error_count": self.error_count,
            "rewards": self.rewards,
            "created_at": self.created_at.isoformat(),
        }


class RewardSignals:
    """奖励信号计算器"""

    # 奖励权重
    TASK_COMPLETION_POSITIVE = 1.0
    TASK_COMPLETION_NEGATIVE = -0.5
    EVALUATION_WEIGHT = 0.3
    EFFICIENCY_WEIGHT = 0.2
    ERROR_PENALTY = -0.1
    TOKEN_EFFICIENCY_WEIGHT = 0.1
    MAX_REASONABLE_STEPS = 20
    MAX_REASONABLE_TOKENS = 1000

    @classmethod
    def compute(cls, experience: Experience) -> dict:
        """计算多维度奖励"""
        rewards = {}

        # 1. 任务完成奖励 (主奖励)
        if experience.success:
            rewards["task_completion"] = cls.TASK_COMPLETION_POSITIVE
        else:
            rewards["task_completion"] = cls.TASK_COMPLETION_NEGATIVE

        # 2. 评估分数奖励 (0-1 -> 0-0.3)
        rewards["evaluation"] = experience.evaluation_score * cls.EVALUATION_WEIGHT

        # 3. 效率奖励 (步骤数惩罚)
        step_efficiency = max(0, 1 - experience.tool_call_count / cls.MAX_REASONABLE_STEPS)
        rewards["efficiency"] = step_efficiency * cls.EFFICIENCY_WEIGHT

        # 4. 错误惩罚
        error_penalty = cls.ERROR_PENALTY * experience.error_count
        rewards["error"] = error_penalty

        # 5. Token 效率
        if experience.token_count > 0:
            token_efficiency = max(0, 1 - experience.token_count / cls.MAX_REASONABLE_TOKENS)
            rewards["token_efficiency"] = token_efficiency * cls.TOKEN_EFFICIENCY_WEIGHT

        # 总奖励
        rewards["total"] = sum(rewards.values())

        return rewards

    @classmethod
    def compute_simple(cls, success: bool, score: float = 0.0) -> float:
        """简单奖励计算（仅任务完成+评估分数）"""
        reward = cls.TASK_COMPLETION_POSITIVE if success else cls.TASK_COMPLETION_NEGATIVE
        reward += score * cls.EVALUATION_WEIGHT
        return reward
