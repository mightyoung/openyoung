"""
Task Matcher - 任务匹配与路由

基于能力匹配的任务路由系统
使用多阶段匹配策略：快速召回 → 能力过滤 → 重排序
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from src.package_manager.agent_retriever import AgentRetriever, SearchMode

logger = logging.getLogger(__name__)


class MatchStrategy(Enum):
    """匹配策略"""

    FAST = "fast"  # 快速模式 - 仅关键词
    ACCURATE = "accurate"  # 精确模式 - 向量语义
    HYBRID = "hybrid"  # 混合模式 - 最佳效果


@dataclass
class TaskRequirements:
    """任务需求"""

    description: str
    required_capabilities: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    max_latency_ms: Optional[int] = None
    min_success_rate: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchResult:
    """匹配结果"""

    agent_name: str
    agent_spec: Any
    score: float
    match_type: str  # "exact", "capability", "keyword", "fallback"
    reasoning: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TaskMatcher:
    """
    任务匹配器

    使用多阶段匹配策略：
    1. Stage 1: 快速召回 - 使用关键词快速获取候选
    2. Stage 2: 能力过滤 - 过滤掉不满足需求的Agent
    3. Stage 3: 重排序 - 使用语义相似度重排序
    """

    def __init__(
        self,
        retriever: Optional[AgentRetriever] = None,
        strategy: MatchStrategy = MatchStrategy.HYBRID,
    ):
        self._retriever = retriever or AgentRetriever()
        self._strategy = strategy

    async def match(
        self,
        task: TaskRequirements,
        top_k: int = 5,
    ) -> list[MatchResult]:
        """
        匹配任务到最佳Agent

        Args:
            task: 任务需求
            top_k: 返回前k个最佳匹配

        Returns:
            list[MatchResult]: 排序后的匹配结果
        """
        results = []

        # Stage 1: 快速召回
        candidates = await self._recall_candidates(task, top_k * 3)
        if not candidates:
            logger.warning(f"No candidates found for task: {task.description[:50]}...")
            return []

        # Stage 2: 能力过滤
        filtered = self._filter_by_capabilities(candidates, task)
        if not filtered:
            # 如果没有精确匹配，回退到所有候选
            filtered = candidates

        # Stage 3: 计算匹配分数并排序
        for agent_spec in filtered:
            match_result = self._calculate_match_score(agent_spec, task)
            results.append(match_result)

        # 排序返回
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    async def match_single(
        self,
        task: TaskRequirements,
    ) -> Optional[MatchResult]:
        """匹配单个最佳Agent"""
        matches = await self.match(task, top_k=1)
        return matches[0] if matches else None

    async def _recall_candidates(self, task: TaskRequirements, limit: int) -> list[Any]:
        """Stage 1: 快速召回候选"""
        # 根据策略选择搜索模式
        if self._strategy == MatchStrategy.FAST:
            mode = SearchMode.KEYWORD
        elif self._strategy == MatchStrategy.ACCURATE:
            mode = SearchMode.SEMANTIC
        else:
            mode = SearchMode.HYBRID

        # 构建查询
        query = task.description
        if task.required_capabilities:
            query += " " + " ".join(task.required_capabilities)

        # 搜索
        try:
            result = await self._retriever.search(
                query=query,
                mode=mode,
                limit=limit,
                filters={"tags": task.tags, "tools": task.required_tools}
                if task.tags or task.required_tools
                else None,
            )
            return result.agents
        except Exception as e:
            logger.error(f"Candidate recall error: {e}")
            return []

    def _filter_by_capabilities(self, candidates: list[Any], task: TaskRequirements) -> list[Any]:
        """Stage 2: 能力过滤"""
        if not task.required_capabilities:
            return candidates

        filtered = []
        for agent in candidates:
            # 检查是否满足能力要求
            agent_caps = getattr(agent, "capabilities", []) or []
            if any(cap in agent_caps for cap in task.required_capabilities):
                filtered.append(agent)

        return filtered if filtered else candidates

    def _calculate_match_score(self, agent_spec: Any, task: TaskRequirements) -> MatchResult:
        """Stage 3: 计算匹配分数"""
        score = 0.0
        match_type = "fallback"
        reasoning_parts = []

        # 1. 关键词匹配
        keyword_score = self._keyword_match_score(task.description, agent_spec)
        if keyword_score > 0:
            score += keyword_score * 0.3
            reasoning_parts.append(f"keyword={keyword_score:.2f}")

        # 2. 能力匹配
        capability_score = self._capability_match_score(task.required_capabilities, agent_spec)
        if capability_score > 0:
            score += capability_score * 0.4
            reasoning_parts.append(f"capability={capability_score:.2f}")
            match_type = "capability"

        # 3. 工具匹配
        tool_score = self._tool_match_score(task.required_tools, agent_spec)
        if tool_score > 0:
            score += tool_score * 0.3
            reasoning_parts.append(f"tools={tool_score:.2f}")

        # 4. 检查是否是精确匹配
        if task.required_capabilities and capability_score >= 1.0:
            match_type = "exact"
            reasoning_parts.append("exact_match")

        # 归一化分数
        score = min(score, 1.0)

        return MatchResult(
            agent_name=getattr(agent_spec, "name", "unknown"),
            agent_spec=agent_spec,
            score=score,
            match_type=match_type,
            reasoning=", ".join(reasoning_parts) if reasoning_parts else "default",
            metadata={
                "description": getattr(agent_spec, "description", ""),
                "tags": getattr(agent_spec, "tags", []),
            },
        )

    def _keyword_match_score(self, query: str, agent_spec: Any) -> float:
        """计算关键词匹配分数"""
        score = 0.0
        query_lower = query.lower()

        # name匹配
        agent_name = getattr(agent_spec, "name", "").lower()
        if query_lower in agent_name:
            score += 1.0

        # description匹配
        agent_desc = getattr(agent_spec, "description", "").lower()
        if query_lower in agent_desc:
            score += 0.5

        # tags匹配
        agent_tags = getattr(agent_spec, "tags", [])
        for tag in agent_tags:
            if isinstance(tag, str) and query_lower in tag.lower():
                score += 0.3

        return min(score, 1.0)

    def _capability_match_score(self, required: list[str], agent_spec: Any) -> float:
        """计算能力匹配分数"""
        if not required:
            return 0.5  # 无要求时给予中等分数

        agent_caps = getattr(agent_spec, "capabilities", []) or []
        if not agent_caps:
            return 0.0

        matches = sum(1 for cap in required if cap in agent_caps)
        return matches / len(required)

    def _tool_match_score(self, required: list[str], agent_spec: Any) -> float:
        """计算工具匹配分数"""
        if not required:
            return 0.3  # 无要求时给予基础分数

        agent_tools = getattr(agent_spec, "tools", []) or []
        if not agent_tools:
            return 0.0

        matches = sum(1 for tool in required if tool in agent_tools)
        return matches / len(required)

    # ========== 便捷方法 ==========

    async def list_available_agents(self) -> list[str]:
        """列出所有可用Agent"""
        agents = await self._retriever.list_all()
        return [getattr(a, "name", "unknown") for a in agents]


# ========== 便捷函数 ==========


def create_matcher(strategy: MatchStrategy = MatchStrategy.HYBRID) -> TaskMatcher:
    """创建TaskMatcher实例"""
    return TaskMatcher(strategy=strategy)


async def match_task(
    task_description: str,
    required_capabilities: Optional[list[str]] = None,
    strategy: MatchStrategy = MatchStrategy.HYBRID,
) -> Optional[MatchResult]:
    """快速匹配任务（单行API）"""
    task = TaskRequirements(
        description=task_description,
        required_capabilities=required_capabilities or [],
    )
    matcher = create_matcher(strategy)
    return await matcher.match_single(task)
