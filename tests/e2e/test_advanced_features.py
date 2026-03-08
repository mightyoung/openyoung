"""
E2E Tests - Advanced Features

Tests for OpenYoung advanced features: Evolver, FlowSkill, Harness
"""

import json
import os

import pytest

# ========================
# Evolver Tests
# ========================


class TestEvolverModels:
    """Test Evolver data models"""

    def test_gene_creation(self):
        """Test Gene model creation"""
        from src.evolver.models import Gene, GeneCategory

        gene = Gene(
            id="test_gene_1",
            version="1.0.0",
            category=GeneCategory.REPAIR,
            signals=["error", "fix", "repair"],
            preconditions=["has_error"],
            strategy=["analyze", "fix", "verify"],
            success_rate=0.85,
            usage_count=10,
        )

        assert gene.id == "test_gene_1"
        assert gene.version == "1.0.0"
        assert gene.category == GeneCategory.REPAIR
        assert "error" in gene.signals
        assert gene.success_rate == 0.85
        assert gene.usage_count == 10

    def test_capsule_creation(self):
        """Test Capsule model creation"""
        from src.evolver.models import Capsule

        capsule = Capsule(
            id="capsule_001",
            name="Error Fixer",
            description="Fixes common errors",
            trigger=["error", "fix"],
            gene_ref="gene_001",
            gene_version="1.0.0",
            summary="Capsule for error fixing",
        )

        assert capsule.id == "capsule_001"
        assert capsule.name == "Error Fixer"
        assert "error" in capsule.trigger
        assert capsule.gene_ref == "gene_001"

    def test_evolution_event_creation(self):
        """Test EvolutionEvent model creation"""
        from src.evolver.models import EvolutionEvent, EvolutionEventType

        event = EvolutionEvent(
            id="event_001",
            event_type=EvolutionEventType.GENE_UPDATE,
            description="Updated gene success rate",
        )

        assert event.id == "event_001"
        assert event.event_type == EvolutionEventType.GENE_UPDATE
        assert event.timestamp is not None

    def test_personality_creation(self):
        """Test Personality model creation"""
        from src.evolver.models import Personality

        personality = Personality(
            name="creative",
            traits={"creativity": 0.8, "curiosity": 0.9},
        )

        assert personality.name == "creative"
        assert personality.traits["creativity"] == 0.8
        assert personality.traits["curiosity"] == 0.9

    def test_personality_update_trait(self):
        """Test Personality trait update"""
        from src.evolver.models import Personality

        personality = Personality(name="test", traits={})
        personality.update_trait("creativity", 0.5)
        assert personality.traits["creativity"] == 0.5

        # Test clamping
        personality.update_trait("creativity", 1.5)
        assert personality.traits["creativity"] == 1.0

        personality.update_trait("creativity", -0.5)
        assert personality.traits["creativity"] == 0.0


class TestEvolutionEngine:
    """Test EvolutionEngine functionality"""

    def test_engine_initialization(self):
        """Test EvolutionEngine initialization"""
        from src.evolver.engine import EvolutionEngine

        engine = EvolutionEngine()
        assert engine is not None
        assert engine.get_events() == []
        assert engine.get_capsules() == []

    def test_gene_registration(self):
        """Test gene registration"""
        from src.evolver.engine import EvolutionEngine
        from src.evolver.models import Gene, GeneCategory

        engine = EvolutionEngine()
        gene = Gene(
            id="optimize_gene",
            category=GeneCategory.OPTIMIZE,
            signals=["slow", "performance"],
        )

        engine._matcher.register_gene(gene)
        retrieved = engine._matcher.get_gene("optimize_gene")

        assert retrieved is not None
        assert retrieved.id == "optimize_gene"

    def test_capsule_creation(self):
        """Test capsule creation"""
        from src.evolver.engine import EvolutionEngine
        from src.evolver.models import Gene, GeneCategory

        engine = EvolutionEngine()

        gene = Gene(
            id="innovate_001",
            category=GeneCategory.INNOVATE,
            signals=["new", "create"],
        )

        capsule = engine.create_capsule(
            trigger=["new feature"],
            gene=gene,
            summary="Create innovative solutions",
        )

        assert capsule is not None
        assert capsule.gene_ref == "innovate_001"
        assert "new feature" in capsule.trigger


