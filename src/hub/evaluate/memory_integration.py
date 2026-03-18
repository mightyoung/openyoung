"""
Memory-Harness Integration - 记忆系统与评估引擎集成

功能:
- Task 执行前查询 SemanticMemory 获取相关经验
- Task 完成后沉淀执行结果到 SemanticMemory
- Harness 中断恢复支持

集成方式:
- 通过 Middleware 模式集成，不修改 Harness 核心代码
- 使用 SemanticMemory 的 retrieve/store 接口
- 复用现有 Checkpoint 机制
"""

import logging
from typing import Any, Optional

from .benchmark import BenchmarkTask
from .metrics import TaskMetrics, EvalTrial
from .middleware import BaseMiddleware, MiddlewareResult

logger = logging.getLogger(__name__)


class MemoryIntegrationMiddleware(BaseMiddleware):
    """
    Memory-Harness 集成中间件

    在 Task 执行前后与 Memory 系统交互:
    - before_task: 从 SemanticMemory 检索相关经验，注入到 task context
    - after_task: 将执行结果沉淀到 SemanticMemory

    用法:
        harness = EvaluationHarness(
            middleware=[MemoryIntegrationMiddleware()]
        )
    """

    name = "memory_integration"

    def __init__(
        self,
        memory_facade=None,  # MemoryFacade instance, will use global if None
        experience_category: str = "evaluation_experience",
        store_results: bool = True,
        retrieve_experiences: bool = True,
    ):
        self._memory_facade = memory_facade
        self._experience_category = experience_category
        self._store_results = store_results
        self._retrieve_experiences = retrieve_experiences

    # ====================
    # Middleware Hooks
    # ====================

    async def before_task(self, task: BenchmarkTask) -> MiddlewareResult:
        """Task 执行前: 查询相关经验"""
        if not self._retrieve_experiences:
            return MiddlewareResult.pass_through()

        try:
            facade = await self._get_memory_facade()
            if not facade:
                return MiddlewareResult.pass_through()

            # 构建查询上下文
            query_context = {
                "task_id": task.id,
                "task_desc": task.desc,
                "eval_type": task.eval_type.value if hasattr(task.eval_type, 'value') else str(task.eval_type),
            }

            # 查询相关经验
            results = await facade.retrieve(
                query=task.desc,
                layer=None,  # auto-route
                context=query_context,
                limit=5,
            )

            if results:
                # 格式化经验内容
                experiences = []
                for result in results:
                    entry = result.entry if hasattr(result, 'entry') else result
                    exp_content = f"[相关度:{result.relevance_score:.2f}] {entry.content}"
                    experiences.append(exp_content)

                experience_text = "\n---\n".join(experiences)

                logger.info(f"Retrieved {len(results)} relevant experiences for task {task.id}")

                return MiddlewareResult(
                    allowed=True,
                    modified_context={
                        "relevant_experiences": experience_text,
                        "experience_count": len(results),
                    },
                )

        except Exception as e:
            logger.warning(f"Failed to retrieve experiences for task {task.id}: {e}")

        return MiddlewareResult.pass_through()

    async def after_task(
        self,
        task: BenchmarkTask,
        metrics: TaskMetrics,
    ) -> MiddlewareResult:
        """Task 完成后: 沉淀执行结果到 SemanticMemory"""
        if not self._store_results:
            return MiddlewareResult.pass_through()

        try:
            facade = await self._get_memory_facade()
            if not facade:
                return MiddlewareResult.pass_through()

            # 从 metrics 构建知识内容
            content = self._build_result_content(task, metrics)

            # 提取标签
            tags = [
                "evaluation",
                task.eval_type.value if hasattr(task.eval_type, 'value') else "unknown",
                "task_result",
            ]

            # 元数据
            metadata = {
                "task_id": task.id,
                "eval_type": task.eval_type.value if hasattr(task.eval_type, 'value') else str(task.eval_type),
                "pass_rate": metrics.pass_at_1,
                "avg_score": metrics.avg_score,
                "total_trials": metrics.total_trials,
            }

            # 存储结果
            entry_id = await facade.store(
                content=content,
                layer=None,  # auto-route to semantic
                category=self._experience_category,
                tags=tags,
                metadata=metadata,
            )

            logger.info(f"Stored evaluation result for task {task.id}: {entry_id}")

        except Exception as e:
            logger.warning(f"Failed to store evaluation result for task {task.id}: {e}")

        return MiddlewareResult.pass_through()

    # ====================
    # Checkpoint Integration
    # ====================

    async def before_suite(self, suite) -> None:
        """Suite 执行前: 可以做检查点恢复检查"""
        # 如果需要从上次中断点恢复，可以在这里实现
        # 目前由 Harness 的 checkpoint 机制处理
        pass

    async def after_suite(self, suite, metrics) -> None:
        """Suite 完成后: 清理或最终化检查点"""
        # 标记所有 task 的检查点为最终状态
        pass

    # ====================
    # 辅助方法
    # ====================

    async def _get_memory_facade(self):
        """获取 MemoryFacade 实例"""
        if self._memory_facade:
            return self._memory_facade

        # 延迟导入避免循环依赖
        from src.core.memory import get_memory_facade

        try:
            return await get_memory_facade()
        except Exception as e:
            logger.warning(f"Failed to get memory facade: {e}")
            return None

    def _build_result_content(
        self,
        task: BenchmarkTask,
        metrics: TaskMetrics,
    ) -> str:
        """构建结果知识内容"""
        lines = [
            f"Evaluation Result: {task.id}",
            f"Description: {task.desc}",
            f"Eval Type: {task.eval_type.value if hasattr(task.eval_type, 'value') else task.eval_type}",
            "",
            f"Pass Rate: {metrics.pass_at_1:.1%}",
            f"Average Score: {metrics.avg_score:.2f}",
            f"Total Trials: {metrics.total_trials}",
        ]

        # 添加每次 trial 的结果摘要
        if metrics.trials:
            lines.append("")
            lines.append("Trial Results:")
            for i, trial in enumerate(metrics.trials[:3]):  # 最多 3 个
                status = "PASS" if trial.passed else "FAIL"
                score = trial.overall_score if hasattr(trial, 'overall_score') and trial.overall_score else 0.0
                lines.append(f"  Trial {i+1}: {status} (score: {score:.2f})")

        return "\n".join(lines)


