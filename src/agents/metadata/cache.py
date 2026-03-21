"""
Metadata Cache - 元数据缓存层

提供元数据的缓存管理:
- 内存缓存
- 持久化缓存
- 过期策略
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .schema import AgentMetadata, MetadataLevel

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""

    metadata: AgentMetadata
    timestamp: float
    ttl: float  # 生存时间（秒）
    level: MetadataLevel

    def is_expired(self) -> bool:
        """是否过期"""
        if self.ttl <= 0:
            return False
        return time.time() - self.timestamp > self.ttl


class MetadataCache:
    """元数据缓存

    支持内存缓存和持久化缓存
    """

    DEFAULT_TTL = 3600  # 默认 TTL: 1 小时

    def __init__(
        self,
        max_size: int = 100,
        persist_path: Optional[str] = None,
        default_ttl: float = DEFAULT_TTL,
    ):
        self._max_size = max_size
        self._persist_path = persist_path
        self._default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

        # 加载持久化缓存
        if persist_path:
            self._load_persistent()

    async def get(self, agent_id: str) -> Optional[AgentMetadata]:
        """获取缓存

        Args:
            agent_id: Agent ID

        Returns:
            元数据或 None
        """
        async with self._lock:
            entry = self._cache.get(agent_id)
            if not entry:
                return None

            if entry.is_expired():
                del self._cache[agent_id]
                return None

            return entry.metadata

    async def set(
        self,
        agent_id: str,
        metadata: AgentMetadata,
        ttl: Optional[float] = None,
    ):
        """设置缓存

        Args:
            agent_id: Agent ID
            metadata: 元数据
            ttl: 可选的 TTL
        """
        async with self._lock:
            # 检查大小
            if len(self._cache) >= self._max_size:
                await self._evict_oldest()

            entry = CacheEntry(
                metadata=metadata,
                timestamp=time.time(),
                ttl=ttl or self._default_ttl,
                level=metadata.loaded_level,
            )
            self._cache[agent_id] = entry

            # 持久化
            if self._persist_path:
                await self._persist()

    async def delete(self, agent_id: str):
        """删除缓存"""
        async with self._lock:
            if agent_id in self._cache:
                del self._cache[agent_id]
                if self._persist_path:
                    await self._persist()

    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
            if self._persist_path:
                await self._persist()

    async def _evict_oldest(self):
        """驱逐最老的条目"""
        if not self._cache:
            return

        # 找到最老的
        oldest = min(self._cache.items(), key=lambda x: x[1].timestamp)
        del self._cache[oldest[0]]
        logger.debug(f"Evicted {oldest[0]} from cache")

    def _load_persistent(self):
        """加载持久化缓存"""
        if not self._persist_path:
            return

        path = Path(self._persist_path)
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text())
            for agent_id, entry_data in data.items():
                metadata = AgentMetadata(
                    agent_id=entry_data["agent_id"],
                    name=entry_data["name"],
                    description=entry_data.get("description", ""),
                    version=entry_data.get("version", "1.0.0"),
                    source_repo=entry_data.get("source_repo", ""),
                    badges=entry_data.get("badges", []),
                )
                entry = CacheEntry(
                    metadata=metadata,
                    timestamp=entry_data["timestamp"],
                    ttl=entry_data.get("ttl", self._default_ttl),
                    level=MetadataLevel(entry_data.get("level", 1)),
                )
                if not entry.is_expired():
                    self._cache[agent_id] = entry

            logger.info(f"Loaded {len(self._cache)} entries from persistent cache")
        except Exception as e:
            logger.warning(f"Failed to load persistent cache: {e}")

    async def _persist(self):
        """持久化缓存"""
        if not self._persist_path:
            return

        try:
            data = {}
            for agent_id, entry in self._cache.items():
                data[agent_id] = {
                    "agent_id": entry.metadata.agent_id,
                    "name": entry.metadata.name,
                    "description": entry.metadata.description,
                    "version": entry.metadata.version,
                    "source_repo": entry.metadata.source_repo,
                    "badges": entry.metadata.badges,
                    "timestamp": entry.timestamp,
                    "ttl": entry.ttl,
                    "level": entry.level.value,
                }

            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data, indent=2))

        except Exception as e:
            logger.error(f"Failed to persist cache: {e}")

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        return {
            "enabled": True,
            "size": len(self._cache),
            "max_size": self._max_size,
            "persist_path": self._persist_path,
            "default_ttl": self._default_ttl,
        }