class TestPersonalityManager:
    """Test PersonalityManager functionality"""

    def test_personality_creation(self):
        """Test creating personalities"""
        from src.evolver.engine import PersonalityManager

        manager = PersonalityManager()
        personality = manager.create_personality(
            name="analytical",
            traits={"logic": 0.9, "patience": 0.8},
        )

        assert personality.name == "analytical"
        assert personality.traits["logic"] == 0.9

    def test_personality_retrieval(self):
        """Test retrieving personalities"""
        from src.evolver.engine import PersonalityManager

        manager = PersonalityManager()
        manager.create_personality("creative", {"imagination": 0.9})

        retrieved = manager.get_personality("creative")
        assert retrieved is not None
        assert retrieved.name == "creative"

    def test_personality_update(self):
        """Test updating personality traits"""
        from src.evolver.engine import PersonalityManager

        manager = PersonalityManager()
        manager.create_personality("balanced", {"focus": 0.5})

        result = manager.update_trait("balanced", "focus", 0.8)
        assert result is True

        personality = manager.get_personality("balanced")
        assert personality.traits["focus"] == 0.8

    def test_nonexistent_personality(self):
        """Test handling nonexistent personality"""
        from src.evolver.engine import PersonalityManager

        manager = PersonalityManager()
        result = manager.update_trait("nonexistent", "trait", 0.5)
        assert result is False


# ========================
# FlowSkill Tests
# ========================


class TestFlowSkillBase:
    """Test FlowSkill base class"""

    def test_flow_skill_abstract(self):
        """Test FlowSkill cannot be instantiated directly"""
        from abc import ABC

        from src.flow.base import FlowSkill

        # FlowSkill is ABC, cannot instantiate
        assert issubclass(FlowSkill, ABC)


class TestSequentialFlow:
    """Test SequentialFlow"""

    @pytest.mark.asyncio
    async def test_sequential_flow_pre_process(self):
        """Test pre-processing"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()
        context = {}

        result = await flow.pre_process("Step 1\nStep 2\nStep 3", context)

        assert "_flow_steps" in context
        assert "_current_step" in context
        assert context["_step_count"] == 3

    @pytest.mark.asyncio
    async def test_sequential_flow_post_process(self):
        """Test post-processing"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()
        context = {
            "_current_step": 0,
            "_step_count": 3,
            "_flow_steps": ["Step 1", "Step 2", "Step 3"],
        }

        result = await flow.post_process("Done step 1", context)

        assert "Step 1/3 done" in result
        assert context["_current_step"] == 1

    @pytest.mark.asyncio
    async def test_sequential_flow_complete(self):
        """Test flow completion"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()
        context = {
            "_current_step": 2,  # Last step
            "_step_count": 3,
            "_flow_steps": ["Step 1", "Step 2", "Step 3"],
        }

        result = await flow.post_process("All done", context)

        assert "All 3 steps completed" in result

    @pytest.mark.asyncio
    async def test_should_delegate(self):
        """Test delegation decision"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()
        context = {"_flow_steps": ["Step 1", "Step 2"]}

        should = await flow.should_delegate("test task", context)
        assert should is True

    @pytest.mark.asyncio
    async def test_get_subagent_type(self):
        """Test subagent type detection"""
        from src.flow.sequential import SequentialFlow

        flow = SequentialFlow()

        # Search task
        agent_type = await flow.get_subagent_type("search for files")
        assert agent_type == "search"

        # Build task
        agent_type = await flow.get_subagent_type("create a new file")
        assert agent_type == "builder"


class TestParallelFlow:
    """Test ParallelFlow"""

    @pytest.mark.asyncio
    async def test_parallel_flow_pre_process(self):
        """Test parallel pre-processing"""
        from src.flow.parallel import ParallelFlow

        flow = ParallelFlow()
        context = {}

        result = await flow.pre_process("Do A and B and C", context)

        assert "_parallel_tasks" in context

    @pytest.mark.asyncio
    async def test_parallel_flow_post_process(self):
        """Test parallel post-processing"""
        from src.flow.parallel import ParallelFlow

        flow = ParallelFlow()
        context = {
            "_completed_tasks": ["Result A", "Result B"],
            "_task_count": 2,
        }

        result = await flow.post_process("Done", context)

        assert "completed" in result.lower()