# ====================
# Standalone Memory-Harness 集成器
# ====================


class HarnessMemoryConnector:
    """
    独立的 Harness-Memory 连接器

    用于在 Harness 外部管理 memory 集成:
    - 初始化 memory 系统
    - 提供便捷的查询/存储方法

    用法:
        connector = HarnessMemoryConnector()
        await connector.initialize()

        # 在执行 task 前
        experiences = await connector.get_relevant_experiences(task_desc)

        # 在 task 完成后
        await connector.store_execution_result(task, metrics)
    """

    def __init__(
        self,
        experience_category: str = "evaluation_experience",
    ):
        self._experience_category = experience_category
        self._facade = None

    async def initialize(self) -> None:
        """初始化连接器"""
        from src.core.memory import get_memory_facade

        self._facade = await get_memory_facade()
        logger.info("HarnessMemoryConnector initialized")

    async def get_relevant_experiences(
        self,
        query: str,
        context: Optional[dict[str, Any]] = None,
        limit: int = 5,
    ) -> list[str]:
        """获取相关经验

        Args:
            query: 查询文本
            context: 上下文信息
            limit: 返回数量

        Returns:
            经验内容列表
        """
        if not self._facade:
            await self.initialize()

        results = await self._facade.retrieve(
            query=query,
            context=context,
            limit=limit,
        )

        experiences = []
        for result in results:
            entry = result.entry if hasattr(result, 'entry') else result
            experiences.append(entry.content)

        return experiences

    async def store_execution_result(
        self,
        task_id: str,
        task_desc: str,
        eval_type: str,
        metrics: TaskMetrics,
    ) -> str:
        """存储执行结果

        Args:
            task_id: 任务 ID
            task_desc: 任务描述
            eval_type: 评估类型
            metrics: 评估指标

        Returns:
            存储的 entry_id
        """
        if not self._facade:
            await self.initialize()

        content = self._build_content(task_id, task_desc, eval_type, metrics)

        tags = ["evaluation", eval_type, "execution_result"]
        metadata = {
            "task_id": task_id,
            "eval_type": eval_type,
            "pass_rate": metrics.pass_at_1,
            "avg_score": metrics.avg_score,
        }

        return await self._facade.store(
            content=content,
            layer=None,
            category=self._experience_category,
            tags=tags,
            metadata=metadata,
        )

    def _build_content(
        self,
        task_id: str,
        task_desc: str,
        eval_type: str,
        metrics: TaskMetrics,
    ) -> str:
        """构建存储内容"""
        lines = [
            f"Task: {task_id}",
            f"Description: {task_desc}",
            f"Eval Type: {eval_type}",
            f"Pass@1: {metrics.pass_at_1:.1%}",
            f"Pass@3: {metrics.pass_at_3:.1%}",
            f"Average Score: {metrics.avg_score:.2f}",
            f"Total Trials: {metrics.total_trials}",
        ]
        return "\n".join(lines)
