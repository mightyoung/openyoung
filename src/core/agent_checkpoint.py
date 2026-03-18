"""
Agent Checkpoint Manager - Agent 状态检查点管理

基于 PostgreSQL 存储，支持 Agent 状态的保存和恢复
参考 OpenCode Checkpoint 机制
"""

import json
import logging
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
    state: dict[str, Any]  # 序列化后的状态
    event_history: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_final: bool = False


class AgentCheckpointManager:
    """Agent 状态检查点管理器

    使用 PostgreSQL 存储，支持:
    - 检查点保存/恢复
    - 状态版本管理
    - 失败恢复
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        if not self.database_url:
            # 从环境变量获取
            import os
            self.database_url = os.getenv("DATABASE_URL")
            if not self.database_url:
                raise ValueError("DATABASE_URL not configured")

        self._pool = await asyncpg.create_pool(self.database_url)
        await self._init_tables()
        logger.info("AgentCheckpointManager initialized with PostgreSQL")

    async def _init_tables(self) -> None:
        """初始化数据库表"""
        async with self._pool.acquire() as conn:
            # Agent 检查点表
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

            # 索引
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
        """关闭连接池"""
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

        logger.info(f"Saved checkpoint {checkpoint_id} for agent {agent_id}")
        return checkpoint_id

    async def get(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """获取检查点"""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                FROM agent_checkpoints
                WHERE id = $1
                """,
                checkpoint_id,
            )

        if not row:
            return None

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

    async def get_latest(self, agent_id: str, task_id: Optional[str] = None) -> Optional[AgentCheckpoint]:
        """获取最新的检查点"""
        async with self._pool.acquire() as conn:
            if task_id:
                row = await conn.fetchrow(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1 AND task_id = $2
                    ORDER BY created_at DESC
                    LIMIT 1
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
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    agent_id,
                )

        if not row:
            return None

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

    async def list(self, agent_id: str, task_id: Optional[str] = None, limit: int = 10) -> list[AgentCheckpoint]:
        """列出检查点"""
        async with self._pool.acquire() as conn:
            if task_id:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_id, task_id, state, event_history, metadata, created_at, is_final
                    FROM agent_checkpoints
                    WHERE agent_id = $1 AND task_id = $2
                    ORDER BY created_at DESC
                    LIMIT $3
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
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    agent_id,
                    limit,
                )

        return [
            AgentCheckpoint(
                id=str(row["id"]),
                agent_id=row["agent_id"],
                task_id=row["task_id"],
                state=row["state"],
                event_history=row["event_history"],
                metadata=row["metadata"],
                created_at=row["created_at"],
                is_final=row["is_final"],
            )
            for row in rows
        ]

    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM agent_checkpoints WHERE id = $1",
                checkpoint_id,
            )
        return result != "DELETE 0"

    async def cleanup_old(self, agent_id: str, keep_count: int = 5) -> int:
        """清理旧检查点，保留最新的 N 个"""
        async with self._pool.acquire() as conn:
            # 获取需要保留的检查点 ID
            keep_ids = await conn.fetch(
                """
                SELECT id FROM agent_checkpoints
                WHERE agent_id = $1 AND is_final = FALSE
                ORDER BY created_at DESC
                LIMIT $2
                """,
                agent_id,
                keep_count,
            )
            keep_ids = [str(row["id"]) for row in keep_ids]

            if not keep_ids:
                return 0

            # 删除不在保留列表中的非最终检查点
            result = await conn.execute(
                """
                DELETE FROM agent_checkpoints
                WHERE agent_id = $1 AND is_final = FALSE AND id != ALL($2)
                """,
                agent_id,
                keep_ids,
            )

        return len(keep_ids)

    async def mark_final(self, checkpoint_id: str) -> bool:
        """标记为最终检查点"""
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


# 全局实例
_checkpoint_manager: Optional[AgentCheckpointManager] = None


async def get_checkpoint_manager() -> AgentCheckpointManager:
    """获取全局检查点管理器"""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = AgentCheckpointManager()
        await _checkpoint_manager.initialize()
    return _checkpoint_manager
