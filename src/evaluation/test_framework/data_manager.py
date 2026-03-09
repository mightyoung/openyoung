"""
Test Data Manager - 测试数据管理

管理测试数据集：
- 预设测试集
- 真实任务采样
- 数据加载
"""

from dataclasses import dataclass
from typing import Any, Optional

from .models import Difficulty, TaskType, TestCase, TestSuite

# 预设测试数据集
# 50+ 场景，覆盖主要任务类型
PRESET_DATASET = {
    "default": [
        # ========== 代码生成 (10 cases) ==========
        TestCase(
            id="code_gen_001",
            task_description="用 Python 写一个函数，计算列表的平均值",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["python", "函数", "平均"],
            validation_rules={"output_contains": {"required": ["def", "return", "sum"]}},
        ),
        TestCase(
            id="code_gen_002",
            task_description="实现一个快速排序算法",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["快速排序", "算法"],
            validation_rules={"output_contains": {"required": ["def", "quick"]}},
        ),
        TestCase(
            id="code_gen_003",
            task_description="写一个 Python 类来表示银行账户",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["class", "银行", "账户"],
            validation_rules={"output_contains": {"required": ["class"]}},
        ),
        TestCase(
            id="code_gen_004",
            task_description="用 Python 实现一个二分查找函数",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["二分查找", "算法"],
            validation_rules={"output_contains": {"required": ["def", "return"]}},
        ),
        TestCase(
            id="code_gen_005",
            task_description="写一个函数来合并两个有序列表",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["合并", "有序", "列表"],
            validation_rules={"output_contains": {"required": ["def", "return"]}},
        ),
        # ========== 代码修复 (8 cases) ==========
        TestCase(
            id="code_fix_001",
            task_description="这个函数有 bug，帮我修一下：def add(a,b): return a-b",
            task_type=TaskType.CODE_FIX,
            expected_intent="code_fix",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["bug", "修复", "错误"],
        ),
        TestCase(
            id="code_fix_002",
            task_description="修复这个无限循环：while True: print('hello')",
            task_type=TaskType.CODE_FIX,
            expected_intent="code_fix",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["无限循环", "修复"],
        ),
        TestCase(
            id="code_fix_003",
            task_description="这段代码有空指针错误，帮我修复",
            task_type=TaskType.CODE_FIX,
            expected_intent="code_fix",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["空指针", "None", "修复"],
        ),
        # ========== 文本生成 (8 cases) ==========
        TestCase(
            id="text_gen_001",
            task_description="写一篇关于 AI 发展的博客文章",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="markdown",
            difficulty=Difficulty.MEDIUM,
            keywords=["AI", "发展", "文章"],
        ),
        TestCase(
            id="text_gen_002",
            task_description="用 Python 写一个生成随机密码的函数",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["密码", "随机", "生成"],
            validation_rules={"output_contains": {"required": ["def", "random"]}},
        ),
        TestCase(
            id="text_gen_003",
            task_description="解释一下什么是 REST API",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["REST", "API", "解释"],
        ),
        TestCase(
            id="text_gen_004",
            task_description="写一封求职邮件",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["求职", "邮件"],
        ),
        # ========== 数据处理 (6 cases) ==========
        TestCase(
            id="data_001",
            task_description="分析这个 CSV 文件并给出统计摘要",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["CSV", "分析", "统计"],
        ),
        TestCase(
            id="data_002",
            task_description="计算这个列表的平均值和最大值：[1,2,3,4,5,6,7,8,9,10]",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["平均", "最大", "计算"],
        ),
        TestCase(
            id="data_003",
            task_description="把这个 JSON 数据按某个字段排序",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="json",
            difficulty=Difficulty.MEDIUM,
            keywords=["排序", "JSON"],
        ),
        # ========== 信息查询 (6 cases) ==========
        TestCase(
            id="query_001",
            task_description="Python 异步编程的最佳实践是什么?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Python", "异步", "最佳实践"],
        ),
        TestCase(
            id="query_002",
            task_description="什么是 CQRS 模式?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["CQRS", "模式"],
        ),
        TestCase(
            id="query_003",
            task_description="查找 GitHub 上最火的 Python 项目",
            task_type=TaskType.INFORMATION_QUERY,
            expected_intent="information_query",
            expected_output_format="text",
            difficulty=Difficulty.HARD,
            keywords=["GitHub", "Python", "项目"],
        ),
        # ========== 任务执行 (6 cases) ==========
        TestCase(
            id="exec_001",
            task_description="运行项目中的所有测试",
            task_type=TaskType.TASK_EXECUTION,
            expected_intent="task_execution",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["运行", "测试"],
        ),
        TestCase(
            id="exec_002",
            task_description="执行这个 Python 脚本",
            task_type=TaskType.TASK_EXECUTION,
            expected_intent="task_execution",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["执行", "脚本"],
        ),
        # ========== 问题解答 (8 cases) ==========
        TestCase(
            id="qa_001",
            task_description="什么是机器学习?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["机器学习", "解释"],
        ),
        TestCase(
            id="qa_002",
            task_description="解释什么是 Docker 容器",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["Docker", "容器", "解释"],
        ),
        TestCase(
            id="qa_003",
            task_description="什么是微服务架构?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["微服务", "架构"],
        ),
        TestCase(
            id="qa_004",
            task_description="如何优化 Python 代码性能?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Python", "性能", "优化"],
        ),
        # ========== 代码生成 (15 cases) ==========
        TestCase(
            id="code_gen_006",
            task_description="用 Python 写一个递归函数计算阶乘",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["递归", "阶乘"],
            validation_rules={"output_contains": {"required": ["def", "return"]}},
        ),
        TestCase(
            id="code_gen_007",
            task_description="实现一个栈数据结构类",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["栈", "stack", "class"],
            validation_rules={"output_contains": {"required": ["class", "push", "pop"]}},
        ),
        TestCase(
            id="code_gen_008",
            task_description="写一个 Python 函数来检查回文数",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["回文", "palindrome"],
            validation_rules={"output_contains": {"required": ["def"]}},
        ),
        TestCase(
            id="code_gen_009",
            task_description="实现一个链表数据结构",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["链表", "linked list", "class"],
            validation_rules={"output_contains": {"required": ["class", "Node"]}},
        ),
        TestCase(
            id="code_gen_010",
            task_description="写一个生成斐波那契数列的函数",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["斐波那契", "fibonacci"],
            validation_rules={"output_contains": {"required": ["def"]}},
        ),
        # ========== 代码修复 (5 cases) ==========
        TestCase(
            id="code_fix_004",
            task_description="这段代码有索引越界错误，请修复",
            task_type=TaskType.CODE_FIX,
            expected_intent="code_fix",
            expected_output_format="python_code",
            difficulty=Difficulty.MEDIUM,
            keywords=["索引", "越界", "修复"],
        ),
        TestCase(
            id="code_fix_005",
            task_description="修复这个除零错误",
            task_type=TaskType.CODE_FIX,
            expected_intent="code_fix",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["除零", "ZeroDivision", "修复"],
        ),
        # ========== 代码审查 (3 cases) ==========
        TestCase(
            id="code_review_001",
            task_description="审查这段代码并提出改进建议",
            task_type=TaskType.CODE_REVIEW,
            expected_intent="code_review",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["审查", "review", "改进"],
        ),
        TestCase(
            id="code_review_002",
            task_description="检查这段代码是否有安全漏洞",
            task_type=TaskType.CODE_REVIEW,
            expected_intent="code_review",
            expected_output_format="text",
            difficulty=Difficulty.HARD,
            keywords=["安全", "漏洞", "审查"],
        ),
        # ========== 文本生成 (5 cases) ==========
        TestCase(
            id="text_gen_005",
            task_description="写一封商务邮件邀请客户",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["邮件", "商务", "邀请"],
        ),
        TestCase(
            id="text_gen_006",
            task_description="创作一个关于AI的短故事",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["故事", "AI", "创作"],
        ),
        TestCase(
            id="text_gen_007",
            task_description="写一段产品描述文案",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["产品", "描述", "文案"],
        ),
        # ========== 数据处理 (3 cases) ==========
        TestCase(
            id="data_004",
            task_description="对这个列表进行去重并排序：[3,1,4,1,5,9,2,6]",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["去重", "排序", "列表"],
        ),
        TestCase(
            id="data_005",
            task_description="统计这段文本中每个单词出现的次数",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["统计", "单词", "次数"],
        ),
        # ========== 信息查询 (4 cases) ==========
        TestCase(
            id="query_004",
            task_description="查找 Docker 和 Kubernetes 的区别",
            task_type=TaskType.INFORMATION_QUERY,
            expected_intent="information_query",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Docker", "Kubernetes", "区别"],
        ),
        TestCase(
            id="query_005",
            task_description="搜索最新的 React 18 新特性",
            task_type=TaskType.INFORMATION_QUERY,
            expected_intent="information_query",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["React", "新特性", "搜索"],
        ),
        # ========== 任务执行 (3 cases) ==========
        TestCase(
            id="exec_003",
            task_description="执行 pytest 运行所有测试",
            task_type=TaskType.TASK_EXECUTION,
            expected_intent="task_execution",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["pytest", "执行", "测试"],
        ),
        TestCase(
            id="exec_004",
            task_description="启动这个 Flask 应用",
            task_type=TaskType.TASK_EXECUTION,
            expected_intent="task_execution",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["启动", "Flask", "应用"],
        ),
        # ========== 问题解答 (5 cases) ==========
        TestCase(
            id="qa_005",
            task_description="什么是微服务架构?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["微服务", "架构"],
        ),
        TestCase(
            id="qa_006",
            task_description="Docker 容器和虚拟机有什么区别?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Docker", "虚拟机", "区别"],
        ),
        TestCase(
            id="qa_007",
            task_description="如何提高 Python 代码性能?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Python", "性能", "优化"],
        ),
        TestCase(
            id="qa_008",
            task_description="解释一下 Git 的工作原理",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["Git", "原理", "解释"],
        ),
        # ========== 补充到 50+ ==========
        TestCase(
            id="code_gen_011",
            task_description="用 Python 实现冒泡排序",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["冒泡排序", "bubble sort"],
            validation_rules={"output_contains": {"required": ["def"]}},
        ),
        TestCase(
            id="code_gen_012",
            task_description="写一个 Python 函数判断素数",
            task_type=TaskType.CODE_GENERATION,
            expected_intent="code_generation",
            expected_output_format="python_code",
            difficulty=Difficulty.EASY,
            keywords=["素数", "prime"],
            validation_rules={"output_contains": {"required": ["def"]}},
        ),
        TestCase(
            id="qa_009",
            task_description="什么是对称加密和非对称加密?",
            task_type=TaskType.QUESTION_ANSWERING,
            expected_intent="question_answering",
            expected_output_format="text",
            difficulty=Difficulty.HARD,
            keywords=["加密", "对称", "非对称"],
        ),
        TestCase(
            id="text_gen_008",
            task_description="写一段技术博客介绍 TypeScript",
            task_type=TaskType.TEXT_GENERATION,
            expected_intent="text_generation",
            expected_output_format="text",
            difficulty=Difficulty.MEDIUM,
            keywords=["TypeScript", "技术博客"],
        ),
        TestCase(
            id="data_006",
            task_description="把这两个列表合并成一个字典",
            task_type=TaskType.DATA_PROCESSING,
            expected_intent="data_processing",
            expected_output_format="text",
            difficulty=Difficulty.EASY,
            keywords=["合并", "字典"],
        ),
        # ========== Web 爬取 (10 cases) ==========
        TestCase(
            id="web_001",
            task_description="从小红书上爬取热榜前十的帖子信息与评论",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.HARD,
            keywords=["小红书", "热榜", "爬取"],
            validation_rules={
                "output_contains": {"required": ["title", "author", "likes"]},
                "file_exists": {"path": "output/xiaohongshu/posts.json"},
            },
        ),
        TestCase(
            id="web_002",
            task_description="爬取知乎热榜前20个问题的回答",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.HARD,
            keywords=["知乎", "热榜", "爬取"],
            validation_rules={
                "output_contains": {"required": ["question", "answer"]},
            },
        ),
        TestCase(
            id="web_003",
            task_description="从豆瓣电影 Top250 页面提取电影信息",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.MEDIUM,
            keywords=["豆瓣", "电影", "Top250"],
            validation_rules={
                "output_contains": {"required": ["title", "rating"]},
            },
        ),
        TestCase(
            id="web_004",
            task_description="爬取微博热搜榜前50条",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.HARD,
            keywords=["微博", "热搜", "爬取"],
            validation_rules={
                "output_contains": {"required": ["rank", "title"]},
            },
        ),
        TestCase(
            id="web_005",
            task_description="从B站获取播放量最高的前10个视频信息",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.HARD,
            keywords=["B站", "视频", "播放量"],
            validation_rules={
                "output_contains": {"required": ["title", "view"]},
            },
        ),
        TestCase(
            id="web_006",
            task_description="爬取简书首页推荐文章列表",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.MEDIUM,
            keywords=["简书", "推荐", "文章"],
            validation_rules={
                "output_contains": {"required": ["title", "author"]},
            },
        ),
        TestCase(
            id="web_007",
            task_description="从淘宝获取某商品的评论信息",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.HARD,
            keywords=["淘宝", "商品", "评论"],
            validation_rules={
                "output_contains": {"required": ["comment", "rating"]},
            },
        ),
        TestCase(
            id="web_008",
            task_description="爬取天气预报网站数据",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.EASY,
            keywords=["天气", "预报", "爬取"],
            validation_rules={
                "output_contains": {"required": ["temperature", "weather"]},
            },
        ),
        TestCase(
            id="web_009",
            task_description="从GitHub获取某仓库的Star历史",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.MEDIUM,
            keywords=["GitHub", "Star", "历史"],
            validation_rules={
                "output_contains": {"required": ["date", "stars"]},
            },
        ),
        TestCase(
            id="web_010",
            task_description="爬取Stack Overflow某标签下的热门问题",
            task_type=TaskType.WEB_SCRAPING,
            expected_intent="web_scraping",
            expected_output_format="json",
            difficulty=Difficulty.MEDIUM,
            keywords=["Stack Overflow", "问题", "热门"],
            validation_rules={
                "output_contains": {"required": ["title", "votes"]},
            },
        ),
    ]
}


