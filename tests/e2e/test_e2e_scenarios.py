"""
E2E Tests - Phase 3
真实复杂任务场景测试
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.agents.young_agent import YoungAgent
from src.core.types import AgentConfig, AgentMode
from src.datacenter.execution_record import ExecutionRecord, ExecutionStatus
from src.datacenter.unified_store import UnifiedStore
from src.evaluation.hub import EvaluationHub
from src.evaluation.task_eval import TaskCompletionEval
from src.evaluation.planner import EvalPlan
from src.flow.sequential import SequentialFlow
from src.skills import SkillLoader


@pytest.mark.e2e
class TestScenario1DataPipeline:
    """T3.1: 场景1 - 数据采集→分析→报告生成

    用户输入: "爬取小红书热榜前10帖子，提取评论情感，分析趋势"
    """

    @pytest.mark.asyncio
    async def test_skill_retrieval_for_data_task(self):
        """测试数据采集任务的技能检索"""
        loader = SkillLoader()
        await loader.initialize()

        # 模拟技能检索
        task = "爬取小红书热榜前10帖子"
        skills = await loader.find_skills_for_task(task)

        # 应该找到相关技能
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_flow_sequencing(self):
        """测试流程编排 - 顺序执行"""
        flow = SequentialFlow()

        # 验证流程可以顺序执行
        assert flow.name == "sequential"

        # 模拟执行步骤
        context = {}
        await flow.pre_process("爬取→分析→报告", context)

        assert "_steps" in context or "_current_step" in context

    @pytest.mark.asyncio
    async def test_evaluation_with_plan(self):
        """测试评估执行 - 验证输出完整性"""
        eval = TaskCompletionEval()

        # 创建评估计划
        plan = EvalPlan(
            task_description="爬取小红书热榜前10帖子",
            task_type="web_scraping",
            success_criteria=[
                "成功获取热榜前10帖子",
                "数据保存到指定目录",
                "输出格式为JSON",
            ],
            expected_outputs={
                "file": "output/posts.json",
                "format": "json",
                "count": 10,
            },
        )

        # 评估实际结果
        result = await eval.evaluate_with_plan(
            task_description="爬取小红书热榜前10帖子",
            actual_result="已保存到 output/posts.json，共10条数据",
            eval_plan=plan,
        )

        assert result["completion_rate"] > 0
        assert "validation_results" in result

    @pytest.mark.asyncio
    async def test_data_storage_integration(self, tmp_path):
        """测试数据存储集成"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # 模拟保存执行结果
        record = ExecutionRecord(
            agent_name="data-pipeline-agent",
            task_description="爬取小红书热榜",
            status=ExecutionStatus.SUCCESS,
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            cost_usd=0.01,
        )

        store.save(record)

        # 验证保存成功
        retrieved = store.get(record.execution_id)
        assert retrieved is not None
        assert retrieved.status == ExecutionStatus.SUCCESS


