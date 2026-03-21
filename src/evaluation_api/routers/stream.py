"""
Stream Router - SSE 实时流 API

提供 Server-Sent Events 实时推送
"""

import asyncio
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

# 使用 sse-starlette 实现 Server-Sent Events
try:
    from sse_starlette import EventSourceResponse
except ImportError:
    EventSourceResponse = None

router = APIRouter()


# 模拟的任务状态存储（生产环境应使用 Redis）
_task_status: dict[str, dict] = {}


async def event_generator(task_id: str):
    """生成 SSE 事件流"""
    if EventSourceResponse is None:
        yield {"event": "error", "data": "SSE not supported"}
        return

    while True:
        # 检查任务状态
        if task_id in _task_status:
            status = _task_status[task_id]

            # 发送状态更新
            yield {
                "event": "status",
                "data": json.dumps(status),
            }

            # 如果任务完成，发送完成事件
            if status.get("status") in ["success", "failed", "timeout"]:
                yield {
                    "event": "done",
                    "data": json.dumps(status),
                }
                break

            # 如果出错，发送错误事件
            if status.get("error"):
                yield {
                    "event": "error",
                    "data": json.dumps({"error": status.get("error")}),
                }
                break
        else:
            # 任务不存在
            yield {
                "event": "error",
                "data": json.dumps({"error": "Task not found"}),
            }
            break

        # 等待 1 秒
        await asyncio.sleep(1)


@router.get("/stream/{task_id}")
async def stream_task(task_id: str):
    """
    实时推送任务状态

    Event Types:
    - status: 任务状态更新
    - evaluation: 评估结果
    - error: 错误信息
    - done: 任务完成
    """
    if EventSourceResponse is None:
        raise HTTPException(
            status_code=500,
            detail="SSE not supported. Install sse-starlette.",
        )

    return EventSourceResponse(event_generator(task_id))


@router.post("/stream/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    progress: Optional[float] = None,
    result: Optional[dict] = None,
    error: Optional[str] = None,
):
    """
    更新任务状态（供内部调用）

    用于模拟任务执行过程中的状态更新
    """
    _task_status[task_id] = {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "result": result,
        "error": error,
        "updated_at": datetime.now().isoformat(),
    }

    return {"task_id": task_id, "status": "updated"}


@router.get("/stream/{task_id}/status")
async def get_task_status(task_id: str):
    """获取任务当前状态"""
    if task_id not in _task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    return _task_status[task_id]


# 模拟任务生成器（用于测试）
async def simulate_task(task_id: str):
    """模拟任务执行"""
    for i in range(10):
        _task_status[task_id] = {
            "task_id": task_id,
            "status": "running",
            "progress": (i + 1) * 10,
            "updated_at": datetime.now().isoformat(),
        }
        await asyncio.sleep(1)

    # 任务完成
    _task_status[task_id] = {
        "task_id": task_id,
        "status": "success",
        "progress": 100,
        "result": {"score": 0.85, "passed": True},
        "updated_at": datetime.now().isoformat(),
    }


@router.post("/stream/{task_id}/simulate")
async def simulate_task_endpoint(task_id: str):
    """启动模拟任务执行"""
    asyncio.create_task(simulate_task(task_id))
    return {"task_id": task_id, "status": "started"}
