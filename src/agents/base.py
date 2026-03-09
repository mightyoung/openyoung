"""
Base Agent - Agent 抽象基类

基于 Andrej Karpathy 的 "LLM as OS" 理念:
- Agent 只需要: Memory(记忆), Tools(工具), Loop(循环)

参考 Anthropic 的 Agent 架构模式:
- plan(): 任务规划
- execute(): 执行动作
- reflect(): 结果反思
- learn(): 经验学习
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AgentState(Enum):
    """Agent 状态"""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str
    model: str = "claude-3-5-sonnet-20241022"
    max_iterations: int = 100
    timeout_seconds: int = 300
    temperature: float = 0.7
    tools: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentContext:
    """Agent 运行时上下文"""

    task: str = ""
    state: AgentState = AgentState.IDLE
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    tools_used: list = field(default_factory=list)
    iterations: int = 0
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        """计算执行时长(毫秒)"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0


@dataclass
class AgentResult:
    """Agent 执行结果"""

    success: bool
    output: str
    state: AgentState
    duration_ms: int = 0
    iterations: int = 0
    tools_used: list = field(default_factory=list)
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent 抽象基类

    定义 Agent 的核心接口:
    - plan(): 制定执行计划
    - execute(): 执行计划
    - reflect(): 反思执行结果
    - learn(): 从经验中学习

    设计原则 (来自顶级专家):
    - 单一职责: Agent 只做"理解-执行-反思"循环
    - 依赖注入: 工具和内存通过构造器注入
    - 可组合性: 通过组合而非继承实现扩展
    """

    def __init__(self, config: AgentConfig):
        """初始化 Agent

        Args:
            config: Agent 配置
        """
        self.config = config
        self.context = AgentContext()
        self._llm_client = None
        self._tools: dict[str, Any] = {}
        self._memory: dict[str, Any] = {}
        self._hooks: list = []

    @property
    def name(self) -> str:
        """Agent 名称"""
        return self.config.name

    @property
    def state(self) -> AgentState:
        """当前状态"""
        return self.context.state

    # === 核心抽象方法 ===

    @abstractmethod
    async def plan(self, task: str) -> list[str]:
        """制定执行计划

        Args:
            task: 任务描述

        Returns:
            执行计划步骤列表
        """
        pass

    @abstractmethod
    async def execute(self, plan: list[str]) -> str:
        """执行计划

        Args:
            plan: 执行计划步骤列表

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def reflect(self, result: str) -> dict[str, Any]:
        """反思执行结果

        Args:
            result: 执行结果

        Returns:
            反思反馈字典，包含:
            - score: 质量分数 (0-1)
            - should_learn: 是否应该学习
            - feedback: 反馈信息
        """
        pass

    async def learn(self, experience: dict[str, Any]) -> None:
        """从经验中学习

        默认实现为空，子类可以重写。

        Args:
            experience: 经验字典，包含 task, result, feedback
        """
        pass

    # === 主循环 ===

    async def run(self, task: str) -> AgentResult:
        """主循环: plan → execute → reflect → learn

        Args:
            task: 任务描述

        Returns:
            AgentResult: 执行结果
        """
        self.context = AgentContext(task=task, start_time=datetime.now())
        self.context.state = AgentState.PLANNING

        try:
            # 1. 规划
            plan = await self.plan(task)
            self.context.iterations += 1

            # 2. 执行
            self.context.state = AgentState.EXECUTING
            output = await self.execute(plan)

            # 3. 反思
            self.context.state = AgentState.REFLECTING
            feedback = await self.reflect(output)

            # 4. 学习
            if feedback.get("should_learn", False):
                self.context.state = AgentState.LEARNING
                await self.learn({"task": task, "result": output, "feedback": feedback})

            self.context.state = AgentState.FINISHED
            self.context.end_time = datetime.now()

            return AgentResult(
                success=True,
                output=output,
                state=self.context.state,
                duration_ms=self.context.duration_ms,
                iterations=self.context.iterations,
                tools_used=self.context.tools_used.copy(),
                metadata=feedback,
            )

        except Exception as e:
            self.context.state = AgentState.ERROR
            self.context.error = str(e)
            self.context.end_time = datetime.now()

            return AgentResult(
                success=False,
                output="",
                state=self.context.state,
                duration_ms=self.context.duration_ms,
                iterations=self.context.iterations,
                error=str(e),
            )

    # === 工具管理 ===

    def register_tool(self, name: str, func: Any) -> None:
        """注册工具

        Args:
            name: 工具名称
            func: 工具函数
        """
        self._tools[name] = func

    def unregister_tool(self, name: str) -> None:
        """注销工具

        Args:
            name: 工具名称
        """
        self._tools.pop(name, None)

    async def call_tool(self, name: str, **kwargs: Any) -> Any:
        """调用工具

        Args:
            name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        self.context.tools_used.append(name)
        func = self._tools[name]

        # 支持异步和同步函数
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        else:
            return func(**kwargs)

    def has_tool(self, name: str) -> bool:
        """检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            是否存在
        """
        return name in self._tools

    def list_tools(self) -> list[str]:
        """列出所有工具

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    # === 记忆管理 ===

    def remember(self, key: str, value: Any) -> None:
        """存储记忆

        Args:
            key: 记忆键
            value: 记忆值
        """
        self._memory[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        """回忆记忆

        Args:
            key: 记忆键
            default: 默认值

        Returns:
            记忆值
        """
        return self._memory.get(key, default)

    def forget(self, key: str) -> None:
        """遗忘记忆

        Args:
            key: 记忆键
        """
        self._memory.pop(key, None)

    def clear_memory(self) -> None:
        """清空记忆"""
        self._memory.clear()

    def has_memory(self, key: str) -> bool:
        """检查记忆是否存在

        Args:
            key: 记忆键

        Returns:
            是否存在
        """
        return key in self._memory

    # === Hooks ===

    def register_hook(self, hook: Any) -> None:
        """注册 Hook

        Args:
            hook: Hook 函数
        """
        self._hooks.append(hook)

    def trigger_hooks(self, event: str, context: dict[str, Any]) -> list:
        """触发 Hooks

        Args:
            event: 事件名称
            context: 上下文

        Returns:
            Hook 执行结果列表
        """
        results = []
        for hook in self._hooks:
            try:
                result = hook(event, context)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results

    # === 状态管理 ===

    def reset(self) -> None:
        """重置 Agent 状态"""
        self.context = AgentContext()
        self._hooks.clear()

    def get_status(self) -> dict[str, Any]:
        """获取 Agent 状态

        Returns:
            状态字典
        """
        return {
            "name": self.name,
            "state": self.context.state.value,
            "task": self.context.task,
            "iterations": self.context.iterations,
            "tools_used": len(self.context.tools_used),
            "memory_keys": list(self._memory.keys()),
            "tools": list(self._tools.keys()),
        }

    # === LLM 客户端 ===

    def set_llm_client(self, client: Any) -> None:
        """设置 LLM 客户端

        Args:
            client: LLM 客户端
        """
        self._llm_client = client

    def get_llm_client(self) -> Any:
        """获取 LLM 客户端

        Returns:
            LLM 客户端
        """
        return self._llm_client


class SimpleAgent(BaseAgent):
    """简单 Agent 实现

    提供基于 LLM 的默认实现:
    - plan(): 使用 LLM 分解任务
    - execute(): 顺序执行步骤
    - reflect(): 评估结果质量
    """

    async def plan(self, task: str) -> list[str]:
        """使用 LLM 分解任务

        Args:
            task: 任务描述

        Returns:
            步骤列表
        """
        if not self._llm_client:
            # 无 LLM 客户端时，返回简单一步
            return [task]

        prompt = f"""分解以下任务为具体步骤，每行一个步骤:
{task}

请只输出步骤列表，每行一个步骤，不要有其他内容。"""

        response = await self._llm_client.chat([{"role": "user", "content": prompt}])

        content = response.content if hasattr(response, "content") else str(response)
        steps = [s.strip() for s in content.split("\n") if s.strip()]
        return steps if steps else [task]

    async def execute(self, plan: list[str]) -> str:
        """顺序执行步骤

        Args:
            plan: 步骤列表

        Returns:
            执行结果
        """
        results = []
        for i, step in enumerate(plan):
            self.context.iterations += 1
            result = await self._execute_step(step)
            results.append(f"Step {i + 1}: {result}")

        return "\n\n".join(results)

    async def _execute_step(self, step: str) -> str:
        """执行单个步骤

        Args:
            step: 步骤描述

        Returns:
            步骤结果
        """
        # 子类可以重写此方法实现自定义执行
        if not self._llm_client:
            return f"Executed: {step}"

        response = await self._llm_client.chat([{"role": "user", "content": step}])

        return response.content if hasattr(response, "content") else str(response)

    async def reflect(self, result: str) -> dict[str, Any]:
        """评估结果质量

        Args:
            result: 执行结果

        Returns:
            反馈字典
        """
        # 默认实现：基于结果是否为空判断
        success = bool(result and len(result.strip()) > 0)

        return {
            "score": 1.0 if success else 0.0,
            "should_learn": not success,
            "feedback": "Task completed" if success else "Task failed",
        }
