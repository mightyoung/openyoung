"""
Output Tester - 输出质量测试

验证 Agent 输出的质量：
- 规则检查
- LLM Judge 评估
- 格式验证

参考 OpenAI Evals 的输出评估设计
"""

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import (
    EvaluationDimension,
    TestCase,
    TestResult,
    TestType,
)


class OutputTester:
    """输出质量测试器

    评估 Agent 输出的质量
    """

    def __init__(self, agent, llm_judge=None):
        """
        Args:
            agent: YoungAgent 实例
            llm_judge: LLM Judge 评估器（可选）
        """
        self.agent = agent
        self.llm_judge = llm_judge
        self.rule_checker = RuleChecker()

    async def run(self, test_case: TestCase) -> TestResult:
        """运行输出质量测试

        Args:
            test_case: 测试用例

        Returns:
            TestResult: 测试结果
        """
        start_time = datetime.now()

        # 1. 执行任务获取输出
        output = await self._execute_task(test_case.task_description)

        # 2. 规则检查
        rule_score = 0.0
        if test_case.validation_rules:
            rule_score = await self.rule_checker.check(
                test_case.task_description,
                output,
                test_case.validation_rules
            )
        else:
            # 默认：检查是否有输出
            rule_score = 1.0 if output and len(output) > 0 else 0.0

        # 3. LLM Judge 评估（可选）
        llm_score = 0.0
        if self.llm_judge and test_case.expected_output_sample:
            try:
                llm_score = await self.llm_judge.evaluate(
                    test_case.task_description,
                    output,
                    test_case.expected_output_sample
                )
            except Exception as e:
                # LLM Judge 失败时使用规则分数
                pass

        # 4. 综合评分
        # 如果有 LLM Judge：规则 50% + LLM 50%
        # 否则：100% 规则分数
        if llm_score > 0:
            score = rule_score * 0.5 + llm_score * 0.5
        else:
            score = rule_score

        # 5. 判断是否通过
        passed = score >= 0.6

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return TestResult(
            test_id=test_case.id,
            test_type=TestType.OUTPUT_QUALITY,
            dimension=EvaluationDimension.COMPLETENESS,
            passed=passed,
            score=score,
            details={
                "output": output[:500] if output else "",  # 截断
                "rule_score": rule_score,
                "llm_score": llm_score,
            },
            duration_ms=duration_ms,
            task_description=test_case.task_description,
            actual_output=output,
        )

    async def _execute_task(self, task_description: str) -> str:
        """执行任务获取输出"""
        try:
            result = await self.agent.run(task_description)
            return str(result) if result else ""
        except Exception as e:
            return f"Error: {str(e)}"


class RuleChecker:
    """规则检查器

    基于预定义规则验证输出
    """

    def __init__(self):
        self.check_registry = {
            "file_exists": self._check_file_exists,
            "json_format": self._check_json_format,
            "code_syntax": self._check_code_syntax,
            "output_contains": self._check_output_contains,
            "output_length": self._check_output_length,
            "output_not_contains": self._check_output_not_contains,
        }

    async def check(
        self,
        task_description: str,
        output: str,
        rules: dict
    ) -> float:
        """执行规则检查

        Args:
            task_description: 任务描述
            output: Agent 输出
            rules: 规则定义

        Returns:
            float: 分数 0-1
        """
        if not rules:
            # 默认：检查是否有输出
            return 1.0 if output and len(output) > 0 else 0.0

        results = []
        for rule_name, rule_params in rules.items():
            checker = self.check_registry.get(rule_name)
            if checker:
                result = await checker(task_description, output, rule_params)
                results.append(result)

        return sum(results) / len(results) if results else 0.0

    async def _check_file_exists(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查文件是否存在"""
        file_path = params.get("path")

        if not file_path:
            # 从输出中提取路径
            patterns = [
                r'(?:保存|输出|写入|创建)\s+(.+\.(?:json|txt|csv|py|md))',
                r'文件\s*[:：]\s*(.+\.(?:json|txt|csv|py|md))',
                r'(.+\.(?:json|txt|csv|py|md))',
            ]
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    file_path = match.group(1)
                    break

        if not file_path:
            return 0.0

        # 检查文件
        try:
            # 支持绝对路径和相对路径
            path = Path(file_path)
            if not path.is_absolute():
                # 相对路径基于当前目录
                path = Path.cwd() / path

            exists = path.exists() and path.is_file()
            return 1.0 if exists else 0.0
        except Exception:
            return 0.0

    async def _check_json_format(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查 JSON 格式"""
        try:
            # 尝试从输出中提取 JSON
            json_match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', output)
            if json_match:
                json.loads(json_match.group())
                return 1.0
        except Exception:
            pass
        return 0.0

    async def _check_code_syntax(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查代码语法（简化版）"""
        language = params.get("language", "python")

        if language == "python":
            # 简单检查：是否有 def/class 定义
            has_def = "def " in output or "class " in output
            return 1.0 if has_def else 0.0

        # 其他语言暂时返回 0.5
        return 0.5

    async def _check_output_contains(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查输出是否包含关键内容"""
        required = params.get("required", [])
        if not required:
            return 1.0

        output_lower = output.lower()
        found = sum(1 for kw in required if kw.lower() in output_lower)

        return found / len(required)

    async def _check_output_length(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查输出长度"""
        min_length = params.get("min", 0)
        max_length = params.get("max", float('inf'))

        length = len(output)

        if length < min_length:
            return 0.0
        if length > max_length:
            return 0.5  # 超过但不是严重问题

        return 1.0

    async def _check_output_not_contains(
        self,
        task: str,
        output: str,
        params: dict
    ) -> float:
        """检查输出不包含禁止内容"""
        forbidden = params.get("forbidden", [])
        if not forbidden:
            return 1.0

        output_lower = output.lower()
        found = sum(1 for kw in forbidden if kw.lower() in output_lower)

        # 发现任何禁止内容返回 0
        return 0.0 if found > 0 else 1.0
