"""
ConditionalFlow - 条件分支工作流
"""

from .base import FlowSkill


class ConditionalFlow(FlowSkill):
    """条件分支 Flow - 根据条件选择执行路径"""

    def __init__(
        self,
        conditions: dict[str, str] | None = None,
        default_branch: str = "default",
    ):
        """
        Args:
            conditions: 条件到分支的映射 {"条件": "分支名"}
            default_branch: 默认分支
        """
        self._conditions = conditions or {}
        self.default_branch = default_branch

    @property
    def name(self) -> str:
        return "conditional"

    @property
    def description(self) -> str:
        return "条件分支执行"

    @property
    def trigger_patterns(self) -> list[str]:
        return ["如果", "则", "否则", "if", "then", "else"]

    async def pre_process(self, user_input: str, context: dict) -> str:
        """解析条件并设置分支"""
        branch = self._evaluate_condition(user_input)
        context["_current_branch"] = branch
        context["_branch_results"] = {}
        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        """处理分支结果"""
        branch = context.get("_current_branch", self.default_branch)
        context["_branch_results"][branch] = agent_output

        return f"Branch '{branch}' result: {agent_output}"

    def _evaluate_condition(self, user_input: str) -> str:
        """评估条件并返回分支名"""
        user_lower = user_input.lower()

        for condition, branch in self._conditions.items():
            if condition.lower() in user_lower:
                return branch

        return self.default_branch

    def add_condition(self, condition: str, branch: str):
        """添加条件"""
        self._conditions[condition] = branch

    async def should_delegate(self, task: str, context: dict) -> bool:
        """有多个条件时可能需要委托"""
        return len(self._conditions) > 1

    async def get_subagent_type(self, task: str) -> str | None:
        if "search" in task or "find" in task:
            return "search"
        return "general"
