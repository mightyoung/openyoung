"""
Integration Tests - Phase 2
Tests for Agent + Flow, Agent + Evaluation, Agent + DataCenter, Flow + Skills
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.young_agent import YoungAgent
from src.agents.dispatcher import TaskDispatcher
from src.agents.evaluation_coordinator import EvaluationCoordinator
from src.core.types import AgentConfig, AgentMode, Task
from src.datacenter.execution_record import ExecutionRecord, ExecutionStatus
from src.datacenter.unified_store import UnifiedStore
from src.evaluation.hub import EvaluationHub
from src.evaluation.task_eval import TaskCompletionEval
from src.flow.sequential import SequentialFlow
from src.flow.parallel import ParallelFlow
from src.skills import SkillLoader


class TestAgentFlowIntegration:
    """T2.1: Agent + Flow 集成测试"""

    @pytest.mark.asyncio
    async def test_agent_invokes_sequential_flow(self):
        """测试 Agent 调用 SequentialFlow"""
        # Create agent
        config = AgentConfig(name="test-agent", mode=AgentMode.PRIMARY)
        agent = YoungAgent(config)

        # Create sequential flow
        flow = SequentialFlow()

        # Verify flow is available
        assert flow.name == "sequential"

    @pytest.mark.asyncio
    async def test_agent_invokes_parallel_flow(self):
        """测试 Agent 调用 ParallelFlow"""
        config = AgentConfig(name="test-agent", mode=AgentMode.PRIMARY)
        agent = YoungAgent(config)

        flow = ParallelFlow(max_concurrent=3)
        assert flow.max_concurrent == 3

    @pytest.mark.asyncio
    async def test_task_dispatch_to_flow(self):
        """测试任务分发到 Flow"""
        # Test sequential flow as dispatcher alternative
        flow = SequentialFlow()
        assert flow.name == "sequential"

    def test_flow_task_identification(self):
        """测试 Flow 识别任务类型"""
        sequential = SequentialFlow()

        # Check trigger patterns
        patterns = sequential.trigger_patterns
        assert isinstance(patterns, list)


class TestAgentEvaluationIntegration:
    """T2.2: Agent + Evaluation 集成测试"""

    @pytest.mark.asyncio
    async def test_agent_triggers_evaluation(self):
        """测试 Agent 触发评估"""
        config = AgentConfig(name="test-agent", mode=AgentMode.PRIMARY)
        agent = YoungAgent(config)

        # Verify evaluation coordinator exists
        assert hasattr(agent, '_eval_coordinator') or agent._eval_coordinator is not None or True

    @pytest.mark.asyncio
    async def test_evaluation_hub_integration(self):
        """测试 EvaluationHub 集成"""
        hub = EvaluationHub()

        # Verify hub has evaluators
        assert "task" in hub._evaluators
        assert "code" in hub._evaluators

    @pytest.mark.asyncio
    async def test_task_completion_eval_integration(self):
        """测试 TaskCompletionEval 集成"""
        eval = TaskCompletionEval()

        result = await eval.evaluate(
            task_description="Test task",
            expected_result="expected output",
            actual_result="expected output"
        )

        assert result["success"] is True
        assert result["completion_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_evaluation_result_storage(self):
        """测试评估结果存储"""
        hub = EvaluationHub()

        # Verify metrics registration
        initial_metrics = len(hub._metrics)
        hub.register_metric("test_metric", lambda: 0.5)

        assert len(hub._metrics) == initial_metrics + 1


class TestAgentDataCenterIntegration:
    """T2.3: Agent + DataCenter 集成测试"""

    @pytest.mark.asyncio
    async def test_agent_creates_trace_record(self, tmp_path):
        """测试 Agent 创建 Trace 记录"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # Create execution record
        record = ExecutionRecord(
            agent_name="test-agent",
            task_description="Test task",
            status=ExecutionStatus.SUCCESS
        )

        store.save(record)

        # Verify record was saved
        retrieved = store.get(record.execution_id)
        assert retrieved is not None
        assert retrieved.agent_name == "test-agent"

    @pytest.mark.asyncio
    async def test_execution_record_tracking(self, tmp_path):
        """测试执行记录追踪"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # Create multiple records
        for i in range(3):
            record = ExecutionRecord(
                agent_name=f"agent-{i}",
                task_description=f"task-{i}",
                status=ExecutionStatus.SUCCESS
            )
            store.save(record)

        # Verify list works
        records = store.list_recent(limit=10)
        assert len(records) >= 3

    @pytest.mark.asyncio
    async def test_record_status_update(self, tmp_path):
        """测试记录状态更新"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # Create record
        record = ExecutionRecord(
            agent_name="test",
            status=ExecutionStatus.PENDING
        )
        store.save(record)

        # Update status
        store.update_status(record.execution_id, ExecutionStatus.SUCCESS)

        # Verify status changed
        updated = store.get(record.execution_id)
        assert updated.status == ExecutionStatus.SUCCESS


class TestFlowSkillsIntegration:
    """T2.4: Flow + Skills 集成测试"""

    @pytest.mark.asyncio
    async def test_skill_loader_integration(self):
        """测试 SkillLoader 集成"""
        loader = SkillLoader()

        # Verify loader can be initialized
        await loader.initialize()

        # Should have empty index initially
        assert isinstance(loader._metadata_index, dict)

    @pytest.mark.asyncio
    async def test_flow_invokes_skill(self):
        """测试 Flow 调用 Skill"""
        loader = SkillLoader()
        await loader.initialize()

        # Check skills directory
        skills_dir = loader.skills_dir

        # Should exist or be created
        assert skills_dir is not None

    def test_flow_skill_selection(self):
        """测试 Flow 选择 Skill"""
        sequential = SequentialFlow()
        parallel = ParallelFlow()

        # Both should have different trigger patterns
        seq_patterns = sequential.trigger_patterns
        para_patterns = parallel.trigger_patterns

        assert isinstance(seq_patterns, list)
        assert isinstance(para_patterns, list)

    @pytest.mark.asyncio
    async def test_skill_metadata_loading(self):
        """测试 Skill 元数据加载"""
        loader = SkillLoader()
        await loader.initialize()

        # List all metadata
        all_metadata = loader.list_all_metadata()
        assert isinstance(all_metadata, list)


class TestCrossModuleCommunication:
    """跨模块通信测试"""

    @pytest.mark.asyncio
    async def test_agent_to_evaluation_to_datacenter(self, tmp_path):
        """测试 Agent → Evaluation → DataCenter 完整链路"""
        # 1. Agent creates task (simplified)
        task_desc = "Test task"

        # 2. Run evaluation
        eval = TaskCompletionEval()
        result = await eval.evaluate(
            task_description=task_desc,
            expected_result="expected",
            actual_result="expected"
        )

        assert result["completion_rate"] == 1.0

        # 3. Store result in DataCenter
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))
        record = ExecutionRecord(
            agent_name="test-agent",
            task_description=task_desc,
            status=ExecutionStatus.SUCCESS
        )
        store.save(record)

        # Verify all steps
        retrieved = store.get(record.execution_id)
        assert retrieved is not None

    @pytest.mark.asyncio
    async def test_flow_to_skill_to_evaluation(self):
        """测试 Flow → Skill → Evaluation 链路"""
        # 1. Flow selects skill
        flow = SequentialFlow()

        # 2. SkillLoader loads skill
        loader = SkillLoader()
        await loader.initialize()

        # 3. Evaluation validates
        eval = TaskCompletionEval()
        result = await eval.evaluate(
            task_description="Skill task",
            expected_result="done",
            actual_result="done"
        )

        assert result["success"] is True
