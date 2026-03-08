"""
Agent Weights - 任务类型评分权重配置

根据任务类型动态调整评分权重。
"""

from typing import Dict

# ========== 动态评分权重配置 ==========
# 根据任务类型动态调整评分权重
TASK_TYPE_WEIGHTS: Dict[str, Dict[str, float]] = {
    # 代码生成任务：正确性最重要
    "coding": {
        "base_score": 0.6,  # LLMJudge 评分权重
        "completion_rate": 0.3,  # 任务完成度权重
        "efficiency": 0.1,  # 效率权重
    },
    # 通用任务：平衡权重
    "general": {
        "base_score": 0.5,
        "completion_rate": 0.3,
        "efficiency": 0.2,
    },
    # 对话任务：清晰度和安全性重要
    "conversation": {
        "base_score": 0.5,
        "completion_rate": 0.2,
        "efficiency": 0.3,
    },
    # 研究任务：准确性和完整性重要
    "research": {
        "base_score": 0.6,
        "completion_rate": 0.3,
        "efficiency": 0.1,
    },
    # 数据处理任务：正确性优先
    "data_processing": {
        "base_score": 0.7,
        "completion_rate": 0.2,
        "efficiency": 0.1,
    },
    # 网络爬取任务：正确性和效率并重
    "web_scraping": {
        "base_score": 0.5,
        "completion_rate": 0.3,
        "efficiency": 0.2,
    },
    # 搜索任务：准确性和相关性
    "search": {
        "base_score": 0.6,
        "completion_rate": 0.2,
        "efficiency": 0.2,
    },
    # 文件操作任务：正确性优先
    "file_operation": {
        "base_score": 0.6,
        "completion_rate": 0.3,
        "efficiency": 0.1,
    },
}

# 默认权重（未知任务类型使用）
DEFAULT_WEIGHTS: Dict[str, float] = {
    "base_score": 0.5,
    "completion_rate": 0.3,
    "efficiency": 0.2,
}


def calculate_weighted_score(
    task_type: str,
    base_score: float,
    completion_rate: float,
    efficiency: float = 1.0,
) -> float:
    """根据任务类型计算加权评分

    Args:
        task_type: 任务类型 (coding/general/conversation/research/...)
        base_score: LLMJudge 基础评分 (0-1)
        completion_rate: 任务完成度 (0-1)
        efficiency: 执行效率 (0-1)

    Returns:
        加权后的评分 (0-1)
    """
    weights = TASK_TYPE_WEIGHTS.get(task_type, DEFAULT_WEIGHTS)

    score = (
        base_score * weights["base_score"]
        + completion_rate * weights["completion_rate"]
        + efficiency * weights["efficiency"]
    )

    # 确保评分在 0-1 范围内
    return max(0.0, min(1.0, score))
