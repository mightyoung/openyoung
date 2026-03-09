"""
SubAgent - 子 Agent 执行引擎

对标 Claude Code Task 协议
"""

import json

from src.core.types import SubAgentConfig, Task


class SubAgent:
    """真正的 SubAgent 执行引擎 - 对标 OpenCode/Claude Code

    支持：
    1. 独立 LLM 调用
    2. 工具执行
    3. 上下文隔离
    4. 会话管理
    """

    def __init__(self, config: SubAgentConfig, llm_client=None, tool_executor=None):
        self.config = config
        self.name = config.name
        self.type = config.type
        self.description = config.description
        self.instructions = config.instructions
        self.model = config.model or "deepseek-chat"
        self.temperature = config.temperature or 0.7
        self._llm = llm_client
        self._tool_executor = tool_executor
        self._history = []
        self._session_id = None

    async def run(self, task: Task, context: dict) -> str:
        """执行 SubAgent 任务

        对标 Claude Code Task 协议：
        1. 构建系统提示
        2. 构建消息历史
        3. 调用 LLM
        4. 执行工具
        5. 返回结果
        """
        self._session_id = task.id

        # 1. 构建系统提示
        system_prompt = self._build_system_prompt(task, context)

        # 2. 构建消息
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": task.input})

        # 3. 调用 LLM
        max_iterations = 5
        for iteration in range(max_iterations):
            # 调用 LLM
            response = await self._call_llm(messages)

            # 4. 解析工具调用
            tool_calls = self._parse_tool_calls(response)
            if not tool_calls:
                # 没有工具调用，返回结果
                return response

            # 5. 执行工具
            for tool_call in tool_calls:
                result = await self._execute_tool(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call.get("id", "unknown"),
                    }
                )

        # 达到最大迭代次数
        return f"[SubAgent {self.name}] Max iterations reached. Last response: {messages[-1].get('content', '')[:200]}"

    def _build_system_prompt(self, task: Task, context: dict) -> str:
        """构建系统提示"""
        base_prompt = (
            self.instructions
            or f"""你是一个 {self.type} 类型的 SubAgent。
你的职责是：{self.description}

可用工具：read, write, edit, glob, grep, bash"""
        )

        # 添加上下文信息
        if context.get("parent_summary"):
            base_prompt += f"\n\n父任务摘要：{context['parent_summary']}"

        if context.get("relevant_files"):
            base_prompt += f"\n相关文件：{', '.join(context['relevant_files'])}"

        return base_prompt

    async def _call_llm(self, messages: list) -> str:
        """调用 LLM"""
        if not self._llm:
            # 尝试创建新的 LLM 客户端
            try:
                from src.llm.client_adapter import LLMClient

                self._llm = LLMClient()
            except Exception as e:
                return f"[SubAgent {self.name}] LLM not available: {e}"

        try:
            # 调用 LLM（使用工具）
            tools = self._tool_executor.get_tool_schemas() if self._tool_executor else None
            response = await self._llm.chat(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=tools,
            )

            # 解析响应 - 兼容新旧格式
            message = response.get("choices", [{}])[0].get("message", {})
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])

            # 如果有工具调用，先执行工具再返回
            if tool_calls:
                for tool_call in tool_calls:
                    func = tool_call.get("function", {})
                    tool_name = func.get("name")
                    arguments = json.loads(func.get("arguments", "{}"))
                    print(f"\n[SubAgent {self.name}] Executing tool: {tool_name}")

                    if self._tool_executor:
                        result = await self._tool_executor.execute(tool_name, arguments)
                        tool_result = result.result if result.success else f"Error: {result.error}"
                        messages.append(
                            {
                                "role": "assistant",
                                "content": content,
                                "tool_calls": [tool_call],
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", "unknown"),
                                "content": tool_result,
                            }
                        )
                        print(f"[SubAgent {self.name}] Tool result: {tool_result[:100]}...")

                # 再次调用 LLM 处理工具结果
                return await self._call_llm(messages)

            return content
        except Exception as e:
            return f"[Error] LLM call failed: {str(e)}"

    def _parse_tool_calls(self, response: str) -> list:
        """解析工具调用 - 支持 JSON 和自然语言格式"""
        import json
        import re

        tool_calls = []

        # 尝试解析 JSON 格式的工具调用
        try:
            # 匹配 [TOOL_CALL] ... [/TOOL_CALL] 格式
            pattern = r"\[TOOL_CALL\](.*?)\[/TOOL_CALL\]"
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                try:
                    tool_call = json.loads(match.strip())
                    tool_calls.append(tool_call)
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        # 尝试解析自然语言格式 "我将使用 xxx 工具..."
        if not tool_calls:
            # 简单检测是否需要工具
            if "write" in response.lower() or "edit" in response.lower():
                pass  # 需要进一步解析

        return tool_calls

    async def _execute_tool(self, tool_call: dict) -> str:
        """执行工具调用"""
        if not self._tool_executor:
            return f"[SubAgent {self.name}] Tool executor not configured"

        try:
            tool_name = tool_call.get("name")
            arguments = tool_call.get("arguments", {})

            result = await self._tool_executor.execute(tool_name, arguments)

            if result.success:
                return result.result
            else:
                return f"Error: {result.error}"
        except Exception as e:
            return f"[SubAgent {self.name}] Tool execution error: {str(e)}"
