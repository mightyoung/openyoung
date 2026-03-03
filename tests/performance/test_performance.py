"""
Performance Tests
Benchmark tests to measure system performance and resource usage
"""

import pytest
import time
import asyncio
import tracemalloc
import gc
import sys
from typing import Callable, Any

# Import modules to test
from src.agents.young_agent import YoungAgent
from src.agents.dispatcher import TaskDispatcher
from src.core.types import AgentConfig, AgentMode, PermissionConfig, PermissionAction
from src.flow.sequential import SequentialFlow
from src.memory.auto_memory import AutoMemory
from src.memory.checkpoint import CheckpointManager
from src.prompts.templates import PromptTemplate, PromptRegistry, TemplateType
from src.config.loader import ConfigLoader
from src.package_manager.manager import PackageManager
from src.evaluation.hub import EvaluationHub
from src.harness import Harness
from src.distillation import KnowledgeDistiller
from src.skills import SkillManager, Skill
from src.mcp import MCPClient, MCPServer


class PerformanceTimer:
    """Helper class to time operations"""

    def __init__(self):
        self.start_time = 0
        self.end_time = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()

    @property
    def elapsed(self) -> float:
        return self.end_time - self.start_time


class TestAgentPerformance:
    """Performance tests for agent operations"""

    def test_agent_creation_time(self):
        """Test agent creation performance"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )

        times = []
        for _ in range(100):
            with PerformanceTimer() as timer:
                agent = YoungAgent(config)
            times.append(timer.elapsed)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        print(
            f"\nAgent creation: avg={avg_time * 1000:.2f}ms, max={max_time * 1000:.2f}ms"
        )
        assert avg_time < 0.05, f"Average creation time too high: {avg_time}s"

    def test_agent_initialization_memory(self):
        """Test memory usage during agent initialization"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )

        tracemalloc.start()
        """Test memory usage during agent initialization"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )
        """Test memory usage during agent initialization"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARYPermissionConfig(
                _global, permission == PermissionAction.ALLOW
            ),
        )

        tracemalloc.start()

        # Create multiple agents
        for i in range(10):
            agent = YoungAgent(config)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"\nAgent initialization peak memory: {peak_mb:.2f}MB")
        assert peak_mb < 50, f"Memory usage too high: {peak_mb}MB"

    def test_multiple_agents_creation(self):
        """Test creating many agents"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )

        start = time.perf_counter()

        agents = [YoungAgent(config) for i in range(50)]

        elapsed = time.perf_counter() - start
        per_agent = elapsed / 50

        print(
            f"\nCreated 50 agents in {elapsed * 1000:.2f}ms ({per_agent * 1000:.2f}ms each)"
        )
        assert elapsed < 2.0, f"Too slow: {elapsed}s"


class TestMemoryPerformance:
    """Performance tests for memory operations"""

    @pytest.mark.asyncio
    async def test_memory_operations_speed(self):
        """Test memory add/retrieve speed"""
        memory = AutoMemory()

        start = time.perf_counter()
        for i in range(100):
            await memory.add_memory(f"data_{i}", layer="session")
        elapsed = time.perf_counter() - start

        print(f"\n100 memory writes: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Memory operations too slow: {elapsed}s"

    @pytest.mark.asyncio
    async def test_memory_retrieval_speed(self):
        """Test memory retrieval speed"""
        memory = AutoMemory()

        # Populate memory
        for i in range(100):
            await memory.add_memory(f"data_{i}", layer="session")

        # Time retrieval
        start = time.perf_counter()
        for _ in range(100):
            _ = memory.session_memory
        elapsed = time.perf_counter() - start

        print(f"\n100 memory retrievals: {elapsed * 1000:.2f}ms")
        assert elapsed < 0.5, f"Retrieval too slow: {elapsed}s"

    def test_checkpoint_performance(self):
        """Test checkpoint operations"""
        checkpoint_mgr = CheckpointManager()

        start = time.perf_counter()
        for i in range(100):
            checkpoint_mgr.create_checkpoint(f"state_{i}", {"data": i})
        elapsed = time.perf_counter() - start

        print(f"\n100 checkpoint creates: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Checkpoint too slow: {elapsed}s"


class TestFlowPerformance:
    """Performance tests for flow operations"""

    def test_sequential_flow_creation(self):
        """Test sequential flow creation speed"""
        times = []
        for _ in range(100):
            with PerformanceTimer() as timer:
                flow = SequentialFlow()
            times.append(timer.elapsed)

        avg_time = sum(times) / len(times)
        print(f"\nSequentialFlow creation: avg={avg_time * 1000:.3f}ms")
        assert avg_time < 0.01, f"Flow creation too slow: {avg_time}s"


class TestConfigPerformance:
    """Performance tests for configuration"""

    def test_config_operations(self):
        """Test config get/set speed"""
        loader = ConfigLoader()

        # Set values
        for i in range(100):
            loader.set(f"key_{i}", f"value_{i}")

        # Time retrieval
        start = time.perf_counter()
        for i in range(100):
            _ = loader.get(f"key_{i}")
        elapsed = time.perf_counter() - start

        print(f"\n100 config gets: {elapsed * 1000:.2f}ms")
        assert elapsed < 0.5, f"Config access too slow: {elapsed}s"

    def test_config_merging(self):
        """Test config merging performance"""
        loader = ConfigLoader()

        configs = [{f"key_{i}": f"value_{i}"} for i in range(50)]

        start = time.perf_counter()
        result = loader.merge_configs(*configs)
        elapsed = time.perf_counter() - start

        print(f"\nMerged 50 configs in {elapsed * 1000:.2f}ms")
        assert elapsed < 0.5, f"Config merge too slow: {elapsed}s"


class TestPromptPerformance:
    """Performance tests for prompt templates"""

    def test_template_rendering_speed(self):
        """Test prompt template rendering"""
        template = PromptTemplate(
            name="perf",
            template_type=TemplateType.DEVIN,
            content="Hello {{name}}, your task is: {{task}}. Context: {{ctx}}",
        )

        start = time.perf_counter()
        for _ in range(1000):
            result = template.render(name="User", task="Test task", ctx="Some context")
        elapsed = time.perf_counter() - start

        print(f"\n1000 template renders: {elapsed * 1000:.2f}ms")
        assert elapsed < 2.0, f"Template rendering too slow: {elapsed}s"

    def test_registry_operations(self):
        """Test prompt registry operations"""
        registry = PromptRegistry()

        # Register many templates
        for i in range(50):
            t = PromptTemplate(
                name=f"tpl_{i}",
                template_type=TemplateType.DEVIN,
                content=f"Template {i}",
            )
            registry.register(t)

        # Time retrieval
        start = time.perf_counter()
        for i in range(50):
            _ = registry.get(f"tpl_{i}")
        elapsed = time.perf_counter() - start
        start = time.perf_counter()
        for i in range(50):
            _ = registry.get_template(f"tpl_{i}")
        elapsed = time.perf_counter() - start

        print(f"\n50 template retrievals: {elapsed * 1000:.2f}ms")
        assert elapsed < 0.5, f"Registry too slow: {elapsed}s"


class TestEvaluationPerformance:
    """Performance tests for evaluation"""

    @pytest.mark.asyncio
    async def test_evaluation_speed(self):
        """Test evaluation execution speed"""
        hub = EvaluationHub()

        # Register metric - must be async
        async def fast_metric(data):
            return 0.95

        hub.register_metric("fast", fast_metric)

        start = time.perf_counter()
        for _ in range(100):
            result = await hub.evaluate("fast", "test data")
        elapsed = time.perf_counter() - start
    """Performance tests for evaluation"""

    @pytest.mark.asyncio
    async def test_evaluation_speed(self):
        """Test evaluation execution speed"""
        hub = EvaluationHub()

        # Register metric
        def fast_metric(data):
            return 0.95

        hub.register_metric("fast", fast_metric)

        start = time.perf_counter()
        for _ in range(100):
            result = await hub.evaluate("fast", "test data")
        elapsed = time.perf_counter() - start

        print(f"\n100 evaluations: {elapsed * 1000:.2f}ms")
        assert elapsed < 2.0, f"Evaluation too slow: {elapsed}s"


class TestHarnessPerformance:
    """Performance tests for harness"""

    def test_harness_operations(self):
        """Test harness step recording"""
        harness = Harness()
        harness.start()

        start = time.perf_counter()
        for i in range(1000):
            harness.record_step(i % 2 == 0)
        elapsed = time.perf_counter() - start

        print(f"\n1000 step recordings: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Harness too slow: {elapsed}s"

    def test_status_retrieval(self):
        """Test status retrieval speed"""
        harness = Harness()
        harness.start()

        for i in range(100):
            harness.record_step(True)

        start = time.perf_counter()
        for _ in range(100):
            status = harness.get_status()
        elapsed = time.perf_counter() - start

        print(f"\n100 status retrievals: {elapsed * 1000:.2f}ms")
        assert elapsed < 0.5, f"Status retrieval too slow: {elapsed}s"


class TestDistillationPerformance:
    """Performance tests for knowledge distillation"""

    def test_extraction_performance(self):
        """Test knowledge extraction speed"""
        distiller = KnowledgeDistiller()

        history = [
            {"action": f"action_{i}", "result": f"result_{i}", "success": i % 2 == 0}
            for i in range(100)
        ]

        start = time.perf_counter()
        for _ in range(50):
            knowledge = distiller.extract_from_history(history)
        elapsed = time.perf_counter() - start

        print(f"\n50 extractions from 100 history items: {elapsed * 1000:.2f}ms")
        assert elapsed < 2.0, f"Extraction too slow: {elapsed}s"

    def test_compression_performance(self):
        """Test knowledge compression speed"""
        distiller = KnowledgeDistiller()

        from src.distillation import Knowledge

        knowledge = Knowledge(
            experience_count=1000,
            patterns=[f"p_{i}" for i in range(100)],
            key_insights=[f"i_{i}" for i in range(50)],
        )

        start = time.perf_counter()
        for _ in range(100):
            compressed = distiller.compress(knowledge)
        elapsed = time.perf_counter() - start

        print(f"\n100 compressions: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Compression too slow: {elapsed}s"


class TestSkillsPerformance:
    """Performance tests for skill management"""

    def test_skill_registration(self):
        """Test skill registration speed"""
        manager = SkillManager()

        start = time.perf_counter()
        for i in range(100):
            skill = Skill(name=f"skill_{i}", handler=lambda: None)
            manager.register(skill)
        elapsed = time.perf_counter() - start

        print(f"\n100 skill registrations: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Registration too slow: {elapsed}s"

    def test_skill_execution(self):
        """Test skill execution speed"""
        manager = SkillManager()

        def fast_handler(x):
            return x * 2

        skill = Skill(name="fast", handler=fast_handler, is_loaded=True)
        manager.register(skill)

        start = time.perf_counter()
        for i in range(1000):
            result = manager.execute_skill("fast", i)
        elapsed = time.perf_counter() - start

        print(f"\n1000 skill executions: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Execution too slow: {elapsed}s"


class TestMCPPerformance:
    """Performance tests for MCP"""

    def test_connection_speed(self):
        """Test MCP connection speed"""
        times = []
        for _ in range(10):
            server = MCPServer("http://localhost:8080")
            client = MCPClient(server)
            with PerformanceTimer() as timer:
                client.connect()
            times.append(timer.elapsed)
            client.disconnect()

        avg_time = sum(times) / len(times)
        print(f"\nMCP connection: avg={avg_time * 1000:.2f}ms")
        assert avg_time < 0.1, f"Connection too slow: {avg_time}s"

    def test_tool_call_performance(self):
        """Test tool call speed"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        from src.mcp import MCPTool

        tool = MCPTool(name="perf", description="", input_schema={})
        client.register_tool(tool)

        start = time.perf_counter()
        for i in range(100):
            result = client.call_tool("perf", {"i": i})
        elapsed = time.perf_counter() - start

        print(f"\n100 tool calls: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"Tool call too slow: {elapsed}s"


class TestAsyncPerformance:
    """Performance tests for async operations"""

    @pytest.mark.asyncio
    async def test_async_package_install(self):
        """Test async package installation"""
        pm = PackageManager()

        start = time.perf_counter()
        for i in range(10):
            await pm.install(f"package_{i}")
        elapsed = time.perf_counter() - start

        print(f"\n10 async installs: {elapsed * 1000:.2f}ms")
        assert elapsed < 2.0, f"Async install too slow: {elapsed}s"


class TestMemoryLeak:
    """Memory leak detection tests"""

    @pytest.mark.asyncio
    async def test_no_memory_leak_in_loop(self):
        """Test no memory leak in repeated operations"""
        tracemalloc.start()

        initial = tracemalloc.get_traced_memory()[1]

        # Perform many operations
        for _ in range(10):
            memory = AutoMemory()
            for i in range(100):
                await memory.add_memory(f"d{i}", layer="session")
            del memory

        gc.collect()

        final = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        growth = (final - initial) / 1024 / 1024
        print(f"\nMemory growth after 10 iterations: {growth:.2f}MB")

        # Allow some growth but not excessive
        assert growth < 20, f"Possible memory leak: {growth}MB"

    def test_object_creation_cleanup(self):
        """Test objects are properly cleaned up"""
        config = AgentConfig(
            name="perf",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )

        tracemalloc.start()

        # Create many objects
        for _ in range(100):
            agent = YoungAgent(config)
            flow = SequentialFlow()
            memory = AutoMemory()

        gc.collect()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"\nPeak memory with 100 iterations: {peak_mb:.2f}MB")
        assert peak_mb < 50, f"Peak memory too high: {peak_mb}MB"


