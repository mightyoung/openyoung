"""
Multi-Agent Crew - 多Agent协作系统

基于CrewAI、LangChain模式的Agent团队协作
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class ProcessType(Enum):
    """编排类型"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    HIERARCHICAL = "hierarchical"  # 层级执行


class AgentRole(Enum):
    """Agent角色"""

    PLANNER = "planner"  # 规划者
    WORKER = "worker"  # 执行者
    REVIEWER = "reviewer"  # 审查者
    COORDINATOR = "coordinator"  # 协调者


@dataclass
class AgentSpec:
    """Agent规格定义"""

    id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:8]}")
    name: str = ""
    role: AgentRole = AgentRole.WORKER
    goal: str = ""
    backstory: str = ""
    tools: list[str] = field(default_factory=list)
    max_iterations: int = 5
    temperature: float = 0.7


@dataclass
class TaskDefinition:
    """任务定义"""

    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    description: str = ""
    expected_output: str = ""
    agent_id: str = ""  # 指定执行Agent
    dependencies: list[str] = field(default_factory=list)
    priority: int = 0
    context: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务结果"""

    task_id: str
    agent_id: str
    success: bool
    output: Any
    error: str = ""
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CrewResult:
    """团队执行结果"""

    success: bool
    results: list[TaskResult] = field(default_factory=list)
    final_output: Any = None
    total_duration_ms: int = 0
    metadata: dict = field(default_factory=dict)


class BaseAgent:
    """基础Agent"""

    def __init__(self, spec: AgentSpec):
        self.spec = spec
        self._history: list[dict] = []

    async def execute(self, task: TaskDefinition) -> TaskResult:
        """执行任务 - 子类实现"""
        raise NotImplementedError

    def add_to_history(self, entry: dict):
        """添加到历史"""
        self._history.append(
            {
                **entry,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def get_history(self) -> list[dict]:
        """获取历史"""
        return self._history


class MultiAgentCrew:
    """多Agent协作团队"""

    def __init__(
        self,
        agents: list[BaseAgent],
        process: ProcessType = ProcessType.SEQUENTIAL,
    ):
        self.agents = {agent.spec.id: agent for agent in agents}
        self.process = process
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.result_cache: dict[str, TaskResult] = {}

    async def execute(self, tasks: list[TaskDefinition]) -> CrewResult:
        """执行任务"""
        start_time = datetime.now()
        results = []

        if self.process == ProcessType.SEQUENTIAL:
            results = await self._execute_sequential(tasks)
        elif self.process == ProcessType.PARALLEL:
            results = await self._execute_parallel(tasks)
        elif self.process == ProcessType.HIERARCHICAL:
            results = await self._execute_hierarchical(tasks)

        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # 聚合最终输出
        final_output = self._aggregate_results(results)

        success = all(r.success for r in results)

        return CrewResult(
            success=success,
            results=results,
            final_output=final_output,
            total_duration_ms=duration_ms,
            metadata={
                "process": self.process.value,
                "agent_count": len(self.agents),
                "task_count": len(tasks),
            },
        )

    async def _execute_sequential(self, tasks: list[TaskDefinition]) -> list[TaskResult]:
        """顺序执行"""
        results = []
        for task in tasks:
            # 检查依赖
            if not self._check_dependencies(task):
                results.append(
                    TaskResult(
                        task_id=task.id,
                        agent_id="",
                        success=False,
                        output=None,
                        error="Dependencies not met",
                    )
                )
                continue

            # 获取执行Agent
            agent = self._get_agent_for_task(task)
            if not agent:
                results.append(
                    TaskResult(
                        task_id=task.id,
                        agent_id="",
                        success=False,
                        output=None,
                        error="No suitable agent found",
                    )
                )
                continue

            # 执行
            result = await agent.execute(task)
            results.append(result)
            self.result_cache[task.id] = result

        return results

    async def _execute_parallel(self, tasks: list[TaskDefinition]) -> list[TaskResult]:
        """并行执行"""
        # 过滤可执行任务
        runnable_tasks = [t for t in tasks if self._check_dependencies(t)]

        # 为每个任务分配Agent
        agent_tasks = []
        for task in runnable_tasks:
            agent = self._get_agent_for_task(task)
            if agent:
                agent_tasks.append(self._run_task(agent, task))
            else:
                agent_tasks.append(
                    asyncio.sleep(
                        0,
                        result=TaskResult(
                            task_id=task.id,
                            agent_id="",
                            success=False,
                            output=None,
                            error="No suitable agent",
                        ),
                    )
                )

        # 并行执行
        results = await asyncio.gather(*agent_tasks)

        # 更新缓存
        for result in results:
            self.result_cache[result.task_id] = result

        return list(results)

    async def _execute_hierarchical(self, tasks: list[TaskDefinition]) -> list[TaskResult]:
        """层级执行 - Planner -> Worker -> Reviewer"""
        # 1. Planner 分解任务
        planner = self._get_agent_by_role(AgentRole.PLANNER)
        if not planner:
            return await self._execute_sequential(tasks)

        # 2. 分配任务给Workers
        worker_tasks = []
        for task in tasks:
            worker = self._get_agent_for_task(task)
            if worker:
                worker_tasks.append(self._run_task(worker, task))
            else:
                worker_tasks.append(
                    asyncio.sleep(
                        0,
                        result=TaskResult(
                            task_id=task.id,
                            agent_id="",
                            success=False,
                            output=None,
                            error="No worker",
                        ),
                    )
                )

        worker_results = await asyncio.gather(*worker_tasks)

        # 3. Reviewer 审查
        reviewer = self._get_agent_by_role(AgentRole.REVIEWER)
        if reviewer:
            # 简单审查：检查所有结果
            all_success = all(r.success for r in worker_results)
            if not all_success:
                # 失败重试
                failed_tasks = [t for t, r in zip(tasks, worker_results) if not r.success]
                retry_results = await self._execute_sequential(failed_tasks)
                return worker_results + retry_results

        return worker_results

    async def _run_task(self, agent: BaseAgent, task: TaskDefinition) -> TaskResult:
        """运行单个任务"""
        start = datetime.now()
        try:
            result = await agent.execute(task)
            return result
        except Exception as e:
            end = datetime.now()
            return TaskResult(
                task_id=task.id,
                agent_id=agent.spec.id,
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((end - start).total_seconds() * 1000),
            )

    def _check_dependencies(self, task: TaskDefinition) -> bool:
        """检查依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in self.result_cache:
                return False
            if not self.result_cache[dep_id].success:
                return False
        return True

    def _get_agent_for_task(self, task: TaskDefinition) -> Optional[BaseAgent]:
        """获取任务的执行Agent"""
        # 如果指定了Agent
        if task.agent_id and task.agent_id in self.agents:
            return self.agents[task.agent_id]

        # 否则根据任务类型选择
        # 简单规则：包含"分析"选planner，包含"审查"选reviewer
        if "分析" in task.description or "分析" in task.description.lower():
            return self._get_agent_by_role(AgentRole.PLANNER)
        elif "审查" in task.description or "review" in task.description.lower():
            return self._get_agent_by_role(AgentRole.REVIEWER)
        else:
            return self._get_agent_by_role(AgentRole.WORKER)

    def _get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        """根据角色获取Agent"""
        for agent in self.agents.values():
            if agent.spec.role == role:
                return agent
        # 默认返回第一个
        return next(iter(self.agents.values())) if self.agents else None

    def _aggregate_results(self, results: list[TaskResult]) -> Any:
        """聚合结果"""
        if not results:
            return None

        # 如果只有一个结果，直接返回
        if len(results) == 1:
            return results[0].output

        # 否则返回结果列表
        return {
            "outputs": [r.output for r in results],
            "summary": {
                "total": len(results),
                "success": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
            },
        }


# ========== 便捷函数 ==========


def create_crew(
    agent_specs: list[AgentSpec],
    process: str = "sequential",
) -> MultiAgentCrew:
    """创建多Agent团队"""
    process_type = ProcessType(process)
    agents = [BaseAgent(spec) for spec in agent_specs]
    return MultiAgentCrew(agents, process_type)
