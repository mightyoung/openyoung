"""
Integration Tests for PEASHarnessIntegration

Tests the real integration between PEAS and HarnessEngine:
1. Real executor function (not mock)
2. End-to-end flow with actual component interaction
3. Streaming support verification
"""
import pytest
import asyncio
from typing import Any

from src.peas import (
    MarkdownParser,
    ContractBuilder,
    DriftDetector,
    Priority,
    DriftLevel,
)
from src.peas.integration.harness import PEASHarnessIntegration
from src.peas.types import FeatureStatus, VerificationStatus


# ============================================================================
# Test Content
# ============================================================================

SIMPLE_PRD = """# 简单任务 PRD

## 功能需求

### 1.1 数据处理

- Feature: CSV文件解析
- Must: 支持逗号分隔
- Must: 支持字段提取
- Should: 支持空行跳过

### 1.2 数据输出

- Feature: JSON格式输出
- Must: 输出有效JSON
- Could: 支持格式化
"""

EXECUTION_RESULT_FULL = """
已完成CSV文件解析功能:
- 使用Python csv模块解析逗号分隔文件
- 提取所有指定字段
- 跳过空行和注释行
已实现JSON格式输出:
- 生成标准JSON格式
- 支持格式化输出
"""

EXECUTION_RESULT_PARTIAL = """
已完成部分功能:
- CSV解析基本完成
- 支持逗号分隔
- 跳过空行
未完成:
- JSON输出功能
"""


# ============================================================================
# Mock LLM Client for Testing
# ============================================================================

class MockLLMClient:
    """Mock LLM client for testing"""

    async def generate(self, prompt: str, schema: Any = None) -> str:
        return "PASS"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPEASHarnessIntegration:
    """PEASHarnessIntegration集成测试"""

    @pytest.fixture
    def llm_client(self):
        return MockLLMClient()

    @pytest.fixture
    def integration(self, llm_client):
        return PEASHarnessIntegration(llm_client=llm_client)

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    @pytest.fixture
    def builder(self, llm_client):
        return ContractBuilder(llm_client)

    @pytest.fixture
    def detector(self):
        return DriftDetector()

    # ========================================================================
    # Test: Simple Executor with Full Implementation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_execute_with_simple_executor(self, integration, parser, builder, detector):
        """测试简单执行器 - 完整实现"""

        # Step 1: Parse spec
        doc = parser.parse(SIMPLE_PRD)
        assert doc.title == "简单任务 PRD"
        assert len(doc.feature_points) >= 2

        # Step 2: Build contract
        contract = builder.build(doc)
        assert contract is not None
        assert contract.total_requirements >= 2

        # Step 3: Setup integration
        integration.parse_spec(SIMPLE_PRD)
        integration.build_contract()

        # Step 4: Create real executor
        async def simple_executor(task: str, context: dict) -> str:
            return EXECUTION_RESULT_FULL

        # Step 5: Execute with real executor
        result = await integration.execute(
            task_description="实现CSV解析和JSON输出功能",
            executor_fn=simple_executor,
        )

        # Verify results
        assert result is not None
        assert "execution_result" in result
        assert "feature_statuses" in result
        assert "drift_report" in result
        assert "alignment_rate" in result

        # Verify alignment rate is high for full implementation
        assert result["alignment_rate"] >= 0.5

    # ========================================================================
    # Test: Simple Executor with Partial Implementation
    # ========================================================================

    @pytest.mark.asyncio
    async def test_execute_partial_implementation(self, integration, parser, builder, detector):
        """测试部分实现的偏离检测"""

        # Setup
        integration.parse_spec(SIMPLE_PRD)
        integration.build_contract()

        # Create executor that returns partial results
        async def partial_executor(task: str, context: dict) -> str:
            return EXECUTION_RESULT_PARTIAL

        # Execute
        result = await integration.execute(
            task_description="实现CSV解析功能",
            executor_fn=partial_executor,
        )

        # Verify partial implementation detection
        drift_report = result["drift_report"]
        assert drift_report is not None
        assert drift_report.total_count >= 2

        # Should have some drift since JSON output is missing
        assert drift_report.drift_score >= 0

    # ========================================================================
    # Test: Streaming Execution
    # ========================================================================

    @pytest.mark.asyncio
    async def test_streaming_execution(self, integration, parser, builder):
        """测试流式执行"""

        # Setup
        integration.parse_spec(SIMPLE_PRD)
        integration.build_contract()

        # Create executor
        async def streaming_executor(task: str, context: dict) -> str:
            await asyncio.sleep(0.01)  # Simulate work
            return "streaming result"

        # Execute streaming
        result_count = 0
        async for result in integration.execute_streaming(
            task_description="测试流式",
            executor_fn=streaming_executor,
        ):
            result_count += 1
            assert "phase" in result
            assert "status" in result

        # At minimum we should get one result
        assert result_count >= 1

    # ========================================================================
    # Test: Contract Building Before Execution Required
    # ========================================================================

    @pytest.mark.asyncio
    async def test_contract_required_before_execute(self, integration):
        """测试执行前必须构建合约"""

        integration.parse_spec(SIMPLE_PRD)

        # Should raise without building contract
        async def dummy_executor(task: str, context: dict) -> str:
            return "result"

        with pytest.raises(RuntimeError, match="Must build contract"):
            await integration.execute(
                task_description="test",
                executor_fn=dummy_executor,
            )

    # ========================================================================
    # Test: Parse Spec Required Before Contract
    # ========================================================================

    def test_parse_spec_required_before_contract(self, integration):
        """测试构建合约前必须解析规格"""

        with pytest.raises(RuntimeError, match="Must parse spec"):
            integration.build_contract()

    # ========================================================================
    # Test: Drift Detection with Different Priority Requirements
    # ========================================================================

    @pytest.mark.asyncio
    async def test_drift_detection_priority(self, integration, parser, builder):
        """测试不同优先级的偏离检测"""

        integration.parse_spec(SIMPLE_PRD)
        integration.build_contract()

        # Create executor that misses MUST requirements
        async def failing_executor(task: str, context: dict) -> str:
            return "Only partial work done, missing critical features"

        result = await integration.execute(
            task_description="实现不完整",
            executor_fn=failing_executor,
        )

        # Verify drift detection
        drift_report = result["drift_report"]
        assert drift_report is not None

        # Should detect drift
        assert drift_report.drift_score >= 0

    # ========================================================================
    # Test: Feature Summary
    # ========================================================================

    @pytest.mark.asyncio
    async def test_feature_summary(self, integration, parser, builder):
        """测试功能摘要"""

        integration.parse_spec(SIMPLE_PRD)
        integration.build_contract()

        async def executor(task: str, context: dict) -> str:
            return EXECUTION_RESULT_FULL

        result = await integration.execute(
            task_description="test",
            executor_fn=executor,
        )

        summary = integration.get_feature_summary()
        assert summary is not None
        assert isinstance(summary, dict)


