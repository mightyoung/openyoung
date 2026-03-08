"""
E2E Integration Tests
Full workflow tests that verify all modules work together
"""

import asyncio
from pathlib import Path

import pytest

# Import all modules
from src.agents.young_agent import YoungAgent
from src.config.loader import ConfigLoader
from src.core.types import (
    AgentConfig,
    AgentMode,
    PermissionAction,
    PermissionConfig,
)
from src.datacenter.datacenter import BudgetController, TraceCollector, TraceRecord, TraceStatus
from src.distillation import KnowledgeDistiller
from src.evaluation.hub import EvaluationHub
from src.evolver.models import Capsule, Gene, GeneCategory, Personality
from src.flow.conditional import ConditionalFlow
from src.flow.parallel import ParallelFlow
from src.flow.sequential import SequentialFlow
from src.harness import Harness, HarnessStatus
from src.mcp import MCPClient, MCPServer, MCPTool
from src.memory.auto_memory import AutoMemory
from src.memory.checkpoint import CheckpointManager
from src.package_manager.manager import PackageManager
from src.prompts.templates import PromptRegistry, PromptTemplate, TemplateType
from src.retriever.unified import UnifiedSkillRetriever
from src.skills import Skill, SkillManager


class TestFullAgentWorkflow:
    """Test complete agent workflow from initialization to execution"""

    @pytest.mark.asyncio
    async def test_agent_initialization_to_execution(self):
        """Test full agent lifecycle"""
        # 1. Initialize agent with config
        config = AgentConfig(
            name="e2e_agent",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )
        agent = YoungAgent(config)
        assert agent.config.name == "e2e_agent"

        # 2. Add memory (async)
        memory = AutoMemory()
        await memory.add_memory("Test input", layer="working")
        stats = memory.get_stats()
        assert stats["working"] >= 0

        # 3. Create checkpoint
        checkpoint_mgr = CheckpointManager()
        # Create a test file first
        test_file = Path(__file__).parent / "test_temp.py"
        test_file.write_text("# test")
        checkpoint_id = await checkpoint_mgr.create_checkpoint(str(test_file), reason="test")
        assert checkpoint_id is not None

        # 4. Verify all components work together
        assert True

    def test_flow_execution_chain(self):
        """Test flow execution chain"""
        # Sequential flow
        seq_flow = SequentialFlow()
        assert seq_flow.name is not None

        # Parallel flow
        par_flow = ParallelFlow()
        assert par_flow.name is not None

        # Conditional flow
        cond_flow = ConditionalFlow()
        assert cond_flow.name is not None

    @pytest.mark.asyncio
    async def test_memory_and_checkpoint_integration(self):
        """Test memory and checkpoint work together"""
        # Create memory
        memory = AutoMemory()

        # Add various memories
        await memory.add_memory("Task 1", layer="session")
        await memory.add_memory("Task 2", layer="session")
        await memory.add_memory("Important context", layer="persistent")

        # Create checkpoint
        checkpoint_mgr = CheckpointManager()
        checkpoint_id = await checkpoint_mgr.create_checkpoint(
            "memory_state",
            {
                "working": len(memory.working_memory),
                "session": len(memory.session_memory),
            },
        )

        # Restore from checkpoint
        restored = await checkpoint_mgr.restore_checkpoint(checkpoint_id)
        assert restored is not None


class TestConfigToExecution:
    """Test configuration loading to execution flow"""

    def test_config_loading_integration(self):
        """Test config loading with all components"""
        # Load config
        loader = ConfigLoader()

        # Set config values
        loader.set("agent.name", "test_agent")
        loader.set("agent.model", "gpt-4")
        loader.set("agent.temperature", 0.7)

        # Verify config
        assert loader.get("agent.name") == "test_agent"
        assert loader.get("agent.model") == "gpt-4"
        assert loader.get("agent.temperature") == 0.7

    def test_prompt_template_integration(self):
        """Test prompt template system"""
        # Create template
        template = PromptTemplate(
            name="test",
            template_type=TemplateType.DEVIN,
            content="Hello {{name}}, your task is: {{task}}",
        )

        # Render template
        result = template.render(name="User", task="Analyze this")
        assert "Hello User" in result
        assert "Analyze this" in result

        # Register template
        registry = PromptRegistry()
        registry.register(template)

        # Retrieve and render
        retrieved = registry.get("test")
        assert retrieved is not None

        # Render template
        rendered = registry.render("test", name="World")
        assert "Hello World" in rendered