class TestDataManager:
    """测试数据管理器

    负责加载和管理测试数据
    """

    def __init__(self):
        self.datasets = PRESET_DATASET.copy()

    def load_dataset(self, name: str = "default") -> list[TestCase]:
        """加载测试数据集

        Args:
            name: 数据集名称

        Returns:
            list[TestCase]: 测试用例列表
        """
        return self.datasets.get(name, self.datasets.get("default", []))

    def load_suite(self, suite_name: str, dataset_name: str = "default") -> TestSuite:
        """加载测试套件

        Args:
            suite_name: 套件名称 (unit, integration, e2e)
            dataset_name: 数据集名称

        Returns:
            TestSuite: 测试套件
        """
        test_cases = self.load_dataset(dataset_name)

        # 根据套件类型筛选
        if suite_name == "unit":
            # 单元测试：简单任务
            filtered = [tc for tc in test_cases if tc.difficulty == Difficulty.EASY]
        elif suite_name == "integration":
            # 集成测试：中等难度
            filtered = [tc for tc in test_cases if tc.difficulty == Difficulty.MEDIUM]
        elif suite_name == "e2e":
            # E2E 测试：所有难度
            filtered = test_cases
        else:
            filtered = test_cases

        return TestSuite(
            name=suite_name,
            description=f"{suite_name} test suite",
            test_cases=filtered,
        )

    def get_by_task_type(
        self, task_type: TaskType, dataset_name: str = "default"
    ) -> list[TestCase]:
        """按任务类型获取测试用例"""
        all_cases = self.load_dataset(dataset_name)
        return [tc for tc in all_cases if tc.task_type == task_type]

    def get_by_difficulty(
        self, difficulty: Difficulty, dataset_name: str = "default"
    ) -> list[TestCase]:
        """按难度获取测试用例"""
        all_cases = self.load_dataset(dataset_name)
        return [tc for tc in all_cases if tc.difficulty == difficulty]

    def add_test_case(self, test_case: TestCase, dataset_name: str = "default"):
        """添加测试用例到数据集"""
        if dataset_name not in self.datasets:
            self.datasets[dataset_name] = []
        self.datasets[dataset_name].append(test_case)

    def get_stats(self, dataset_name: str = "default") -> dict:
        """获取数据集统计信息"""
        cases = self.load_dataset(dataset_name)

        # 按任务类型统计
        by_type = {}
        for tc in cases:
            type_name = tc.task_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        # 按难度统计
        by_difficulty = {}
        for tc in cases:
            diff_name = tc.difficulty.value
            by_difficulty[diff_name] = by_difficulty.get(diff_name, 0) + 1

        return {
            "total": len(cases),
            "by_type": by_type,
            "by_difficulty": by_difficulty,
        }