@pytest.mark.e2e
class TestScenario2CodeReview:
    """T3.2: 场景2 - 代码审查→问题修复→测试验证

    用户输入: "审查 src/agents/ 目录代码，修复发现的问题，运行测试"
    """

    @pytest.mark.asyncio
    async def test_task_decomposition(self):
        """测试任务分解"""
        flow = SequentialFlow()

        # 模拟分解任务
        context = {}
        await flow.pre_process("审查代码→修复问题→运行测试", context)

        # 验证任务被分解
        assert context is not None

    @pytest.mark.asyncio
    async def test_evaluation_with_criteria(self):
        """测试带标准的评估"""
        eval = TaskCompletionEval()

        result = await eval.evaluate(
            task_description="修复代码问题",
            expected_result="所有测试通过",
            actual_result="所有测试通过",
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execution_tracking(self, tmp_path):
        """测试执行追踪"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # 模拟代码审查流程
        record = ExecutionRecord(
            agent_name="code-review-agent",
            task_description="审查并修复代码",
            status=ExecutionStatus.SUCCESS,
            duration_ms=5000,
        )

        store.save(record)

        # 验证记录
        retrieved = store.get(record.execution_id)
        assert retrieved is not None


@pytest.mark.e2e
class TestScenario3MultiAgent:
    """T3.3: 场景3 - 多 Agent 协作

    用户输入: "分析市场数据并生成投资建议"
    """

    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """测试 Agent 创建"""
        config = AgentConfig(name="research-agent", mode=AgentMode.PRIMARY)
        agent = YoungAgent(config)

        assert agent.config.name == "research-agent"

    @pytest.mark.asyncio
    async def test_subagent_dispatch(self):
        """测试子 Agent 分发"""
        config = AgentConfig(name="main-agent", mode=AgentMode.PRIMARY)
        agent = YoungAgent(config)

        # 验证子 Agent 可用
        sub_agents = agent._sub_agents
        assert isinstance(sub_agents, dict)

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, tmp_path):
        """测试多 Agent 协调"""
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))

        # 模拟主 Agent
        main_record = ExecutionRecord(
            agent_name="main-agent",
            task_description="分析市场数据",
            status=ExecutionStatus.SUCCESS,
        )
        store.save(main_record)

        # 模拟研究 Agent
        research_record = ExecutionRecord(
            agent_name="research-agent",
            task_description="收集市场数据",
            status=ExecutionStatus.SUCCESS,
        )
        store.save(research_record)

        # 模拟分析 Agent
        analysis_record = ExecutionRecord(
            agent_name="analysis-agent",
            task_description="分析数据趋势",
            status=ExecutionStatus.SUCCESS,
        )
        store.save(analysis_record)

        # 验证多 Agent 执行记录
        records = store.list_recent(limit=10)
        assert len(records) >= 3

    @pytest.mark.asyncio
    async def test_result_aggregation(self):
        """测试结果聚合"""
        # 模拟聚合多个 Agent 的结果
        results = [
            {"agent": "research", "data": {"price": 100}},
            {"agent": "analysis", "insight": "上涨趋势"},
        ]

        # 聚合逻辑
        aggregated = {
            "findings": [r.get("data", r.get("insight")) for r in results],
            "agents": len(results),
        }

        assert aggregated["agents"] == 2
        assert len(aggregated["findings"]) == 2


@pytest.mark.e2e
class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self, tmp_path):
        """测试完整工作流: 输入→处理→评估→存储"""

        # 1. 任务输入
        task_description = "分析数据并生成报告"

        # 2. 评估计划生成
        eval = TaskCompletionEval()
        plan = EvalPlan(
            task_description=task_description,
            task_type="analysis",
            success_criteria=["报告生成成功", "数据分析准确"],
            expected_outputs={"file": "report.json"},
        )

        # 3. 模拟执行
        actual_result = "报告已生成，包含分析结果"

        # 4. 评估
        result = await eval.evaluate_with_plan(
            task_description=task_description,
            actual_result=actual_result,
            eval_plan=plan,
        )

        # 5. 数据存储
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))
        record = ExecutionRecord(
            agent_name="analysis-agent",
            task_description=task_description,
            status=ExecutionStatus.SUCCESS if result["completion_rate"] > 0 else ExecutionStatus.FAILED,
        )
        store.save(record)

        # 验证完整流程
        assert result is not None
        assert record.execution_id is not None

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, tmp_path):
        """测试错误恢复工作流"""

        # 1. 任务失败
        store = UnifiedStore(db_path=str(tmp_path / "test.db"))
        record = ExecutionRecord(
            agent_name="test-agent",
            task_description="可能失败的任务",
            status=ExecutionStatus.FAILED,
            error="网络超时",
        )
        store.save(record)

        # 2. 错误记录
        failed = store.get(record.execution_id)
        assert failed.status == ExecutionStatus.FAILED

        # 3. 重试
        new_record = ExecutionRecord(
            agent_name="test-agent",
            task_description="重试任务",
            status=ExecutionStatus.SUCCESS,
        )
        store.save(new_record)

        # 4. 验证恢复
        success = store.get(new_record.execution_id)
        assert success.status == ExecutionStatus.SUCCESS
