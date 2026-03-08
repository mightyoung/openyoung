"""
EvaluationHub - 评估中心
整合所有评估器
"""

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .code_eval import CodeEval
from .indexer import EvalDimension, EvalLevel, EvalPackage, IndexBuilder
from .llm_judge import LLMJudgeEval
from .metrics import (
    BUILTIN_METRICS,
)
from .planner import EvalPlan, EvalPlanner
from .safety_eval import SafetyEval
from .task_eval import TaskCompletionEval


@dataclass
class EvaluationResult:
    """评估结果"""

    metric: str
    score: float
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    evaluator: str = "unknown"


class EvaluationHub:
    """评估中心 - 管理和执行评估

    整合 CodeEval, TaskCompletionEval, LLMJudgeEval, SafetyEval
    提供统一的评估接口
    """

    # 评估专用模型配置
    EVALUATION_MODEL = os.getenv("OPENYOUNG_EVAL_MODEL", "qwen-plus")

    def __init__(self, llm_client=None):
        self._metrics: dict[str, Callable] = {}
        self._results: list[EvaluationResult] = []
        self._packages: dict[str, Any] = {}

        # 评估使用专门的模型
        eval_client = llm_client
        if not eval_client:
            from src.llm.client_adapter import LLMClient

            eval_client = LLMClient()

        # Initialize index builder first (needed for packages)
        self._index_builder = IndexBuilder()

        # Initialize evaluators - 评估使用 qwen 模型
        self._evaluators = {
            "code": CodeEval(),
            "task": TaskCompletionEval(),
            "llm_judge": LLMJudgeEval(eval_client),
            "safety": SafetyEval(),
        }

        # P3-6: 初始化内置评估包注册表
        self._builtin_packages: dict[str, Any] = {}
        self._register_builtin_packages(eval_client)

        # Initialize eval planner
        self._eval_planner = EvalPlanner()

        # Initialize plugin registry
        self._plugin_registry = None
        self._init_plugin_registry()

    def _init_plugin_registry(self):
        """初始化插件注册中心"""
        try:
            from .plugins import PluginRegistry
            self._plugin_registry = PluginRegistry()
        except ImportError:
            self._plugin_registry = None

    def _register_builtin_packages(self, eval_client):
        """注册内置评估包

        将内置评估器注册为包，便于通过统一的包接口访问
        """
        from .indexer import EvalDimension, EvalLevel

        # 创建内置评估包
        self._builtin_packages = {
            "builtin-correctness": {
                "name": "builtin-correctness",
                "version": "1.0.0",
                "dimension": EvalDimension.CORRECTNESS,
                "level": EvalLevel.UNIT,
                "description": "Built-in correctness evaluator",
                "evaluators": [self._evaluators.get("code"), self._evaluators.get("task")],
            },
            "builtin-safety": {
                "name": "builtin-safety",
                "version": "1.0.0",
                "dimension": EvalDimension.SAFETY,
                "level": EvalLevel.UNIT,
                "description": "Built-in safety evaluator",
                "evaluators": [self._evaluators.get("safety")],
            },
            "builtin-quality": {
                "name": "builtin-quality",
                "version": "1.0.0",
                "dimension": EvalDimension.EFFICIENCY,
                "level": EvalLevel.INTEGRATION,
                "description": "Built-in LLM judge evaluator",
                "evaluators": [self._evaluators.get("llm_judge")],
            },
        }

        # 注册到索引构建器
        for pkg_info in self._builtin_packages.values():
            from .indexer import EvalPackage

            pkg = EvalPackage(
                name=pkg_info["name"],
                version=pkg_info["version"],
                dimension=pkg_info["dimension"],
                level=pkg_info["level"],
                description=pkg_info["description"],
            )
            self._index_builder.register_package(pkg)

    async def generate_plan(self, task_description: str) -> EvalPlan:
        """生成评估计划

        Args:
            task_description: 任务描述

        Returns:
            评估计划 (EvalPlan)
        """
        return await self._eval_planner.generate_plan(task_description)

    def register_metric(self, name: str, func: Callable):
        """注册评估指标"""
        self._metrics[name] = func

    def register_package(self, name: str, package: Any):
        """注册评估包"""
        self._packages[name] = package

    def register_evaluator(self, name: str, evaluator: Any):
        """注册自定义评估器"""
        self._evaluators[name] = evaluator

    async def evaluate(
        self,
        metric: str,
        input_data: Any,
        evaluator_type: str = "task",
    ) -> EvaluationResult:
        """执行评估

        Args:
            metric: 指标名称
            input_data: 输入数据
            evaluator_type: 评估器类型 (code/task/llm_judge/safety)

        Returns:
            评估结果
        """
        # 1. 尝试使用自定义指标
        if metric in self._metrics:
            func = self._metrics[metric]
            score = await func(input_data) if callable(func) else 0.0
            result = EvaluationResult(
                metric=metric,
                score=score,
                evaluator="custom",
            )
            self._results.append(result)
            return result

        # 2. 使用内置评估器
        evaluator = self._evaluators.get(evaluator_type)
        if not evaluator:
            return EvaluationResult(
                metric=metric,
                score=0.0,
                details={"error": f"Evaluator not found: {evaluator_type}"},
                evaluator="error",
            )

        try:
            result = await self._run_evaluator(evaluator, evaluator_type, metric, input_data)
            self._results.append(result)
            return result
        except Exception as e:
            return EvaluationResult(
                metric=metric,
                score=0.0,
                details={"error": str(e)},
                evaluator=evaluator_type,
            )

    async def evaluate_full(
        self,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """全面评估 - 运行所有评估器

        Args:
            input_data: 包含所有评估所需数据的字典

        Returns:
            完整的评估报告
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0.0,
            "dimensions": {},
            "results": [],
        }

        # Code Evaluation
        if "code" in input_data:
            code_result = await self.evaluate(
                metric="code_quality",
                input_data=input_data["code"],
                evaluator_type="code",
            )
            report["dimensions"]["correctness"] = code_result.score
            report["results"].append(code_result)

        # Task Completion Evaluation
        if "task" in input_data:
            task_result = await self.evaluate(
                metric="task_completion",
                input_data=input_data["task"],
                evaluator_type="task",
            )
            report["dimensions"]["efficacy"] = task_result.score
            report["results"].append(task_result)

        # LLM Judge Evaluation
        if "llm_judge" in input_data:
            judge_result = await self.evaluate(
                metric="quality",
                input_data=input_data["llm_judge"],
                evaluator_type="llm_judge",
            )
            report["dimensions"]["quality"] = judge_result.score
            report["results"].append(judge_result)

        # Safety Evaluation
        if "safety" in input_data:
            safety_result = await self.evaluate(
                metric="safety_score",
                input_data=input_data["safety"],
                evaluator_type="safety",
            )
            report["dimensions"]["safety"] = safety_result.score
            report["results"].append(safety_result)

        # 计算总体评分
        if report["dimensions"]:
            report["overall_score"] = sum(report["dimensions"].values()) / len(report["dimensions"])

        return report

    async def _run_evaluator(
        self,
        evaluator: Any,
        evaluator_type: str,
        metric: str,
        input_data: Any,
    ) -> EvaluationResult:
        """运行评估器"""

        if evaluator_type == "code":
            result = await evaluator.evaluate(
                code=input_data.get("code", ""),
                expected_output=input_data.get("expected_output"),
                test_cases=input_data.get("test_cases"),
                language=input_data.get("language", "python"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("overall_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "task":
            # 检查是否有评估计划
            eval_plan = input_data.get("eval_plan")
            if eval_plan:
                result = await evaluator.evaluate_with_plan(
                    task_description=input_data.get("description", ""),
                    actual_result=input_data.get("actual"),
                    eval_plan=eval_plan,
                    execution_trace=input_data.get("trace"),
                )
            else:
                result = await evaluator.evaluate(
                    task_description=input_data.get("description", ""),
                    expected_result=input_data.get("expected"),
                    actual_result=input_data.get("actual"),
                    execution_trace=input_data.get("trace"),
                )
            return EvaluationResult(
                metric=metric,
                score=result.get("overall_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "llm_judge":
            result = await evaluator.evaluate(
                input_text=input_data.get("input", ""),
                output_text=input_data.get("output", ""),
                expected_output=input_data.get("expected"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("average_score", 0.0) / 5.0,  # 转换为 0-1
                details=result,
                evaluator=evaluator_type,
            )

        elif evaluator_type == "safety":
            result = await evaluator.evaluate(
                output_text=input_data.get("output", ""),
                input_text=input_data.get("input"),
            )
            return EvaluationResult(
                metric=metric,
                score=result.get("safety_score", 0.0),
                details=result,
                evaluator=evaluator_type,
            )

        return EvaluationResult(
            metric=metric,
            score=0.0,
            details={"error": f"Unknown evaluator type: {evaluator_type}"},
            evaluator="error",
        )

    def list_metrics(self) -> list[str]:
        """列出所有指标"""
        return list(self._metrics.keys()) + list(BUILTIN_METRICS.keys())

    def list_packages(self) -> list[str]:
        """列出所有评估包"""
        return list(self._packages.keys())

    def list_evaluators(self) -> list[str]:
        """列出所有评估器"""
        return list(self._evaluators.keys())

    def optimize_agent_config(
        self, agent_name: str, eval_result: EvaluationResult
    ) -> dict[str, Any]:
        """根据评估结果优化 agent 配置

        Args:
            agent_name: Agent 名称
            eval_result: 评估结果

        Returns:
            配置更新字典，包含 model, temperature, max_tokens 等
        """
        config_updates = {
            "model": None,
            "temperature": None,
            "max_tokens": None,
            "reason": "",
        }

        score = eval_result.score
        details = eval_result.details or {}

        # 低分优化策略
        if score < 0.5:
            config_updates["model"] = "gpt-4o"
            config_updates["temperature"] = 0.3
            config_updates["reason"] = f"Low score ({score:.2f}) - switched to more capable model"
        elif score < 0.7:
            # 轻微调整温度
            new_temp = max(0.1, score - 0.3)
            config_updates["temperature"] = new_temp
            config_updates["reason"] = f"Medium score ({score:.2f}) - adjusted temperature"

        # 执行效率优化
        step_efficiency = details.get("step_efficiency", 1.0)
        if step_efficiency > 0.8:
            config_updates["max_tokens"] = 8192
            config_updates["reason"] += " | High efficiency - increased token limit"

        # 延迟优化
        latency_ms = details.get("latency_ms", 0)
        if latency_ms > 10000:  # 超过 10 秒
            config_updates["max_tokens"] = 2048  # 减少 token 限制以加速
            config_updates["reason"] += " | High latency - reduced token limit"

        return config_updates

    def get_latest_result(self) -> EvaluationResult | None:
        """获取最新的评估结果"""
        return self._results[-1] if self._results else None

    # ========== 历史评估追踪 ==========

    def _get_db_path(self) -> Path:
        """获取数据库路径"""
        import os
        from pathlib import Path

        data_dir = Path(os.getenv("OPENYOUNG_DATA", ".young"))
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "evaluation_history.db"

    def save_history(self, agent_name: str, eval_result: EvaluationResult) -> bool:
        """保存评估历史到 SQLite"""
        import sqlite3

        db_path = self._get_db_path()
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    score REAL NOT NULL,
                    evaluator TEXT,
                    details TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            # 插入记录
            cursor.execute(
                """
                INSERT INTO evaluation_history
                (agent_name, metric, score, evaluator, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    agent_name,
                    eval_result.metric,
                    eval_result.score,
                    eval_result.evaluator,
                    str(eval_result.details),
                    eval_result.timestamp.isoformat(),
                ),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[EvaluationHub] Save history error: {e}")
            return False

    def get_history(self, agent_name: str, limit: int = 10) -> list[dict[str, Any]]:
        """获取评估历史"""
        import sqlite3

        db_path = self._get_db_path()
        if not db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM evaluation_history
                WHERE agent_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (agent_name, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "metric": row["metric"],
                        "score": row["score"],
                        "evaluator": row["evaluator"],
                        "details": row["details"],
                        "timestamp": row["timestamp"],
                    }
                )

            conn.close()
            return results
        except Exception as e:
            print(f"[EvaluationHub] Get history error: {e}")
            return []

    def get_trend(self, agent_name: str, metric: str = None) -> dict[str, Any]:
        """获取评估趋势"""
        import sqlite3

        db_path = self._get_db_path()
        if not db_path.exists():
            return {}

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            if metric:
                cursor.execute(
                    """
                    SELECT score, timestamp FROM evaluation_history
                    WHERE agent_name = ? AND metric = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """,
                    (agent_name, metric),
                )
            else:
                cursor.execute(
                    """
                    SELECT score, timestamp FROM evaluation_history
                    WHERE agent_name = ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """,
                    (agent_name,),
                )

            scores = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not scores:
                return {}

            return {
                "count": len(scores),
                "average": sum(scores) / len(scores),
                "max": max(scores),
                "min": min(scores),
                "latest": scores[0],
                "scores": scores,
            }
        except Exception as e:
            print(f"[EvaluationHub] Get trend error: {e}")
            return {}

    async def evaluate_with_plugins(
        self,
        task_description: str,
        task_type: str,
        output_data: Any,
        plugins: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """使用插件系统进行评估

        Args:
            task_description: 任务描述
            task_type: 任务类型
            output_data: 输出数据
            plugins: 要使用的插件名称列表，None 表示全部

        Returns:
            评估结果字典
        """
        if not self._plugin_registry:
            return {
                "error": "Plugin registry not initialized",
                "results": []
            }

        try:
            from .plugins import EvalContext

            # 创建评估上下文
            context = EvalContext(
                task_description=task_description,
                task_type=task_type,
                output_data=output_data,
            )

            # 运行插件评估
            results = self._plugin_registry.evaluate_all(context, plugins)

            # 转换为字典格式
            return {
                "results": [r.to_dict() for r in results],
                "summary": {
                    "total": len(results),
                    "passed": sum(1 for r in results if r.passed),
                    "failed": sum(1 for r in results if not r.passed),
                    "average_score": sum(r.score for r in results) / len(results) if results else 0,
                }
            }
        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }

    def get_results(self) -> list[EvaluationResult]:
        """获取评估结果"""
        return self._results

    def get_results_by_metric(self, metric: str) -> list[EvaluationResult]:
        """获取指定指标的结果"""
        return [r for r in self._results if r.metric == metric]

    def clear_results(self):
        """清空评估结果"""
        self._results.clear()

    def save_results(self, filepath: str) -> None:
        """保存评估结果到JSON文件"""
        import json
        from pathlib import Path

        data = []
        for r in self._results:
            data.append(
                {
                    "metric": r.metric,
                    "score": r.score,
                    "details": r.details,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "evaluator": r.evaluator,
                }
            )
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_results(self, filepath: str) -> None:
        """从JSON文件加载评估结果"""
        import json
        from pathlib import Path

        if not Path(filepath).exists():
            return
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            result = EvaluationResult(
                metric=item.get("metric", ""),
                score=item.get("score", 0.0),
                details=item.get("details", {}),
                timestamp=datetime.fromisoformat(item["timestamp"])
                if item.get("timestamp")
                else datetime.now(),
                evaluator=item.get("evaluator", "unknown"),
            )
            self._results.append(result)

    def clear_results(self):
        """清空评估结果"""
        self._results.clear()

    def get_trend(self, limit: int = 10) -> dict:
        """获取评估趋势数据

        Args:
            limit: 返回最近 N 条记录

        Returns:
            趋势数据字典
        """
        if not self._results:
            return {
                "count": 0,
                "average_score": 0.0,
                "scores": [],
                "task_types": {},
            }

        recent = self._results[-limit:] if len(self._results) > limit else self._results

        # 计算统计数据
        scores = [r.score for r in recent]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # 按任务类型统计
        task_types = {}
        for r in recent:
            task_type = r.details.get("task_type", "unknown") if r.details else "unknown"
            if task_type not in task_types:
                task_types[task_type] = {"count": 0, "total_score": 0.0}
            task_types[task_type]["count"] += 1
            task_types[task_type]["total_score"] += r.score

        # 计算每个任务类型的平均分
        for tt in task_types:
            count = task_types[tt]["count"]
            task_types[tt]["avg_score"] = (
                task_types[tt]["total_score"] / count if count > 0 else 0.0
            )
            del task_types[tt]["total_score"]

        return {
            "count": len(self._results),
            "recent_count": len(recent),
            "average_score": avg_score,
            "scores": scores,
            "task_types": task_types,
            "latest_score": recent[-1].score if recent else 0.0,
        }

    def register_eval_package(self, package: EvalPackage):
        """注册评估包到索引"""
        self._index_builder.register_package(package)

    def search_packages(
        self,
        feature_codes: list[str] = None,
        dimension: EvalDimension = None,
        level: EvalLevel = None,
    ) -> list[Any]:
        """搜索评估包

        Args:
            feature_codes: 特征码列表
            dimension: 评估维度
            level: 评估层级

        Returns:
            匹配的评估包列表（包括内置包字典）
        """
        # 先从索引获取包
        indexed_packages = self._index_builder.search(
            dimension=dimension,
            level=level,
            tags=feature_codes,
        )

        # 合并内置包
        results = list(indexed_packages)

        # 添加匹配的内置包
        for pkg_name, pkg_dict in self._builtin_packages.items():
            # 如果指定了维度/层级过滤
            if dimension and pkg_dict.get("dimension") != dimension:
                continue
            if level and pkg_dict.get("level") != level:
                continue
            # 添加到结果（作为字典）
            results.append(pkg_dict)

        return results

    def load_evaluators(self, package: EvalPackage) -> list[Any]:
        """从包中加载评估器

        Args:
            package: 评估包

        Returns:
            评估器实例列表
        """
        evaluators = []

        # 如果包是字典（内置包）
        if isinstance(package, dict):
            evaluators = package.get("evaluators", [])
            return [e for e in evaluators if e is not None]

        # 如果包有 evaluator_classes，使用它
        if hasattr(package, "evaluator_classes"):
            for evaluator_class in package.evaluator_classes:
                try:
                    evaluator = evaluator_class()
                    evaluators.append(evaluator)
                except Exception as e:
                    print(f"[EvaluationHub] Failed to load evaluator: {e}")

        # 如果包有 evaluators 属性
        elif hasattr(package, "evaluators"):
            evaluators = package.evaluators

        return evaluators

    def search_eval_packages(
        self, dimension: EvalDimension = None, level: EvalLevel = None, tags: list[str] = None
    ) -> list[EvalPackage]:
        """搜索评估包"""
        return self._index_builder.search(dimension, level, tags)

    def get_eval_package(self, name: str) -> EvalPackage:
        """获取评估包"""
        return self._index_builder.get_package(name)

    def list_all_eval_packages(self) -> list[EvalPackage]:
        """列出所有评估包"""
        return self._index_builder.list_all()


def create_evaluation_hub(llm_client=None) -> EvaluationHub:
    """创建 EvaluationHub 实例"""
    return EvaluationHub(llm_client)
