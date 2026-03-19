"""
Executions Router - 执行记录查询 API

提供执行记录查询端点
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

# 导入数据模型
from src.datacenter import ExecutionRecord, UnifiedStore, get_unified_store

router = APIRouter()


def get_store() -> UnifiedStore:
    """获取数据存储"""
    return get_unified_store()


@router.get("/executions")
async def list_executions(
    session_id: Optional[str] = Query(None, description="Session ID"),
    agent_name: Optional[str] = Query(None, description="Agent name"),
    status: Optional[str] = Query(None, description="Execution status"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(50, ge=1, le=100, description="Results limit"),
    offset: int = Query(0, ge=0, description="Results offset"),
):
    """
    获取执行记录列表

    查询参数:
    - session_id: 按 session ID 过滤
    - agent_name: 按 agent name 过滤
    - status: 执行状态 (pending/running/success/failed/timeout)
    - start_date: 开始日期
    - end_date: 结束日期
    - limit: 返回结果数量 (默认 50, 最大 100)
    - offset: 结果偏移量
    """
    try:
        store = get_store()

        # 构建查询条件
        filters = {}
        if session_id:
            filters["session_id"] = session_id
        if agent_name:
            filters["agent_name"] = agent_name
        if status:
            filters["status"] = status

        # 查询数据
        records = store.query_records(
            limit=limit,
            offset=offset,
            filters=filters,
        )

        # 获取总数
        total = store.count(status=status)

        return {
            "items": [r.to_dict() for r in records],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to query executions: {e}")
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }


@router.get("/executions/{execution_id}")
async def get_execution(execution_id: str):
    """获取单个执行记录详情"""
    try:
        store = get_store()
        record = store.get_record(execution_id)
        if not record:
            raise HTTPException(status_code=404, detail="Execution not found")
        return record.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail="Execution not found")


@router.post("/executions")
async def create_execution(
    agent_name: str,
    task_description: str,
    session_id: Optional[str] = None,
):
    """创建新的执行记录"""
    record = ExecutionRecord(
        agent_name=agent_name,
        task_description=task_description,
        session_id=session_id or "",
    )

    try:
        store = get_store()
        store.save_record(record)
    except Exception as e:
        logger.warning(f"Failed to save trace record: {e}")

    return record.to_dict()
