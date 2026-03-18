"""
Memory-Harness Integration Tests - 记忆系统与评估引擎集成测试

测试模块:
- src/hub/evaluate/memory_integration.py - MemoryIntegrationMiddleware
- src/core/memory/facade.py - MemoryFacade

覆盖:
1. MemoryIntegrationMiddleware.before_task - 检索相关经验
2. MemoryIntegrationMiddleware.after_task - 沉淀执行结果
3. MemoryIntegrationMiddleware 链式调用
4. HarnessMemoryConnector 独立连接器
5. 记忆沉淀流程验证
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.hub.evaluate.memory_integration import (
    MemoryIntegrationMiddleware,
    HarnessMemoryConnector,
)
from src.hub.evaluate.benchmark import BenchmarkTask, EvalType, GraderConfig, GraderType, GradingMode
from src.hub.evaluate.metrics import TaskMetrics, EvalTrial, TrialMetrics, GraderResult
from src.hub.evaluate.middleware import MiddlewareResult
from src.core.memory.facade import MemoryFacade, MemoryLayer


# ========== Fixtures ==========


@pytest.fixture
def mock_memory_facade():
    """创建 Mock MemoryFacade"""
    facade = MagicMock(spec=MemoryFacade)
    facade.retrieve = AsyncMock()
    facade.store = AsyncMock(return_value="entry-001")
    facade._initialized = True
    return facade


@pytest.fixture
def sample_task():
    """创建示例 BenchmarkTask"""
    return BenchmarkTask(
        id="test-task-001",
        desc="Implement authentication for API",
        prompt="Add JWT authentication to the API",
        graders=[
            GraderConfig(
                grader_type=GraderType.CODE_BASED,
                name="has-test",
                required=True,
            )
        ],
        eval_type=EvalType.CAPABILITY,
        tags=["security", "auth"],
    )


@pytest.fixture
def sample_task_metrics(sample_task):
    """创建示例 TaskMetrics"""
    trial = EvalTrial(
        task_id=sample_task.id,
        trial_number=1,
        passed=True,
        overall_score=0.85,
        grader_results=[
            GraderResult(
                grader_name="has-test",
                passed=True,
                score=0.85,
                details="All tests passed",
            )
        ],
        metrics=TrialMetrics(
            latency_ms=1500.0,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost_usd=0.01,
        ),
    )

    return TaskMetrics(
        task_id=sample_task.id,
        eval_type=sample_task.eval_type,
        pass_at_1=1.0,
        pass_at_3=1.0,
        pass_at_k=1.0,
        pass_rate=1.0,
        avg_latency_ms=1500.0,
        avg_cost_usd=0.01,
        avg_score=0.85,
        total_trials=1,
        successful_trials=1,
        first_success_trial=1,
        trials=[trial],
    )


# ========== Test MemoryIntegrationMiddleware ==========


class TestMemoryIntegrationMiddleware:
    """MemoryIntegrationMiddleware 测试"""

    def test_middleware_initialization(self):
        """测试中间件初始化"""
        middleware = MemoryIntegrationMiddleware()

        assert middleware.name == "memory_integration"
        assert middleware._store_results is True
        assert middleware._retrieve_experiences is True
        assert middleware._experience_category == "evaluation_experience"

    def test_middleware_initialization_custom_params(self):
        """测试自定义参数初始化"""
        middleware = MemoryIntegrationMiddleware(
            experience_category="custom_category",
            store_results=False,
            retrieve_experiences=False,
        )

        assert middleware._experience_category == "custom_category"
        assert middleware._store_results is False
        assert middleware._retrieve_experiences is False

    @pytest.mark.asyncio
    async def test_before_task_retrieves_experiences(self, mock_memory_facade, sample_task):
        """测试 before_task 从 SemanticMemory 检索经验"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)

        # Mock 返回检索结果
        mock_result = MagicMock()
        mock_result.entry.content = "Previous experience: Use JWT tokens"
        mock_result.relevance_score = 0.92
        mock_memory_facade.retrieve.return_value = [mock_result]

        result = await middleware.before_task(sample_task)

        assert result.allowed is True
        assert result.modified_context is not None
        assert "relevant_experiences" in result.modified_context
        assert "experience_count" in result.modified_context
        assert result.modified_context["experience_count"] == 1
        assert "JWT tokens" in result.modified_context["relevant_experiences"]

        # 验证调用了 facade.retrieve
        mock_memory_facade.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_before_task_no_experiences(self, mock_memory_facade, sample_task):
        """测试 before_task 无相关经验时 pass_through"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        mock_memory_facade.retrieve.return_value = []

        result = await middleware.before_task(sample_task)

        assert result.allowed is True
        assert result.modified_context is None

    @pytest.mark.asyncio
    async def test_before_task_disabled_retrieve(self, mock_memory_facade, sample_task):
        """测试禁用检索时 pass_through"""
        middleware = MemoryIntegrationMiddleware(
            memory_facade=mock_memory_facade,
            retrieve_experiences=False,
        )

        result = await middleware.before_task(sample_task)

        assert result.allowed is True
        mock_memory_facade.retrieve.assert_not_called()

    @pytest.mark.asyncio
    async def test_before_task_exception_handling(self, mock_memory_facade, sample_task):
        """测试异常处理 - 失败时 pass_through"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        mock_memory_facade.retrieve.side_effect = Exception("Connection error")

        result = await middleware.before_task(sample_task)

        assert result.allowed is True
        assert result.modified_context is None

    @pytest.mark.asyncio
    async def test_after_task_stores_results(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试 after_task 沉淀结果到 SemanticMemory"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)

        result = await middleware.after_task(sample_task, sample_task_metrics)

        assert result.allowed is True
        mock_memory_facade.store.assert_called_once()

        # 验证调用参数
        call_args = mock_memory_facade.store.call_args
        assert call_args.kwargs["category"] == "evaluation_experience"
        assert "evaluation" in call_args.kwargs["tags"]
        assert call_args.kwargs["metadata"]["task_id"] == sample_task.id

    @pytest.mark.asyncio
    async def test_after_task_disabled_store(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试禁用存储时 pass_through"""
        middleware = MemoryIntegrationMiddleware(
            memory_facade=mock_memory_facade,
            store_results=False,
        )

        result = await middleware.after_task(sample_task, sample_task_metrics)

        assert result.allowed is True
        mock_memory_facade.store.assert_not_called()

    @pytest.mark.asyncio
    async def test_after_task_exception_handling(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试异常处理 - 失败时 pass_through"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        mock_memory_facade.store.side_effect = Exception("Storage error")

        result = await middleware.after_task(sample_task, sample_task_metrics)

        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_build_result_content(self, sample_task, sample_task_metrics):
        """测试结果内容构建"""
        middleware = MemoryIntegrationMiddleware()
        content = middleware._build_result_content(sample_task, sample_task_metrics)

        assert sample_task.id in content
        assert "Pass Rate" in content
        assert "Average Score" in content
        assert "Trial Results" in content


# ========== Test Middleware Chain ==========


class TestMiddlewareChain:
    """中间件链式调用测试"""

    @pytest.mark.asyncio
    async def test_multiple_middleware_chain(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试多个中间件顺序执行"""
        # 创建多个中间件实例
        middleware1 = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        middleware2 = MemoryIntegrationMiddleware(
            memory_facade=mock_memory_facade,
            experience_category="custom",
        )

        # Mock 返回值
        mock_result = MagicMock()
        mock_result.entry.content = "Experience content"
        mock_result.relevance_score = 0.9
        mock_memory_facade.retrieve.return_value = [mock_result]

        # 顺序执行 before_task
        result1 = await middleware1.before_task(sample_task)
        result2 = await middleware2.before_task(sample_task)

        # 两个中间件都成功执行
        assert result1.allowed is True
        assert result2.allowed is True

        # 验证各自使用了不同的 category
        call1 = mock_memory_facade.retrieve.call_args_list[0]
        call2 = mock_memory_facade.retrieve.call_args_list[1]

    @pytest.mark.asyncio
    async def test_middleware_preserves_task_context(self, mock_memory_facade, sample_task):
        """测试中间件保留原始 task 上下文"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        mock_memory_facade.retrieve.return_value = []

        result = await middleware.before_task(sample_task)

        # 验证 task 本身未被修改
        assert result.allowed is True
        # pass_through 时 modified_context 为 None
        assert result.modified_context is None


# ========== Test HarnessMemoryConnector ==========


class TestHarnessMemoryConnector:
    """HarnessMemoryConnector 测试"""

    @pytest.mark.asyncio
    async def test_connector_initialization(self):
        """测试连接器初始化"""
        connector = HarnessMemoryConnector()

        assert connector._experience_category == "evaluation_experience"
        assert connector._facade is None

    @pytest.mark.asyncio
    async def test_connector_custom_category(self):
        """测试自定义 category"""
        connector = HarnessMemoryConnector(experience_category="my_experiences")
        assert connector._experience_category == "my_experiences"

    @pytest.mark.asyncio
    async def test_get_relevant_experiences(self, mock_memory_facade):
        """测试获取相关经验"""
        connector = HarnessMemoryConnector()
        connector._facade = mock_memory_facade

        mock_result = MagicMock()
        mock_result.entry.content = "Test experience"
        mock_memory_facade.retrieve.return_value = [mock_result]

        experiences = await connector.get_relevant_experiences(
            query="authentication",
            limit=3,
        )

        assert len(experiences) == 1
        assert experiences[0] == "Test experience"
        mock_memory_facade.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_execution_result(self, mock_memory_facade, sample_task_metrics):
        """测试存储执行结果"""
        connector = HarnessMemoryConnector()
        connector._facade = mock_memory_facade

        entry_id = await connector.store_execution_result(
            task_id="task-001",
            task_desc="Test task",
            eval_type="capability",
            metrics=sample_task_metrics,
        )

        assert entry_id == "entry-001"
        mock_memory_facade.store.assert_called_once()

        # 验证 metadata
        call_args = mock_memory_facade.store.call_args
        assert call_args.kwargs["metadata"]["task_id"] == "task-001"
        assert call_args.kwargs["metadata"]["eval_type"] == "capability"
        assert call_args.kwargs["metadata"]["pass_rate"] == sample_task_metrics.pass_at_1

    @pytest.mark.asyncio
    async def test_store_execution_result_auto_init(self, mock_memory_facade, sample_task_metrics):
        """测试自动初始化时存储"""
        connector = HarnessMemoryConnector()
        # _facade 为 None，调用时会自动初始化

        with patch("src.core.memory.get_memory_facade", new_callable=AsyncMock) as mock_get_facade:
            mock_get_facade.return_value = mock_memory_facade

            entry_id = await connector.store_execution_result(
                task_id="task-001",
                task_desc="Test task",
                eval_type="capability",
                metrics=sample_task_metrics,
            )

            assert entry_id == "entry-001"


# ========== Test Memory沉淀流程 ==========


class TestMemorySedimentation:
    """记忆沉淀流程测试"""

    @pytest.mark.asyncio
    async def test_full_sedimentation_flow(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试完整沉淀流程"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)

        # 1. Task 执行前 - 检索经验
        mock_result = MagicMock()
        mock_result.entry.content = "Previous solution approach"
        mock_result.relevance_score = 0.88
        mock_memory_facade.retrieve.return_value = [mock_result]

        before_result = await middleware.before_task(sample_task)

        # 2. Task 执行后 - 沉淀结果
        after_result = await middleware.after_task(sample_task, sample_task_metrics)

        # 验证流程完整执行
        assert before_result.allowed is True
        assert after_result.allowed is True
        assert mock_memory_facade.retrieve.call_count == 1
        assert mock_memory_facade.store.call_count == 1

    @pytest.mark.asyncio
    async def test_sedimentation_without_prior_experience(self, mock_memory_facade, sample_task, sample_task_metrics):
        """测试无先前经验时的沉淀"""
        middleware = MemoryIntegrationMiddleware(memory_facade=mock_memory_facade)
        mock_memory_facade.retrieve.return_value = []  # 无经验

        before_result = await middleware.before_task(sample_task)
        after_result = await middleware.after_task(sample_task, sample_task_metrics)

        # 仍然沉淀结果
        assert before_result.allowed is True
        assert after_result.allowed is True
        mock_memory_facade.store.assert_called_once()


# ========== Test MemoryFacade Integration ==========


class TestMemoryFacadeIntegration:
    """MemoryFacade 与 Harness 集成测试"""

    @pytest.mark.asyncio
    async def test_facade_retrieve_auto_route(self):
        """测试 facade 自动路由"""
        facade = MemoryFacade()

        mock_working = MagicMock()
        mock_context = MagicMock()
        mock_context.task_id = "test-001"
        mock_context.task_description = "Test task"
        mock_context.messages = []
        mock_context.variables = {}
        mock_working.get_current_context.return_value = mock_context
        facade.working_memory = mock_working

        mock_semantic = AsyncMock()
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        # 工作关键词应该路由到 Working Memory
        results = await facade.retrieve(
            query="current task context",
            layer=None,
        )

        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_facade_store_semantic(self):
        """测试 facade 存储到 semantic"""
        facade = MemoryFacade()

        mock_semantic = AsyncMock()
        mock_semantic.store.return_value = "entry-002"
        facade.semantic_memory = mock_semantic

        facade._initialized = True

        entry_id = await facade.store(
            content="Test knowledge",
            layer=MemoryLayer.SEMANTIC,
            category="test",
        )

        assert entry_id == "entry-002"
        mock_semantic.store.assert_called_once()


# ========== Test MiddlewareResult ==========


class TestMiddlewareResult:
    """MiddlewareResult 测试"""

    def test_pass_through(self):
        """测试 pass_through"""
        result = MiddlewareResult.pass_through()
        assert result.allowed is True
        assert result.modified_context is None

    def test_block(self):
        """测试 block"""
        result = MiddlewareResult.block("Task timeout")
        assert result.allowed is False
        assert "Task timeout" in result.warnings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
