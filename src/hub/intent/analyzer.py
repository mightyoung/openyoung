"""
Intent Analyzer - LLM 意图理解
使用 LLM 分析用户输入，理解真实意图，推荐合适的 Agent
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(Enum):
    """意图类型"""

    CODE = "code"  # 代码开发
    REVIEW = "review"  # 代码审查
    RESEARCH = "research"  # 调研研究
    DEBUG = "debug"  # 调试修复
    REFACTOR = "refactor"  # 重构优化
    TEST = "test"  # 编写测试
    DEPLOY = "deploy"  # 部署发布
    DATA = "data"  # 数据处理
    DOCUMENT = "document"  # 文档编写
    IMPORT = "import"  # 导入/安装 Agent
    SEARCH = "search"  # 搜索发现
    GENERAL = "general"  # 通用任务
    UNKNOWN = "unknown"  # 未知


@dataclass
class Intent:
    """用户意图"""

    type: IntentType
    confidence: float  # 0-1
    description: str
    keywords: list[str] = field(default_factory=list)
    suggested_agents: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)


class IntentAnalyzer:
    """意图分析器

    功能：
    1. 使用 LLM 分析用户输入
    2. 识别意图类型
    3. 推荐合适的 Agent
    """

    # 意图关键词映射
    INTENT_KEYWORDS = {
        IntentType.CODE: [
            "写",
            "实现",
            "开发",
            "创建",
            "编写",
            "code",
            "write",
            "implement",
            "create",
            "build",
        ],
        IntentType.REVIEW: ["审查", "review", "检查", "看", "审阅", "review code"],
        IntentType.RESEARCH: ["调研", "研究", "搜索", "查找", "调查", "research", "search", "find"],
        IntentType.DEBUG: ["调试", "修复", "错误", "bug", "debug", "fix", "error", "问题"],
        IntentType.REFACTOR: ["重构", "优化", "改进", "refactor", "optimize", "improve"],
        IntentType.TEST: ["测试", "test", "单元测试", "写测试"],
        IntentType.DEPLOY: ["部署", "发布", "deploy", "release", "上线"],
        IntentType.DATA: ["数据", "处理", "分析", "data", "process", "analyze"],
        IntentType.DOCUMENT: ["文档", "说明", "写", "document", "docs", "readme"],
        IntentType.IMPORT: ["导入", "安装", "import", "install", "clone", "下载"],
        IntentType.SEARCH: ["找", "搜索", "发现", "search", "find", "discover", "agent"],
    }

    # Agent 推荐映射
    AGENT_RECOMMENDATIONS = {
        IntentType.CODE: ["agent-coder", "claude-code", "my-agent"],
        IntentType.REVIEW: ["agent-reviewer", "claude-code"],
        IntentType.RESEARCH: ["agent-researcher", "everything-claude"],
        IntentType.DEBUG: ["agent-coder", "claude-code"],
        IntentType.REFACTOR: ["agent-coder", "claude-code"],
        IntentType.TEST: ["agent-coder", "test-agent"],
        IntentType.DEPLOY: ["claude-code", "claude-flow"],
        IntentType.DATA: ["claude-code", "everything-claude"],
        IntentType.DOCUMENT: ["claude-code", "default"],
        IntentType.IMPORT: ["default"],
        IntentType.SEARCH: ["default"],
    }

    def __init__(self, llm_client=None):
        self._llm = llm_client

    async def analyze(self, user_input: str) -> Intent:
        """分析用户意图

        Args:
            user_input: 用户输入

        Returns:
            Intent: 识别出的意图
        """
        # 1. 快速关键词匹配
        quick_intent = self._quick_match(user_input)
        if quick_intent:
            return quick_intent

        # 2. 使用 LLM 深度分析
        if self._llm:
            return await self._llm_analyze(user_input)

        # 3. 回退到通用意图
        return Intent(
            type=IntentType.GENERAL,
            confidence=0.5,
            description="通用任务",
            suggested_agents=["default"],
        )

    def _quick_match(self, user_input: str) -> Intent | None:
        """快速关键词匹配

        用于简单场景的快速响应
        """
        user_input_lower = user_input.lower()
        matches = []

        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in user_input_lower)
            if count > 0:
                matches.append((intent_type, count))

        if not matches:
            return None

        # 选择匹配最多的意图
        matches.sort(key=lambda x: x[1], reverse=True)
        best_type, best_count = matches[0]

        confidence = min(best_count * 0.3, 0.9)

        return Intent(
            type=best_type,
            confidence=confidence,
            description=self._get_intent_description(best_type, user_input),
            keywords=self._extract_keywords(user_input, best_type),
            suggested_agents=self.AGENT_RECOMMENDATIONS.get(best_type, ["default"]),
            required_capabilities=self._get_required_capabilities(best_type),
        )

    async def _llm_analyze(self, user_input: str) -> Intent:
        """使用 LLM 深度分析意图"""
        prompt = f"""分析以下用户输入，识别其意图：

