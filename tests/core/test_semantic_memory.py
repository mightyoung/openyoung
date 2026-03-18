"""
Semantic Memory (L2) 单元测试

测试:
1. 知识存储和检索
2. LLM 推理检索 (Mock)
3. 分类和标签查询
4. 内存模式降级
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.memory.semantic import (
    SemanticMemory,
    KnowledgeEntry,
    RetrievalResult,
)


class TestKnowledgeEntry:
    """KnowledgeEntry 数据类测试"""

    def test_create_entry(self):
        """测试创建知识条目"""
        entry = KnowledgeEntry(
            id="test-001",
            content="Test content",
            category="test",
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            agent_id="agent-001",
            task_id="task-001",
        )

        assert entry.id == "test-001"
        assert entry.content == "Test content"
        assert entry.category == "test"
        assert entry.tags == ["tag1", "tag2"]
        assert entry.metadata == {"key": "value"}
        assert entry.agent_id == "agent-001"
        assert entry.task_id == "task-001"
        assert entry.access_count == 0


class TestRetrievalResult:
    """RetrievalResult 数据类测试"""

    def test_create_result(self):
        """测试创建检索结果"""
        entry = KnowledgeEntry(
            id="test-001",
            content="Test content",
            category="test",
        )
        result = RetrievalResult(
            entry=entry,
            relevance_score=0.95,
            reasoning="Highly relevant",
        )

        assert result.entry == entry
        assert result.relevance_score == 0.95
        assert result.reasoning == "Highly relevant"


class TestSemanticMemoryInMemory:
    """内存模式 SemanticMemory 测试"""

    @pytest.fixture
    def memory(self):
        """创建内存模式的 SemanticMemory"""
        mem = SemanticMemory()
        # 模拟未配置 DATABASE_URL 的情况
        mem._in_memory_mode = True
        mem._memory_store = {}
        return mem

    @pytest.mark.asyncio
    async def test_store_knowledge(self, memory):
        """测试存储知识条目"""
        entry_id = await memory.store(
            content="Python is a great language",
            category="programming",
            tags=["python", "coding"],
            metadata={"rating": 5},
        )

        assert entry_id is not None
        assert entry_id in memory._memory_store

        entry = memory._memory_store[entry_id]
        assert entry.content == "Python is a great language"
        assert entry.category == "programming"
        assert entry.tags == ["python", "coding"]
        assert entry.metadata == {"rating": 5}

    @pytest.mark.asyncio
    async def test_get_knowledge(self, memory):
        """测试获取知识条目"""
        entry_id = await memory.store(
            content="Test content",
            category="test",
        )

        entry = await memory.get(entry_id)

        assert entry is not None
        assert entry.id == entry_id
        assert entry.content == "Test content"
        assert entry.access_count == 1  # 获取后计数增加

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, memory):
        """测试获取不存在的条目"""
        entry = await memory.get("nonexistent-id")
        assert entry is None

    @pytest.mark.asyncio
    async def test_list_by_category(self, memory):
        """测试按分类列出知识"""
        # 存储多个条目
        await memory.store(content="Content 1", category="tech")
        await memory.store(content="Content 2", category="tech")
        await memory.store(content="Content 3", category="other")

        entries = await memory.list_by_category("tech")

        assert len(entries) == 2
        assert all(e.category == "tech" for e in entries)

    @pytest.mark.asyncio
    async def test_list_by_tags(self, memory):
        """测试按标签列出知识"""
        await memory.store(content="Content 1", category="tech", tags=["python", "ai"])
        await memory.store(content="Content 2", category="tech", tags=["python", "web"])
        await memory.store(content="Content 3", category="other", tags=["design"])

        entries = await memory.list_by_tags(["python"])

        assert len(entries) == 2
        assert all("python" in e.tags for e in entries)

    @pytest.mark.asyncio
    async def test_simple_retrieve_keyword(self, memory):
        """测试简单关键词检索"""
        await memory.store(content="Python is a programming language", category="tech")
        await memory.store(content="JavaScript is for web development", category="tech")
        await memory.store(content="Design patterns are important", category="design")

        results = await memory.retrieve(
            query="Python programming",
            use_llm=False,  # 禁用 LLM，使用简单检索
        )

        assert len(results) > 0
        # 应该找到包含 Python 的条目
        assert any("Python" in r.entry.content for r in results)


class TestSemanticMemoryLLM:
    """LLM 推理检索测试"""

    @pytest.fixture
    def memory_with_llm(self):
        """创建带 LLM client 的 SemanticMemory"""
        mem = SemanticMemory()
        mem._in_memory_mode = True
        mem._memory_store = {}

        # Mock LLM client
        mem.llm_client = AsyncMock()
        mem.llm_client.chat = AsyncMock(return_value=MagicMock(
            content="1. [1] - Most relevant because Python is mentioned"
        ))

        return mem

    @pytest.mark.asyncio
    async def test_retrieve_with_llm(self, memory_with_llm):
        """测试 LLM 推理检索"""
        # 存储一些知识
        await memory_with_llm.store(
            content="Python is a great programming language",
            category="tech",
        )
        await memory_with_llm.store(
            content="JavaScript is for web development",
            category="tech",
        )

        results = await memory_with_llm.retrieve(
            query="Which is better for AI?",
            use_llm=True,
        )

        # 应该调用 LLM
        assert memory_with_llm.llm_client.chat.called

    @pytest.mark.asyncio
    async def test_retrieve_fallback_on_llm_failure(self, memory_with_llm):
        """测试 LLM 失败时降级到简单检索"""
        # 模拟 LLM 调用失败
        memory_with_llm.llm_client.chat.side_effect = Exception("LLM Error")

        await memory_with_llm.store(
            content="Python is a programming language",
            category="tech",
        )

        results = await memory_with_llm.retrieve(
            query="Python",
            use_llm=True,
        )

        # 应该降级到简单检索并返回结果
        assert len(results) > 0


class TestSemanticMemoryGlobal:
    """全局实例测试"""

    def test_get_global_instance(self):
        """测试获取全局实例"""
        from src.core.memory.semantic import get_semantic_memory

        # 这个测试只是验证函数存在
        assert callable(get_semantic_memory)

    def test_set_global_instance(self):
        """测试设置全局实例"""
        from src.core.memory.semantic import set_semantic_memory, get_semantic_memory

        custom_memory = SemanticMemory()
        custom_memory._in_memory_mode = True
        custom_memory._memory_store = {}

        set_semantic_memory(custom_memory)

        # 验证已设置
        from src.core.memory import semantic as sem_module
        assert sem_module._semantic_memory_instance == custom_memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
