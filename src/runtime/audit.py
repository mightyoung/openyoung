"""
Audit - 安全审计日志

提供沙箱执行的审计功能
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """审计事件"""

    timestamp: datetime
    event_type: str  # execute, create, destroy, error
    sandbox_id: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None

    # 执行详情
    language: Optional[str] = None
    code_length: int = 0
    command: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: int = 0

    # 资源使用
    memory_used_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

    # 安全
    blocked: bool = False
    block_reason: Optional[str] = None

    # 错误
    error: Optional[str] = None

    # 元数据
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, log_dir: str = ".young/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 当前日志文件
        self._current_date = datetime.now().date()
        self._log_file = self._get_log_file()

        # 事件缓冲
        self._buffer: list[AuditEvent] = []
        self._buffer_size = 100

    def _get_log_file(self) -> Path:
        """获取当前日志文件"""
        today = datetime.now().date()
        if today != self._current_date:
            self._current_date = today
            self._flush_buffer()

        return self.log_dir / f"audit_{today.isoformat()}.jsonl"

    def _flush_buffer(self) -> None:
        """刷新缓冲区到磁盘"""
        if self._buffer:
            with open(self._log_file, "a") as f:
                for event in self._buffer:
                    f.write(json.dumps(event.to_dict()) + "\n")
            self._buffer.clear()

    def log_event(self, event: AuditEvent) -> None:
        """记录审计事件"""
        # 添加到缓冲区
        self._buffer.append(event)

        # 如果缓冲区满，写入磁盘
        if len(self._buffer) >= self._buffer_size:
            self._flush_buffer()

        # 同时记录到标准日志
        log_level = logging.WARNING if event.blocked else logging.INFO
        logger.log(
            log_level,
            f"Audit: {event.event_type} sandbox={event.sandbox_id} "
            f"blocked={event.blocked} exit={event.exit_code}"
        )

    def log_execute(
        self,
        sandbox_id: str,
        language: str,
        code: str,
        exit_code: int,
        duration_ms: int,
        blocked: bool = False,
        block_reason: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """记录执行事件"""
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="execute",
            sandbox_id=sandbox_id,
            language=language,
            code_length=len(code) if code else 0,
            exit_code=exit_code,
            duration_ms=duration_ms,
            blocked=blocked,
            block_reason=block_reason,
            error=error,
        )
        self.log_event(event)

    def log_create(self, sandbox_id: str, agent_id: Optional[str] = None) -> None:
        """记录创建事件"""
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="create",
            sandbox_id=sandbox_id,
            agent_id=agent_id,
        )
        self.log_event(event)

    def log_destroy(self, sandbox_id: str) -> None:
        """记录销毁事件"""
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type="destroy",
            sandbox_id=sandbox_id,
        )
        self.log_event(event)

    def log_error(
        self,
        sandbox_id: str,
        error: str,
        event_type: str = "error",
    ) -> None:
        """记录错误事件"""
        event = AuditEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            sandbox_id=sandbox_id,
            error=error,
        )
        self.log_event(event)

    def query(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sandbox_id: Optional[str] = None,
        event_type: Optional[str] = None,
        blocked: Optional[bool] = None,
    ) -> list[AuditEvent]:
        """查询审计事件"""
        results = []

        # 读取所有日志文件
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        for log_file in log_files:
            with open(log_file) as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        event = AuditEvent(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            event_type=data["event_type"],
                            sandbox_id=data["sandbox_id"],
                            user_id=data.get("user_id"),
                            agent_id=data.get("agent_id"),
                            language=data.get("language"),
                            code_length=data.get("code_length", 0),
                            command=data.get("command"),
                            exit_code=data.get("exit_code"),
                            duration_ms=data.get("duration_ms", 0),
                            blocked=data.get("blocked", False),
                            block_reason=data.get("block_reason"),
                            error=data.get("error"),
                            metadata=data.get("metadata", {}),
                        )

                        # 应用过滤
                        if start_date and event.timestamp < start_date:
                            continue
                        if end_date and event.timestamp > end_date:
                            continue
                        if sandbox_id and event.sandbox_id != sandbox_id:
                            continue
                        if event_type and event.event_type != event_type:
                            continue
                        if blocked is not None and event.blocked != blocked:
                            continue

                        results.append(event)

                    except json.JSONDecodeError:
                        continue

        return results

    def get_statistics(self, days: int = 7) -> dict:
        """获取统计信息"""
        from datetime import timedelta

        start_date = datetime.now() - timedelta(days=days)
        events = self.query(start_date=start_date)

        # 计算统计
        total = len(events)
        blocked = sum(1 for e in events if e.blocked)
        errors = sum(1 for e in events if e.event_type == "error")

        # 按类型分组
        by_type: dict[str, int] = {}
        for e in events:
            by_type[e.event_type] = by_type.get(e.event_type, 0) + 1

        # 按语言分组
        by_language: dict[str, int] = {}
        for e in events:
            if e.language:
                by_language[e.language] = by_language.get(e.language, 0) + 1

        # 平均执行时间
        exec_events = [e for e in events if e.event_type == "execute" and e.duration_ms > 0]
        avg_duration = sum(e.duration_ms for e in exec_events) / len(exec_events) if exec_events else 0

        return {
            "total_events": total,
            "blocked_events": blocked,
            "blocked_percent": (blocked / total * 100) if total > 0 else 0,
            "error_events": errors,
            "by_type": by_type,
            "by_language": by_language,
            "avg_execution_ms": avg_duration,
        }

    def close(self) -> None:
        """关闭日志器，刷新缓冲区"""
        self._flush_buffer()


# ========== Convenience Functions ==========


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志器"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_execution(
    sandbox_id: str,
    language: str,
    code: str,
    exit_code: int,
    duration_ms: int,
    **kwargs,
) -> None:
    """便捷函数：记录执行"""
    get_audit_logger().log_execute(
        sandbox_id=sandbox_id,
        language=language,
        code=code,
        exit_code=exit_code,
        duration_ms=duration_ms,
        **kwargs,
    )
