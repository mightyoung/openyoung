"""
Pipeline - 声明式任务管道
对标 LangGraph StateGraph，实现 DAG 编排
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StageStatus(Enum):
    """Stage 执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Stage:
    """管道阶段"""
    name: str
    description: str = ""
    skill: str | None = None  # 使用的 Skill
    agent: str | None = None   # 使用的 Agent
    handler: Callable | None = None  # 自定义处理函数
    params: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None  # 条件执行
    depends_on: list[str] = field(default_factory=list)  # 依赖的 Stage

    def __hash__(self):
        return hash(self.name)


@dataclass
class PipelineContext:
    """管道执行上下文"""
    initial_data: dict[str, Any] = field(default_factory=dict)
    stage_results: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_result(self, stage_name: str) -> Any:
        """获取 Stage 执行结果"""
        return self.stage_results.get(stage_name)

    def set_result(self, stage_name: str, result: Any):
        """设置 Stage 执行结果"""
        self.stage_results[stage_name] = result

    def get_error(self, stage_name: str) -> str | None:
        """获取 Stage 错误"""
        return self.errors.get(stage_name)

    def set_error(self, stage_name: str, error: str):
        """设置 Stage 错误"""
        self.errors[stage_name] = error

    def is_ready(self, stage: Stage) -> bool:
        """检查 Stage 是否准备好执行（所有依赖已完成）"""
        for dep in stage.depends_on:
            if dep not in self.stage_results:
                return False
            if dep in self.errors:
                return False
        return True


class Pipeline(ABC):
    """管道抽象类

    使用方式：
    1. 继承 Pipeline
    2. 定义 stages()
    3. 实现 execute_stage()
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._stages: list[Stage] = []
        self._build()

    @abstractmethod
    def _build(self):
        """构建管道 Stages"""
        pass

    @abstractmethod
    async def execute_stage(self, stage: Stage, context: PipelineContext) -> Any:
        """执行单个 Stage"""
        pass

    def add_stage(self, stage: Stage):
        """添加 Stage"""
        self._stages.append(stage)

    def get_stages(self) -> list[Stage]:
        """获取所有 Stages"""
        return self._stages

    def get_stage(self, name: str) -> Stage | None:
        """获取指定 Stage"""
        for s in self._stages:
            if s.name == name:
                return s
        return None

    def topological_sort(self) -> list[Stage]:
        """拓扑排序（用于确定执行顺序）"""
        # 计算入度
        in_degree = {s.name: len(s.depends_on) for s in self._stages}
        # 找到入度为 0 的节点
        queue = [s for s in self._stages if in_degree[s.name] == 0]
        result = []

        while queue:
            # 按优先级排序（可选）
            queue.sort(key=lambda s: s.name)
            stage = queue.pop(0)
            result.append(stage)

            # 更新依赖该 Stage 的节点
            for s in self._stages:
                if stage.name in s.depends_on:
                    in_degree[s.name] -= 1
                    if in_degree[s.name] == 0:
                        queue.append(s)

        if len(result) != len(self._stages):
            raise ValueError("Pipeline has circular dependencies")

        return result

    async def execute(self, initial_data: dict | None = None) -> PipelineContext:
        """执行管道"""
        context = PipelineContext(initial_data=initial_data or {})
        execution_order = self.topological_sort()

        # 执行每个 Stage
        for stage in execution_order:
            # 检查是否准备好执行
            if not context.is_ready(stage):
                context.set_error(stage.name, "Dependencies not satisfied")
                continue

            # 检查条件
            if stage.condition:
                # 简单条件评估（后续可以扩展）
                should_skip = self._evaluate_condition(stage.condition, context)
                if should_skip:
                    continue

            try:
                # 执行 Stage
                result = await self.execute_stage(stage, context)
                context.set_result(stage.name, result)
            except Exception as e:
                context.set_error(stage.name, str(e))

        return context

    def _evaluate_condition(self, condition: str, context: PipelineContext) -> bool:
        """评估条件"""
        # 简单实现：检查是否包含某个结果
        # 后续可以扩展为更复杂的表达式评估
        if condition.startswith("has:"):
            key = condition[4:]
            return key in context.stage_results
        if condition.startswith("not:"):
            key = condition[4:]
            return key not in context.stage_results
        return True


class PipelineExecutor:
    """管道执行器 - 执行多个 Pipeline"""

    def __init__(self):
        self.pipelines: dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline):
        """注册管道"""
        self.pipelines[pipeline.name] = pipeline

    async def execute(self, pipeline_name: str, initial_data: dict | None = None) -> PipelineContext:
        """执行管道"""
        if pipeline_name not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_name}")

        pipeline = self.pipelines[pipeline_name]
        return await pipeline.execute(initial_data)

    async def execute_parallel(
        self, pipeline_names: list[str], initial_data: dict | None = None
    ) -> dict[str, PipelineContext]:
        """并行执行多个管道"""
        tasks = []
        for name in pipeline_names:
            tasks.append(self.execute(name, initial_data))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = {}
        for name, result in zip(pipeline_names, results):
            if isinstance(result, Exception):
                ctx = PipelineContext()
                ctx.set_error(name, str(result))
                output[name] = ctx
            else:
                output[name] = result

        return output


# ========== 便捷函数 ==========

def create_pipeline(
    name: str,
    stages: list[dict[str, Any]],
    executor: Callable | None = None
) -> Pipeline:
    """创建管道的便捷函数

    Args:
        name: 管道名称
        stages: Stage 配置列表
            [
                {"name": "stage1", "depends_on": []},
                {"name": "stage2", "depends_on": ["stage1"]}
            ]
        executor: 自定义执行函数

    Returns:
        Pipeline 实例
    """

    class SimplePipeline(Pipeline):
        def _build(self):
            for s in stages:
                stage = Stage(
                    name=s["name"],
                    description=s.get("description", ""),
                    depends_on=s.get("depends_on", [])
                )
                self.add_stage(stage)

        async def execute_stage(self, stage: Stage, context: PipelineContext) -> Any:
            if executor:
                return await executor(stage, context)
            return f"Executed: {stage.name}"

    return SimplePipeline(name)


# ========== 示例 ==========

class ExamplePipeline(Pipeline):
    """示例管道：代码开发流程"""

    def _build(self):
        # 添加 Stages
        self.add_stage(Stage(
            name="analyze",
            description="分析需求",
            depends_on=[]
        ))
        self.add_stage(Stage(
            name="design",
            description="设计架构",
            depends_on=["analyze"]
        ))
        self.add_stage(Stage(
            name="implement",
            description="实现代码",
            depends_on=["design"]
        ))
        self.add_stage(Stage(
            name="test",
            description="编写测试",
            depends_on=["implement"]
        ))
        self.add_stage(Stage(
            name="deploy",
            description="部署发布",
            depends_on=["test"]
        ))

    async def execute_stage(self, stage: Stage, context: PipelineContext) -> Any:
        # 获取依赖结果
        if stage.depends_on:
            dep_result = context.get_result(stage.depends_on[0])
            print(f"[{stage.name}] Based on: {dep_result}")

        # 执行逻辑
        result = f"Completed: {stage.name}"
        print(f"[{stage.name}] {result}")
        return result
