"""
Semantic Memory (L2) - LLM 推理知识检索

参考 PageIndex 思路 - 用 LLM 理解查询意图，无需向量数据库

功能:
- 知识条目存储 (PostgreSQL JSONB)
- LLM 推理检索 (可选)
- 知识分类和标签
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
class KnowledgeEntry:
    """知识条目"""

    id: str
    content: str  # 知识内容
    category: str  # 分类
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0


@dataclass
class RetrievalResult:
    """检索结果"""

    entry: KnowledgeEntry
    relevance_score: float  # 相关度分数
    reasoning: str  # LLM 推理说明


class SemanticMemory:
    """Semantic Memory - LLM 推理知识检索 (L2)

    特点:
    - PostgreSQL JSONB 存储
    - LLM 推理检索 (可选)
    - 知识分类和标签
    - 访问计数和权重
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        llm_client: Optional[Any] = None,  # UnifiedLLMClient
    ):
        self.database_url = database_url
        self.llm_client = llm_client
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初始化数据库连接"""
        if not self.database_url:
            import os
            self.database_url = os.getenv("DATABASE_URL")
            if not self.database_url:
                logger.warning("DATABASE_URL not configured, SemanticMemory will use in-memory mode")
                self._in_memory_mode = True
                self._memory_store: dict[str, KnowledgeEntry] = {}
                return

        self._pool = await asyncpg.create_pool(self.database_url)
        await self._init_tables()
        self._in_memory_mode = False
        logger.info("SemanticMemory initialized with PostgreSQL")

    async def _init_tables(self) -> None:
        """初始化表"""
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content TEXT NOT NULL,
                    category VARCHAR(255) NOT NULL,
                    tags JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}',
                    agent_id VARCHAR(255),
                    task_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    access_count INTEGER DEFAULT 0
                )
            """)

            # 索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_category
                ON semantic_memory(category)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_tags
                USING GIN (tags)
            """)

    async def close(self) -> None:
        """关闭连接"""
        if self._pool:
            await self._pool.close()

    # ====================
    # 知识存储
    # ====================

    async def store(
        self,
        content: str,
        category: str,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """存储知识条目

        Args:
            content: 知识内容
            category: 分类
            tags: 标签
            metadata: 元数据
            agent_id: Agent ID
            task_id: 任务 ID

        Returns:
            entry_id
        """
        entry_id = str(uuid4())
        now = datetime.now()

        if self._in_memory_mode:
            entry = KnowledgeEntry(
                id=entry_id,
                content=content,
                category=category,
                tags=tags or [],
                metadata=metadata or {},
                agent_id=agent_id,
                task_id=task_id,
                created_at=now,
                updated_at=now,
            )
            self._memory_store[entry_id] = entry
            return entry_id

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO semantic_memory
                (id, content, category, tags, metadata, agent_id, task_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                entry_id,
                content,
                category,
                json.dumps(tags or []),
                json.dumps(metadata or {}),
                agent_id,
                task_id,
                now,
                now,
            )

        logger.info(f"Stored knowledge entry: {entry_id}")
        return entry_id

    async def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """获取知识条目"""
        if self._in_memory_mode:
            entry = self._memory_store.get(entry_id)
            if entry:
                entry.access_count += 1
            return entry

        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM semantic_memory WHERE id = $1",
                entry_id,
            )

        if not row:
            return None

        # 更新访问计数
        await conn.execute(
            "UPDATE semantic_memory SET access_count = access_count + 1 WHERE id = $1",
            entry_id,
        )

        return self._row_to_entry(row)

    async def list_by_category(
        self,
        category: str,
        limit: int = 20,
    ) -> list[KnowledgeEntry]:
        """按分类列出知识"""
        if self._in_memory_mode:
            return [
                e for e in self._memory_store.values()
                if e.category == category
            ][:limit]

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM semantic_memory
                WHERE category = $1
                ORDER BY access_count DESC, created_at DESC
                LIMIT $2
                """,
                category,
                limit,
            )

        return [self._row_to_entry(row) for row in rows]

    async def list_by_tags(
        self,
        tags: list[str],
        limit: int = 20,
    ) -> list[KnowledgeEntry]:
        """按标签列出知识"""
        if self._in_memory_mode:
            return [
                e for e in self._memory_store.values()
                if any(t in e.tags for t in tags)
            ][:limit]

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM semantic_memory
                WHERE tags ?| $1
                ORDER BY access_count DESC, created_at DESC
                LIMIT $2
                """,
                tags,
                limit,
            )

        return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row: dict) -> KnowledgeEntry:
        """数据库行转换为 KnowledgeEntry"""
        return KnowledgeEntry(
            id=str(row["id"]),
            content=row["content"],
            category=row["category"],
            tags=row["tags"] or [],
            metadata=row["metadata"] or {},
            agent_id=row["agent_id"],
            task_id=row["task_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            access_count=row["access_count"],
        )

    # ====================
    # LLM 推理检索 (可选)
    # ====================

    async def retrieve(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        limit: int = 5,
        use_llm: bool = True,
    ) -> list[RetrievalResult]:
        """检索知识

        Args:
            query: 查询文本
            context: 上下文信息
            limit: 返回数量
            use_llm: 是否使用 LLM 推理 (需要配置 LLM client)

        Returns:
            检索结果列表
        """
        if not use_llm or not self.llm_client:
            # 简单关键词匹配
            return await self._simple_retrieve(query, limit)

        # LLM 推理检索
        return await self._llm_retrieve(query, context, limit)

    async def _simple_retrieve(
        self,
        query: str,
        limit: int,
    ) -> list[RetrievalResult]:
        """简单关键词检索"""
        if self._in_memory_mode:
            entries = list(self._memory_store.values())
        else:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM semantic_memory
                    WHERE content ILIKE $1
                    ORDER BY access_count DESC
                    LIMIT $2
                    """,
                    f"%{query}%",
                    limit,
                )
            entries = [self._row_to_entry(row) for row in rows]

        # 计算简单相关度
        results = []
        query_lower = query.lower()
        for entry in entries[:limit]:
            score = sum(
                1 for word in entry.content.lower().split()
                if word in query_lower
            ) / max(len(query.split()), 1)
            results.append(RetrievalResult(
                entry=entry,
                relevance_score=score,
                reasoning="Keyword matching",
            ))

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)

    async def _llm_retrieve(
        self,
        query: str,
        context: Optional[dict[str, Any]],
        limit: int,
    ) -> list[RetrievalResult]:
        """LLM 推理检索"""
        # 1. 先获取候选知识
        candidates = await self._simple_retrieve(query, limit * 3)

        if not candidates or not self.llm_client:
            return candidates[:limit]

        # 2. 用 LLM 推理相关度
        prompt = self._build_relevance_prompt(query, candidates, context)

        try:
            response = await self.llm_client.chat(
                model="haiku",  # 用便宜的模型
                messages=[{"role": "user", "content": prompt}],
            )

            # 解析 LLM 响应，提取相关条目
            results = self._parse_llm_response(response.content, candidates)
            return results[:limit]

        except Exception as e:
            logger.warning(f"LLM retrieval failed: {e}, falling back to simple")
            return candidates[:limit]

    def _build_relevance_prompt(
        self,
        query: str,
        candidates: list[RetrievalResult],
        context: Optional[dict],
    ) -> str:
        """构建相关度判断 Prompt"""
        entries_text = "\n".join([
            f"- [{i+1}] {c.entry.content[:200]}..."
            for i, c in enumerate(candidates)
        ])

        return f"""Given the query: "{query}"

Evaluate which knowledge entries are most relevant. Return the indices (1-based) of the top entries, with a brief reason.

Knowledge entries:
{entries_text}

Return in format:
1. [index] - reason
2. [index] - reason
"""

    def _parse_llm_response(
        self,
        llm_response: str,
        candidates: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """解析 LLM 响应"""
        results = []
        for line in llm_response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            # 尝试提取索引
            for i, c in enumerate(candidates):
                if f"[{i+1}]" in line or f"{i+1}." in line:
                    c.relevance_score = 0.9
                    c.reasoning = line
                    results.append(c)
                    break

        # 如果没有解析成功，返回原候选
        if not results:
            return candidates

        return sorted(results, key=lambda r: r.relevance_score, reverse=True)


# ====================
# 全局实例
# ====================

_semantic_memory_instance: Optional[SemanticMemory] = None


async def get_semantic_memory() -> SemanticMemory:
    """获取全局 SemanticMemory 实例"""
    global _semantic_memory_instance
    if _semantic_memory_instance is None:
        _semantic_memory_instance = SemanticMemory()
        await _semantic_memory_instance.initialize()
    return _semantic_memory_instance


def set_semantic_memory(memory: SemanticMemory) -> None:
    """设置全局 SemanticMemory 实例"""
    global _semantic_memory_instance
    _semantic_memory_instance = memory
