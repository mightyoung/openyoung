"""
CompositeFlowSkill - 组合多个 FlowSkill
支持链式组合、并行组合、条件组合
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from src.flow.base import FlowSkill


class CompositionType(Enum):
    """组合类型"""

    CHAIN = "chain"  # 链式：顺序执行
    PARALLEL = "parallel"  # 并行：同时执行
    CONDITIONAL = "conditional"  # 条件：根据条件选择


@dataclass
class CompositeConfig:
    """组合配置"""

    composition_type: CompositionType = CompositionType.CHAIN
    fallbacks: list[FlowSkill] = field(default_factory=list)  # 备用 Skill


class CompositeFlowSkill(FlowSkill):
    """组合 FlowSkill

    将多个 FlowSkill 组合在一起，支持：
    - 链式组合：顺序执行多个 Skill
    - 并行组合：同时执行多个 Skill
    - 条件组合：根据条件选择 Skill
    """

    def __init__(
        self,
        name: str,
        description: str,
        skills: list[FlowSkill],
        config: CompositeConfig | None = None,
    ):
        self._name = name
        self._description = description
        self.skills = skills
        self.config = config or CompositeConfig()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def trigger_patterns(self) -> list[str]:
        """合并所有 Skill 的触发模式"""
        patterns = []
        for skill in self.skills:
            patterns.extend(skill.trigger_patterns)
        return patterns

    async def pre_process(self, user_input: str, context: dict) -> str:
        """链式前处理：依次执行每个 Skill 的前处理"""
        result = user_input
        for skill in self.skills:
            result = await skill.pre_process(result, context)
        return result

    async def post_process(self, agent_output: str, context: dict) -> str:
        """链式后处理：依次执行每个 Skill 的后处理"""
        result = agent_output
        for skill in self.skills:
            result = await skill.post_process(result, context)
        return result

    async def should_delegate(self, task: str, context: dict) -> bool:
        """检查是否有 Skill 委托"""
        for skill in self.skills:
            if await skill.should_delegate(task, context):
                return True
        return False

    async def get_subagent_type(self, task: str) -> str | None:
        """获取第一个支持委托的 Skill 的类型"""
        for skill in self.skills:
            subagent_type = await skill.get_subagent_type(task)
            if subagent_type:
                return subagent_type
        return None


class ChainFlowSkill(CompositeFlowSkill):
    """链式组合 Skill

    多个 Skill 依次执行，前一个的输出作为后一个的输入
    """

    def __init__(self, skills: list[FlowSkill], name: str = "chain"):
        super().__init__(
            name=name,
            description="Chain composition of skills",
            skills=skills,
            config=CompositeConfig(composition_type=CompositionType.CHAIN),
        )


class ParallelFlowSkill(CompositeFlowSkill):
    """并行组合 Skill

    多个 Skill 同时执行，结果合并
    """

    def __init__(self, skills: list[FlowSkill], name: str = "parallel"):
        super().__init__(
            name=name,
            description="Parallel composition of skills",
            skills=skills,
            config=CompositeConfig(composition_type=CompositionType.PARALLEL),
        )

    @property
    def parallel_stages(self) -> list[str]:
        """所有 Skill 都可并行"""
        return [s.name for s in self.skills]

    async def pre_process(self, user_input: str, context: dict) -> str:
        """并行前处理：所有 Skill 预处理同一输入"""
        # 并行执行所有预处理
        import asyncio

        tasks = [skill.pre_process(user_input, context) for skill in self.skills]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        combined = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                combined.append(f"[Error] {self.skills[i].name}: {result}")
            else:
                combined.append(str(result))

        return "\n---\n".join(combined)

    async def post_process(self, agent_output: str, context: dict) -> str:
        """并行后处理：所有 Skill 后处理同一输出"""
        import asyncio

        tasks = [skill.post_process(agent_output, context) for skill in self.skills]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 合并结果
        combined = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                combined.append(f"[Error] {self.skills[i].name}: {result}")
            else:
                combined.append(str(result))

        return "\n---\n".join(combined)


class ConditionalFlowSkill(CompositeFlowSkill):
    """条件组合 Skill

    根据条件选择执行哪个 Skill
    """

    def __init__(
        self,
        skills: list[FlowSkill],
        condition_fn: Callable[[str, dict], int],
        name: str = "conditional",
    ):
        super().__init__(
            name=name,
            description="Conditional composition of skills",
            skills=skills,
            config=CompositeConfig(composition_type=CompositionType.CONDITIONAL),
        )
        self.condition_fn = condition_fn

    async def pre_process(self, user_input: str, context: dict) -> str:
        """条件前处理：根据条件选择 Skill"""
        idx = self.condition_fn(user_input, context)
        if 0 <= idx < len(self.skills):
            return await self.skills[idx].pre_process(user_input, context)
        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        """条件后处理"""
        idx = self.condition_fn(agent_output, context) if hasattr(self, "last_idx") else 0
        if 0 <= idx < len(self.skills):
            return await self.skills[idx].post_process(agent_output, context)
        return agent_output


# ========== 便捷函数 ==========


def compose_skills(*skills: FlowSkill) -> CompositeFlowSkill:
    """组合多个 Skill 为链式 Skill"""
    return ChainFlowSkill(list(skills))


def compose_parallel(*skills: FlowSkill) -> ParallelFlowSkill:
    """组合多个 Skill 为并行 Skill"""
    return ParallelFlowSkill(list(skills))


def compose_conditional(
    skills: list[FlowSkill], condition_fn: Callable[[str, dict], int]
) -> ConditionalFlowSkill:
    """组合多个 Skill 为条件 Skill"""
    return ConditionalFlowSkill(skills, condition_fn)
