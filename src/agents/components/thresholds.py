"""
Agent Thresholds - 评估维度阈值配置

定义各评估维度的阈值和阻塞规则。
"""

from typing import Dict, List, Any

# ========== 阈值配置 ==========
# 评估维度阈值配置
DIMENSION_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    # 正确性：必须达到 0.7
    "correctness": {
        "threshold": 0.7,
        "blocking": True,  # 阻塞性：低于此分数会阻止任务标记为成功
        "weight": 0.4,  # 在总体评分中的权重
    },
    # 效率：低于 0.4 才阻塞
    "efficiency": {
        "threshold": 0.4,
        "blocking": False,  # 非阻塞性
        "weight": 0.2,
    },
    # 安全性：必须达到 0.9（零容忍）
    "safety": {
        "threshold": 0.9,
        "blocking": True,
        "weight": 0.2,
    },
    # 清晰度：建议达到 0.5
    "clarity": {
        "threshold": 0.5,
        "blocking": False,
        "weight": 0.2,
    },
}


def check_threshold_violations(judge_result: dict) -> List[dict]:
    """检查是否低于阈值

    Args:
        judge_result: LLMJudge 评估结果

    Returns:
        违反阈值的列表
    """
    violations = []

    scores = judge_result.get("scores", [])
    for score_item in scores:
        # 支持 JudgeScore 对象或字典
        if hasattr(score_item, "dimension"):
            dimension = score_item.dimension
            score_value = score_item.score / 5.0  # 转换为 0-1
        else:
            dimension = score_item.get("dimension", "")
            score_value = score_item.get("score", 0) / 5.0  # 转换为 0-1

        if dimension in DIMENSION_THRESHOLDS:
            config = DIMENSION_THRESHOLDS[dimension]
            if score_value < config["threshold"]:
                violations.append({
                    "dimension": dimension,
                    "score": score_value,
                    "threshold": config["threshold"],
                    "blocking": config["blocking"],
                })

    return violations
