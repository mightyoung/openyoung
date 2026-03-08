"""
Evaluation Dataset - 2026 Best Practice

包含 20+ 真实用例，覆盖多种任务类型：
- coding: 代码编写、调试、重构
- general: 通用对话、问答
- research: 调研、信息检索
- web_scraping: 网页抓取
- data_processing: 数据处理
- file_operations: 文件操作

基于 2026 行业最佳实践:
- 多指标评估
- 任务特定评估
- 可重现性
- 公平性检查
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvalTestCase:
    """评估测试用例"""
    id: str
    task_type: str  # coding, general, research, web_scraping, data_processing
    task_description: str
    expected_outputs: dict[str, Any]
    success_criteria: list[str]
    difficulty: str  # easy, medium, hard
    domain: str  # 技术、业务、通用


# 评估数据集
EVALUATION_DATASET: list[EvalTestCase] = [
    # ========== CODING 任务 ==========
    EvalTestCase(
        id="code_001",
        task_type="coding",
        task_description="写一个 Python 函数，实现二分查找算法",
        expected_outputs={"function": "binary_search", "has_docstring": True},
        success_criteria=[
            "函数定义正确",
            "使用二分查找算法",
            "包含边界条件处理",
            "有文档字符串",
        ],
        difficulty="easy",
        domain="技术",
    ),
    EvalTestCase(
        id="code_002",
        task_type="coding",
        task_description="用 Python 实现一个LRU缓存类",
        expected_outputs={"class_name": "LRUCache", "has_eviction": True},
        success_criteria=[
            "类定义完整",
            "实现 get/put 方法",
            "包含淘汰策略",
            "时间复杂度 O(1)",
        ],
        difficulty="medium",
        domain="技术",
    ),
    EvalTestCase(
        id="code_003",
        task_type="coding",
        task_description="修复以下 Python 代码的 bug: 列表去重函数返回结果顺序错误",
        expected_outputs={"fixed": True, "preserves_order": True},
        success_criteria=[
            "修复了 bug",
            "保持原有顺序",
            "代码简洁",
        ],
        difficulty="easy",
        domain="技术",
    ),
    EvalTestCase(
        id="code_004",
        task_type="coding",
        task_description="重构以下代码，使用设计模式提高可读性",
        expected_outputs={"refactored": True, "pattern_used": "strategy"},
        success_criteria=[
            "使用了设计模式",
            "代码更可读",
            "保持原有功能",
        ],
        difficulty="medium",
        domain="技术",
    ),
    EvalTestCase(
        id="code_005",
        task_type="coding",
        task_description="编写单元测试，测试用户登录功能",
        expected_outputs={"test_file": "test_login.py", "coverage": ">80%"},
        success_criteria=[
            "测试文件创建",
            "覆盖主要场景",
            "包含边界条件",
        ],
        difficulty="medium",
        domain="技术",
    ),

    # ========== GENERAL 任务 ==========
    EvalTestCase(
        id="gen_001",
        task_type="general",
        task_description="解释什么是机器学习",
        expected_outputs={"format": "markdown", "has_examples": True},
        success_criteria=[
            "解释清晰",
            "包含例子",
            "适合初学者",
        ],
        difficulty="easy",
        domain="通用",
    ),
    EvalTestCase(
        id="gen_002",
        task_type="general",
        task_description="帮我写一封商业邮件，询问产品合作事宜",
        expected_outputs={"format": "email", "tone": "professional"},
        success_criteria=[
            "格式正确",
            "语气专业",
            "内容完整",
        ],
        difficulty="easy",
        domain="业务",
    ),
    EvalTestCase(
        id="gen_003",
        task_type="general",
        task_description="总结以下文章的主要观点",
        expected_outputs={"summary_length": "<200字"},
        success_criteria=[
            "概括核心观点",
            "简洁明了",
            "保留关键信息",
        ],
        difficulty="easy",
        domain="通用",
    ),
    EvalTestCase(
        id="gen_004",
        task_type="general",
        task_description="用比喻解释量子计算的基本原理",
        expected_outputs={"has_analogy": True, "accurate": True},
        success_criteria=[
            "使用比喻",
            "原理准确",
            "通俗易懂",
        ],
        difficulty="medium",
        domain="通用",
    ),

    # ========== RESEARCH 任务 ==========
    EvalTestCase(
        id="res_001",
        task_type="research",
        task_description="调研当前最流行的 React 状态管理方案",
        expected_outputs={"report": "markdown", "sources": ">3"},
        success_criteria=[
            "包含多个方案对比",
            "有优缺点分析",
            "引用可靠来源",
        ],
        difficulty="medium",
        domain="技术",
    ),
    EvalTestCase(
        id="res_002",
        task_type="research",
        task_description="搜索并总结 AI Agent 评估的最佳实践",
        expected_outputs={"format": "report", "has_examples": True},
        success_criteria=[
            "包含实践方法",
            "有具体案例",
            "来源可靠",
        ],
        difficulty="medium",
        domain="技术",
    ),
    EvalTestCase(
        id="res_003",
        task_type="research",
        task_description="调查 Python 异步编程的现状和发展趋势",
        expected_outputs={"format": "report", "trend_analysis": True},
        success_criteria=[
            "分析现状",
            "预测趋势",
            "有数据支持",
        ],
        difficulty="hard",
        domain="技术",
    ),

    # ========== WEB_SCRAPING 任务 ==========
    EvalTestCase(
        id="scrape_001",
        task_type="web_scraping",
        task_description="爬取知乎热榜前10个问题的标题和链接",
        expected_outputs={"file": "output/zhihu_hot.json", "count": 10},
        success_criteria=[
            "获取前10问题",
            "包含标题和链接",
            "保存到 JSON 文件",
        ],
        difficulty="medium",
        domain="技术",
    ),
    EvalTestCase(
        id="scrape_002",
        task_type="web_scraping",
        task_description="爬取天气网站，获取北京未来3天的天气信息",
        expected_outputs={"file": "output/weather.json", "days": 3},
        success_criteria=[
            "获取3天天气",
            "包含温度和天气状况",
            "保存到文件",
        ],
        difficulty="easy",
        domain="技术",
    ),
    EvalTestCase(
        id="scrape_003",
        task_type="web_scraping",
        task_description="爬取小红书热榜前10的帖子信息与评论",
        expected_outputs={"file": "output/xiaohongshu/posts.json", "count": 10},
        success_criteria=[
            "获取前10帖子",
            "包含评论数据",
            "数据保存到文件",
        ],
        difficulty="hard",
        domain="技术",
    ),

    # ========== DATA_PROCESSING 任务 ==========
    EvalTestCase(
        id="data_001",
        task_type="data_processing",
        task_description="分析 CSV 文件中的销售数据，计算月度销售额",
        expected_outputs={"output_file": "output/monthly_sales.csv"},
        success_criteria=[
            "读取 CSV 文件",
            "计算月度汇总",
            "输出结果文件",
        ],
        difficulty="medium",
        domain="业务",
    ),
    EvalTestCase(
        id="data_002",
        task_type="data_processing",
        task_description="将 JSON 数据转换为 Excel 格式",
        expected_outputs={"output_file": "output/data.xlsx"},
        success_criteria=[
            "读取 JSON",
            "转换为 Excel",
            "保留格式",
        ],
        difficulty="easy",
        domain="业务",
    ),
    EvalTestCase(
        id="data_003",
        task_type="data_processing",
        task_description="清洗日志文件，提取错误信息并统计",
        expected_outputs={"output_file": "output/errors.json", "stats": True},
        success_criteria=[
            "提取错误行",
            "统计错误类型",
            "输出分析结果",
        ],
        difficulty="medium",
        domain="技术",
    ),

    # ========== FILE_OPERATIONS 任务 ==========
    EvalTestCase(
        id="file_001",
        task_type="file_operations",
        task_description="创建一个 README.md 文件，包含项目说明",
        expected_outputs={"file": "README.md", "has_sections": True},
        success_criteria=[
            "文件创建成功",
            "包含必要章节",
            "格式规范",
        ],
        difficulty="easy",
        domain="通用",
    ),
    EvalTestCase(
        id="file_002",
        task_type="file_operations",
        task_description="批量重命名目录中的图片文件，按序号排列",
        expected_outputs={"renamed_count": ">0"},
        success_criteria=[
            "文件重命名",
            "按序号排列",
            "保持扩展名",
        ],
        difficulty="easy",
        domain="技术",
    ),
    EvalTestCase(
        id="file_003",
        task_type="file_operations",
        task_description="合并多个文本文件到一个文件",
        expected_outputs={"output_file": "output/merged.txt"},
        success_criteria=[
            "读取所有文件",
            "合并内容",
            "保存到新文件",
        ],
        difficulty="easy",
        domain="通用",
    ),
]


def get_test_cases_by_type(task_type: str) -> list[EvalTestCase]:
    """按任务类型获取测试用例"""
    return [tc for tc in EVALUATION_DATASET if tc.task_type == task_type]


def get_test_cases_by_difficulty(difficulty: str) -> list[EvalTestCase]:
    """按难度获取测试用例"""
    return [tc for tc in EVALUATION_DATASET if tc.difficulty == difficulty]


def get_test_case_by_id(test_id: str) -> EvalTestCase | None:
    """根据 ID 获取测试用例"""
    for tc in EVALUATION_DATASET:
        if tc.id == test_id:
            return tc
    return None


def get_dataset_stats() -> dict[str, Any]:
    """获取数据集统计"""
    stats = {
        "total": len(EVALUATION_DATASET),
        "by_type": {},
        "by_difficulty": {},
        "by_domain": {},
    }

    for tc in EVALUATION_DATASET:
        # by_type
        stats["by_type"][tc.task_type] = stats["by_type"].get(tc.task_type, 0) + 1
        # by_difficulty
        stats["by_difficulty"][tc.difficulty] = stats["by_difficulty"].get(tc.difficulty, 0) + 1
        # by_domain
        stats["by_domain"][tc.domain] = stats["by_domain"].get(tc.domain, 0) + 1

    return stats


if __name__ == "__main__":
    # 打印数据集统计
    stats = get_dataset_stats()
    print("=" * 50)
    print("Evaluation Dataset Statistics")
    print("=" * 50)
    print(f"Total test cases: {stats['total']}")
    print("\nBy task type:")
    for task_type, count in stats["by_type"].items():
        print(f"  {task_type}: {count}")
    print("\nBy difficulty:")
    for difficulty, count in stats["by_difficulty"].items():
        print(f"  {difficulty}: {count}")
    print("\nBy domain:")
    for domain, count in stats["by_domain"].items():
        print(f"  {domain}: {count}")
