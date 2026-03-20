"""
Graders - 评估裁判模块

三类 Grader:
- CodeGrader: 确定性检查 (lint/测试/状态验证)
- ModelGrader: LLM-as-Judge (基于 rubric 的评判)
- HumanGrader: 人工判定

参考 Anthropic grader 设计
"""

from .base import BaseGrader, GraderOutput
from .code import CodeGrader
from .human import HumanGrader
from .model import ModelGrader

__all__ = [
    "BaseGrader",
    "GraderOutput",
    "CodeGrader",
    "ModelGrader",
    "HumanGrader",
]
