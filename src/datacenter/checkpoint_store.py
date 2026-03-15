"""
Checkpoint Store - 检查点存储

用于保存和恢复Agent状态
参考 LangGraph Checkpointer 设计
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    session_id: str
    state_snapshot: dict
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class CheckpointStore:
    """
    检查点存储

    功能:
    - 保存状态快照
    - 恢复状态
    - 列出检查点
    - 清理旧检查点
    """

    def __init__(self, storage_path: str = "./data/checkpoints"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._checkpoints: dict[str, list[Checkpoint]] = {}

    def _get_session_file(self, session_id: str) -> Path:
        """获取会话检查点文件路径"""
        return self._storage_path / f"{session_id}.json"

    def save_checkpoint(
        self,
        session_id: str,
        state: dict,
        metadata: dict = None,
    ) -> str:
        """
        保存检查点

        Args:
            session_id: 会话ID
            state: 状态快照
            metadata: 额外元数据

        Returns:
            str: 检查点ID
        """
        checkpoint_id = str(uuid.uuid4())

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            session_id=session_id,
            state_snapshot=state,
            metadata=metadata or {},
        )

        # 内存存储
        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        self._checkpoints[session_id].append(checkpoint)

        # 持久化
        self._persist_checkpoint(checkpoint)

        return checkpoint_id

    def _persist_checkpoint(self, checkpoint: Checkpoint):
        """持久化检查点到磁盘"""
        file_path = self._get_session_file(checkpoint.session_id)

        data = []
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)

        data.append({
            "checkpoint_id": checkpoint.checkpoint_id,
            "session_id": checkpoint.session_id,
            "state_snapshot": checkpoint.state_snapshot,
            "created_at": checkpoint.created_at.isoformat(),
            "metadata": checkpoint.metadata,
        })

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """加载检查点"""
        for checkpoints in self._checkpoints.values():
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    return cp
        return None

    def load_latest(self, session_id: str) -> Optional[Checkpoint]:
        """加载最新的检查点"""
        checkpoints = self._checkpoints.get(session_id, [])
        if checkpoints:
            return checkpoints[-1]
        return None

    def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        """列出会话的所有检查点"""
        return self._checkpoints.get(session_id, [])

    def delete_old_checkpoints(self, session_id: str, keep_count: int = 5):
        """删除旧的检查点，保留最近的N个"""
        checkpoints = self._checkpoints.get(session_id, [])
        if len(checkpoints) <= keep_count:
            return 0

        to_remove = checkpoints[:-keep_count]
        self._checkpoints[session_id] = checkpoints[-keep_count:]

        # 从磁盘删除
        for cp in to_remove:
            self._remove_from_disk(cp)

        return len(to_remove)

    def _remove_from_disk(self, checkpoint: Checkpoint):
        """从磁盘删除检查点"""
        file_path = self._get_session_file(checkpoint.session_id)
        if not file_path.exists():
            return

        with open(file_path, "r") as f:
            data = json.load(f)

        data = [c for c in data if c["checkpoint_id"] != checkpoint.checkpoint_id]

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)


# 全局实例
_checkpoint_store: Optional[CheckpointStore] = None


def get_checkpoint_store(storage_path: str = "./data/checkpoints") -> CheckpointStore:
    """获取检查点存储单例"""
    global _checkpoint_store

    if _checkpoint_store is None:
        _checkpoint_store = CheckpointStore(storage_path)

    return _checkpoint_store
