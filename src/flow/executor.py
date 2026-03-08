"""
Flow Executor - 流程编排执行器
支持 sequential、parallel、loop 三种模式
"""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class FlowType(Enum):
    """Flow 类型"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    LOOP = "loop"  # 循环执行
    CONDITIONAL = "conditional"  # 条件执行


@dataclass
class FlowStep:
    """Flow 步骤"""

    name: str
    task: str
    handler: Callable | None = None


class FlowExecutor:
    """Flow 执行器 - 简单的流程编排"""

    def __init__(self):
        self.flows: dict[str, list[FlowStep]] = {}

    def register_flow(self, name: str, steps: list[FlowStep]):
        """注册一个 flow"""
        self.flows[name] = steps

    async def execute_sequential(self, steps: list[FlowStep], context: dict) -> list[Any]:
        """顺序执行"""
        results = []
        for step in steps:
            if step.handler:
                result = await step.handler(step.task, context)
            else:
                result = f"[Sequential] {step.name}: {step.task}"
            results.append(result)
        return results

    async def execute_parallel(self, steps: list[FlowStep], context: dict) -> list[Any]:
        """并行执行"""
        tasks = []
        for step in steps:
            if step.handler:
                task = step.handler(step.task, context)
            else:
                task = asyncio.coroutine(lambda s=step: f"[Parallel] {s.name}: {s.task}")()
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def execute_loop(
        self, steps: list[FlowStep], context: dict, max_iterations: int = 3
    ) -> list[Any]:
        """循环执行"""
        results = []
        for i in range(max_iterations):
            context["iteration"] = i + 1
            iteration_results = await self.execute_sequential(steps, context)
            results.extend(iteration_results)
        return results

    async def execute(
        self, flow_name: str, flow_type: FlowType, context: dict | None = None
    ) -> Any:
        """执行 flow"""
        if flow_name not in self.flows:
            return {"error": f"Flow not found: {flow_name}"}

        steps = self.flows[flow_name]
        context = context or {}

        if flow_type == FlowType.SEQUENTIAL:
            return await self.execute_sequential(steps, context)
        elif flow_type == FlowType.PARALLEL:
            return await self.execute_parallel(steps, context)
        elif flow_type == FlowType.LOOP:
            return await self.execute_loop(steps, context)
        else:
            return {"error": f"Unknown flow type: {flow_type}"}


# 内置 Flows
def get_builtin_flows() -> dict[str, list[FlowStep]]:
    """获取内置 Flows"""
    return {
        "code-review": [
            FlowStep(name="read-code", task="读取代码"),
            FlowStep(name="analyze", task="分析代码质量"),
            FlowStep(name="report", task="生成审查报告"),
        ],
        "test-generate": [
            FlowStep(name="analyze", task="分析代码结构"),
            FlowStep(name="generate", task="生成测试用例"),
            FlowStep(name="validate", task="验证测试用例"),
        ],
    }
