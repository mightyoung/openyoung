"""
Evaluation Prompts - 评估提示词模板

基于行业最佳实践设计:
- SWE-bench: 代码任务评估
- AgentBench: 多步骤任务评估
- Anthropic: AI Agent 评估框架

包含:
- 评估计划生成提示词
- 复杂度判断提示词
- 评估理由说明
"""

from dataclasses import dataclass, field
from typing import Any

# ==================== 评估维度定义 ====================


class EvalDimension:
    """评估维度枚举"""

    CORRECTNESS = "correctness"  # 正确性
    SAFETY = "safety"  # 安全性
    EFFICIENCY = "efficiency"  # 效率
    ROBUSTNESS = "robustness"  # 鲁棒性
    PLANNING = "planning"  # 规划能力
    COLLABORATION = "collaboration"  # 协作能力


class TaskType:
    """任务类型枚举"""

    CODING = "coding"  # 代码生成/修复
    RESEARCH = "research"  # 信息检索
    DIALOGUE = "dialogue"  # 对话
    TOOL_USE = "tool_use"  # 工具调用
    MIXED = "mixed"  # 混合任务


class TaskComplexity:
    """任务复杂度枚举"""

    SIMPLE = "simple"  # 简单 - 跳过评估
    MEDIUM = "medium"  # 中等 - 基础评估
    HIGH = "high"  # 高 - 完整评估
    SKIP = "skip"  # 跳过 - 无需评估


# ==================== 评估计划生成提示词 ====================

EVALUATION_PLAN_PROMPT = """
# 角色
你是一个专业的 AI Agent 评估专家。你的任务是根据用户任务描述，生成一个结构化的评估计划。

# 背景
你正在为 OpenYoung 系统设计评估方案。OpenYoung 是一个 AI Agent 执行平台，
会在 Rust 容器中运行目标 Agent，并需要评估其执行质量。

# 用户任务
{task_description}

# 任务类型识别
请首先识别任务的类型：
- coding: 代码生成、bug 修复、代码审查
- research: 信息检索、总结、分析
- dialogue: 问答、解释、讨论
- tool_use: 工具调用、数据处理
- mixed: 混合任务

# 任务复杂度判断
基于以下因素判断任务复杂度：

## 简单任务特征（跳过评估）
- 单步即可完成
- 输出确定性高
- 无需多轮交互
- 评估标准明确

## 中等复杂度
- 需2-5个步骤
- 有多个子目标
- 需要一定推理

## 高复杂度
- 需5+步骤
- 不确定性高
- 需要规划能力
- 可能有副作用

# 评估维度选择

根据任务类型和复杂度，选择合适的评估维度：

### 必需维度（所有任务）
- correctness: 任务是否正确完成

### 可选维度（根据任务类型）
- safety: 代码/输出安全性（coding 任务必需）
- efficiency: 资源使用效率
- robustness: 边界条件处理
- planning: 任务规划能力
- collaboration: 多轮对话质量（对话任务）

# 评估标准设计

对于每个评估维度，请设计：
1. **评估标准**：具体、可验证的判断条件
2. **通过阈值**：多少分算通过
3. **评估方法**：代码执行 / LLM 判断 / 静态分析 / 轨迹审查
4. **评分理由**：为什么要用这个维度/阈值

# 输出格式（JSON）

请输出以下 JSON 结构：

```json
{
  "task_type": "coding|research|dialogue|tool_use|mixed",
  "complexity": "simple|medium|high|skip",
  "skip_evaluation": true|false,
  "evaluation_dimensions": [
    {
      "name": "correctness",
      "weight": 0.4,
      "threshold": 0.8,
      "criteria": "具体评估标准描述",
      "evaluation_method": "code_execution|llm_judge|static_analysis|trace_review",
      "scoring_reason": "为什么选择这个维度和阈值"
    }
  ],
  "max_iterations": 3,
  "timeout_seconds": 300,
  "notes": "任何额外说明"
}
```

# 重要提醒
1. 如果任务复杂度为 "simple" 或 "skip"，设置 skip_evaluation: true
2. 每个维度都需要提供 scoring_reason
3. weight 总和应为 1.0
4. threshold 应基于任务难度合理设置

# 开始生成
请根据以上指导，生成评估计划。
"""


# ==================== 复杂度判断提示词 ====================

COMPLEXITY_JUDGE_PROMPT = """
# 任务复杂度判断

请分析以下任务，判断其复杂度：

## 任务描述
{task}

## 判断标准

### 简单任务 (complexity: simple)
- 单一操作即可完成
- 输出确定性高
- 示例："Hello，说声 hi"、"计算 1+1"

### 中等任务 (complexity: medium)
- 需要 2-5 个操作步骤
- 有明确的子目标
- 示例："写一个函数实现排序"、"修复这个 bug"

### 高复杂度 (complexity: high)
- 需要 5+ 步骤
- 需要任务规划
- 不确定性高
- 示例："重构整个模块"、"实现一个新功能"

### 跳过评估 (complexity: skip)
- 纯问候/闲聊
- 无实际产出
- 确定性对话

## 输出
请输出 JSON：
```json
{
  "complexity": "simple|medium|high|skip",
  "reasoning": "判断理由",
  "estimated_steps": 预估步骤数,
  "sub_goals": ["子目标1", "子目标2"]
}
```
"""


# ==================== 评估理由说明模板 ====================

