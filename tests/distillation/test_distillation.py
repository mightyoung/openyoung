"""
Distillation Module Tests
"""

import pytest
from src.distillation import KnowledgeDistiller, Knowledge


class TestKnowledgeDistiller:
    """Test KnowledgeDistiller functionality"""

    def test_distiller_initialization(self):
        """Test KnowledgeDistiller initialization"""
        distiller = KnowledgeDistiller()
        assert distiller._knowledge_cache == {}

    def test_extract_from_agent(self):
        """Test extracting knowledge from agent"""
        distiller = KnowledgeDistiller()

        class MockAgent:
            name = "test_agent"

        knowledge = distiller.extract(MockAgent())

        assert knowledge.experience_count == 1
        assert len(knowledge.patterns) > 0
        assert len(knowledge.key_insights) > 0

    def test_extract_from_history(self):
        """Test extracting knowledge from execution history"""
        distiller = KnowledgeDistiller()

        history = [
            {"action": "analyze", "result": "done", "success": True},
            {"action": "execute", "result": "ok", "success": True},
            {"action": "failed_action", "result": "error", "success": False},
        ]

        knowledge = distiller.extract_from_history(history)

        assert knowledge.experience_count == 3
        assert "analyze" in knowledge.action_patterns
        assert "execute" in knowledge.action_patterns
        assert len(knowledge.success_patterns) == 2

    def test_extract_from_empty_history(self):
        """Test extracting from empty history"""
        distiller = KnowledgeDistiller()

        knowledge = distiller.extract_from_history([])

        assert knowledge.experience_count == 0
        assert knowledge.action_patterns == []
        assert knowledge.success_patterns == []

    def test_compress_knowledge(self):
        """Test knowledge compression"""
        distiller = KnowledgeDistiller()

        knowledge = Knowledge(
            experience_count=10, patterns=["p1", "p2", "p3"], key_insights=["i1", "i2"]
        )

        compressed = distiller.compress(knowledge)

        assert compressed.compressed_representation is not None
        assert "3 patterns" in compressed.compressed_representation

    def test_store_and_get_knowledge(self):
        """Test knowledge cache operations"""
        distiller = KnowledgeDistiller()

        knowledge = Knowledge(experience_count=5)
        distiller.store_knowledge("agent_1", knowledge)

        retrieved = distiller.get_knowledge("agent_1")

        assert retrieved is not None
        assert retrieved.experience_count == 5

    def test_get_nonexistent_knowledge(self):
        """Test getting nonexistent knowledge"""
        distiller = KnowledgeDistiller()

        knowledge = distiller.get_knowledge("nonexistent")

        assert knowledge is None


class TestKnowledge:
    """Test Knowledge dataclass"""

    def test_knowledge_defaults(self):
        """Test Knowledge default values"""
        knowledge = Knowledge()

        assert knowledge.experience_count == 0
        assert knowledge.patterns == []
        assert knowledge.key_insights == []
        assert knowledge.action_patterns == []
        assert knowledge.success_patterns == []
        assert knowledge.compressed_representation is None

    def test_knowledge_with_values(self):
        """Test Knowledge with custom values"""
        knowledge = Knowledge(
            experience_count=10,
            patterns=["pattern1", "pattern2"],
            key_insights=["insight1"],
            action_patterns=["action1"],
            success_patterns=["success1"],
            compressed_representation="compressed_data",
        )

        assert knowledge.experience_count == 10
        assert len(knowledge.patterns) == 2
        assert len(knowledge.key_insights) == 1
        assert knowledge.compressed_representation == "compressed_data"