用户输入：{user_input}

请返回 JSON 格式的分析结果：
{{
    "type": "code|review|research|debug|refactor|test|deploy|data|document|import|search|general",
    "confidence": 0.0-1.0,
    "description": "简短描述用户想要做什么",
    "required_capabilities": ["需要的技能列表"]
}}

只返回 JSON，不要其他内容。"""

        try:
            response = await self._llm.chat([{"role": "user", "content": prompt}])
            result = json.loads(response)

            intent_type = IntentType(result.get("type", "general"))
            return Intent(
                type=intent_type,
                confidence=result.get("confidence", 0.8),
                description=result.get("description", ""),
                suggested_agents=self.AGENT_RECOMMENDATIONS.get(intent_type, ["default"]),
                required_capabilities=result.get("required_capabilities", []),
            )
        except Exception as e:
            print(f"[IntentAnalyzer] LLM error: {e}")
            return Intent(
                type=IntentType.GENERAL,
                confidence=0.5,
                description="通用任务",
                suggested_agents=["default"],
            )

    def _get_intent_description(self, intent_type: IntentType, user_input: str) -> str:
        """获取意图描述"""
        descriptions = {
            IntentType.CODE: "需要编写或开发代码",
            IntentType.REVIEW: "需要审查或检查代码",
            IntentType.RESEARCH: "需要调研或搜索信息",
            IntentType.DEBUG: "需要调试或修复问题",
            IntentType.REFACTOR: "需要重构或优化代码",
            IntentType.TEST: "需要编写测试",
            IntentType.DEPLOY: "需要部署或发布",
            IntentType.DATA: "需要处理或分析数据",
            IntentType.DOCUMENT: "需要编写文档",
            IntentType.IMPORT: "需要导入或安装 Agent",
            IntentType.SEARCH: "需要搜索或发现 Agent",
            IntentType.GENERAL: "通用任务",
        }
        return descriptions.get(intent_type, "通用任务")

    def _extract_keywords(self, user_input: str, intent_type: IntentType) -> list[str]:
        """提取关键词"""
        import re

        # 提取中英文单词
        keywords = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]{2,}", user_input)
        return keywords[:5]

    def _get_required_capabilities(self, intent_type: IntentType) -> list[str]:
        """获取所需能力"""
        capabilities = {
            IntentType.CODE: ["coding", "file_edit", "bash"],
            IntentType.REVIEW: ["code_analysis", "read"],
            IntentType.RESEARCH: ["search", "web_fetch", "read"],
            IntentType.DEBUG: ["code_analysis", "bash", "read"],
            IntentType.REFACTOR: ["coding", "code_analysis"],
            IntentType.TEST: ["coding", "bash"],
            IntentType.DEPLOY: ["bash", "file_edit"],
            IntentType.DATA: ["bash", "file_edit"],
            IntentType.DOCUMENT: ["write", "read"],
            IntentType.IMPORT: ["github_api", "file_edit"],
            IntentType.SEARCH: ["search"],
        }
        return capabilities.get(intent_type, [])

    async def recommend_agents(self, user_input: str) -> list[dict[str, Any]]:
        """推荐 Agent

        Args:
            user_input: 用户输入

        Returns:
            List[Dict]: 推荐 Agent 列表，包含匹配度原因
        """
        intent = await self.analyze(user_input)

        recommendations = []
        for agent_name in intent.suggested_agents:
            recommendations.append(
                {
                    "agent": agent_name,
                    "match_reason": f"适合 {intent.description}",
                    "confidence": intent.confidence,
                    "intent_type": intent.type.value,
                }
            )

        return recommendations


# ========== 便捷函数 ==========


def create_analyzer(llm_client=None) -> IntentAnalyzer:
    """创建意图分析器"""
    return IntentAnalyzer(llm_client)


async def analyze_intent(user_input: str) -> Intent:
    """分析用户意图（快速版本）"""
    analyzer = IntentAnalyzer()
    return await analyzer.analyze(user_input)
