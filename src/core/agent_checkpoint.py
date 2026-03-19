"""
Agent Checkpoint Manager - Agent 状态检查点管理

基于 PostgreSQL 或内存存储，支持 Agent 状态的保存和恢复
参考 OpenCode Checkpoint 机制

Graceful Degradation: PostgreSQL 可选，缺失时自动降级到内存存储
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class AgentCheckpoint:
    """Agent 检查点"""

    id: str
    agent_id: str
    task_id: Optional[str]
    state: dict[str, Any]
    event_history: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_final: bool = False


class CheckpointStorage(ABC):
    """检查点存储抽象基类"""

    @abstractmethod
    async def save(
        self,
        agent_id: str,
        state: dict[str, Any],
        task_id: Optional[str] = None,
        event_history: Optional[list[dict]] = None,
        metadata: Optional[dict[str, Any]] = None,
        is_final: bool = False,
    ) -> str:
        """保存检查点，返回 checkpoint_id"""
        pass

    @abstractmethod
    async def get(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """获取检查点"""
        pass

    @abstractmethod
    async def get_latest(
        self, agent_id: str, task_id: Optional[str] = None
    ) -> Optional[AgentCheckpoint]:
        """获取最新的检查点"""
        pass

    @abstractmethod
    async def list(
        self, agent_id: str, task_id: Optional[str] = None, limit: int = 10
    ) -> list[AgentCheckpoint]:
        """列出检查点"""
        pass

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        pass

    @abstractmethod
    async def cleanup_old(self, agent_id: str, keep_count: int = 5) -> int:
        """清理旧检查点"""
        pass

    @abstractmethod
    async def mark_final(self, checkpoint_id: str) -> bool:
        """标记为最终检查点"""
        pass


class InMemoryCheckpointStorage(CheckpointStorage):
    """内存检查点存储 - 无 PostgreSQL 时的降级方案"""

    def __init__(self):
        self._checkpoints: list[dict] = []

    async def save(
        self,
        agent_id: str,
        state: dict[str, Any],
        task_id: Optional[str] = None,
        event_history: Optional[list[dict]] = None,
        metadata: Optional[dict[str, Any]] = None,
        is_final: bool = False,
    ) -> str:
        checkpoint_id = str(uuid4())
        checkpoint = {
            "id": checkpoint_id,
            "agent_id": agent_id,
            "task_id": task_id,
            "state": state,
            "event_history": event_history or [],
            "metadata": metadata or {},
            "created_at": datetime.now(),
            "is_final": is_final,
        }
        self._checkpoints.append(checkpoint)
        logger.info(f"[InMemory] Saved checkpoint {checkpoint_id} for agent {agent_id}")
        return checkpoint_id

    async def get(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        for row in self._checkpoints:
            if row["id"] == checkpoint_id:
                return self._row_to_checkpoint(row)
        return None

    async def get_latest(
        self, agent_id: str, task_id: Optional[str] = None
    ) -> Optional[AgentCheckpoint]:
        filtered = [
            row
            for row in reversed(self._checkpoints)
            if row["agent_id"] == agent_id and (task_id is None or row["task_id"] == task_id)
        ]
        return self._row_to_checkpoint(filtered[0]) if filtered else None

    async def list(
        self, agent_id: str, task_id: Optional[str] = None, limit: int = 10
    ) -> list[AgentCheckpoint]:
        filtered = [
            row
            for row in reversed(self._checkpoints)
            if row["agent_id"] == agent_id and (task_id is None or row["task_id"] == task_id)
        ]
        return [self._row_to_checkpoint(row) for row in filtered[:limit]]

    async def delete(self, checkpoint_id: str) -> bool:
        for i, row in enumerate(self._checkpoints):
            if row["id"] == checkpoint_id:
                self._checkpoints.pop(i)
                return True
        return False

    async def cleanup_old(self, agent_id: str, keep_count: int = 5) -> int:
        agent_checkpoints = [
            (i, row)
            for i, row in enumerate(self._checkpoints)
            if row["agent_id"] == agent_id and not row["is_final"]
        ]
        if len(agent_checkpoints) <= keep_count:
            return 0
        to_remove = agent_checkpoints[:-keep_count]
        for i, _ in reversed(to_remove):
            self._checkpoints.pop(i)
        return len(to_remove)

    async def mark_final(self, checkpoint_id: str) -> bool:
        for row in self._checkpoints:
            if row["id"] == checkpoint_id:
                row["is_final"] = True
                return True
        return False

    def _row_to_checkpoint(self, row: dict) -> AgentCheckpoint:
        return AgentCheckpoint(
            id=row["id"],
            agent_id=row["agent_id"],
            task_id=row["task_id"],
            state=row["state"],
            event_history=row["event_history"],
            metadata=row["metadata"],
            created_at=row["created_at"],
            is_final=row["is_final"],
        )


class PostgresCheckpointStorage(CheckpointStorage):
    """PostgreSQL 检查点存储"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        self._pool = await asyncpg.create_pool(self.database_url)
        await self._init_tables()
        logger.info("PostgresCheckpointStorage initialized")

    async def _init_tables(self) -> None:
        """初始化数据库表"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_checkpoints (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(255) NOT NULL,
                    task_id VARCHAR(255),
                    state JSONB NOT NULL,
                    event_history JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}',
                    is_final BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_agent_id
                ON agent_checkpoints(agent_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_task_id
                ON agent_checkpoints(task_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at
                ON agent_checkpoints(created_at DESC)
            """)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def save(
        self,
        agent_id: str,
        state: dict[str, Any],
        task_id: Optional[str] = None,
        event_history: Optional[list[dict]] = None,
        metadata: Optional[dict[str, Any]] = None,
        is_final: bool = False,
    ) -> str:
        checkpoint_id = str(uuid4())
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_checkpoints
                (id, agent_id, task_id, state, event_history, metadata, is_final)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                checkpoint_id,
                agent_id,
                task_id,
                json.dumps(state),
                json.dumps(event_history or []),
                json.dumps(metadata or {}),
                is_final,
            )
        logger.info(f"[Postgres] Saved checkpoint {checkpoint_id} for agent {agent_id}")
        return checkpoint_id

    async def get(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                FROM agent_checkpoints WHERE id = $1
                """,
                checkpoint_id,
            )
        if not row:
            return None
        return self._row_to_checkpoint(row)

    async def get_latest(
        self, agent_id: str, task_id: Optional[str] = None
    ) -> Optional[AgentCheckpoint]:
        async with self._pool.acquire() as conn:
            if task_id:
                row = await conn.fetchrow(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1 AND task_id = $2
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    agent_id,
                    task_id,
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    agent_id,
                )
        if not row:
            return None
        return self._row_to_checkpoint(row)

    async def list(
        self, agent_id: str, task_id: Optional[str] = None, limit: int = 10
    ) -> list[AgentCheckpoint]:
        async with self._pool.acquire() as conn:
            if task_id:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1 AND task_id = $2
                    ORDER BY created_at DESC LIMIT $3
                    """,
                    agent_id,
                    task_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1
                    ORDER BY created_at DESC LIMIT $2
                    """,
                    agent_id,
                    limit,
                )
        return [self._row_to_checkpoint(row) for row in rows]

    async def delete(self, checkpoint_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM agent_checkpoints WHERE id = $1",
                checkpoint_id,
            )
        return result != "DELETE 0"

    async def cleanup_old(self, agent_id: str, keep_count: int = 5) -> int:
        async with self._pool.acquire() as conn:
            keep_ids = await conn.fetch(
                """
                SELECT id FROM agent_checkpoints
                WHERE agent_id = $1 AND is_final = FALSE
                ORDER BY created_at DESC LIMIT $2
                """,
                agent_id,
                keep_count,
            )
            keep_ids = [str(row["id"]) for row in keep_ids]
            if not keep_ids:
                return 0
            await conn.execute(
                """
                DELETE FROM agent_checkpoints
                WHERE agent_id = $1 AND is_final = FALSE AND id != ALL($2)
                """,
                agent_id,
                keep_ids,
            )
        return len(keep_ids)

    async def mark_final(self, checkpoint_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE agent_checkpoints
                SET is_final = TRUE, updated_at = NOW()
                WHERE id = $1
                """,
                checkpoint_id,
            )
        return result != "UPDATE 0"

    def _row_to_checkpoint(self, row) -> AgentCheckpoint:
        return AgentCheckpoint(
            id=str(row["id"]),
            agent_id=row["agent_id"],
            task_id=row["task_id"],
            state=row["state"],
            event_history=row["event_history"],
            metadata=row["metadata"],
            created_at=row["created_at"],
            is_final=row["is_final"],
        )

