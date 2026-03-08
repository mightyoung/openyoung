"""
Evaluation Dashboard - 评估仪表板

对标 LangSmith Comparison View，提供：
- 评估结果对比视图
- 趋势分析
- 多维度统计

参考 LangSmith 设计：
- Comparison View: 并排比较多个评估结果
- Metrics View: 多维度指标展示
- Trending View: 历史趋势分析
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .hub import EvaluationHub, EvaluationResult


@dataclass
class ComparisonResult:
    """对比结果"""

    left_id: str
    right_id: str
    left_score: float
    right_score: float
    score_diff: float
    winner: str  # "left", "right", "tie"


@dataclass
class DashboardMetrics:
    """仪表板指标"""

    total_evaluations: int
    average_score: float
    pass_rate: float
    median_score: float
    std_dev: float
    trend: str  # "up", "down", "stable"
    trend_delta: float


@dataclass
class TrendPoint:
    """趋势数据点"""

    timestamp: datetime
    score: float
    count: int


class EvalDashboard:
    """评估仪表板

    提供评估结果的对比和趋势分析功能
    """

    def __init__(self, hub: Optional[EvaluationHub] = None):
        self._hub = hub or EvaluationHub()

    @property
    def hub(self) -> EvaluationHub:
        """获取评估中心"""
        return self._hub

    def get_metrics(self) -> DashboardMetrics:
        """获取仪表板指标

        Returns:
            仪表板指标
        """
        results = self._hub.get_results()

        if not results:
            return DashboardMetrics(
                total_evaluations=0,
                average_score=0.0,
                pass_rate=0.0,
                median_score=0.0,
                std_dev=0.0,
                trend="stable",
                trend_delta=0.0,
            )

        scores = [r.score for r in results]

        # 计算统计数据
        avg_score = sum(scores) / len(scores)
        median_score = sorted(scores)[len(scores) // 2]
        pass_count = sum(1 for s in scores if s >= 0.7)
        pass_rate = pass_count / len(scores)

        # 计算标准差
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # 计算趋势 (最近5个 vs 之前5个)
        trend = "stable"
        trend_delta = 0.0

        if len(results) >= 10:
            recent = scores[-5:]
            previous = scores[-10:-5]
            recent_avg = sum(recent) / len(recent)
            previous_avg = sum(previous) / len(previous)
            trend_delta = recent_avg - previous_avg

            if trend_delta > 0.05:
                trend = "up"
            elif trend_delta < -0.05:
                trend = "down"

        return DashboardMetrics(
            total_evaluations=len(results),
            average_score=avg_score,
            pass_rate=pass_rate,
            median_score=median_score,
            std_dev=std_dev,
            trend=trend,
            trend_delta=trend_delta,
        )

    def compare(
        self,
        left_id: int,
        right_id: int,
    ) -> ComparisonResult:
        """对比两个评估结果

        Args:
            left_id: 左侧结果索引
            right_id: 右侧结果索引

        Returns:
            对比结果
        """
        results = self._hub.get_results()

        if left_id < 0 or left_id >= len(results):
            raise ValueError(f"Invalid left_id: {left_id}")
        if right_id < 0 or right_id >= len(results):
            raise ValueError(f"Invalid right_id: {right_id}")

        left = results[left_id]
        right = results[right_id]

        score_diff = right.score - left.score

        if score_diff > 0.01:
            winner = "right"
        elif score_diff < -0.01:
            winner = "left"
        else:
            winner = "tie"

        return ComparisonResult(
            left_id=str(left_id),
            right_id=str(right_id),
            left_score=left.score,
            right_score=right.score,
            score_diff=score_diff,
            winner=winner,
        )

    def compare_multiple(self, ids: list[int]) -> list[ComparisonResult]:
        """对比多个评估结果

        Args:
            ids: 结果索引列表

        Returns:
            对比结果列表
        """
        if len(ids) < 2:
            raise ValueError("Need at least 2 IDs to compare")

        results = self._hub.get_results()
        comparisons = []

        # 以第一个为基准，逐一对比
        base_id = ids[0]
        base_result = results[base_id]

        for i in range(1, len(ids)):
            compare_id = ids[i]
            compare_result = results[compare_id]

            score_diff = compare_result.score - base_result.score

            if score_diff > 0.01:
                winner = f"id_{compare_id}"
            elif score_diff < -0.01:
                winner = f"id_{base_id}"
            else:
                winner = "tie"

            comparisons.append(
                ComparisonResult(
                    left_id=str(base_id),
                    right_id=str(compare_id),
                    left_score=base_result.score,
                    right_score=compare_result.score,
                    score_diff=score_diff,
                    winner=winner,
                )
            )

        return comparisons

    def get_trend(self, limit: int = 20) -> list[TrendPoint]:
        """获取评估趋势

        Args:
            limit: 返回数据点数量

        Returns:
            趋势数据点列表
        """
        results = self._hub.get_results()

        if not results:
            return []

        # 取最近的 limit 个结果
        recent = results[-limit:] if len(results) > limit else results

        return [
            TrendPoint(
                timestamp=r.timestamp,
                score=r.score,
                count=1,
            )
            for r in recent
        ]

    def get_dimension_trend(self, dimension: str, limit: int = 20) -> list[TrendPoint]:
        """获取特定维度的趋势

        Args:
            dimension: 维度名称
            limit: 返回数据点数量

        Returns:
            趋势数据点列表
        """
        results = self._hub.get_results()

        # 过滤特定维度的结果
        filtered = [r for r in results if r.metric == dimension]

        if not filtered:
            return []

        recent = filtered[-limit:] if len(filtered) > limit else filtered

        return [
            TrendPoint(
                timestamp=r.timestamp,
                score=r.score,
                count=1,
            )
            for r in recent
        ]

    def get_summary(self) -> dict[str, Any]:
        """获取评估摘要

        Returns:
            评估摘要
        """
        results = self._hub.get_results()
        metrics = self.get_metrics()

        # 按指标分组统计
        by_metric: dict[str, dict[str, Any]] = {}

        for r in results:
            metric = r.metric
            if metric not in by_metric:
                by_metric[metric] = {
                    "count": 0,
                    "scores": [],
                    "avg_score": 0.0,
                }

            by_metric[metric]["count"] += 1
            by_metric[metric]["scores"].append(r.score)

        # 计算每个指标的平均分
        for metric, data in by_metric.items():
            scores = data["scores"]
            data["avg_score"] = sum(scores) / len(scores) if scores else 0.0

        return {
            "metrics": {
                "total": metrics.total_evaluations,
                "average_score": metrics.average_score,
                "pass_rate": metrics.pass_rate,
                "median_score": metrics.median_score,
                "std_dev": metrics.std_dev,
                "trend": metrics.trend,
                "trend_delta": metrics.trend_delta,
            },
            "by_dimension": by_metric,
            "recent_trend": [
                {"timestamp": tp.timestamp.isoformat(), "score": tp.score}
                for tp in self.get_trend(10)
            ],
        }

    def export_comparison_report(
        self,
        left_id: int,
        right_id: int,
        format: str = "text",
    ) -> str:
        """导出对比报告

        Args:
            left_id: 左侧结果索引
            right_id: 右侧结果索引
            format: 报告格式 (text/json)

        Returns:
            格式化的报告
        """
        results = self._hub.get_results()

        if left_id < 0 or left_id >= len(results):
            raise ValueError(f"Invalid left_id: {left_id}")
        if right_id < 0 or right_id >= len(results):
            raise ValueError(f"Invalid right_id: {right_id}")

        left = results[left_id]
        right = results[right_id]
        comparison = self.compare(left_id, right_id)

        if format == "json":
            import json

            return json.dumps(
                {
                    "left": {
                        "id": left_id,
                        "metric": left.metric,
                        "score": left.score,
                        "success": left.success,
                        "timestamp": left.timestamp.isoformat(),
                    },
                    "right": {
                        "id": right_id,
                        "metric": right.metric,
                        "score": right.score,
                        "success": right.success,
                        "timestamp": right.timestamp.isoformat(),
                    },
                    "comparison": {
                        "score_diff": comparison.score_diff,
                        "winner": comparison.winner,
                    },
                },
                indent=2,
            )

        # Text format
        left_status = "✅" if left.success else "❌"
        right_status = "✅" if right.success else "❌"

        lines = []
        lines.append("=" * 60)
        lines.append("EVALUATION COMPARISON REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"{'Metric':<20} {'Left (ID:' + str(left_id) + ')':<20} {'Right (ID:' + str(right_id) + ')':<20}")
        lines.append("-" * 60)
        lines.append(
            f"{'Score':<20} {left.score:.4f} {left_status:<18} {right.score:.4f} {right_status}"
        )
        lines.append(
            f"{'Success':<20} {str(left.success):<20} {str(right.success):<20}"
        )
        lines.append("-" * 60)
        lines.append(f"{'Difference:':<20} {comparison.score_diff:+.4f}")
        lines.append(f"{'Winner:':<20} {comparison.winner}")
        lines.append("=" * 60)

        return "\n".join(lines)


# ========== Convenience Functions ==========


def create_dashboard(hub: Optional[EvaluationHub] = None) -> EvalDashboard:
    """创建评估仪表板"""
    return EvalDashboard(hub)
