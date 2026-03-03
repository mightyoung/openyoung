"""
Tests for Phase 6-11 modules
"""

import pytest
from src.package_manager.manager import PackageManager
from src.datacenter.datacenter import (
    TraceCollector,
    BudgetController,
    PatternDetector,
    Trace,
)
from src.evolver.models import (
    Gene,
    Capsule,
    EvolutionEvent,
    Personality,
    GeneLoader,
    EvolutionEventType,
)
from src.evaluation.hub import EvaluationHub, EvaluationResult
from src.retriever.unified import UnifiedSkillRetriever, Skill
from src.config.loader import ConfigLoader
from datetime import datetime


class TestPackageManager:
    @pytest.mark.asyncio
    async def test_install(self):
        pm = PackageManager()
        result = await pm.install("test-package", "1.0.0")
        assert result is True
        assert "test-package" in pm.list_packages()

    @pytest.mark.asyncio
    async def test_uninstall(self):
        pm = PackageManager()
        await pm.install("test-package")
        result = await pm.uninstall("test-package")
        assert result is True
        assert "test-package" not in pm.list_packages()


class TestDataCenter:
    def test_trace_collector(self):
        tc = TraceCollector()
        trace = Trace(id="1", agent_id="agent1", action="test", input="", output="")
        tc.add_trace(trace)
        assert len(tc.get_traces()) == 1
        assert len(tc.get_traces("agent1")) == 1

    def test_budget_controller(self):
        bc = BudgetController(max_tokens=100)
        assert bc.check_budget(50) is True
        assert bc.check_budget(150) is False
        bc.use_tokens(30)
        assert bc.used_tokens == 30

    def test_pattern_detector(self):
        pd = PatternDetector()
        pd.record_pattern("pattern1")
        pd.record_pattern("pattern1")
        pd.record_pattern("pattern2")
        top = pd.get_top_patterns()
        assert top[0][0] == "pattern1"
        assert top[0][1] == 2


class TestEvolver:
    def test_gene(self):
        gene = Gene(name="creativity", value=0.8)
        assert gene.name == "creativity"
        assert gene.value == 0.8

    def test_capsule(self):
        genes = [Gene(name="speed", value=0.5)]
        capsule = Capsule(id="c1", name="test", description="test capsule", genes=genes)
        assert len(capsule.genes) == 1

    def test_personality(self):
        p = Personality(name="assistant", traits={"helpful": 0.8})
        p.update_trait("helpful", 0.9)
        assert p.traits["helpful"] == 0.9

    def test_gene_loader(self):
        data = {"genes": {"speed": 0.5, "accuracy": 0.9}}
        genes = GeneLoader.load_genes(data)
        assert len(genes) == 2


class TestEvaluationHub:
    @pytest.mark.asyncio
    async def test_register_and_evaluate(self):
        hub = EvaluationHub()

        async def mock_metric(data):
            return 0.95

        hub.register_metric("quality", mock_metric)
        result = await hub.evaluate("quality", {"input": "test"})

        assert result.score == 0.95
        assert "quality" in hub.list_metrics()


class TestUnifiedSkillRetriever:
    def test_register_and_retrieve(self):
        retriever = UnifiedSkillRetriever()
        skill = Skill("test-skill", "A test skill", tags=["testing"])
        retriever.register_skill(skill)

        results = retriever.retrieve_by_keyword("test")
        assert len(results) >= 1

        results = retriever.retrieve_by_tags(["testing"])
        assert len(results) >= 1


class TestConfigLoader:
    def test_get_set(self):
        loader = ConfigLoader()
        loader.set("agent.name", "test-agent")
        assert loader.get("agent.name") == "test-agent"
        assert loader.get("agent.nonexistent", "default") == "default"

    def test_merge_configs(self):
        loader = ConfigLoader()
        configs = [{"a": 1}, {"b": 2}]
        merged = loader.merge_configs(*configs)
        assert merged == {"a": 1, "b": 2}
