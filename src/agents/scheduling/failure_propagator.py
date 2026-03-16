"""
Failure Propagator - 失败传播器

实现多种失败传播策略:
- CASCADE: 所有下游任务失败
- ISOLATE: 仅失败任务停止，依赖任务可继续
- RESCHEDULE: 失败任务重新排队
- FALLBACK: 使用备用方案

参考:
- Apache Airflow Trigger Rules: https://airflow.apache.org/docs/apache-airflow/stable/
- Dagster: https://docs.dagster.io/
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """失败类型"""

    TEMPORARY = "temporary"  # 临时失败，可恢复
    PERMANENT = "permanent"  # 永久失败，不可恢复
    TIMEOUT = "timeout"  # 超时失败
    RESOURCE = "resource"  # 资源不足
    UNKNOWN = "unknown"  # 未知原因


class PropagationAction(Enum):
    """传播动作"""

    CASCADE = "cascade"  # 向下传播失败
    STOP = "stop"  # 停止传播
    RESCHEDULE = "reschedule"  # 重新调度
    FALLBACK = "fallback"  # 使用备用方案


@dataclass
class FailureContext:
    """失败上下文"""

    task_id: str
    failure_type: FailureType
    error_message: str
    attempt: int
    max_attempts: int
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureRule:
    """失败规则"""

    failure_type: FailureType
    action: PropagationAction
    max_cascade_depth: int = -1  # -1 表示无限深度


class FailurePropagator:
    """失败传播器

    负责:
    - 失败分类
    - 传播决策
    - 失败处理
    """

    def __init__(self):
        self._rules: list[FailureRule] = []
        self._fallback_handler: Optional[Callable] = None
        self._failure_history: list[FailureContext] = []

        # 默认规则
        self._setup_default_rules()

    def _setup_default_rules(self):
        """设置默认规则"""
        self._rules = [
            # 临时失败 - 重新调度
            FailureRule(
                failure_type=FailureType.TEMPORARY,
                action=PropagationAction.RESCHEDULE,
            ),
            # 永久失败 - 停止传播
            FailureRule(
                failure_type=FailureType.PERMANENT,
                action=PropagationAction.STOP,
            ),
            # 超时 - 重新调度
            FailureRule(
                failure_type=FailureType.TIMEOUT,
                action=PropagationAction.RESCHEDULE,
            ),
            # 资源不足 - 停止传播，防止资源耗尽
            FailureRule(
                failure_type=FailureType.RESOURCE,
                action=PropagationAction.STOP,
            ),
        ]

    def add_rule(self, rule: FailureRule):
        """添加失败规则"""
        self._rules.append(rule)

    def set_fallback_handler(self, handler: Callable[[FailureContext], Any]):
        """设置备用处理器"""
        self._fallback_handler = handler

    def classify_failure(
        self,
        error: Exception,
        attempt: int,
        max_attempts: int,
    ) -> FailureType:
        """分类失败类型

        Args:
            error: 异常对象
            attempt: 当前尝试次数
            max_attempts: 最大尝试次数

        Returns:
            失败类型
        """
        error_msg = str(error).lower()

        # 超时
        if "timeout" in error_msg or "timed out" in error_msg:
            return FailureType.TIMEOUT

        # 资源不足
        if any(kw in error_msg for kw in ["memory", "cpu", "resource", "quota", "limit"]):
            return FailureType.RESOURCE

        # 永久错误
        permanent_keywords = [
            "syntax",
            "parse error",
            "invalid",
            "unauthorized",
            "forbidden",
            "not found",
            "does not exist",
            "permission denied",
            "authentication failed",
        ]
        if any(kw in error_msg for kw in permanent_keywords):
            return FailureType.PERMANENT

        # 如果还有重试次数，认为是临时的
        if attempt < max_attempts:
            return FailureType.TEMPORARY

        # 超过重试次数，归类为永久失败
        return FailureType.PERMANENT

    def determine_action(self, context: FailureContext) -> PropagationAction:
        """确定传播动作

        Args:
            context: 失败上下文

        Returns:
            传播动作
        """
        # 查找匹配的规则
        for rule in self._rules:
            if rule.failure_type == context.failure_type:
                logger.info(
                    f"Failure type: {context.failure_type.value} -> Action: {rule.action.value}"
                )
                return rule.action

        # 默认动作
        return PropagationAction.STOP

    def propagate(
        self,
        failed_task_id: str,
        error: Exception,
        attempt: int,
        max_attempts: int,
        downstream_tasks: list[str],
    ) -> tuple[PropagationAction, list[str]]:
        """传播失败

        Args:
            failed_task_id: 失败的任务 ID
            error: 异常对象
            attempt: 当前尝试次数
            max_attempts: 最大尝试次数
            downstream_tasks: 下游任务列表

        Returns:
            (传播动作, 受影响的任务列表)
        """
        import time

        # 分类失败
        failure_type = self.classify_failure(error, attempt, max_attempts)

        # 创建上下文
        context = FailureContext(
            task_id=failed_task_id,
            failure_type=failure_type,
            error_message=str(error),
            attempt=attempt,
            max_attempts=max_attempts,
            timestamp=time.time(),
        )
        self._failure_history.append(context)

        # 确定动作
        action = self.determine_action(context)

        # 根据动作确定受影响的任务
        affected_tasks = []

        if action == PropagationAction.CASCADE:
            affected_tasks = downstream_tasks
        elif action == PropagationAction.STOP:
            affected_tasks = [failed_task_id]
        elif action == PropagationAction.RESCHEDULE:
            affected_tasks = [failed_task_id]
        elif action == PropagationAction.FALLBACK:
            affected_tasks = [failed_task_id]
            if self._fallback_handler:
                try:
                    self._fallback_handler(context)
                except Exception as e:
                    logger.error(f"Fallback handler failed: {e}")

        logger.info(
            f"Failure propagated: task={failed_task_id}, type={failure_type.value}, "
            f"action={action.value}, affected={affected_tasks}"
        )

        return action, affected_tasks

    def get_failure_history(self, task_id: Optional[str] = None) -> list[FailureContext]:
        """获取失败历史

        Args:
            task_id: 可选的任务 ID 过滤

        Returns:
            失败上下文列表
        """
        if task_id:
            return [f for f in self._failure_history if f.task_id == task_id]
        return self._failure_history.copy()

    def clear_history(self):
        """清除失败历史"""
        self._failure_history.clear()


# ============================================================================
# Dead Letter Queue (DLQ)
# ============================================================================


@dataclass
class DLQEntry:
    """死信队列条目"""

    task_id: str
    error: str
    attempts: int
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


class DeadLetterQueue:
    """死信队列

    存储失败的任务以便人工介入或后续处理
    """

    def __init__(self):
        self._queue: list[DLQEntry] = []

    def add(self, entry: DLQEntry):
        """添加失败任务到队列"""
        self._queue.append(entry)

    def get_all(self) -> list[DLQEntry]:
        """获取所有条目"""
        return self._queue.copy()

    def get_by_task(self, task_id: str) -> list[DLQEntry]:
        """获取特定任务的条目"""
        return [e for e in self._queue if e.task_id == task_id]

    def clear(self):
        """清空队列"""
        self._queue.clear()

    def size(self) -> int:
        """队列大小"""
        return len(self._queue)
