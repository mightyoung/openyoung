"""
评估记录存储 - Phase 1 数据基础设施

提供 EvaluationStore 用于持久化评估记录
"""

import uuid
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage
from .evaluation_record import (
    EvaluationDimension,
    EvaluationRecord,
    EvaluationStatus,
    EvaluatorType,
)


class EvaluationStore(BaseStorage):
    """评估记录存储"""

    def __init__(self, db_path: str = ".young/evaluations.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库表"""
        # 评估记录表
        self._create_table(
            "evaluations",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "evaluation_id": "TEXT NOT NULL UNIQUE",
                "execution_id": "TEXT NOT NULL",
                "overall_score": "REAL DEFAULT 0.0",
                "passed": "INTEGER DEFAULT 0",
                "evaluator_type": "TEXT DEFAULT 'llm_judge'",
                "feedback": "TEXT",
                "iteration": "INTEGER DEFAULT 0",
                "max_iterations": "INTEGER DEFAULT 5",
                "evaluated_at": "TIMESTAMP",
                "metadata": "TEXT",
                "tags": "TEXT",
            },
            indexes=[
                ("idx_execution", "execution_id"),
                ("idx_evaluated_at", "evaluated_at"),
                ("idx_passed", "passed"),
            ],
        )

        # 评估维度表
        self._create_table(
            "evaluation_dimensions",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "evaluation_id": "TEXT NOT NULL",
                "dimension_name": "TEXT NOT NULL",
                "score": "REAL DEFAULT 0.0",
                "threshold": "REAL DEFAULT 0.7",
                "passed": "INTEGER DEFAULT 0",
                "reasoning": "TEXT",
                "evidence": "TEXT",
                "weight": "REAL DEFAULT 1.0",
            },
            indexes=[
                ("idx_eval_dim", "evaluation_id, dimension_name"),
            ],
        )

    def save_evaluation(self, record: EvaluationRecord) -> str:
        """保存评估记录"""
        evaluation_id = record.id or f"eval_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT OR REPLACE INTO evaluations
            (evaluation_id, execution_id, overall_score, passed, evaluator_type,
             feedback, iteration, max_iterations, evaluated_at, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                record.execution_id,
                record.overall_score,
                1 if record.passed else 0,
                record.evaluator_type.value
                if isinstance(record.evaluator_type, EvaluatorType)
                else record.evaluator_type,
                record.feedback,
                record.iteration,
                record.max_iterations,
                record.evaluated_at.isoformat()
                if record.evaluated_at
                else datetime.now().isoformat(),
                self._json_serialize(record.metadata),
                self._json_serialize(record.tags),
            ),
        )

        # 保存评估维度
        for dimension in record.dimensions:
            self._execute(
                """
                INSERT OR REPLACE INTO evaluation_dimensions
                (evaluation_id, dimension_name, score, threshold, passed, reasoning, evidence, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    dimension.name,
                    dimension.score,
                    dimension.threshold,
                    1 if dimension.passed else 0,
                    dimension.reasoning,
                    self._json_serialize(dimension.evidence),
                    dimension.weight,
                ),
            )

        return evaluation_id

    def get_evaluation(self, evaluation_id: str) -> EvaluationRecord | None:
        """获取评估记录"""
        # 获取主记录
        rows = self._execute(
            "SELECT * FROM evaluations WHERE evaluation_id = ?",
            (evaluation_id,),
            fetch=True,
        )

        if not rows:
            return None

        row = rows[0]

        # 获取维度
        dimension_rows = self._execute(
            "SELECT * FROM evaluation_dimensions WHERE evaluation_id = ?",
            (evaluation_id,),
            fetch=True,
        )

        dimensions = []
        for d in dimension_rows:
            dimensions.append(
                EvaluationDimension(
                    name=d["dimension_name"],
                    score=d["score"],
                    threshold=d["threshold"],
                    passed=bool(d["passed"]),
                    reasoning=d["reasoning"] or "",
                    evidence=self._json_deserialize(d["evidence"]) or [],
                    weight=d["weight"],
                )
            )

        # 构建记录
        evaluator_type = row["evaluator_type"]
        if isinstance(evaluator_type, str):
            try:
                evaluator_type = EvaluatorType(evaluator_type)
            except ValueError:
                evaluator_type = EvaluatorType.LLM_JUDGE

        evaluated_at = row["evaluated_at"]
        if isinstance(evaluated_at, str):
            evaluated_at = datetime.fromisoformat(evaluated_at)

        return EvaluationRecord(
            id=row["evaluation_id"],
            execution_id=row["execution_id"],
            dimensions=dimensions,
            overall_score=row["overall_score"],
            passed=bool(row["passed"]),
            evaluator_type=evaluator_type,
            feedback=row["feedback"] or "",
            iteration=row["iteration"],
            max_iterations=row["max_iterations"],
            evaluated_at=evaluated_at,
            metadata=self._json_deserialize(row["metadata"]) or {},
            tags=self._json_deserialize(row["tags"]) or [],
        )

    def query_evaluations(
        self,
        execution_id: str | None = None,
        passed: bool | None = None,
        min_score: float | None = None,
        max_score: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvaluationRecord]:
        """查询评估记录"""
        conditions = []
        params = []

        if execution_id:
            conditions.append("execution_id = ?")
            params.append(execution_id)

        if passed is not None:
            conditions.append("passed = ?")
            params.append(1 if passed else 0)

        if min_score is not None:
            conditions.append("overall_score >= ?")
            params.append(min_score)

        if max_score is not None:
            conditions.append("overall_score <= ?")
            params.append(max_score)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT evaluation_id FROM evaluations
            {where_clause}
            ORDER BY evaluated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = self._execute(query, tuple(params), fetch=True)

        results = []
        for row in rows:
            eval_record = self.get_evaluation(row["evaluation_id"])
            if eval_record:
                results.append(eval_record)

        return results

    def count_evaluations(
        self,
        execution_id: str | None = None,
        passed: bool | None = None,
    ) -> int:
        """统计评估记录数量"""
        conditions = []
        params = []

        if execution_id:
            conditions.append("execution_id = ?")
            params.append(execution_id)

        if passed is not None:
            conditions.append("passed = ?")
            params.append(1 if passed else 0)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"SELECT COUNT(*) as cnt FROM evaluations {where_clause}"
        rows = self._execute(query, tuple(params) if params else None, fetch=True)

        return rows[0]["cnt"] if rows else 0

    def delete_evaluation(self, evaluation_id: str) -> bool:
        """删除评估记录"""
        # 先删除维度
        self._execute(
            "DELETE FROM evaluation_dimensions WHERE evaluation_id = ?",
            (evaluation_id,),
        )
        # 再删除主记录
        self._execute(
            "DELETE FROM evaluations WHERE evaluation_id = ?",
            (evaluation_id,),
        )
        return True


# ========== 便捷函数 ==========


_evaluation_store: EvaluationStore | None = None


def get_evaluation_store(db_path: str = ".young/evaluations.db") -> EvaluationStore:
    """获取评估存储实例（单例）"""
    global _evaluation_store
    if _evaluation_store is None:
        _evaluation_store = EvaluationStore(db_path)
    return _evaluation_store