class AgentCheckpointManager:
    """Agent 状态检查点管理器

    支持:
    - 检查点保存/恢复
    - 状态版本管理
    - 失败恢复
    - Graceful Degradation: PostgreSQL 不可用时自动降级到内存存储
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url
        self._storage: Optional[CheckpointStorage] = None

    async def initialize(self) -> None:
        """初始化存储后端，PostgreSQL 不可用时自动降级到内存"""
        database_url = self.database_url or os.getenv("DATABASE_URL")
        if database_url:
            try:
                pg_storage = PostgresCheckpointStorage(database_url)
                await pg_storage.initialize()
                self._storage = pg_storage
                logger.info("AgentCheckpointManager initialized with PostgreSQL")
            except Exception as e:
                logger.warning(f"PostgreSQL unavailable ({e}), falling back to in-memory storage")
                self._storage = InMemoryCheckpointStorage()
                logger.info("AgentCheckpointManager initialized with In-Memory storage")
        else:
            self._storage = InMemoryCheckpointStorage()
            logger.info("AgentCheckpointManager initialized with In-Memory storage (no DATABASE_URL)")

    async def close(self) -> None:
        """关闭存储连接"""
        if self._storage and hasattr(self._storage, "close"):
            await self._storage.close()

    async def save(
        self,
        agent_id: str,
        state: dict[str, Any],
        task_id: Optional[str] = None,
        event_history: Optional[list[dict]] = None,
        metadata: Optional[dict[str, Any]] = None,
        is_final: bool = False,
    ) -> str:
        """保存检查点

        Args:
            agent_id: Agent ID
            state: Agent 状态
            task_id: 任务 ID
            event_history: 事件历史
            metadata: 元数据
            is_final: 是否为最终检查点

        Returns:
            checkpoint_id
        """
        return await self._storage.save(agent_id, state, task_id, event_history, metadata, is_final)

    async def get(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """获取检查点"""
        return await self._storage.get(checkpoint_id)

    async def get_latest(self, agent_id: str, task_id: Optional[str] = None) -> Optional[AgentCheckpoint]:
        """获取最新的检查点"""
        return await self._storage.get_latest(agent_id, task_id)

    async def list(self, agent_id: str, task_id: Optional[str] = None, limit: int = 10) -> list[AgentCheckpoint]:
        """列出检查点"""
        return await self._storage.list(agent_id, task_id, limit)

    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        return await self._storage.delete(checkpoint_id)

    async def cleanup_old(self, agent_id: str, keep_count: int = 5) -> int:
        """清理旧检查点，保留最新的 N 个"""
        return await self._storage.cleanup_old(agent_id, keep_count)

    async def mark_final(self, checkpoint_id: str) -> bool:
        """标记为最终检查点"""
        return await self._storage.mark_final(checkpoint_id)


# 全局实例
_checkpoint_manager: Optional[AgentCheckpointManager] = None


async def get_checkpoint_manager() -> AgentCheckpointManager:
    """获取全局检查点管理器"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = AgentCheckpointManager()
        await _checkpoint_manager.initialize()
    return _checkpoint_manager