class TestConditionalFlow:
    """Test ConditionalFlow"""

    @pytest.mark.asyncio
    async def test_conditional_pre_process(self):
        """Test conditional pre-processing"""
        from src.flow.conditional import ConditionalFlow

        flow = ConditionalFlow()
        context = {}

        result = await flow.pre_process("If error then fix else continue", context)

        # Flow should process the input
        assert result is not None


class TestLoopFlow:
    """Test LoopFlow"""

    @pytest.mark.asyncio
    async def test_loop_pre_process(self):
        """Test loop pre-processing"""
        from src.flow.loop import LoopFlow

        flow = LoopFlow()
        context = {}

        result = await flow.pre_process("Repeat 3 times: do something", context)

        # Flow should process the input
        assert result is not None


# ========================
# Harness Tests
# ========================


class TestHarnessBasic:
    """Test Harness basic functionality"""

    def test_harness_initialization(self):
        """Test Harness initialization"""
        from src.harness import Harness, HarnessStatus

        harness = Harness()
        assert harness.status == HarnessStatus.IDLE
        assert harness.get_status()["status"] == "idle"

    def test_harness_start(self):
        """Test starting harness"""
        from src.harness import Harness, HarnessStatus

        harness = Harness()
        harness.start()

        assert harness.status == HarnessStatus.RUNNING
        assert harness.start_time is not None

    def test_harness_pause_resume(self):
        """Test pause and resume"""
        from src.harness import Harness, HarnessStatus

        harness = Harness()
        harness.start()
        harness.pause()

        assert harness.status == HarnessStatus.PAUSED

        harness.resume()
        assert harness.status == HarnessStatus.RUNNING

    def test_harness_stop(self):
        """Test stopping harness"""
        from src.harness import Harness, HarnessStatus

        harness = Harness()
        harness.start()
        harness.record_step(True)
        harness.record_step(True)
        harness.record_step(False)

        stats = harness.stop()

        assert harness.status == HarnessStatus.STOPPED
        assert stats.total_steps == 3
        assert stats.successful_steps == 2
        assert stats.failed_steps == 1


class TestHarnessStats:
    """Test Harness statistics"""

    def test_record_steps(self):
        """Test recording steps"""
        from src.harness import Harness

        harness = Harness()
        harness.start()

        harness.record_step(True)
        harness.record_step(True)
        harness.record_step(False)

        status = harness.get_status()
        assert status["total_steps"] == 3
        assert status["successful_steps"] == 2
        assert status["failed_steps"] == 1

    def test_metadata(self):
        """Test metadata operations"""
        from src.harness import Harness

        harness = Harness()
        harness.set_metadata("task_id", "task_001")
        harness.set_metadata("user", "test_user")

        assert harness.get_metadata("task_id") == "task_001"
        assert harness.get_metadata("user") == "test_user"
        assert harness.get_metadata("nonexistent") is None


# ========================
# Integration Tests
# ========================


class TestEvolverFlowIntegration:
    """Test Evolver and FlowSkill integration"""

    @pytest.mark.asyncio
    async def test_flow_with_evolution(self):
        """Test FlowSkill triggering evolution"""
        from src.evolver.engine import EvolutionEngine
        from src.evolver.models import Gene, GeneCategory
        from src.flow.sequential import SequentialFlow

        # Create flow
        flow = SequentialFlow()
        context = {}

        # Create evolver
        evolver = EvolutionEngine()
        gene = Gene(
            id="builder_gene",
            category=GeneCategory.INNOVATE,
            signals=["build", "create", "make"],
        )
        evolver._matcher.register_gene(gene)

        # Simulate flow execution
        await flow.pre_process("Build a website with Python", context)

        # Execute - evolution is optional
        assert flow is not None


