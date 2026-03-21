"""
Tool Selector - 动态工具选择器

根据任务上下文动态选择最合适的工具
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ToolCategory(Enum):
    """工具分类"""

    CODE = "code"  # 代码执行
    SEARCH = "search"  # 搜索
    BROWSER = "browser"  # 浏览器
    FILE = "file"  # 文件操作
    DATA = "data"  # 数据处理
    LLM = "llm"  # LLM调用
    UTILITY = "utility"  # 通用工具


@dataclass
class ToolSpec:
    """工具规格"""

    id: str
    name: str
    description: str
    category: ToolCategory
    keywords: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class ToolSelection:
    """工具选择结果"""

    tool: ToolSpec
    score: float  # 匹配分数
    reasoning: str


class ToolSelector:
    """动态工具选择器"""

    def __init__(self):
        self.tools: dict[str, ToolSpec] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            ToolSpec(
                id="code_executor",
                name="CodeExecutor",
                description="执行Python/JavaScript代码",
                category=ToolCategory.CODE,
                keywords=["代码", "执行", "运行", "code", "execute", "run"],
                capabilities=["python", "javascript", "sandbox"],
            ),
            ToolSpec(
                id="file_writer",
                name="FileWriter",
                description="写入文件",
                category=ToolCategory.FILE,
                keywords=["写", "保存", "创建文件", "write", "save", "create"],
                capabilities=["write", "create"],
            ),
            ToolSpec(
                id="file_reader",
                name="FileReader",
                description="读取文件",
                category=ToolCategory.FILE,
                keywords=["读", "查看", "读取", "read", "view", "get"],
                capabilities=["read", "view"],
            ),
            ToolSpec(
                id="web_search",
                name="WebSearch",
                description="网络搜索",
                category=ToolCategory.SEARCH,
                keywords=["搜索", "查找", "查询", "search", "find", "google"],
                capabilities=["search", "web"],
            ),
            ToolSpec(
                id="browser",
                name="Browser",
                description="浏览器操作",
                category=ToolCategory.BROWSER,
                keywords=["浏览", "点击", "访问", "browser", "click", "navigate"],
                capabilities=["navigate", "click", "screenshot"],
            ),
            ToolSpec(
                id="data_processor",
                name="DataProcessor",
                description="数据处理",
                category=ToolCategory.DATA,
                keywords=["分析", "处理", "转换", "analyze", "process", "transform"],
                capabilities=["csv", "json", "filter", "aggregate"],
            ),
        ]

        for tool in default_tools:
            self.register_tool(tool)

    def register_tool(self, tool: ToolSpec):
        """注册工具"""
        self.tools[tool.id] = tool

    def unregister_tool(self, tool_id: str):
        """注销工具"""
        if tool_id in self.tools:
            del self.tools[tool_id]

    async def select(
        self,
        task: str,
        context: dict = None,
    ) -> list[ToolSelection]:
        """
        选择最合适的工具

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            list[ToolSelection]: 排序后的工具选择列表
        """
        task_lower = task.lower()
        context = context or {}

        scores = []

        for tool in self.tools.values():
            score = self._calculate_score(tool, task_lower, context)
            reasoning = self._explain_score(tool, task_lower, context)
            scores.append(
                ToolSelection(
                    tool=tool,
                    score=score,
                    reasoning=reasoning,
                )
            )

        # 按分数排序
        scores.sort(key=lambda x: x.score, reverse=True)

        # 返回前N个工具
        return scores[:3]

    def _calculate_score(self, tool: ToolSpec, task: str, context: dict) -> float:
        """计算匹配分数"""
        score = 0.0

        # 1. 关键词匹配 (40%)
        keyword_matches = sum(1 for kw in tool.keywords if kw.lower() in task)
        if tool.keywords:
            score += (keyword_matches / len(tool.tool_keywords)) * 0.4

        # 2. 分类匹配 (30%)
        if context.get("preferred_category"):
            if tool.category == context["preferred_category"]:
                score += 0.3

        # 3. 能力匹配 (30%)
        required_capabilities = context.get("required_capabilities", [])
        if required_capabilities:
            cap_matches = sum(1 for cap in required_capabilities if cap in tool.capabilities)
            score += (cap_matches / len(required_capabilities)) * 0.3
        else:
            score += 0.15  # 默认基础分

        return min(1.0, score)

    def _explain_score(self, tool: ToolSpec, task: str, context: dict) -> str:
        """解释分数"""
        reasons = []

        # 关键词匹配
        matched_keywords = [kw for kw in tool.keywords if kw.lower() in task]
        if matched_keywords:
            reasons.append(f"匹配关键词: {', '.join(matched_keywords[:3])}")

        # 分类匹配
        if context.get("preferred_category") == tool.category:
            reasons.append(f"符合偏好分类: {tool.category.value}")

        return "; ".join(reasons) if reasons else "基础匹配"

    def get_tools_by_category(self, category: ToolCategory) -> list[ToolSpec]:
        """获取分类下的所有工具"""
        return [t for t in self.tools.values() if t.category == category]

    def get_tool(self, tool_id: str) -> Optional[ToolSpec]:
        """获取工具"""
        return self.tools.get(tool_id)


class AdaptiveToolSelector(ToolSelector):
    """自适应工具选择器 - 基于历史选择进行学习"""

    def __init__(self):
        super().__init__()
        self.success_history: dict[str, list[str]] = {}  # tool_id -> [tasks]
        self.failure_history: dict[str, list[str]] = {}  # tool_id -> [tasks]

    def record_success(self, tool_id: str, task: str):
        """记录成功使用"""
        if tool_id not in self.success_history:
            self.success_history[tool_id] = []
        self.success_history[tool_id].append(task)

    def record_failure(self, tool_id: str, task: str):
        """记录失败使用"""
        if tool_id not in self.failure_history:
            self.failure_history[tool_id] = []
        self.failure_history[tool_id].append(task)

    async def select_with_learning(
        self,
        task: str,
        context: dict = None,
    ) -> list[ToolSelection]:
        """带学习的选择"""
        # 先获取基础选择
        selections = await self.select(task, context)

        # 根据历史调整分数
        task_lower = task.lower()
        for selection in selections:
            tool_id = selection.tool.id

            # 成功率加权
            successes = len(self.success_history.get(tool_id, []))
            failures = len(self.failure_history.get(tool_id, []))

            if successes + failures > 0:
                success_rate = successes / (successes + failures)
                # 根据成功率调整分数
                adjustment = (success_rate - 0.5) * 0.2  # ±10%
                selection.score = max(0, min(1, selection.score + adjustment))

                selection.reasoning += f" (历史成功率: {success_rate:.0%})"

        # 重新排序
        selections.sort(key=lambda x: x.score, reverse=True)
        return selections
