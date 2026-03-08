"""
Agent Compare - Agent 对比功能
并排比较两个 Agent 的各项指标
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ComparisonDimension(Enum):
    """对比维度"""

    QUALITY = "quality"  # 质量评分
    DOWNLOADS = "downloads"  # 下载/使用次数
    RATING = "rating"  # 评分
    DOCUMENTATION = "documentation"  # 文档完整性
    COMPLETENESS = "completeness"  # 功能完整性
    SECURITY = "security"  # 安全性
    RUNTIME = "runtime"  # 运行时能力


@dataclass
class DimensionResult:
    """单维度对比结果"""

    dimension: str
    agent_a_value: Any
    agent_b_value: Any
    agent_a_score: float
    agent_b_score: float
    winner: str  # "a", "b", "tie"
    reasoning: str


@dataclass
class AgentComparison:
    """Agent 对比结果"""

    agent_a: str
    agent_b: str
    dimensions: list[DimensionResult]
    winner: str | None  # "a", "b", "tie"
    summary: str


class AgentComparer:
    """Agent 对比器"""

    # 维度权重
    DIMENSION_WEIGHTS = {
        ComparisonDimension.QUALITY: 0.30,
        ComparisonDimension.DOWNLOADS: 0.20,
        ComparisonDimension.RATING: 0.15,
        ComparisonDimension.DOCUMENTATION: 0.15,
        ComparisonDimension.COMPLETENESS: 0.10,
        ComparisonDimension.SECURITY: 0.05,
        ComparisonDimension.RUNTIME: 0.05,
    }

    def __init__(self):
        pass

    async def compare(self, agent_a_name: str, agent_b_name: str) -> AgentComparison:
        """对比两个 Agent

        Args:
            agent_a_name: Agent A 名称
            agent_b_name: Agent B 名称

        Returns:
            AgentComparison: 对比结果
        """
        # 获取两个 Agent 的数据
        agent_a_data = await self._get_agent_data(agent_a_name)
        agent_b_data = await self._get_agent_data(agent_b_name)

        if not agent_a_data or not agent_b_data:
            return AgentComparison(
                agent_a=agent_a_name,
                agent_b=agent_b_name,
                dimensions=[],
                winner=None,
                summary="One or both agents not found",
            )

        # 对比各维度
        results = []

        # 1. 质量评分对比
        results.append(self._compare_quality(agent_a_data, agent_b_data))

        # 2. 下载/使用次数对比
        results.append(self._compare_downloads(agent_a_data, agent_b_data))

        # 3. 评分对比
        results.append(self._compare_rating(agent_a_data, agent_b_data))

        # 4. 文档完整性对比
        results.append(self._compare_documentation(agent_a_data, agent_b_data))

        # 5. 功能完整性对比
        results.append(self._compare_completeness(agent_a_data, agent_b_data))

        # 6. 安全性对比
        results.append(self._compare_security(agent_a_data, agent_b_data))

        # 7. 运行时能力对比
        results.append(self._compare_runtime(agent_a_data, agent_b_data))

        # 计算总体胜出者
        a_wins = sum(1 for r in results if r.winner == "a")
        b_wins = sum(1 for r in results if r.winner == "b")

        if a_wins > b_wins:
            winner = "a"
            summary = f"{agent_a_name} 赢得 {a_wins}/{len(results)} 个维度"
        elif b_wins > a_wins:
            winner = "b"
            summary = f"{agent_b_name} 赢得 {b_wins}/{len(results)} 个维度"
        else:
            winner = "tie"
            summary = f"平局 - 各赢得 {a_wins}/{len(results)} 个维度"

        return AgentComparison(
            agent_a=agent_a_name,
            agent_b=agent_b_name,
            dimensions=results,
            winner=winner,
            summary=summary,
        )

    async def _get_agent_data(self, agent_name: str) -> dict | None:
        """获取 Agent 数据"""
        from src.package_manager.agent_evaluator import AgentEvaluator
        from src.package_manager.base_registry import BaseRegistry
        from src.package_manager.registry import AgentRegistry

        # 获取评估数据
        evaluator = AgentEvaluator()
        try:
            report = await evaluator.evaluate(f"packages/{agent_name}")
        except:
            report = None

        # 获取使用统计
        registry = AgentRegistry("packages")
        stats = registry.get_usage_stats(100)
        downloads = 0
        for s in stats:
            if s.get("name") == agent_name:
                downloads = s.get("use_count", 0)
                break

        # 获取评分
        base = BaseRegistry("packages")
        ratings = base.get_ratings("agent_ratings.db")
        rating = ratings.get(agent_name, 0.0)

        return {
            "name": agent_name,
            "quality_score": report.overall_score if report else 0,
            "downloads": downloads,
            "rating": rating,
            "dimensions": {
                d.dimension.value: d.score for d in (report.dimensions if report else [])
            },
        }

    def _compare_quality(self, a: dict, b: dict) -> DimensionResult:
        """对比质量评分"""
        a_score = a.get("quality_score", 0)
        b_score = b.get("quality_score", 0)

        return DimensionResult(
            dimension="Quality",
            agent_a_value=f"{a_score:.2f}",
            agent_b_value=f"{b_score:.2f}",
            agent_a_score=a_score,
            agent_b_score=b_score,
            winner="a" if a_score > b_score else "b" if b_score > a_score else "tie",
            reasoning=f"质量评分 {a_score:.2f} vs {b_score:.2f}",
        )

    def _compare_downloads(self, a: dict, b: dict) -> DimensionResult:
        """对比下载/使用次数"""
        a_count = a.get("downloads", 0)
        b_count = b.get("downloads", 0)

        return DimensionResult(
            dimension="Downloads",
            agent_a_value=str(a_count),
            agent_b_value=str(b_count),
            agent_a_score=min(a_count / 100, 1.0),
            agent_b_score=min(b_count / 100, 1.0),
            winner="a" if a_count > b_count else "b" if b_count > a_count else "tie",
            reasoning=f"使用次数 {a_count} vs {b_count}",
        )

    def _compare_rating(self, a: dict, b: dict) -> DimensionResult:
        """对比评分"""
        a_rating = a.get("rating", 0)
        b_rating = b.get("rating", 0)

        return DimensionResult(
            dimension="Rating",
            agent_a_value=f"{a_rating:.1f}",
            agent_b_value=f"{b_rating:.1f}",
            agent_a_score=a_rating / 5.0,
            agent_b_score=b_rating / 5.0,
            winner="a" if a_rating > b_rating else "b" if b_rating > a_rating else "tie",
            reasoning=f"用户评分 {a_rating:.1f} vs {b_rating:.1f}",
        )

    def _compare_documentation(self, a: dict, b: dict) -> DimensionResult:
        """对比文档完整性"""
        a_score = a.get("dimensions", {}).get("documentation", 0)
        b_score = b.get("dimensions", {}).get("documentation", 0)

        return DimensionResult(
            dimension="Documentation",
            agent_a_value=f"{a_score:.2f}",
            agent_b_value=f"{b_score:.2f}",
            agent_a_score=a_score,
            agent_b_score=b_score,
            winner="a" if a_score > b_score else "b" if b_score > a_score else "tie",
            reasoning=f"文档评分 {a_score:.2f} vs {b_score:.2f}",
        )

    def _compare_completeness(self, a: dict, b: dict) -> DimensionResult:
        """对比功能完整性"""
        a_score = a.get("dimensions", {}).get("completeness", 0)
        b_score = b.get("dimensions", {}).get("completeness", 0)

        return DimensionResult(
            dimension="Completeness",
            agent_a_value=f"{a_score:.2f}",
            agent_b_value=f"{b_score:.2f}",
            agent_a_score=a_score,
            agent_b_score=b_score,
            winner="a" if a_score > b_score else "b" if b_score > a_score else "tie",
            reasoning=f"完整性评分 {a_score:.2f} vs {b_score:.2f}",
        )

    def _compare_security(self, a: dict, b: dict) -> DimensionResult:
        """对比安全性"""
        a_score = a.get("dimensions", {}).get("security", 0)
        b_score = b.get("dimensions", {}).get("security", 0)

        return DimensionResult(
            dimension="Security",
            agent_a_value=f"{a_score:.2f}",
            agent_b_value=f"{b_score:.2f}",
            agent_a_score=a_score,
            agent_b_score=b_score,
            winner="a" if a_score > b_score else "b" if b_score > a_score else "tie",
            reasoning=f"安全性评分 {a_score:.2f} vs {b_score:.2f}",
        )

    def _compare_runtime(self, a: dict, b: dict) -> DimensionResult:
        """对比运行时能力"""
        a_score = a.get("dimensions", {}).get("runtime", 0)
        b_score = b.get("dimensions", {}).get("runtime", 0)

        return DimensionResult(
            dimension="Runtime",
            agent_a_value=f"{a_score:.2f}",
            agent_b_value=f"{b_score:.2f}",
            agent_a_score=a_score,
            agent_b_score=b_score,
            winner="a" if a_score > b_score else "b" if b_score > a_score else "tie",
            reasoning=f"运行时评分 {a_score:.2f} vs {b_score:.2f}",
        )


# ========== 便捷函数 ==========


async def compare_agents(agent_a: str, agent_b: str) -> AgentComparison:
    """对比两个 Agent"""
    comparer = AgentComparer()
    return await comparer.compare(agent_a, agent_b)
