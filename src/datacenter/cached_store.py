"""
Cached DataStore - 带缓存的数据访问层
使用 cachetools 实现 LRU 缓存
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from cachetools import LRUCache, TTLCache
import threading

from .store import DataStore


class CachedDataStore(DataStore):
    """带缓存的 DataStore"""

    def __init__(self, data_dir: str = ".young",
                 maxsize: int = 100,
                 ttl: int = 3600):
        super().__init__(data_dir)

        # LRU 缓存
        self._cache = LRUCache(maxsize=maxsize)

        # TTL 缓存 (用于临时数据)
        self._ttl_cache = TTLCache(maxsize=maxsize // 2, ttl=ttl)

        # 锁
        self._lock = threading.RLock()

        # 缓存统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

    def _make_key(self, entity_type: str, entity_id: str) -> str:
        """生成缓存键"""
        return f"{entity_type}:{entity_id}"

    def _invalidate(self, entity_type: str, entity_id: str):
        """使缓存失效"""
        key = self._make_key(entity_type, entity_id)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._ttl_cache:
                del self._ttl_cache[key]

    def get_agent(self, agent_id: str, use_cache: bool = True) -> Optional[Dict]:
        """获取 Agent (带缓存)"""
        if not use_cache:
            return super().get_agent(agent_id)

        key = self._make_key("agent", agent_id)

        with self._lock:
            if key in self._cache:
                self._stats["hits"] += 1
                return self._cache[key]

            self._stats["misses"] += 1

        # 缓存未命中，查询数据库
        result = super().get_agent(agent_id)

        if result:
            with self._lock:
                self._cache[key] = result

        return result

    def save_agent(self, agent_id: str, data: Dict) -> str:
        """保存 Agent (使缓存失效)"""
        result = super().save_agent(agent_id, data)
        self._invalidate("agent", agent_id)
        return result

    def delete_agent(self, agent_id: str) -> bool:
        """删除 Agent (使缓存失效)"""
        result = super().delete_agent(agent_id)
        self._invalidate("agent", agent_id)
        return result

    def get_run(self, run_id: str, use_cache: bool = True) -> Optional[Dict]:
        """获取 Run (带缓存)"""
        if not use_cache:
            return super().get_run(run_id)

        key = self._make_key("run", run_id)

        with self._lock:
            if key in self._cache:
                self._stats["hits"] += 1
                return self._cache[key]

            self._stats["misses"] += 1

        result = super().get_run(run_id)

        if result:
            with self._lock:
                self._cache[key] = result

        return result

    def save_run(self, run_id: str, data: Dict) -> str:
        """保存 Run (使缓存失效)"""
        result = super().save_run(run_id, data)
        self._invalidate("run", run_id)
        return result

    def get_checkpoint(self, checkpoint_id: str, use_cache: bool = True) -> Optional[Dict]:
        """获取 Checkpoint (带缓存)"""
        if not use_cache:
            return super().get_checkpoint(checkpoint_id)

        key = self._make_key("checkpoint", checkpoint_id)

        with self._lock:
            if key in self._cache:
                self._stats["hits"] += 1
                return self._cache[key]

            self._stats["misses"] += 1

        result = super().get_checkpoint(checkpoint_id)

        if result:
            with self._lock:
                self._cache[key] = result

        return result

    def save_checkpoint(self, checkpoint_id: str, data: Dict) -> str:
        """保存 Checkpoint (使缓存失效)"""
        result = super().save_checkpoint(checkpoint_id, data)
        self._invalidate("checkpoint", checkpoint_id)
        return result

    def get_workspace(self, workspace_id: str, use_cache: bool = True) -> Optional[Dict]:
        """获取 Workspace (带缓存)"""
        if not use_cache:
            return super().get_workspace(workspace_id)

        key = self._make_key("workspace", workspace_id)

        with self._lock:
            if key in self._cache:
                self._stats["hits"] += 1
                return self._cache[key]

            self._stats["misses"] += 1

        result = super().get_workspace(workspace_id)

        if result:
            with self._lock:
                self._cache[key] = result

        return result

    def save_workspace(self, workspace_id: str, data: Dict) -> str:
        """保存 Workspace (使缓存失效)"""
        result = super().save_workspace(workspace_id, data)
        self._invalidate("workspace", workspace_id)
        return result

    def clear_cache(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._ttl_cache.clear()

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0

            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "size": len(self._cache),
                "maxsize": self._cache.maxsize
            }


# ========== 便捷函数 ==========

def get_cached_store(data_dir: str = ".young", maxsize: int = 100, ttl: int = 3600) -> CachedDataStore:
    """获取带缓存的 DataStore"""
    return CachedDataStore(data_dir, maxsize, ttl)
