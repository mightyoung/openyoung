"""
SequentialFlow - 串行执行工作流
"""

from .base import FlowSkill


class SequentialFlow(FlowSkill):
    """串行执行 Flow - 按步骤顺序执行任务"""

    def __init__(self, steps: list[dict] | None = None):
        self._steps = steps or []

    @property
    def name(self) -> str:
        return "sequential"

    @property
    def description(self) -> str:
        return "串行执行多个步骤"

    @property
    def trigger_patterns(self) -> list[str]:
        return ["依次", "逐步", "顺序", "step by step"]

    async def pre_process(self, user_input: str, context: dict) -> str:
        steps = self._steps if self._steps else self._decompose(user_input)
        context["_flow_steps"] = steps
        context["_current_step"] = 0
        context["_step_count"] = len(steps)
        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        current = context.get("_current_step", 0)
        total = context.get("_step_count", 1)

        if current < total - 1:
            context["_current_step"] = current + 1
            next_step = context["_flow_steps"][current + 1]
            return f"Step {current + 1}/{total} done: {agent_output}\n\nNext: {next_step}"

        return f"All {total} steps completed: {agent_output}"

    async def should_delegate(self, task: str, context: dict) -> bool:
        return len(context.get("_flow_steps", [])) > 1

    async def get_subagent_type(self, task: str) -> str | None:
        if "search" in task or "find" in task:
            return "search"
        elif "build" in task or "create" in task:
            return "builder"
        return "general"
