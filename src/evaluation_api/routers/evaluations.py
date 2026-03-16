"""
Evaluations Router - 评估记录管理 API

提供评估记录查询和管理端点
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/evaluations")
async def list_evaluations(
    execution_id: Optional[str] = Query(None, description="Execution ID"),
    passed: Optional[bool] = Query(None, description="Filter by pass status"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum score"),
    max_score: Optional[float] = Query(None, ge=0, le=1, description="Maximum score"),
    limit: int = Query(50, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
):
    """
    获取评估记录列表

    查询参数:
    - execution_id: 按 execution ID 过滤
    - passed: 按通过状态过滤
    - min_score: 最低分数
    - max_score: 最高分数
    - limit: 返回结果数量
    - offset: 结果偏移量
    """
    try:
        from src.datacenter import EvaluationStore

        store = EvaluationStore()
        results = store.query_evaluations(
            execution_id=execution_id,
            passed=passed,
            min_score=min_score,
            max_score=max_score,
            limit=limit,
            offset=offset,
        )
        total = store.count_evaluations(
            execution_id=execution_id,
            passed=passed,
        )
        return {
            "items": [r.model_dump() if hasattr(r, "model_dump") else vars(r) for r in results],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to query evaluations: {e}")
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }


@router.get("/evaluations/{evaluation_id}")
async def get_evaluation(evaluation_id: str):
    """获取单个评估记录详情"""
    try:
        from src.datacenter import EvaluationStore

        store = EvaluationStore()
        record = store.get_evaluation(evaluation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        return record.model_dump() if hasattr(record, "model_dump") else vars(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/evaluations")
async def create_evaluation(
    execution_id: str,
    evaluator_type: str = "llm_judge",
):
    """创建新的评估记录"""
    try:
        from src.datacenter import EvaluationRecord, EvaluationStore

        store = EvaluationStore()
        record = EvaluationRecord(
            execution_id=execution_id,
            evaluator_type=evaluator_type,
        )
        eval_id = store.save_evaluation(record)
        return {"evaluation_id": eval_id}
    except Exception as e:
        logger.error(f"Failed to create evaluation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create evaluation")
