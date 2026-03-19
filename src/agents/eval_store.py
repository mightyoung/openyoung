"""
Lightweight Evaluation Store

提取自 young_agent.py 的 _EvalStore 类。
用于替代 src.evaluation.hub.EvaluationHub 的轻量级内存评估存储。
Evaluation functionality is now handled by the Harness system (src/hub/evaluate/).
"""

from typing import Any


class EvalStore:
    """Lightweight in-memory evaluation store.

    Replaces src.evaluation.hub.EvaluationHub for young_agent.py.
    Evaluation functionality is now handled by the Harness system (src/hub/evaluate/).
    This store keeps a simple in-memory list for API compatibility.
    """

    def __init__(self):
        self._results: list[dict[str, Any]] = []

    def add_result(self, result: dict[str, Any]) -> None:
        """添加评估结果"""
        self._results.append(result)

    def get_latest_result(self) -> dict[str, Any] | None:
        """获取最新评估结果"""
        return self._results[-1] if self._results else None

    def get_results(self) -> list[dict[str, Any]]:
        """获取所有评估结果"""
        return self._results

    def get_trend(self, limit: int = 10) -> dict[str, Any]:
        """获取评估趋势数据

        Args:
            limit: 返回最近 N 条记录

        Returns:
            趋势数据字典
        """
        results = self._results[-limit:] if self._results else []
        if not results:
            return {"error": "No evaluation results yet"}
        return {
            "trend": [r.get("score", 0) for r in results],
            "task_types": [r.get("task_type", "unknown") for r in results],
            "count": len(results),
        }
