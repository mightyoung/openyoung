"""
DataAnalytics - 数据分析
提供统计分析和趋势分析功能
使用 BaseStorage 基类
"""

from datetime import datetime, timedelta
from pathlib import Path

from .base_storage import BaseStorage


class DataAnalytics(BaseStorage):
    """数据分析"""

    def __init__(self, data_dir: str = ".young"):
        # 延迟初始化 db_path，等 runs.db 存在后再设置
        self.data_dir = Path(data_dir)
        self._db_path = str(self.data_dir / "runs.db")
        # 不调用 super().__init__()，因为可能数据库还不存在

    @property
    def db_path(self) -> str:
        """获取数据库路径"""
        return self._db_path

    def _ensure_db_exists(self) -> bool:
        """检查数据库是否存在"""
        return Path(self._db_path).exists()

    def _init_db(self) -> None:
        """Analytics 不需要建表，只是查询"""
        pass

    def _get_stats(self, query: str, params: list = None) -> list:
        """执行查询并返回结果"""
        if not self._ensure_db_exists():
            return []

        return self._execute(query, tuple(params) if params else None, fetch=True) or []

    def get_agent_stats(self, agent_id: str, days: int = 7) -> dict:
        """获取 Agent 统计数据"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration) as avg_duration,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens
            FROM runs
            WHERE agent_id = ? AND started_at >= ?
        """

        rows = self._get_stats(query, [agent_id, start_date])

        if not rows or rows[0].get("total", 0) == 0:
            return {
                "agent_id": agent_id,
                "period_days": days,
                "total_runs": 0,
                "success": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
            }

        row = rows[0]
        total = row.get("total", 0) or 0
        success = row.get("success", 0) or 0

        return {
            "agent_id": agent_id,
            "period_days": days,
            "total_runs": total,
            "success": success,
            "failed": row.get("failed", 0) or 0,
            "success_rate": round(success / total, 3) if total > 0 else 0.0,
            "avg_duration": round(row.get("avg_duration") or 0, 2),
            "total_input_tokens": row.get("input_tokens") or 0,
            "total_output_tokens": row.get("output_tokens") or 0,
        }

    def get_task_stats(self, task_type: str = None, days: int = 7) -> dict:
        """获取任务类型统计"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        # 简化：按任务关键词分组
        query = """
            SELECT
                SUBSTR(task, 1, 30) as task_prefix,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                AVG(duration) as avg_duration
            FROM runs
            WHERE started_at >= ?
            GROUP BY task_prefix
            ORDER BY total DESC
            LIMIT 20
        """

        rows = self._get_stats(query, [start_date])

        tasks = []
        total_runs = 0

        for row in rows:
            task_runs = row.get("total", 0) or 0
            total_runs += task_runs
            tasks.append(
                {
                    "task_prefix": row.get("task_prefix"),
                    "total_runs": task_runs,
                    "success": row.get("success", 0) or 0,
                    "avg_duration": round(row.get("avg_duration") or 0, 2),
                }
            )

        return {
            "period_days": days,
            "total_runs": total_runs,
            "task_count": len(tasks),
            "tasks": tasks,
        }

    def get_trends(self, metric: str = "runs", days: int = 30) -> list[dict]:
        """获取趋势数据"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        if metric == "runs":
            query = """
                SELECT
                    DATE(started_at) as date,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success
                FROM runs
                WHERE started_at >= ?
                GROUP BY DATE(started_at)
                ORDER BY date
            """
        elif metric == "duration":
            query = """
                SELECT
                    DATE(started_at) as date,
                    AVG(duration) as avg_duration
                FROM runs
                WHERE started_at >= ? AND duration IS NOT NULL
                GROUP BY DATE(started_at)
                ORDER BY date
            """
        elif metric == "tokens":
            query = """
                SELECT
                    DATE(started_at) as date,
                    SUM(input_tokens) as input_tokens,
                    SUM(output_tokens) as output_tokens
                FROM runs
                WHERE started_at >= ?
                GROUP BY DATE(started_at)
                ORDER BY date
            """
        else:
            return []

        rows = self._get_stats(query, [start_date])

        trends = []
        for row in rows:
            if metric == "runs":
                trends.append(
                    {
                        "date": row.get("date"),
                        "count": row.get("count", 0),
                        "success": row.get("success", 0) or 0,
                    }
                )
            elif metric == "duration":
                trends.append(
                    {
                        "date": row.get("date"),
                        "avg_duration": round(row.get("avg_duration") or 0, 2),
                    }
                )
            elif metric == "tokens":
                trends.append(
                    {
                        "date": row.get("date"),
                        "input_tokens": row.get("input_tokens") or 0,
                        "output_tokens": row.get("output_tokens") or 0,
                    }
                )

        return trends

    def get_dashboard(self) -> dict:
        """获取仪表盘数据"""
        # 总览统计
        if not self._ensure_db_exists():
            return {
                "summary": {
                    "total_agents": 0,
                    "total_runs": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                },
                "recent_runs": [],
                "charts": {},
            }

        # 获取 agent 数量
        rows = self._execute("SELECT COUNT(DISTINCT agent_id) as count FROM runs", fetch=True)
        total_agents = rows[0].get("count", 0) if rows else 0

        rows = self._execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                AVG(duration) as avg_duration
            FROM runs
        """,
            fetch=True,
        )

        if not rows:
            return {
                "summary": {
                    "total_agents": total_agents,
                    "total_runs": 0,
                    "success_rate": 0.0,
                    "avg_duration": 0.0,
                },
                "recent_runs": [],
                "charts": {},
            }

        row = rows[0]
        total_runs = row.get("total", 0) or 0
        success = row.get("success", 0) or 0
        avg_duration = row.get("avg_duration") or 0

        # 最近运行
        rows = self._execute(
            """
            SELECT run_id, agent_id, task, status, duration, started_at
            FROM runs
            ORDER BY started_at DESC
            LIMIT 10
        """,
            fetch=True,
        )

        recent_runs = []
        for r in rows:
            recent_runs.append(
                {
                    "run_id": r.get("run_id"),
                    "agent_id": r.get("agent_id"),
                    "task": r.get("task"),
                    "status": r.get("status"),
                    "duration": round(r.get("duration") or 0, 2),
                    "started_at": r.get("started_at"),
                }
            )

        # 获取趋势数据
        runs_trend = self.get_trends("runs", days=7)

        return {
            "summary": {
                "total_agents": total_agents,
                "total_runs": total_runs,
                "success_rate": round(success / total_runs, 3) if total_runs > 0 else 0.0,
                "avg_duration": round(avg_duration, 2),
            },
            "recent_runs": recent_runs,
            "charts": {"runs_per_day": runs_trend},
        }


# ========== 便捷函数 ==========


def get_data_analytics(data_dir: str = ".young") -> DataAnalytics:
    """获取数据分析实例"""
    return DataAnalytics(data_dir)