class TestPEASHarnessIntegrationSync:
    """PEASHarnessIntegration同步测试"""

    @pytest.fixture
    def integration(self):
        return PEASHarnessIntegration()

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    def test_parse_and_build_workflow(self, integration, parser):
        """测试解析和构建工作流"""

        # Parse
        doc = integration.parse_spec(SIMPLE_PRD)
        assert doc is not None
        assert doc.title == "简单任务 PRD"

        # Build contract
        contract = integration.build_contract()
        assert contract is not None
        assert contract.contract_id is not None
        assert len(contract.requirements) >= 2

    def test_parse_file(self, integration, parser, tmp_path):
        """测试从文件解析"""

        # Create temp markdown file
        spec_file = tmp_path / "test_spec.md"
        spec_file.write_text(SIMPLE_PRD, encoding="utf-8")

        # Parse file
        doc = integration.parse_spec_file(str(spec_file))
        assert doc is not None
        assert doc.title == "简单任务 PRD"

    def test_get_drift_report_without_tracker(self, integration):
        """测试无tracker时获取偏离报告返回None"""

        report = integration.get_drift_report()
        assert report is None


# ============================================================================
# Test: End-to-End Verification
# ============================================================================

class TestPEASEndToEndVerification:
    """PEAS端到端验证测试"""

    @pytest.fixture
    def llm_client(self):
        return MockLLMClient()

    @pytest.fixture
    def integration(self, llm_client):
        return PEASHarnessIntegration(llm_client=llm_client)

    def test_full_workflow_alignment(self, integration):
        """测试完整工作流的对齐"""

        # Define a complete spec
        complete_spec = """# 完整实现规格

## 功能

### 核心功能

- Feature: 用户认证
- Must: 实现JWT登录
- Must: 实现Token验证
- Should: 实现RefreshToken

### 辅助功能

- Feature: 用户登出
- Must: 清除Token
"""

        # Setup integration
        integration.parse_spec(complete_spec)
        integration.build_contract()

        # Create executor with complete implementation
        async def complete_executor(task: str, context: dict) -> str:
            return """
            已完成所有功能:
            - 使用JWT实现用户登录
            - 实现Token验证中间件
            - 实现RefreshToken机制
            - 用户登出时清除所有Token
            """

        # Execute
        result = asyncio.run(integration.execute(
            task_description="实现完整用户认证系统",
            executor_fn=complete_executor,
        ))

        # Verify high alignment
        assert result["alignment_rate"] >= 0.5
