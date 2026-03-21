"""
Exports Router - 数据导出 API

提供数据导出端点
"""

import io
from datetime import datetime
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.datacenter import EvaluationStore

router = APIRouter()


def get_evaluation_store() -> EvaluationStore:
    """获取评估存储"""
    return EvaluationStore()


@router.get("/exports")
async def export_data(
    execution_ids: Optional[str] = Query(None, description="Comma-separated execution IDs"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    format: str = Query("json", description="Export format: json, csv, parquet"),
):
    """
    导出评估数据

    查询参数:
    - execution_ids: 执行ID列表 (逗号分隔)
    - start_date: 开始日期
    - end_date: 结束日期
    - format: 导出格式 (json, csv, parquet)
    """
    try:
        store = get_evaluation_store()

        # 查询数据
        records = store.query_evaluations(limit=10000)

        # 转换为 DataFrame
        data = []
        for record in records:
            row = {
                "evaluation_id": record.id,
                "execution_id": record.execution_id,
                "overall_score": record.overall_score,
                "passed": record.passed,
                "evaluator_type": record.evaluator_type.value
                if hasattr(record.evaluator_type, "value")
                else record.evaluator_type,
                "feedback": record.feedback,
                "iteration": record.iteration,
                "evaluated_at": record.evaluated_at.isoformat() if record.evaluated_at else None,
            }

            # 添加维度数据
            for dim in record.dimensions:
                row[f"dim_{dim.name}_score"] = dim.score
                row[f"dim_{dim.name}_passed"] = dim.passed

            data.append(row)

        df = pd.DataFrame(data)

        # 根据格式导出
        if format.lower() == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                },
            )

        elif format.lower() == "parquet":
            output = io.BytesIO()
            df.to_parquet(output, index=False)
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename=evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                },
            )

        else:  # json
            return {
                "items": data,
                "total": len(data),
                "exported_at": datetime.now().isoformat(),
                "format": format,
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/exports/summary")
async def export_summary(
    format: str = Query("json", description="Summary format: json, csv"),
):
    """导出汇总统计"""
    try:
        store = get_evaluation_store()

        # 统计
        total = store.count_evaluations()
        passed = store.count_evaluations(passed=True)
        failed = total - passed

        records = store.query_evaluations(limit=10000)
        scores = [r.overall_score for r in records]

        avg_score = sum(scores) / len(scores) if scores else 0
        median_score = sorted(scores)[len(scores) // 2] if scores else 0

        summary = {
            "total_evaluations": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "average_score": avg_score,
            "median_score": median_score,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
        }

        if format.lower() == "csv":
            df = pd.DataFrame([summary])
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                },
            )

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
