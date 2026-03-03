"""
AutoMemory - 自动记忆系统（三层记忆）
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Memory:
    """记忆单元"""

    id: str
    content: str
    importance: float
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    tags: List[str] = field(default_factory=list)


class AutoMemory:
    """自动记忆系统 - 三层记忆架构

    - Working Memory: 当前任务相关
    - Session Memory: 当前会话
    - Persistent Memory: 长期记忆
    """

    def __init__(self, max_memories: int = 100, importance_threshold: float = 0.5):
        self.max_memories = max_memories
        self.importance_threshold = importance_threshold

        # 三层记忆
        self.working_memory: List[Memory] = []  # 当前任务
        self.session_memory: List[Memory] = []  # 当前会话
        self.persistent_memory: List[Memory] = []  # 长期记忆

    async def add_memory(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        layer: str = "session",
    ) -> Optional[Memory]:
        """添加记忆

        Args:
            content: 记忆内容
            context: 上下文
            layer: 记忆层 (working/session/persistent)

        Returns:
            创建的 Memory 或 None
        """
        # 评估重要性
        importance = await self._evaluate_importance(content, context)

        # 只保留重要记忆
        if importance < self.importance_threshold and layer != "working":
            return None

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            importance=importance,
            created_at=datetime.now(),
            last_accessed=datetime.now(),
        )

        # 添加到对应层
        if layer == "working":
            self.working_memory.append(memory)
        elif layer == "session":
            self.session_memory.append(memory)
        else:
            self.persistent_memory.append(memory)

        # 清理
        await self._cleanup()

        return memory

    async def get_relevant_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """获取相关记忆

        按重要性排序，返回最相关的记忆
        """
        # 合并所有记忆层
        all_memories = (
            self.working_memory + self.session_memory + self.persistent_memory
        )

        # 按重要性和访问次数排序
        relevant = sorted(
            all_memories, key=lambda m: (m.importance, m.access_count), reverse=True
        )[:limit]

        # 更新访问记录
        for memory in relevant:
            memory.access_count += 1
            memory.last_accessed = datetime.now()

        return relevant

    async def clear_working_memory(self):
        """清除工作记忆"""
        self.working_memory.clear()

    async def clear_session_memory(self):
        """清除会话记忆"""
        self.session_memory.clear()

    async def promote_to_persistent(self, memory_id: str) -> bool:
        """将记忆提升到持久层"""
        for memory in self.session_memory:
            if memory.id == memory_id:
                self.session_memory.remove(memory)
                self.persistent_memory.append(memory)
                return True
        return False

    async def _evaluate_importance(
        self, content: str, context: Optional[Dict[str, Any]]
    ) -> float:
        """评估记忆重要性

        简单实现：基于内容关键词
        """
        important_keywords = [
            "error",
            "bug",
            "fix",
            "important",
            "critical",
            "learned",
            "remember",
            "config",
            "password",
            "secret",
        ]

        content_lower = content.lower()

        # 计算重要性分数
        score = 0.5  # 默认基础分数

        for keyword in important_keywords:
            if keyword in content_lower:
                score += 0.1

        return min(score, 1.0)  # 最高1.0

    async def _cleanup(self):
        """清理超过限制的记忆"""
        # 限制各层大小
        if len(self.working_memory) > 10:
            self.working_memory = self.working_memory[-10:]

        if len(self.session_memory) > 50:
            self.session_memory = self.session_memory[-50:]

        if len(self.persistent_memory) > self.max_memories:
            self.persistent_memory = self.persistent_memory[-self.max_memories :]

    def get_stats(self) -> Dict[str, int]:
        """获取记忆统计"""
        return {
            "working": len(self.working_memory),
            "session": len(self.session_memory),
            "persistent": len(self.persistent_memory),
            "total": len(self.working_memory)
            + len(self.session_memory)
            + len(self.persistent_memory),
        }