SCORING_REASON_TEMPLATES = {
    "correctness": {
        "high_threshold": "代码任务正确性至关重要，0.8 确保高质量输出",
        "medium_threshold": "中等复杂度任务允许一定容错",
        "low_threshold": "简单任务主要关注正确性",
    },
    "safety": {
        "critical": "安全维度一票否决，必须设置高阈值",
        "coding_required": "代码生成任务必须评估安全性",
    },
    "efficiency": {
        "resource_constraint": "资源受限环境需要关注效率",
        "not_critical": "效率不是主要关注点",
    },
    "robustness": {
        "adversarial": "高风险任务需要对抗性测试",
        "low_risk": "低风险任务可简化鲁棒性评估",
    },
    "planning": {
        "complex_task": "复杂任务需要评估规划能力",
        "simple_task": "简单任务无需评估规划",
    },
}


# ==================== 评估器选择指南 ====================


class EvaluationMethod:
    """评估方法枚举"""

    CODE_EXECUTION = "code_execution"  # 代码执行验证
    LLM_JUDGE = "llm_judge"  # LLM 判断
    STATIC_ANALYSIS = "static_analysis"  # 静态分析
    TRACE_REVIEW = "trace_review"  # 轨迹审查


EVALUATION_METHOD_GUIDE = {
    "correctness": {
        "coding": EvaluationMethod.CODE_EXECUTION,
        "research": EvaluationMethod.LLM_JUDGE,
        "dialogue": EvaluationMethod.LLM_JUDGE,
        "tool_use": EvaluationMethod.CODE_EXECUTION,
    },
    "safety": {
        "coding": EvaluationMethod.STATIC_ANALYSIS,
        "research": EvaluationMethod.LLM_JUDGE,
        "dialogue": EvaluationMethod.LLM_JUDGE,
    },
    "efficiency": {
        "coding": EvaluationMethod.CODE_EXECUTION,
        "research": EvaluationMethod.CODE_EXECUTION,
    },
    "robustness": {
        "coding": EvaluationMethod.STATIC_ANALYSIS,
        "research": EvaluationMethod.LLM_JUDGE,
    },
}


# ==================== 评估维度默认配置 ====================

DEFAULT_DIMENSION_CONFIG = {
    "correctness": {
        "weight": 0.4,
        "threshold": 0.7,
        "evaluation_method": EvaluationMethod.CODE_EXECUTION,
    },
    "safety": {
        "weight": 0.3,
        "threshold": 0.9,
        "evaluation_method": EvaluationMethod.STATIC_ANALYSIS,
    },
    "efficiency": {
        "weight": 0.15,
        "threshold": 0.6,
        "evaluation_method": EvaluationMethod.CODE_EXECUTION,
    },
    "robustness": {
        "weight": 0.15,
        "threshold": 0.5,
        "evaluation_method": EvaluationMethod.STATIC_ANALYSIS,
    },
}


# ==================== 跳过评估模式 ====================

SKIP_EVAL_PATTERNS = [
    # 中文问候（精确匹配）
    r"^(你好|您好|嗨)$",
    # 英文问候（精确匹配）
    r"^(hello|hi|hey|howdy)$",
    # 简单say指令（忽略大小写，允许简单参数）
    r"^say\s+\w+(\s+\w+)*$",
    # 简单计算
    r"^what['\u2019]?s\s+\d+\s*\+\s*\d+\??$",
    r"^compute\s+\d+\s*[\+\-\*\/]\s*\d+$",
    # 简单问题
    r"^who\s+are\s+you\??$",
    r"^tell\s+me\s+about\s+yourself\??$",
]


# ==================== 便捷函数 ====================


def should_skip_evaluation(task_description: str) -> bool:
    """判断任务是否应该跳过评估

    Args:
        task_description: 任务描述

    Returns:
        bool: 是否跳过评估
    """
    import re

    task_lower = task_description.lower().strip()

    for pattern in SKIP_EVAL_PATTERNS:
        if re.match(pattern, task_lower, re.IGNORECASE):
            return True

    return False


def get_default_dimensions_for_task_type(task_type: str) -> list[str]:
    """获取任务类型对应的默认评估维度

    Args:
        task_type: 任务类型

    Returns:
        list[str]: 评估维度列表
    """
    task_dimensions = {
        TaskType.CODING: ["correctness", "safety", "efficiency", "robustness"],
        TaskType.RESEARCH: ["correctness", "efficiency"],
        TaskType.DIALOGUE: ["correctness", "collaboration"],
        TaskType.TOOL_USE: ["correctness", "efficiency", "robustness"],
        TaskType.MIXED: ["correctness", "safety", "efficiency", "robustness"],
    }

    return task_dimensions.get(task_type, ["correctness"])


def get_dimension_weight(dimension: str) -> float:
    """获取评估维度的默认权重

    Args:
        dimension: 评估维度

    Returns:
        float: 权重值
    """
    return DEFAULT_DIMENSION_CONFIG.get(dimension, {}).get("weight", 0.25)


def get_dimension_threshold(dimension: str, complexity: str) -> float:
    """获取评估维度的默认阈值

    Args:
        dimension: 评估维度
        complexity: 任务复杂度

    Returns:
        float: 阈值
    """
    base_threshold = DEFAULT_DIMENSION_CONFIG.get(dimension, {}).get("threshold", 0.7)

    # 根据复杂度调整阈值
    if complexity == TaskComplexity.HIGH:
        return base_threshold * 0.9  # 高复杂度降低阈值
    elif complexity == TaskComplexity.SIMPLE:
        return base_threshold * 1.1  # 简单任务提高阈值

    return base_threshold
