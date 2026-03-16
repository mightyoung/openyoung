"""
Team Memory - 团队共享记忆

提供Agent间的共享记忆功能
"""

import asyncio
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryEntry:
    """记忆条目"""

    id: str = field(default_factory=lambda: f"mem_{uuid.uuid4().hex[:8]}")
    key: str = ""
    value: Any = None
    agent_id: str = ""  # 创建者
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    ttl: int = 3600  # 秒，0表示永不过期


class TeamMemory:
    """团队共享记忆"""

    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._memory: dict[str, MemoryEntry] = {}
        self._index: dict[str, set[str]] = defaultdict(set)  # key word -> entry_ids

        # 锁
        self._lock = asyncio.Lock()

    async def store(
        self,
        key: str,
        value: Any,
        agent_id: str,
        ttl: int = None,
    ) -> str:
        """存储记忆"""
        async with self._lock:
            entry = MemoryEntry(
                key=key,
                value=value,
                agent_id=agent_id,
                ttl=ttl or self.default_ttl,
            )

            self._memory[entry.id] = entry

            # 更新索引
            for word in key.lower().split():
                self._index[word].add(entry.id)

            return entry.id

    async def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        async with self._lock:
            # 查找匹配的key
            for entry_id in list(self._memory.keys()):
                entry = self._memory.get(entry_id)
                if entry and entry.key == key:
                    # 更新访问信息
                    entry.accessed_at = datetime.now()
                    entry.access_count += 1
                    return entry.value
            return None

    async def search(self, query: str) -> list[dict]:
        """搜索记忆"""
        query_words = query.lower().split()

        async with self._lock:
            # 收集匹配的entry_ids
            matched_ids = set()
            for word in query_words:
                if word in self._index:
                    matched_ids.update(self._index[word])

            # 获取结果
            results = []
            for entry_id in matched_ids:
                entry = self._memory.get(entry_id)
                if entry:
                    results.append(
                        {
                            "id": entry.id,
                            "key": entry.key,
                            "value": entry.value,
                            "agent_id": entry.agent_id,
                            "created_at": entry.created_at.isoformat(),
                            "access_count": entry.access_count,
                        }
                    )

            return results

    async def delete(self, entry_id: str) -> bool:
        """删除记忆"""
        async with self._lock:
            if entry_id in self._memory:
                entry = self._memory[entry_id]

                # 清理索引
                for word in entry.key.lower().split():
                    if entry_id in self._index[word]:
                        self._index[word].remove(entry_id)

                del self._memory[entry_id]
                return True
            return False

    async def clear(self, agent_id: str = None):
        """清理记忆"""
        async with self._lock:
            if agent_id:
                # 只清理特定Agent的记忆
                to_delete = [eid for eid, e in self._memory.items() if e.agent_id == agent_id]
                for eid in to_delete:
                    await self._delete_entry(eid)
            else:
                # 清理所有
                self._memory.clear()
                self._index.clear()

    async def _delete_entry(self, entry_id: str):
        """删除单个条目"""
        if entry_id in self._memory:
            entry = self._memory[entry_id]
            for word in entry.key.lower().split():
                if entry_id in self._index[word]:
                    self._index[word].remove(entry_id)
            del self._memory[entry_id]

    async def get_stats(self) -> dict:
        """获取统计信息"""
        async with self._lock:
            return {
                "total_entries": len(self._memory),
                "index_size": len(self._index),
                "agents": list(set(e.agent_id for e in self._memory.values())),
            }


class SharedContext:
    """共享上下文 - 跨Agent共享的执行上下文"""

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any):
        """设置上下文"""
        async with self._lock:
            self._context[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        async with self._lock:
            return self._context.get(key, default)

    async def update(self, updates: dict):
        """批量更新"""
        async with self._lock:
            self._context.update(updates)

    async def clear(self):
        """清空上下文"""
        async with self._lock:
            self._context.clear()

    async def to_dict(self) -> dict:
        """转换为字典"""
        async with self._lock:
            return dict(self._context)


class ConflictResolver:
    """冲突解决器"""

    def __init__(self, strategy: str = "last_write_wins"):
        self.strategy = strategy

    async def resolve(
        self,
        key: str,
        values: list[tuple[str, Any]],  # (agent_id, value)
    ) -> tuple[str, Any]:
        """
        解决冲突

        Args:
            key: 键
            values: 值列表 (agent_id, value)

        Returns:
            (winning_agent_id, value)
        """
        if not values:
            return ("", None)

        if len(values) == 1:
            return values[0]

        if self.strategy == "last_write_wins":
            # 最后一个写入获胜
            return values[-1]

        elif self.strategy == "first_write_wins":
            # 第一个写入获胜
            return values[0]

        elif self.strategy == "majority":
            # 多数投票
            from collections import Counter

            value_counts = Counter(v for _, v in values)
            winner_value = value_counts.most_common(1)[0][0]
            for agent_id, value in values:
                if value == winner_value:
                    return (agent_id, value)

        elif self.strategy == "priority":
            # 按Agent优先级 (硬编码)
            priority = {"planner": 3, "reviewer": 2, "worker": 1}
            sorted_values = sorted(
                values,
                key=lambda x: priority.get(x[0], 0),
                reverse=True,
            )
            return sorted_values[0]

        # 默认返回最后一个
        return values[-1]
