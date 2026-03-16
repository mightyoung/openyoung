"""
Progressive Loader - 渐进式加载器

按需加载不同层级的元数据:
- Level 1: Basic (name, description, badges)
- Level 2: Capabilities + Skills
- Level 3: Orchestration
- Level 4: Performance
"""

import asyncio
import logging
from typing import Any, Optional

from .schema import AgentMetadata, MetadataLevel

logger = logging.getLogger(__name__)


class ProgressiveLoader:
    """渐进式元数据加载器

    支持按需加载不同层级的元数据，减少初始加载时间。
    """

    def __init__(self, cache=None):
        self._cache = cache
        self._extractors = {}

    def register_extractor(self, source_type: str, extractor):
        """注册提取器

        Args:
            source_type: 源类型 (github, local, registry)
            extractor: 提取器实例
        """
        self._extractors[source_type] = extractor

    async def load(
        self,
        agent_id: str,
        source_type: str,
        source: str,
        level: MetadataLevel = MetadataLevel.LEVEL_1_BASIC,
        force_refresh: bool = False,
    ) -> AgentMetadata:
        """加载元数据

        Args:
            agent_id: Agent ID
            source_type: 源类型 (github, local, registry)
            source: 源位置 (URL 或路径)
            level: 目标加载层级
            force_refresh: 强制刷新缓存

        Returns:
            Agent 元数据
        """
        # 检查缓存
        if self._cache and not force_refresh:
            cached = await self._cache.get(agent_id)
            if cached and cached.loaded_level.value >= level.value:
                logger.debug(f"Using cached metadata for {agent_id}")
                return cached

        # 获取提取器
        extractor = self._extractors.get(source_type)
        if not extractor:
            raise ValueError(f"No extractor registered for {source_type}")

        # 提取元数据
        if source_type == "github":
            result = await extractor.extract_from_github(source)
            metadata = result.metadata
        elif source_type == "local":
            result = await extractor.extract_from_local(source)
            metadata = result.metadata
        else:
            raise ValueError(f"Unknown source type: {source_type}")

        # 按需升级层级
        await self._ensure_level(metadata, level, source_type, source)

        # 缓存
        if self._cache:
            await self._cache.set(agent_id, metadata)

        return metadata

    async def _ensure_level(
        self,
        metadata: AgentMetadata,
        target_level: MetadataLevel,
        source_type: str,
        source: str,
    ):
        """确保达到目标层级"""
        if metadata.loaded_level.value >= target_level.value:
            return

        # 提取器只负责基础层级
        # 更高级别需要额外的 API 调用或计算
        logger.debug(
            f"Level upgrade not fully implemented: {metadata.loaded_level} -> {target_level}"
        )
        metadata.upgrade_level(target_level)

    async def load_batch(
        self,
        agents: list[dict[str, Any]],
        level: MetadataLevel = MetadataLevel.LEVEL_1_BASIC,
    ) -> dict[str, AgentMetadata]:
        """批量加载元数据

        Args:
            agents: Agent 列表 [{"agent_id": ..., "source_type": ..., "source": ...}, ...]
            level: 目标加载层级

        Returns:
            agent_id -> 元数据 的映射
        """
        results = {}

        # 并行加载
        tasks = [
            self.load(agent["agent_id"], agent["source_type"], agent["source"], level)
            for agent in agents
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        for agent, result in zip(agents, completed):
            if isinstance(result, Exception):
                logger.error(f"Failed to load {agent['agent_id']}: {result}")
            else:
                results[agent["agent_id"]] = result

        return results

    async def prefetch(
        self,
        agent_ids: list[str],
        level: MetadataLevel = MetadataLevel.LEVEL_1_BASIC,
    ):
        """预取多个 Agent 的元数据

        Args:
            agent_ids: Agent ID 列表
            level: 预取层级
        """
        # TODO: 从注册表获取源信息
        pass

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        if self._cache:
            return self._cache.get_stats()
        return {"enabled": False}
