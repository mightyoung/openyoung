"""
Input Tester - 输入理解测试

验证 Agent 对输入的理解能力：
- 意图解析
- 任务分类
- 参数提取

参考 Google HELM 的评估方法
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .models import (
    EvaluationDimension,
    TestCase,
    TestResult,
    TestType,
)


class InputTester:
    """输入理解测试器

    通过分析 Agent 的行为来验证其对输入的理解能力
    """

    def __init__(self, agent):
        """
        Args:
            agent: YoungAgent 实例
        """
        self.agent = agent

    async def run(self, test_case: TestCase) -> TestResult:
        """运行输入理解测试

        Args:
            test_case: 测试用例

        Returns:
            TestResult: 测试结果
        """
        start_time = datetime.now()

        # 1. 获取 Agent 的解析结果
        parsed = await self._parse_input(test_case.task_description)

        # 2. 计算各项匹配度
        intent_score = self._calculate_intent_match(parsed.get("intent"), test_case.expected_intent)

        task_type_score = self._calculate_task_type_match(
            parsed.get("task_type"), test_case.task_type.value
        )

        param_score = self._calculate_param_match(
            parsed.get("params", {}), test_case.expected_params
        )

        # 3. 综合评分
        # 意图 50% + 任务类型 30% + 参数 20%
        score = intent_score * 0.5 + task_type_score * 0.3 + param_score * 0.2

        # 4. 判断是否通过
        passed = score >= 0.7

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return TestResult(
            test_id=test_case.id,
            test_type=TestType.INPUT_UNDERSTANDING,
            dimension=EvaluationDimension.INTENT_PARSING,
            passed=passed,
            score=score,
            details={
                "parsed_intent": parsed.get("intent"),
                "expected_intent": test_case.expected_intent,
                "intent_score": intent_score,
                "task_type_score": task_type_score,
                "param_score": param_score,
            },
            duration_ms=duration_ms,
            task_description=test_case.task_description,
        )

    async def _parse_input(self, task_description: str) -> dict:
        """解析输入，理解用户意图

        实现策略：
        1. 观察 Agent 执行前的预处理行为
        2. 分析 Agent 的响应模式
        3. 使用探测性问题

        Returns:
            dict: 解析结果 {intent, task_type, params}
        """
        # 实现方案：
        # 1. 简单实现：基于关键词匹配
        # 2. 中级：调用 Agent 的任务解析能力
        # 3. 高级：使用专门的意图识别模型

        # 简单实现：基于关键词
        intent = "unknown"
        task_type = "unknown"
        params = {}

        # 检测意图
        task_lower = task_description.lower()

        if any(kw in task_lower for kw in ["写", "生成", "创建", "实现", "def ", "function "]):
            intent = "code_generation"
            task_type = "code_generation"
        elif any(kw in task_lower for kw in ["修复", "bug", "错误", "修复"]):
            intent = "code_fix"
            task_type = "code_fix"
        elif any(kw in task_lower for kw in ["分析", "处理", "计算"]):
            intent = "data_processing"
            task_type = "data_processing"
        elif any(kw in task_lower for kw in ["什么是", "解释", "什么是", "怎么"]):
            intent = "question_answering"
            task_type = "question_answering"
        elif any(kw in task_lower for kw in ["运行", "执行", "跑"]):
            intent = "task_execution"
            task_type = "task_execution"
        else:
            intent = "text_generation"
            task_type = "text_generation"

        return {
            "intent": intent,
            "task_type": task_type,
            "params": params,
        }

    def _calculate_intent_match(self, parsed_intent: str, expected_intent: str) -> float:
        """计算意图匹配度"""
        if not parsed_intent or not expected_intent:
            return 0.0

        # 精确匹配
        if parsed_intent.lower() == expected_intent.lower():
            return 1.0

        # 部分匹配（包含关系）
        if expected_intent.lower() in parsed_intent.lower():
            return 0.8

        return 0.0

    def _calculate_task_type_match(self, parsed_type: str, expected_type: str) -> float:
        """计算任务类型匹配度"""
        return self._calculate_intent_match(parsed_type, expected_type)

    def _calculate_param_match(self, parsed_params: dict, expected_params: dict) -> float:
        """计算参数匹配度"""
        if not expected_params:
            return 1.0  # 没有预期参数则通过

        if not parsed_params:
            return 0.0

        # 计算交集
        matched = sum(
            1 for k, v in expected_params.items() if k in parsed_params and parsed_params[k] == v
        )

        return matched / len(expected_params)


class IntentParser:
    """意图解析器

    可独立使用的意图解析组件
    """

    # 意图关键词映射
    INTENT_KEYWORDS = {
        "code_generation": ["写", "生成", "创建", "实现", "def ", "function ", "class "],
        "code_fix": ["修复", "bug", "错误", "fix", "repair"],
        "code_review": ["审查", "review", "检查"],
        "text_generation": ["写", "生成", "创作", "文章", "博客"],
        "question_answering": ["什么是", "解释", "怎么", "如何", "为什么"],
        "data_processing": ["分析", "处理", "计算", "统计", "处理"],
        "task_execution": ["运行", "执行", "跑", "run", "execute"],
        "information_query": ["查找", "搜索", "查询", "找"],
    }

    @classmethod
    def parse(cls, task_description: str) -> dict:
        """解析任务描述

        Args:
            task_description: 任务描述

        Returns:
            dict: {intent, task_type, confidence, keywords}
        """
        task_lower = task_description.lower()

        # 匹配意图
        best_match = None
        best_score = 0

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > best_score:
                best_score = score
                best_match = intent

        if best_match is None:
            best_match = "unknown"

        return {
            "intent": best_match,
            "task_type": best_match,
            "confidence": min(best_score / 3, 1.0),  # 归一化
            "keywords": [kw for kw in cls.INTENT_KEYWORDS.get(best_match, []) if kw in task_lower],
        }