class TestBenchmark:
    """Overall system benchmarks"""

    def test_full_system_initialization(self):
        """Test full system initialization time"""
        start = time.perf_counter()

        # Initialize all components
        config = AgentConfig(
            name="benchmark",
            model="gpt-4",
            mode=AgentMode.PRIMARY,
            permission=PermissionConfig(_global=PermissionAction.ALLOW),
        )
        agent = YoungAgent(config)
        memory = AutoMemory()
        checkpoint = CheckpointManager()
        flow = SequentialFlow()
        hub = EvaluationHub()
        harness = Harness()
        distiller = KnowledgeDistiller()
        skills = SkillManager()

        elapsed = time.perf_counter() - start

        print(f"\nFull system init: {elapsed * 1000:.2f}ms")
        assert elapsed < 1.0, f"System init too slow: {elapsed}s"

    @pytest.mark.asyncio
    async def test_throughput_operation(self):
        """Test operation throughput"""
        memory = AutoMemory()
        harness = Harness()
        harness.start()

        start = time.perf_counter()

        # Perform mixed operations
        for i in range(50):
            await memory.add_memory(f"d{i}", layer="session")
            harness.record_step(i % 2 == 0)

        elapsed = time.perf_counter() - start
        ops_per_sec = 100 / elapsed

        print(f"\nThroughput: {ops_per_sec:.0f} ops/sec")
        assert ops_per_sec > 50, f"Throughput too low: {ops_per_sec}"
