"""
LoopFlow - 循环执行工作流
"""

from collections.abc import Callable

from .base import FlowSkill


class LoopFlow(FlowSkill):
    """循环执行 Flow - 循环执行直到满足条件"""

    def __init__(
        self,
        max_iterations: int = 10,
        stop_condition: Callable[[str, dict], bool] | None = None,
    ):
        """
        Args:
            max_iterations: 最大迭代次数
            stop_condition: 停止条件函数
        """
        self.max_iterations = max_iterations
        self.stop_condition = stop_condition or (lambda output, ctx: False)

    @property
    def name(self) -> str:
        return "loop"

    @property
    def description(self) -> str:
        return "循环执行直到满足条件"

    @property
    def trigger_patterns(self) -> list[str]:
        return ["循环", "重复", "直到", "loop", "repeat", "until"]

    async def pre_process(self, user_input: str, context: dict) -> str:
        """初始化循环"""
        context["_loop_iteration"] = 0
        context["_loop_results"] = []
        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        """检查循环条件"""
        iteration = context.get("_loop_iteration", 0)
        results = context.get("_loop_results", [])

        results.append(agent_output)
        context["_loop_results"] = results

        # 检查停止条件
        if self.stop_condition(agent_output, context):
            return f"Loop stopped at iteration {iteration + 1}. Result: {agent_output}"

        # 检查最大迭代次数
        if iteration >= self.max_iterations - 1:
            return f"Max iterations ({self.max_iterations}) reached. Final result: {agent_output}"

        # 继续循环
        context["_loop_iteration"] = iteration + 1
        return (
            f"Iteration {iteration + 1}/{self.max_iterations}: {agent_output}\n\nContinuing loop..."
        )

    def set_stop_condition(self, condition: Callable[[str, dict], bool]):
        """设置停止条件"""
        self.stop_condition = condition

    async def should_delegate(self, task: str, context: dict) -> bool:
        """循环任务可能需要委托"""
        return True

    async def get_subagent_type(self, task: str) -> str | None:
        return "general"
