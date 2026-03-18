"""
ParallelFlow - 并行执行工作流
"""

from .base import FlowSkill


class ParallelFlow(FlowSkill):
    """并行执行 Flow - 同时执行多个子任务"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent

    @property
    def name(self) -> str:
        return "parallel"

    @property
    def description(self) -> str:
        return "并行执行多个子任务"

    @property
    def trigger_patterns(self) -> list[str]:
        return ["并行", "同时", "同时执行", "concurrent"]

    async def pre_process(self, user_input: str, context: dict) -> str:
        """识别可并行的子任务"""
        tasks = self._identify_parallel_tasks(user_input)
        context["_parallel_tasks"] = tasks
        context["_completed_tasks"] = []
        context["_task_count"] = len(tasks)
        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        """检查并行任务完成情况"""
        completed = context.get("_completed_tasks", [])
        total = context.get("_task_count", 1)

        completed.append(agent_output)
        context["_completed_tasks"] = completed

        if len(completed) < total:
            remaining = total - len(completed)
            return f"Completed {len(completed)}/{total}. Still {remaining} tasks running..."

        # 汇总所有结果
        results = "\n".join([f"Task {i + 1}: {r}" for i, r in enumerate(completed)])
        return f"All {total} parallel tasks completed:\n{results}"

    def _identify_parallel_tasks(self, user_input: str) -> list[str]:
        """识别可并行的子任务"""
        # 按关键词分割
        separators = ["and", "同时", "并且", "and also", "parallel"]
        tasks = [user_input]

        for sep in separators:
            if sep in user_input:
                tasks = user_input.split(sep)
                break

        return [t.strip() for t in tasks if t.strip()]
        """识别可并行的子任务"""
        # 按关键词分割
        separators = ["同时", "并且", "and also", "parallel"]
        tasks = [user_input]

        for sep in separators:
            if sep in user_input:
                tasks = user_input.split(sep)
                break

        return [t.strip() for t in tasks if t.strip()]

    async def should_delegate(self, task: str, context: dict) -> bool:
        """多个任务时委托"""
        return len(context.get("_parallel_tasks", [])) > 1

    async def get_subagent_type(self, task: str) -> str | None:
        if "search" in task or "find" in task:
            return "search"
        return "general"
