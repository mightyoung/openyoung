"""
RalphLoop - 自主循环直到任务完成
对标 oh-my-openagent 的 Ralph Loop 设计
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class AgentCategory(Enum):
    """Agent 类别 - 按能力分类而非模型"""

    QUICK = "quick"  # 快速简单任务
    VISUAL = "visual"  # 界面/前端相关
    DEEP = "deep"  # 复杂深度任务
    ULTRABRAIN = "ultrabrain"  # 需要深度思考


@dataclass
class AgentCategoryConfig:
    """Agent 类别配置"""

    description: str
    timeout_seconds: int = 60
    max_retries: int = 2


# Agent 类别默认配置
AGENT_CATEGORY_CONFIGS = {
    AgentCategory.QUICK: AgentCategoryConfig(
        description="快速简单任务，如文件操作、简单修改",
        timeout_seconds=60,
    ),
    AgentCategory.VISUAL: AgentCategoryConfig(
        description="界面/前端相关任务",
        timeout_seconds=300,
    ),
    AgentCategory.DEEP: AgentCategoryConfig(
        description="复杂深度任务，如架构设计、重构",
        timeout_seconds=600,
    ),
    AgentCategory.ULTRABRAIN: AgentCategoryConfig(
        description="需要深度思考的任务，如问题诊断、方案设计",
        timeout_seconds=900,
    ),
}


@dataclass
class LoopIteration:
    """循环迭代记录"""

    iteration: int
    plan: str
    executed_tasks: list[dict]
    evaluation: dict
    is_complete: bool


@dataclass
class RalphLoopConfig:
    """Ralph Loop 配置"""

    max_iterations: int = 10
    min_completion_rate: float = 0.8
    enable_parallel: bool = True
    max_parallel_agents: int = 5


class RalphLoop:
    """Ralph Loop - 自主循环直到任务完成

    核心理念：
    1. 不停止直到 100% 完成
    2. 按 Agent 类别分发任务
    3. 并行执行多个子任务
    4. 持续评估进度
    """

    def __init__(
        self,
        config: RalphLoopConfig | None = None,
        executor: Callable | None = None,
    ):
        self.config = config or RalphLoopConfig()
        self.executor = executor
        self.iterations: list[LoopIteration] = []
        self._is_running = False

    async def run_until_complete(
        self,
        task_description: str,
        initial_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """运行循环直到任务完成

        Args:
            task_description: 任务描述
            initial_context: 初始上下文

        Returns:
            包含结果和迭代历史的字典
        """
        self._is_running = True
        self.iterations = []

        context = initial_context or {}
        task_complete = False

        for iteration in range(1, self.config.max_iterations + 1):
            if not self._is_running:
                break

            # 1. 规划当前迭代
            plan = await self._plan_iteration(task_description, context)

            # 2. 并行执行子任务
            if self.config.enable_parallel:
                results = await self._execute_parallel(plan)
            else:
                results = await self._execute_sequential(plan)

            # 3. 评估结果
            evaluation = await self._evaluate_results(results, context)

            # 4. 记录迭代
            loop_iteration = LoopIteration(
                iteration=iteration,
                plan=plan,
                executed_tasks=results,
                evaluation=evaluation,
                is_complete=evaluation.get("is_complete", False),
            )
            self.iterations.append(loop_iteration)

            # 5. 检查是否完成
            if evaluation.get("is_complete", False):
                task_complete = True
                break

            # 6. 更新上下文继续迭代
            context = self._update_context(context, results, evaluation)

        # 聚合结果
        return {
            "task_description": task_description,
            "is_complete": task_complete,
            "iterations": len(self.iterations),
            "final_context": context,
            "iterations_detail": [
                {
                    "iteration": i.iteration,
                    "plan": i.plan,
                    "is_complete": i.is_complete,
                }
                for i in self.iterations
            ],
        }

    async def _plan_iteration(
        self,
        task_description: str,
        context: dict,
    ) -> str:
        """规划当前迭代"""
        # 简单实现：基于上下文生成计划
        prev_results = context.get("prev_results", [])
        if prev_results:
            return f"继续完成剩余部分，已完成 {len(prev_results)} 个任务"
        return f"执行任务: {task_description}"

    async def _execute_parallel(self, plan: str) -> list[dict]:
        """并行执行任务"""
        # 模拟并行执行
        # 实际实现应该 spawn 多个 agent
        await asyncio.sleep(0.1)
        return [{"task": plan, "status": "completed", "result": "ok"}]

    async def _execute_sequential(self, plan: str) -> list[dict]:
        """顺序执行任务"""
        return await self._execute_parallel(plan)

    async def _evaluate_results(
        self,
        results: list[dict],
        context: dict,
    ) -> dict:
        """评估结果"""
        # 简单实现：检查是否有失败
        failed = [r for r in results if r.get("status") == "failed"]

        if failed:
            return {
                "is_complete": False,
                "completion_rate": 0.5,
                "failed_count": len(failed),
            }

        return {
            "is_complete": True,
            "completion_rate": 1.0,
            "success_count": len(results),
        }

    def _update_context(
        self,
        context: dict,
        results: list[dict],
        evaluation: dict,
    ) -> dict:
        """更新上下文"""
        prev_results = context.get("prev_results", [])
        prev_results.extend(results)
        return {
            **context,
            "prev_results": prev_results,
            "completion_rate": evaluation.get("completion_rate", 0),
        }

    def stop(self):
        """停止循环"""
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._is_running

    def get_iteration_count(self) -> int:
        """获取迭代次数"""
        return len(self.iterations)


class TodoEnforcer:
    """Todo Enforcer - 拉回空闲 Agent 确保任务完成

    对标 oh-my-openagent 的设计：
    - 监控空闲的 agent
    - 必要时拉回完成任务
    - 防止任务挂起
    """

    def __init__(self):
        self.idle_agents: dict[str, dict] = {}
        self.active_tasks: dict[str, str] = {}  # task_id -> agent_id

    def register_idle(self, agent_id: str, agent_info: dict | None = None):
        """注册空闲的 Agent"""
        self.idle_agents[agent_id] = agent_info or {}

    def register_busy(self, agent_id: str, task_id: str):
        """注册忙碌的 Agent"""
        if agent_id in self.idle_agents:
            del self.idle_agents[agent_id]
        # 使用 agent_id 作为 key
        self.active_tasks[agent_id] = task_id

    def release_agent(self, agent_id: str):
        """释放 Agent（变为空闲）"""
        if agent_id in self.active_tasks:
            task_id = self.active_tasks.pop(agent_id)
            self.idle_agents[agent_id] = {"last_task": task_id}

    def get_idle_agent(self) -> str | None:
        """获取一个空闲的 Agent"""
        return next(iter(self.idle_agents.keys())) if self.idle_agents else None

    def pull_idle_for_task(self, task_id: str) -> str | None:
        """为任务拉回一个空闲的 Agent"""
        agent_id = self.get_idle_agent()
        if agent_id:
            self.register_busy(agent_id, task_id)
        return agent_id

    @property
    def idle_count(self) -> int:
        """空闲 Agent 数量"""
        return len(self.idle_agents)

    @property
    def busy_count(self) -> int:
        """忙碌 Agent 数量"""
        return len(self.active_tasks)
