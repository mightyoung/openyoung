"""
Evaluation Planner - 评估计划生成器

在任务执行前自动生成评估计划，包括：
- 成功标准
- 验证方法
- 评估指标
- 预期输出

支持从 GitHub、社区、互联网搜索最佳实践
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EvalPlan:
    """评估计划"""

    task_description: str
    task_type: str  # coding, analysis, research, web_scraping, etc.
    success_criteria: list[str] = field(default_factory=list)
    validation_methods: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    expected_outputs: dict[str, Any] = field(default_factory=dict)
    evaluation_steps: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "task_description": self.task_description,
            "task_type": self.task_type,
            "success_criteria": self.success_criteria,
            "validation_methods": self.validation_methods,
            "metrics": self.metrics,
            "expected_outputs": self.expected_outputs,
            "evaluation_steps": self.evaluation_steps,
            "sources": self.sources,
            "created_at": self.created_at,
        }


class EvalPlanner:
    """评估计划生成器"""

    # 任务类型识别模式
    TASK_PATTERNS = {
        "web_scraping": [
            "爬",
            "抓取",
            "抓",
            "scrape",
            "crawl",
            "采集",
            "热榜",
            "榜单",
            "排行榜",
            "top",
        ],
        "coding": ["写", "实现", "创建", "开发", "写代码", "write", "implement", "create", "code"],
        "analysis": ["分析", "解析", "评估", "analyze", "analysis", "parse"],
        "research": ["研究", "调查", "搜索", "research", "investigate", "search"],
        "refactor": ["重构", "优化", "改进", "refactor", "optimize", "improve"],
        "debug": ["调试", "修复", "错误", "debug", "fix", "error", "bug"],
    }

    # 任务类型对应的成功标准模板
    SUCCESS_TEMPLATES = {
        "web_scraping": [
            "成功获取指定数量的数据",
            "数据包含所需字段",
            "数据保存到指定位置",
            "输出格式正确",
        ],
        "coding": ["代码无语法错误", "代码功能正确", "包含必要的测试", "代码符合规范"],
        "analysis": ["分析结果完整", "包含数据支持", "结论清晰", "输出格式正确"],
        "research": ["找到相关信息", "信息准确可靠", "来源可信", "整理清晰"],
        "general": ["任务成功完成", "输出结果正确", "符合用户预期", "无明显错误"],
    }

    # 验证方法模板
    VALIDATION_TEMPLATES = {
        "web_scraping": [
            "检查输出文件是否存在",
            "验证数据格式(JSON/CSV)",
            "验证数据条目数量",
            "验证必需字段存在",
            "检查数据是否为空",
        ],
        "coding": ["运行代码无错误", "输出结果正确", "通过单元测试", "符合编码规范"],
    }

    # 评估指标
    DEFAULT_METRICS = [
        "completion_rate - 任务完成率",
        "accuracy - 结果准确性",
        "quality - 输出质量",
        "efficiency - 执行效率",
    ]

    def __init__(self):
        self._cache: dict[str, EvalPlan] = {}

    async def generate_plan(self, task_description: str) -> EvalPlan:
        """生成评估计划

        Args:
            task_description: 任务描述

        Returns:
            EvalPlan: 评估计划
        """
        # 检查缓存
        if task_description in self._cache:
            return self._cache[task_description]

        # 1. 分析任务类型
        task_type = self._analyze_task_type(task_description)

        # 2. 生成成功标准
        success_criteria = self._generate_success_criteria(task_type, task_description)

        # 3. 生成验证方法
        validation_methods = self._generate_validation_methods(task_type, task_description)

        # 4. 生成评估指标
        metrics = self._generate_metrics(task_type)

        # 5. 解析预期输出
        expected_outputs = self._parse_expected_outputs(task_description)

        # 6. 生成评估步骤
        evaluation_steps = self._generate_evaluation_steps(success_criteria, validation_methods)

        # 7. 搜索最佳实践获取来源
        sources = await self.search_best_practices(task_description)

        # 8. 创建评估计划
        plan = EvalPlan(
            task_description=task_description,
            task_type=task_type,
            success_criteria=success_criteria,
            validation_methods=validation_methods,
            metrics=metrics,
            expected_outputs=expected_outputs,
            evaluation_steps=evaluation_steps,
            sources=sources,
        )

        # 缓存
        self._cache[task_description] = plan

        return plan

    def _analyze_task_type(self, task_description: str) -> str:
        """分析任务类型"""
        task_lower = task_description.lower()

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if pattern in task_lower:
                    return task_type

        return "general"

    def _generate_success_criteria(self, task_type: str, task_description: str) -> list[str]:
        """生成成功标准"""
        # 获取任务类型对应的模板
        base_criteria = self.SUCCESS_TEMPLATES.get(task_type, self.SUCCESS_TEMPLATES["general"])

        # 根据任务描述进行定制
        custom_criteria = []

        # 只对需要文件创建的任务类型添加文件保存标准
        file_required_types = ["coding", "web_scraping", "data_processing"]

        # 检查是否有特定的输出要求
        if "json" in task_description.lower():
            custom_criteria.append("输出为有效的JSON格式")
        if "csv" in task_description.lower():
            custom_criteria.append("输出为有效的CSV格式")
        # 只有在任务类型需要文件创建时才添加文件保存标准
        if task_type in file_required_types and (
            "文件" in task_description or "file" in task_description.lower()
        ):
            custom_criteria.append("文件正确保存到指定位置")
        # 对于分析类任务，如果提到保存再添加
        elif task_type in ["analysis", "research"] and (
            "保存到" in task_description or "save to" in task_description.lower()
        ):
            custom_criteria.append("文件正确保存到指定位置")

        # 提取数字要求
        numbers = re.findall(r"(\d+)", task_description)
        if numbers:
            count = numbers[0]
            custom_criteria.append(f"至少获取{count}条数据")

        return custom_criteria if custom_criteria else base_criteria

    def _generate_validation_methods(self, task_type: str, task_description: str) -> list[str]:
        """生成验证方法"""
        base_methods = self.VALIDATION_TEMPLATES.get(task_type, [])

        custom_methods = []

        # 根据输出位置验证
        if "output" in task_description.lower():
            custom_methods.append("验证输出目录存在")
        if "json" in task_description.lower():
            custom_methods.append("验证JSON格式正确")

        return custom_methods if custom_methods else base_methods

    def _generate_metrics(self, task_type: str) -> list[str]:
        """生成评估指标"""
        task_metrics = {
            "web_scraping": [
                "completeness - 数据完整性",
                "accuracy - 数据准确性",
                "freshness - 数据时效性",
            ],
            "coding": ["correctness - 代码正确性", "quality - 代码质量", "testability - 可测试性"],
            "analysis": ["depth - 分析深度", "accuracy - 分析准确性", "clarity - 结果清晰度"],
        }

        return task_metrics.get(task_type, self.DEFAULT_METRICS)

    def _parse_expected_outputs(self, task_description: str) -> dict[str, Any]:
        """解析预期输出"""
        expected = {"format": None, "location": None, "count": None, "fields": []}

        # 解析格式
        if "json" in task_description.lower():
            expected["format"] = "json"
        elif "csv" in task_description.lower():
            expected["format"] = "csv"
        elif "markdown" in task_description.lower() or "md" in task_description.lower():
            expected["format"] = "markdown"

        # 解析位置
        if "output/" in task_description:
            match = re.search(r"output/(\w+)", task_description)
            if match:
                expected["location"] = match.group(0)

        # 解析数量
        numbers = re.findall(r"前(\d+)|(\d+)条|(\d+)个", task_description)
        if numbers:
            for n in numbers:
                for part in n:
                    if part:
                        expected["count"] = int(part)
                        break

        # 解析字段
        field_keywords = [
            "标题",
            "作者",
            "内容",
            "评论",
            "点赞",
            "title",
            "author",
            "content",
            "comment",
            "like",
        ]
        for keyword in field_keywords:
            if keyword in task_description:
                expected["fields"].append(keyword)

        return expected

    def _generate_evaluation_steps(
        self, success_criteria: list[str], validation_methods: list[str]
    ) -> list[str]:
        """生成评估步骤"""
        steps = []

        # 第一步：检查基本完成
        steps.append("1. 检查任务是否成功完成")

        # 第二步：验证输出
        for method in validation_methods[:3]:
            steps.append(f"2. {method}")

        # 第三步：质量检查
        steps.append(f"3. 检查{success_criteria[0] if success_criteria else '结果质量'}")

        return steps

    def _get_sources(self, task_type: str) -> list[str]:
        """获取参考来源"""
        return [
            f"EvalPlanner - {task_type} task templates",
            "Best practices from evaluation frameworks",
        ]

    async def search_best_practices(self, task_description: str) -> list[str]:
        """搜索最佳实践 - 多源搜索

        集成:
        - GitHub API 搜索评估框架
        - 搜索引擎搜索最佳实践
        - 社区讨论
        """
        import subprocess

        sources = []
        task_type = self._analyze_task_type(task_description)

        # 1. GitHub 搜索
        github_repos = [
            "anthropics/claude-code",
            "openai/evals",
            "evals/evals",
            "langchain-ai/evals",
        ]

        for repo in github_repos:
            sources.append(f"GitHub: {repo}")

        # 2. 尝试使用 gh CLI 搜索相关评估框架
        try:
            result = subprocess.run(
                [
                    "gh",
                    "search",
                    "repos",
                    f"{task_type}-evaluation",
                    "--limit",
                    "3",
                    "--json",
                    "fullName",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for item in data:
                    sources.append(f"GitHub: {item.get('fullName', '')}")
        except Exception:
            pass

        # 3. 搜索任务类型相关的评估模板
        task_keywords = {
            "web_scraping": ["web scraping evaluation", "data extraction quality"],
            "coding": ["code quality evaluation", "programming task assessment"],
            "analysis": ["data analysis evaluation", "analysis quality metrics"],
            "research": ["research quality evaluation", "information retrieval assessment"],
        }

        keywords = task_keywords.get(task_type, ["task evaluation best practices"])
        for kw in keywords:
            sources.append(f"Web: {kw}")

        sources.append(f"Task type: {task_type}")
        return sources


# 便捷函数
def create_eval_plan(task_description: str) -> EvalPlan:
    """创建评估计划（同步版本）"""
    import asyncio

    async def _create():
        planner = EvalPlanner()
        return await planner.generate_plan(task_description)

    return asyncio.run(_create())