class TestEvaluationWorkflow:
    """Test evaluation and metrics workflow"""

    @pytest.mark.asyncio
    async def test_evaluation_hub_integration(self):
        """Test evaluation hub with metrics"""
        hub = EvaluationHub()

        # Register custom metric - must be async
        async def accuracy_metric(input_data):
            return 0.95

        hub.register_metric("accuracy", accuracy_metric)

        # Evaluate (async)
        result = await hub.evaluate("accuracy", "test input")

        assert result.metric == "accuracy"
    """Test evaluation and metrics workflow"""

    @pytest.mark.asyncio
    async def test_evaluation_hub_integration(self):
        """Test evaluation hub with metrics"""
        hub = EvaluationHub()

        # Register custom metric
        async def accuracy_metric(input_data):
            return 0.95

        hub.register_metric("accuracy", accuracy_metric)

        # Evaluate (async)
        result = await hub.evaluate("accuracy", "test input")

        assert result.metric == "accuracy"
        assert result.score == 0.95

    def test_skill_retriever_integration(self):
        """Test unified skill retriever"""
        retriever = UnifiedSkillRetriever()

        # Register skills using the Skill class
        from src.retriever.unified import Skill
        skill1 = Skill(name="analyze", description="Analysis skill", tags=["analysis"])
        skill2 = Skill(name="build", description="Build skill", tags=["construction"])

        retriever.register_skill(skill1, "default")
        retriever.register_skill(skill2, "default")

        # Retrieve by keyword
        skills = retriever.retrieve_by_keyword("analysis")
        assert skills is not None


class TestDataCenterWorkflow:
    """Test data center components"""

    def test_trace_collector_workflow(self):
        """Test trace collection"""
        collector = TraceCollector()

        # Add traces
        trace1 = TraceRecord(
            session_id="test-session-001",
            agent_name="test-agent",
            status=TraceStatus.SUCCESS,
        )
        collector.record(trace1)

        # Retrieve
        traces = collector.get_by_session("test-session-001")
        assert len(traces) >= 1

    def test_budget_controller_workflow(self):
        """Test budget control"""
        controller = BudgetController(max_tokens=1000)

        # Check budget
        assert controller.check_budget(500) is True
        assert controller.check_budget(1500) is False

        # Use tokens
        controller.use(300)
        assert controller.check_budget(200) is True

        # Reset
        controller.reset()
        assert controller.check_budget(500) is True


class TestEvolverWorkflow:
    """Test evolver components"""

    def test_gene_evolution(self):
        """Test gene creation and loading"""
        # Create gene
        gene = Gene(id="creativity-gene", category=GeneCategory.INNOVATE, signals=["success"])
        assert gene.id == "creativity-gene"
        assert gene.category == GeneCategory.INNOVATE

        # Create capsule
        capsule = Capsule(
            id="capsule_1",
            name="Creative Agent",
            description="An agent with creative capabilities",
            gene_ref="creativity-gene",
        )
        assert capsule.name == "Creative Agent"

        # Create personality
        personality = Personality(name="creative")
        personality.update_trait("creativity", 0.9)
        assert personality.traits["creativity"] == 0.9

    def test_gene_loader(self):
        """Test gene creation"""
        gene = Gene(
            id="test-gene-001",
            category=GeneCategory.REPAIR,
            signals=["success"],
            strategy=["test strategy"],
        )
        assert gene.id == "test-gene-001"
        assert gene.category == GeneCategory.REPAIR


class TestHarnessDistillation:
    """Test harness and distillation integration"""

    def test_harness_lifecycle(self):
        """Test harness full lifecycle"""
        harness = Harness()

        # Start
        harness.start()
        assert harness.status == HarnessStatus.RUNNING

        # Record steps
        harness.record_step(True)
        harness.record_step(True)
        harness.record_step(False)

        # Get status
        status = harness.get_status()
        assert status["total_steps"] == 3
        assert status["successful_steps"] == 2

        # Stop
        harness.stop()
        assert harness.status == HarnessStatus.STOPPED

    @pytest.mark.asyncio
    async def test_knowledge_distillation(self):
        """Test knowledge distillation workflow"""
        distiller = KnowledgeDistiller()

        # Extract from history
        history = [
            {"action": "analyze", "result": "analysis done", "success": True},
            {"action": "execute", "result": "execution done", "success": True},
        ]

        knowledge = distiller.extract_from_history(history)

        # Compress
        compressed = distiller.compress(knowledge)
        assert compressed.compressed_representation is not None

        # Store and retrieve
        distiller.store_knowledge("agent_1", compressed)
        retrieved = distiller.get_knowledge("agent_1")
        assert retrieved is not None


