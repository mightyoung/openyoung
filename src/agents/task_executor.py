"""
TaskExecutor - 任务执行器

封装 YoungAgent 的任务执行逻辑：
- LLM 调用循环
- 工具执行循环
- FlowSkill 智能路由
- SubAgent 委托

集成统一异常处理:
- 异常转换
- 上下文增强
- 错误日志
"""

import json

from src.core.exception_handler import (
    AgentExecutionError,
    ExceptionContext,
    ToolExecutionError,
    get_exception_handler,
    handle_exceptions,
)
from src.core.types import Task


class TaskExecutor:
    """任务执行器 - 负责执行任务的核心逻辑

    集成统一异常处理:
    - ToolExecutionError: 工具执行失败
    - AgentExecutionError: Agent 执行失败
    """

    def __init__(
        self,
        tool_executor,
        config,
        flow_skill=None,
        dispatcher=None,
        max_tool_calls: int = 10,
    ):
        self._tool_executor = tool_executor
        self._config = config
        self._flow_skill = flow_skill
        self._dispatcher = dispatcher
        self._max_tool_calls = max_tool_calls
        self._history: list = []
        # 初始化异常处理器
        self._exception_handler = get_exception_handler()

    @handle_exceptions(reraise=False, default="")
    async def execute(self, task: Task) -> str:
        """执行任务 - 支持 SubAgent 委托

        Args:
            task: 要执行的任务

        Returns:
            执行结果字符串
        """
        try:
            # ========== FlowSkill 智能路由 ==========
            if self._flow_skill:
                try:
                    should_delegate = await self._flow_skill.should_delegate(
                        task.description, {}
                    )
                    if should_delegate:
                        subagent_type = await self._flow_skill.get_subagent_type(
                            task.description
                        )
                        if subagent_type and subagent_type != "general":
                            print(f"[FlowSkill] Delegating to subagent: {subagent_type}")
                            task.subagent_type = subagent_type
                            return await self._delegate_to_subagent(task)
                except Exception as e:
                    # 使用异常处理器
                    context = ExceptionContext(
                        function="execute",
                        additional_data={"task": task.description[:50]},
                    )
                    self._exception_handler.handle_exception(e, context, reraise=False)
                    print(f"[FlowSkill] Smart routing error: {e}")

            # 如果是 SubAgent 调用，委托给对应 SubAgent
            if task.subagent_type:
                return await self._delegate_to_subagent(task)

            # 执行任务
            return await self._execute_task(task)
        except Exception as e:
            print(f"[ERROR] TaskExecutor.execute failed: {type(e).__name__}: {e}")
            return f"Error: {type(e).__name__}: {e}"

    async def _delegate_to_subagent(self, task: Task) -> str:
        """委托给 SubAgent"""
        if not self._dispatcher:
            return "SubAgent dispatcher not configured"

        from src.agents.dispatcher import TaskDispatchParams

        params = TaskDispatchParams(
            description=task.description[:50],
            prompt=task.description,
            sub_agent_type=task.subagent_type,
        )
        result = await self._dispatcher.dispatch(params, {})
        return result.get("output", "")

    @handle_exceptions(reraise=False, default="Error: Task execution failed")
    async def _execute_task(self, task: Task) -> str:
        """执行任务核心逻辑

        Args:
            task: 要执行的任务

        Returns:
            执行结果字符串
        """
        messages = []
        system_prompt = (
            self._config.system_prompt
            or """你是一个有帮助的AI助手。你可以通过执行代码来完成任务。可用工具：bash, write, edit, read, glob, grep"""
        )
        messages.append({"role": "system", "content": system_prompt})
        for msg in self._history[-10:]:
            messages.append({"role": msg.role.value, "content": msg.content})
        messages.append({"role": "user", "content": task.description})
        tools = self._tool_executor.get_tool_schemas()

        try:
            from src.llm.client_adapter import LLMClient

            client = LLMClient()
            for i in range(self._max_tool_calls):
                response = await client.chat(
                    model=self._config.model,
                    messages=messages,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                    tools=tools,
                )
                message = response["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    await client.close()
                    return content
                for tool_call in tool_calls:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    arguments = json.loads(func["arguments"])
                    print(f"\n[执行工具] {tool_name}: {arguments}")

                    # 工具执行 - 使用异常处理
                    try:
                        result = await self._tool_executor.execute(tool_name, arguments)
                    except Exception as e:
                        # 转换为统一异常
                        context = ExceptionContext(
                            function="_execute_task",
                            additional_data={"tool_name": tool_name},
                        )
                        converted = self._exception_handler.handle_exception(
                            e, context, reraise=False
                        )
                        result = type('obj', (object,), {
                            'success': False,
                            'error': str(converted)
                        })()

                    messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call],
                        }
                    )
                    tool_result = (
                        result.result if result.success else f"错误: {result.error}"
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"call_{i}"),
                            "content": tool_result,
                        }
                    )
                    print(f"[工具结果] {tool_result[:200]}...")
            await client.close()
            return "已达到最大工具调用次数"
        except Exception as e:
            # 统一异常处理
            print(f"[ERROR] _execute_task failed: {type(e).__name__}: {e}")
            context = ExceptionContext(
                function="_execute_task",
                additional_data={"task": task.description[:50]},
            )
            converted = self._exception_handler.handle_exception(
                e, context, reraise=False
            )
            return f"Error: {type(e).__name__}: {converted}"

    def set_history(self, history: list):
        """设置历史消息"""
        self._history = history

    def update_flow_skill(self, flow_skill):
        """更新 FlowSkill"""
        self._flow_skill = flow_skill
