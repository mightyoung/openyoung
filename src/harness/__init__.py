"""
Harness - 运行时状态管理
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


class HarnessStatus(str, Enum):
    """Harness 状态"""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class HarnessStats:
    """Harness 统计信息"""

    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class Harness:
    """Harness 运行时管理器"""

    def __init__(self):
        self.status = HarnessStatus.IDLE
        self.start_time: Optional[datetime] = None
        self.stats = HarnessStats()
        self._metadata: Dict[str, Any] = {}

    def start(self) -> None:
        """启动 Harness"""
        self.status = HarnessStatus.RUNNING
        self.start_time = datetime.now()
        self.stats.start_time = self.start_time

    def pause(self) -> None:
        """暂停 Harness"""
        if self.status == HarnessStatus.RUNNING:
            self.status = HarnessStatus.PAUSED

    def resume(self) -> None:
        """恢复 Harness"""
        if self.status == HarnessStatus.PAUSED:
            self.status = HarnessStatus.RUNNING

    def stop(self) -> HarnessStats:
        """停止 Harness"""
        self.status = HarnessStatus.STOPPED
        self.stats.end_time = datetime.now()
        return self.stats

    def record_step(self, success: bool) -> None:
        """记录步骤执行"""
        self.stats.total_steps += 1
        if success:
            self.stats.successful_steps += 1
        else:
            self.stats.failed_steps += 1

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "total_steps": self.stats.total_steps,
            "successful_steps": self.stats.successful_steps,
            "failed_steps": self.stats.failed_steps,
            "metadata": self._metadata,
        }

    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value

    def get_metadata(self, key: str) -> Optional[Any]:
        """获取元数据"""
        return self._metadata.get(key)

    def save(self, path: str) -> None:
        """保存 Harness 状态到文件"""
        import json

        data = {
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "stats": {
                "total_steps": self.stats.total_steps,
                "successful_steps": self.stats.successful_steps,
                "failed_steps": self.stats.failed_steps,
                "start_time": self.stats.start_time.isoformat()
                if self.stats.start_time
                else None,
                "end_time": self.stats.end_time.isoformat()
                if self.stats.end_time
                else None,
            },
            "metadata": self._metadata,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "Harness":
        """从文件加载 Harness 状态"""
        import json

        with open(path, "r") as f:
            data = json.load(f)

        harness = cls()
        harness.status = HarnessStatus(data.get("status", "idle"))
        harness.start_time = (
            datetime.fromisoformat(data["start_time"])
            if data.get("start_time")
            else None
        )

        stats_data = data.get("stats", {})
        harness.stats.total_steps = stats_data.get("total_steps", 0)
        harness.stats.successful_steps = stats_data.get("successful_steps", 0)
        harness.stats.failed_steps = stats_data.get("failed_steps", 0)
        harness.stats.start_time = (
            datetime.fromisoformat(stats_data["start_time"])
            if stats_data.get("start_time")
            else None
        )
        harness.stats.end_time = (
            datetime.fromisoformat(stats_data["end_time"])
            if stats_data.get("end_time")
            else None
        )

        harness._metadata = data.get("metadata", {})
        return harness