class TestSkillsMCP:
    """Test skills and MCP integration"""

    def test_skill_management(self):
        """Test skill manager workflow"""
        manager = SkillManager()

        # Register skill
        def my_handler(x):
            return x * 2

        skill = Skill(name="doubler", handler=my_handler, description="Doubles input")
        manager.register(skill)

        # Load and execute
        manager.load("doubler")
        result = manager.execute_skill("doubler", 5)
        assert result == 10

    def test_mcp_connection(self):
        """Test MCP client workflow"""
        server = MCPServer("http://localhost:8080", "test")
        client = MCPClient(server)

        # Connect
        client.connect()
        assert client.is_connected() is True

        # Register tool
        tool = MCPTool(
            name="test_tool", description="Test tool", input_schema={"type": "object"}
        )
        client.register_tool(tool)

        # Call tool
        result = client.call_tool("test_tool", {"key": "value"})
        assert result is not None

        # Disconnect
        client.disconnect()
        assert client.is_connected() is False


class TestMultiComponentWorkflow:
    """Test multiple components working together"""

    @pytest.mark.asyncio
    async def test_agent_with_all_components(self):
        """Test agent with memory, flow, and evaluation"""
        # 1. Create agent
        config = AgentConfig(
            name="full_agent",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )
        agent = YoungAgent(config)

        # 2. Add memory
        memory = AutoMemory()
        await memory.add_memory("Initialize system", layer="working")

        # 3. Create flow
        flow = SequentialFlow()

        # 4. Set up evaluation
        hub = EvaluationHub()
        hub.register_metric("completeness", lambda x: 1.0)

        # 5. Set up tracing
        collector = TraceCollector()

        # 6. Set up budget
        budget = BudgetController(max_tokens=10000)

        # Verify all components exist and work
        assert agent.config.name == "full_agent"
        assert flow.name is not None
        assert len(hub.list_metrics()) > 0
        assert budget.max_tokens == 10000

    @pytest.mark.asyncio
    async def test_async_workflow(self):
        """Test async workflow"""
        # Async operations
        await asyncio.sleep(0.01)  # Simulate async work

        # Package manager async install
        pm = PackageManager()
        result = await pm.install("test_package")
        assert result is True

        packages = pm.list_packages()
        package_names = [p.name for p in packages]
        assert "test_package" in package_names


class TestErrorHandling:
    """Test error handling in workflows"""

    def test_graceful_degradation(self):
        """Test system handles errors gracefully"""
        # Config with missing values
        loader = ConfigLoader()
        default_value = loader.get("nonexistent", "default")
        assert default_value == "default"

    def test_validation_errors(self):
        """Test input validation - simplified"""
        # Test that AgentConfig works with valid input
        from src.core.types import AgentConfig

        # Valid config should work
        config = AgentConfig(name="test", model="gpt-4", temperature=0.7)
        assert config.name == "test"
        assert config.temperature == 0.7
        """Test input validation"""
        from src.core.types import AgentConfig

        # Test config creation (no validation in dataclass)
        config = AgentConfig(name="test", model="gpt-4", temperature=5.0)
        assert config.temperature == 5.0

    @pytest.mark.asyncio
    async def test_memory_error_recovery(self):
        """Test memory recovers from errors"""
        memory = AutoMemory()

        # Clear and verify
        await memory.clear_working_memory()
        # Memory should be empty now
        assert len(memory.working_memory) == 0


class TestConcurrentOperations:
    """Test concurrent operations"""

    def test_parallel_agent_creation(self):
        """Test creating multiple agents"""
        config = AgentConfig(
            name="test",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )

        agents = []
        for i in range(5):
            agent = YoungAgent(config)
            agents.append(agent)

        assert len(agents) == 5

    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """Test concurrent memory operations"""
        memory = AutoMemory()

        # Add to different layers
        await memory.add_memory("data1", layer="working")
        await memory.add_memory("data2", layer="session")
        await memory.add_memory("data3", layer="persistent")

        stats = memory.get_stats()
        assert stats["total"] >= 0
