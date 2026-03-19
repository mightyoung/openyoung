"""
事件处理器实现

实现 TASK_STARTED, TASK_COMPLETED, ERROR 等核心事件处理器
"""

import logging
from datetime import datetime
from typing import Any, Optional

from src.core.agent_checkpoint import AgentCheckpointManager, get_checkpoint_manager
from src.core.events import Event, EventType
from src.core.knowledge import get_knowledge_manager

logger = logging.getLogger(__name__)


class TaskStartedHandler:
    """任务开始处理器

    实现 Claude Code 风格的 Hook:
    1. 启动计时器
    2. 记录开始时间到知识库
    3. 检查资源可用性
    4. 创建检查点
    """

    async def handle(self, event: Event) -> None:
        """处理任务开始事件"""
        data = event.data or {}

        agent_id = data.get("agent_id", "unknown")
        task_id = data.get("task_id")
        task_type = data.get("task_type", "general")
        required_tools = data.get("required_tools", [])

        logger.info(f"Task started: agent={agent_id}, task={task_id}")

        # 1. 启动计时器 (记录到 metadata)
        event.metadata["started_at"] = datetime.now().isoformat()
        event.metadata["timer_started"] = True

        # 2. 记录开始时间到知识库
        try:
            knowledge_mgr = get_knowledge_manager()
            await knowledge_mgr.log_event(
                event_type="task_started",
                agent_id=agent_id,
                task_id=task_id,
                task_type=task_type,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.warning(f"Failed to log to knowledge manager: {e}")

        # 3. 检查资源可用性
        if required_tools:
            await self._check_resources(required_tools)

        # 4. 创建初始检查点
        try:
            checkpoint_mgr = await get_checkpoint_manager()
            initial_state = {
                "agent_id": agent_id,
                "task_id": task_id,
                "phase": "started",
                "tools_used": [],
                "messages": [],
            }
            checkpoint_id = await checkpoint_mgr.save(
                agent_id=agent_id,
                task_id=task_id,
                state=initial_state,
                event_history=[{"type": "task_started", "timestamp": datetime.now().isoformat()}],
                metadata={"task_type": task_type},
            )
            event.metadata["checkpoint_id"] = checkpoint_id
            logger.debug(f"Created initial checkpoint: {checkpoint_id}")
        except Exception as e:
            logger.warning(f"Failed to create checkpoint: {e}")

    async def _check_resources(self, required_tools: list[str]) -> None:
        """检查所需工具是否可用"""
        # TODO: 实现资源检查
        logger.debug(f"Checking resources for tools: {required_tools}")


class TaskCompletedHandler:
    """任务完成处理器

    实现:
    1. 停止计时器
    2. 记录完成到知识库
    3. 触发评估 (如果需要)
    4. 更新统计
    5. 保存最终检查点
    """

    async def handle(self, event: Event) -> None:
        """处理任务完成事件"""
        data = event.data or {}

        agent_id = data.get("agent_id", "unknown")
        task_id = data.get("task_id")
        result = data.get("result", {})
        evaluate = data.get("evaluate", False)

        logger.info(f"Task completed: agent={agent_id}, task={task_id}")

        # 1. 计算持续时间
        started_at = event.metadata.get("started_at")
        if started_at:
            try:
                from datetime import datetime

                start_time = datetime.fromisoformat(started_at)
                duration = (datetime.now() - start_time).total_seconds()
                event.metadata["duration_seconds"] = duration
            except Exception as e:
                logger.debug(f"Failed to calculate task duration: {e}")

        # 2. 记录完成到知识库
        try:
            knowledge_mgr = get_knowledge_manager()
            await knowledge_mgr.log_completion(
                task_id=task_id,
                result=result,
                agent_id=agent_id,
                duration=event.metadata.get("duration_seconds"),
            )
        except Exception as e:
            logger.warning(f"Failed to log completion: {e}")

        # 3. 触发评估 (如果需要)
        if evaluate:
            await self._trigger_evaluation(task_id, result)

        # 4. 更新统计
        event.metadata["completed"] = True

        # 5. 保存最终检查点
        try:
            checkpoint_mgr = await get_checkpoint_manager()
            final_state = {
                "agent_id": agent_id,
                "task_id": task_id,
                "phase": "completed",
                "result": result,
                "duration": event.metadata.get("duration_seconds"),
            }
            checkpoint_id = await checkpoint_mgr.save(
                agent_id=agent_id,
                task_id=task_id,
                state=final_state,
                is_final=True,
            )
            await checkpoint_mgr.mark_final(checkpoint_id)
            logger.debug(f"Created final checkpoint: {checkpoint_id}")
        except Exception as e:
            logger.warning(f"Failed to create final checkpoint: {e}")

    async def _trigger_evaluation(self, task_id: str, result: dict) -> None:
        """触发评估"""
        # TODO: 集成评估器
        logger.info(f"Evaluation triggered for task: {task_id}")


class ErrorHandler:
    """错误处理器

    实现:
    1. 记录错误到知识库
    2. 尝试从检查点恢复
    3. 发送通知 (如果需要)
    """

    async def handle(self, event: Event) -> None:
        """处理错误事件"""
        data = event.data or {}

        agent_id = data.get("agent_id", "unknown")
        task_id = data.get("task_id")
        error_type = data.get("error_type", "unknown")
        message = data.get("message", "")
        recoverable = data.get("recoverable", False)
        notify = data.get("notify", False)

        logger.error(f"Error occurred: agent={agent_id}, task={task_id}, type={error_type}")

        # 1. 记录错误到知识库
        try:
            knowledge_mgr = get_knowledge_manager()
            await knowledge_mgr.log_error(
                error_type=error_type,
                message=message,
                agent_id=agent_id,
                task_id=task_id,
                context=data.get("context", {}),
            )
        except Exception as e:
            logger.warning(f"Failed to log error: {e}")

        # 2. 尝试从检查点恢复
        if recoverable and task_id:
            await self._attempt_recovery(agent_id, task_id, event)

        # 3. 发送通知
        if notify:
            await self._send_notification(error_type, message, data)

    async def _attempt_recovery(self, agent_id: str, task_id: str, event: Event) -> None:
        """尝试从检查点恢复"""
        try:
            checkpoint_mgr = await get_checkpoint_manager()
            last_checkpoint = await checkpoint_mgr.get_latest(agent_id, task_id)

            if last_checkpoint:
                event.metadata["recovery_checkpoint_id"] = last_checkpoint.id
                event.metadata["recovery_state"] = last_checkpoint.state
                logger.info(f"Recovery checkpoint found: {last_checkpoint.id}")
            else:
                logger.warning(f"No checkpoint found for recovery: agent={agent_id}, task={task_id}")
        except Exception as e:
            logger.warning(f"Failed to attempt recovery: {e}")

    async def _send_notification(self, error_type: str, message: str, data: dict) -> None:
        """发送错误通知"""
        # TODO: 实现通知机制
        logger.warning(f"Error notification: type={error_type}, message={message}")


# ====================
# Heartbeat 处理器
# ====================


class HeartbeatHandler:
    """心跳处理器

    处理周期性心跳事件:
    1. 记录心跳时间戳
    2. 更新检查点状态
    3. 检查任务是否超时
    4. 触发健康检查
    """

    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        self._last_heartbeat: dict[str, float] = {}

    async def handle(self, event: Event) -> None:
        """处理心跳事件"""
        data = event.data or {}

        agent_id = data.get("agent_id", "unknown")
        task_id = data.get("task_id")
        phase = data.get("phase", "unknown")

        import time
        current_time = time.time()

        # 1. 记录心跳时间戳
        self._last_heartbeat[agent_id] = current_time
        event.metadata["last_heartbeat"] = current_time
        event.metadata["phase"] = phase

        logger.debug(f"Heartbeat: agent={agent_id}, phase={phase}, task={task_id}")

        # 2. 更新检查点状态
        await self._update_checkpoint(agent_id, task_id, phase)

        # 3. 检查超时
        await self._check_timeout(agent_id, task_id, current_time)

    async def _update_checkpoint(self, agent_id: str, task_id: Optional[str], phase: str) -> None:
        """更新检查点状态"""
        if not task_id:
            return
        try:
            checkpoint_mgr = await get_checkpoint_manager()
            # 查找最近的检查点并更新阶段
            checkpoints = await checkpoint_mgr.list(agent_id, task_id)
            if checkpoints:
                latest = checkpoints[0]
                updated_state = latest.state.copy()
                updated_state["last_heartbeat_phase"] = phase
                await checkpoint_mgr.save(
                    agent_id=agent_id,
                    task_id=task_id,
                    state=updated_state,
                )
        except Exception as e:
            logger.debug(f"Failed to update checkpoint: {e}")

    async def _check_timeout(self, agent_id: str, task_id: Optional[str], current_time: float) -> None:
        """检查是否超时"""
        if not task_id:
            return

        last_time = self._last_heartbeat.get(agent_id)
        if last_time and (current_time - last_time) > self.timeout_seconds:
            logger.warning(f"Agent {agent_id} heartbeat timeout detected")

    def get_last_heartbeat(self, agent_id: str) -> Optional[float]:
        """获取最后心跳时间"""
        return self._last_heartbeat.get(agent_id)


# ====================
# 评估处理器
# ====================


class EvaluationHandler:
    """评估处理器

    处理评估相关事件:
    1. EVALUATION_STARTED - 初始化评估
    2. 触发评估执行
    3. 记录评估结果
    """

    def __init__(self):
        self._pending_evaluations: dict[str, dict] = {}

    async def handle(self, event: Event) -> None:
        """处理评估事件"""
        data = event.data or {}

        task_id = data.get("task_id")
        agent_id = data.get("agent_id", "unknown")
        evaluation_type = data.get("evaluation_type", "default")

        logger.info(f"Evaluation triggered: task={task_id}, type={evaluation_type}")

        # 1. 记录待评估任务
        if task_id:
            self._pending_evaluations[task_id] = {
                "agent_id": agent_id,
                "evaluation_type": evaluation_type,
                "triggered_at": datetime.now().isoformat(),
            }

        # 2. 执行评估
        result = await self._run_evaluation(task_id, agent_id, evaluation_type, data)

        # 3. 记录结果
        event.metadata["evaluation_result"] = result
        event.metadata["evaluation_completed"] = True

    async def _run_evaluation(
        self,
        task_id: Optional[str],
        agent_id: str,
        evaluation_type: str,
        data: dict,
    ) -> dict:
        """运行评估"""
        # TODO: 集成实际的评估器
        # 这里返回模拟结果

        return {
            "task_id": task_id,
            "agent_id": agent_id,
            "evaluation_type": evaluation_type,
            "score": 0.85,
            "passed": True,
            "details": {
                "criteria_met": 8,
                "criteria_total": 10,
            },
        }

    def get_pending_evaluation(self, task_id: str) -> Optional[dict]:
        """获取待评估任务"""
        return self._pending_evaluations.get(task_id)


# ====================
# 全局处理器实例
# ====================

task_started_handler = TaskStartedHandler()
task_completed_handler = TaskCompletedHandler()
error_handler = ErrorHandler()
heartbeat_handler = HeartbeatHandler()
evaluation_handler = EvaluationHandler()


# 注册处理器到 EventBus
def register_event_handlers() -> None:
    """注册所有事件处理器"""
    from src.core.events import EventBus, get_event_bus, EventType

    bus = get_event_bus()

    # 注册 TASK_STARTED 处理器
    bus.subscribe_async(EventType.TASK_STARTED, task_started_handler.handle)

    # 注册 TASK_COMPLETED 处理器
    bus.subscribe_async(EventType.TASK_COMPLETED, task_completed_handler.handle)

    # 注册 ERROR 处理器
    bus.subscribe_async(EventType.ERROR_OCCURRED, error_handler.handle)

    # 注册 HEARTBEAT 处理器
    bus.subscribe_async(EventType.HEARTBEAT_TICK, heartbeat_handler.handle)
    bus.subscribe_async(EventType.HEARTBEAT_PHASE, heartbeat_handler.handle)

    # 注册 EVALUATION 处理器
    bus.subscribe_async(EventType.EVALUATION_STARTED, evaluation_handler.handle)
    bus.subscribe_async(EventType.EVALUATION_COMPLETED, evaluation_handler.handle)

    logger.info("Event handlers registered: TASK_STARTED, TASK_COMPLETED, ERROR, HEARTBEAT, EVALUATION")
