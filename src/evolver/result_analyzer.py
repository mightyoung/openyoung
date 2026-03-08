"""
Result Analyzer - 执行结果分析器
分析 agent 执行结果，提取成功模式，生成新配置
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionPattern:
    """执行模式"""
    task_type: str
    workflow: list[str]
    tools_used: list[str]
    success_indicators: list[str]


class ResultAnalyzer:
    """执行结果分析器"""

    def __init__(self):
        self.patterns = []

    def analyze(self, task: str, result: str, context: dict[str, Any] = None) -> dict[str, Any]:
        """分析执行结果

        Args:
            task: 任务描述
            result: 执行结果
            context: 上下文信息

        Returns:
            分析报告
        """
        analysis = {
            "task_type": self._classify_task(task),
            "success": self._is_success(result),
            "workflow_steps": self._extract_workflow_steps(result),
            "tools_used": self._extract_tools_used(result),
            "key_learnings": self._extract_learnings(task, result),
            "suggested_improvements": self._suggest_improvements(result),
        }

        # 提取模式
        if analysis["success"]:
            pattern = ExecutionPattern(
                task_type=analysis["task_type"],
                workflow=analysis["workflow_steps"],
                tools_used=analysis["tools_used"],
                success_indicators=analysis["key_learnings"],
            )
            self.patterns.append(pattern)

        return analysis

    def _classify_task(self, task: str) -> str:
        """分类任务类型"""
        task_lower = task.lower()

        if any(k in task_lower for k in ["bug", "fix", "错误", "修复"]):
            return "bugfix"
        elif any(k in task_lower for k in ["refactor", "重构", "优化"]):
            return "refactor"
        elif any(k in task_lower for k in ["test", "测试", "验证"]):
            return "testing"
        elif any(k in task_lower for k in ["create", "build", "实现", "创建"]):
            return "implementation"
        elif any(k in task_lower for k in ["analyze", "分析", "review", "审查"]):
            return "analysis"
        else:
            return "general"

    def _is_success(self, result: str) -> bool:
        """判断是否成功"""
        if not result:
            return False

        # 检查错误标记
        error_markers = ["error", "failed", "失败", "错误"]
        if any(m in result.lower() for m in error_markers):
            return False

        # 检查成功标记
        success_markers = ["success", "completed", "完成", "done", "ok"]
        return any(m in result.lower() for m in success_markers)

    def _extract_workflow_steps(self, result: str) -> list[str]:
        """提取工作流步骤"""
        steps = []

        # 提取工具调用
        tool_pattern = r"\[执行工具\]\s*(\w+)"
        matches = re.findall(tool_pattern, result)
        steps.extend(matches)

        return steps[:10]  # 限制步骤数

    def _extract_tools_used(self, result: str) -> list[str]:
        """提取使用的工具"""
        tools = []

        known_tools = ["bash", "write", "edit", "read", "glob", "grep", "web_fetch", "git"]
        for tool in known_tools:
            if tool in result.lower():
                tools.append(tool)

        return tools

    def _extract_learnings(self, task: str, result: str) -> list[str]:
        """提取关键学习"""
        learnings = []

        # 从成功结果中提取关键点
        if self._is_success(result):
            learnings.append("任务成功完成")

        # 提取代码修改
        if "已写入文件" in result or "已编辑文件" in result:
            learnings.append("涉及文件修改")

        # 提取命令执行
        if "[命令执行完成]" in result:
            learnings.append("涉及命令执行")

        return learnings

    def _suggest_improvements(self, result: str) -> list[str]:
        """建议改进"""
        suggestions = []

        if not self._is_success(result):
            suggestions.append("任务执行失败，需要检查错误原因")

        if len(result) > 5000:
            suggestions.append("结果过长，考虑分段处理")

        # 检查是否缺少某些工具
        if "read" not in result.lower() and "cat" not in result.lower():
            suggestions.append("未读取文件，可能需要先了解现有代码")

        return suggestions

    def generate_flowskill_config(self, task_type: str = None) -> dict[str, Any]:
        """根据分析的模式生成 FlowSkill 配置"""
        if not self.patterns:
            return {}

        # 使用最新的模式或指定类型
        patterns = self.patterns
        if task_type:
            patterns = [p for p in self.patterns if p.task_type == task_type]

        if not patterns:
            return {}

        pattern = patterns[-1]  # 使用最新的

        config = {
            "name": f"auto_generated_{pattern.task_type}",
            "description": f"自动生成的 {pattern.task_type} 工作流",
            "trigger_conditions": [pattern.task_type],
            "required_tools": pattern.tools_used,
            "workflow": pattern.workflow,
            "success_indicators": pattern.success_indicators,
        }

        return config

    def get_pattern_summary(self) -> dict[str, Any]:
        """获取模式摘要"""
        if not self.patterns:
            return {"count": 0, "types": {}}

        type_counts = {}
        for p in self.patterns:
            type_counts[p.task_type] = type_counts.get(p.task_type, 0) + 1

        return {
            "count": len(self.patterns),
            "types": type_counts,
            "recent": [
                {"type": p.task_type, "tools": p.tools_used}
                for p in self.patterns[-5:]
            ]
        }