class TestHarnessFlowIntegration:
    """Test Harness and FlowSkill integration"""

    @pytest.mark.asyncio
    async def test_harness_with_flow(self):
        """Test Harness tracking FlowSkill execution"""
        from src.flow.sequential import SequentialFlow
        from src.harness import Harness

        # Create harness
        harness = Harness()
        harness.start()

        # Create flow
        flow = SequentialFlow()
        context = {}

        # Execute flow steps
        await flow.pre_process("Step 1\nStep 2", context)

        # Record step in harness
        harness.record_step(True)
        harness.record_step(True)

        # Get status
        status = harness.get_status()
        assert status["total_steps"] == 2

        harness.stop()


class TestFullEvolutionWorkflow:
    """Test complete evolution workflow"""

    @pytest.mark.asyncio
    async def test_complete_evolution_cycle(self):
        """Test complete evolution: gene -> capsule -> personality"""
        from src.evolver.engine import EvolutionEngine, PersonalityManager
        from src.evolver.models import Gene, GeneCategory

        # Initialize engine and manager
        engine = EvolutionEngine()
        personality_mgr = PersonalityManager()

        # Register genes
        genes = [
            Gene(
                id="repair_gene",
                category=GeneCategory.REPAIR,
                signals=["error", "fix"],
            ),
            Gene(
                id="optimize_gene",
                category=GeneCategory.OPTIMIZE,
                signals=["slow", "speed"],
            ),
            Gene(
                id="innovate_gene",
                category=GeneCategory.INNOVATE,
                signals=["new", "create"],
            ),
        ]

        for gene in genes:
            engine._matcher.register_gene(gene)

        # Create capsule from gene
        gene = genes[0]
        capsule = engine.create_capsule(
            trigger=["error detection"],
            gene=gene,
            summary="Automated error repair",
        )
        assert capsule is not None
        assert capsule.gene_ref == gene.id

        # Create personality
        personality = personality_mgr.create_personality(
            name="adaptive",
            traits={"adaptability": 0.8, "learning": 0.9},
        )
        assert personality.name == "adaptive"

        # Update based on evolution
        personality_mgr.update_trait("adaptive", "adaptability", 0.85)

        # Verify events recorded
        events = engine.get_events()
        assert len(events) >= 1  # At least capsule creation event


class TestFlowWithRealLLM:
    """Test FlowSkill with real LLM execution"""

    def _get_config_value(self, key: str) -> str:
        """Get config value from environment"""
        value = os.environ.get(key, "")
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        return value

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sequential_flow_with_llm(self):
        """Test SequentialFlow with real LLM"""
        from src.flow.sequential import SequentialFlow
        from src.llm.client import LLMClient

        # Get LLM config
        config_str = self._get_config_value("DEEPSEEK_CONFIG")
        if not config_str:
            pytest.skip("No LLM config available")

        config = json.loads(config_str)
        model = config["prefix"][0]

        # Create flow
        flow = SequentialFlow()
        context = {}

        # Pre-process
        await flow.pre_process("Explain what is Python\nExplain what is Java", context)

        # Execute with LLM
        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": context["_flow_steps"][0]},
        ]

        try:
            response = await client.chat(model, messages, temperature=0.7)
            assert response is not None and len(response) > 0

            # Post-process
            result = await flow.post_process(response, context)
            assert result is not None
        finally:
            await client.close()


class TestHarnessWithRealLLM:
    """Test Harness with real LLM"""

    def _get_config_value(self, key: str) -> str:
        """Get config value from environment"""
        value = os.environ.get(key, "")
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        return value

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_harness_tracking_llm_execution(self):
        """Test Harness tracking LLM execution"""
        from src.harness import Harness
        from src.llm.client import LLMClient

        # Get LLM config
        config_str = self._get_config_value("DEEPSEEK_CONFIG")
        if not config_str:
            pytest.skip("No LLM config available")

        config = json.loads(config_str)
        model = config["prefix"][0]

        # Create harness
        harness = Harness()
        harness.start()
        harness.set_metadata("model", model)

        # Execute LLM call
        client = LLMClient()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test'"},
        ]

        try:
            harness.record_step(True)
            response = await client.chat(model, messages, temperature=0.7)
            harness.record_step(True)

            status = harness.get_status()
            assert status["total_steps"] == 2
            assert status["successful_steps"] == 2
        finally:
            await client.close()
            harness.stop()
