"""
MCP Server - STDIO MCP 服务器

提供基于 STDIO 的 MCP 服务器实现，使用 asyncio 和 JSON-RPC 2.0
"""

import asyncio
import logging
import sys
from typing import Any, Optional

from .protocol import JSONRPCProtocol, JSONRPCRequest, JSONRPCResponse, JSONRPCErrorCode
from .tools import MCPToolRegistry, MCPTool

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP 服务器 (STDIO 传输)"""

    def __init__(
        self,
        name: str = "openyoung-mcp",
        version: str = "1.0.0",
        tool_registry: Optional[MCPToolRegistry] = None,
    ):
        self.name = name
        self.version = version
        self.protocol = JSONRPCProtocol()
        self.registry = tool_registry or MCPToolRegistry(name)
        self._running = False

    async def initialize(self):
        """初始化服务器"""
        # 注册 MCP 协议方法
        self.protocol.register_handler("initialize", self._handle_initialize)
        self.protocol.register_handler("initialized", self._handle_initialized)
        self.protocol.register_handler("tools/list", self._handle_tools_list)
        self.protocol.register_handler("tools/call", self._handle_tools_call)

        # 注册自定义工具
        await self._register_builtin_tools()

        logger.info(f"{self.name} v{self.version} initialized")

    async def _register_builtin_tools(self):
        """注册内置工具"""
        # 注册 ping 工具
        @self.registry.register(
            name="ping",
            description="Ping the server",
            input_schema={"type": "object", "properties": {}},
        )
        def ping() -> str:
            return "pong"

        # 注册 echo 工具
        @self.registry.register(
            name="echo",
            description="Echo back the input",
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        )
        def echo(message: str) -> str:
            return message

    async def register_subagent(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        subagent_runner: Any,
    ):
        """注册 SubAgent 作为 MCP 工具

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入 schema (MCP 协议格式)
            subagent_runner: SubAgent 运行器 (具有 run(task, context) 方法)
        """
        from src.core.types import Task
        from src.core.types.agent import TaskStatus

        async def subagent_handler(**params) -> str:
            """SubAgent 工具处理器

            将 MCP 工具调用转换为 SubAgent.run() 调用
            """
            # 从参数构建 Task
            task_input = params.get("task", params.get("input", ""))
            task_id = params.get("id", f"mcp-{name}-{hash(str(params))}")

            # Task 需要 description 字段
            task_description = params.get("description", f"MCP task for {name}")
            task = Task(
                id=task_id,
                description=task_description,
                input=task_input,
            )

            # 构建上下文
            context = {
                "parent_summary": params.get("summary", ""),
                "relevant_files": params.get("files", []),
            }

            # 调用 SubAgent.run()
            try:
                result = await subagent_runner.run(task, context)
                return result if isinstance(result, str) else str(result)
            except Exception as e:
                logger.exception(f"SubAgent {name} execution error")
                return f"[Error] SubAgent {name} failed: {str(e)}"

        # 创建并注册工具
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=subagent_handler,
        )
        self.registry.register_tool(tool)
        logger.info(f"Registered SubAgent tool: {name}")

    async def register_subagents_from_registry(
        self,
        subagent_registry: Any,
        subagent_runner_factory: Any = None,
    ):
        """从 SubAgentRegistry 注册所有 SubAgent

        Args:
            subagent_registry: SubAgentRegistry 实例
            subagent_runner_factory: SubAgent 运行器工厂函数 (接收 SubAgentBinding, 返回 SubAgent 实例)
        """
        # 动态导入避免循环依赖
        from src.agents.sub_agent import SubAgent
        from src.core.types.agent import SubAgentType

        subagents = subagent_registry.list_subagents()
        for subagent_config in subagents:
            if subagent_config.get("hidden"):
                continue

            name = subagent_config["name"]
            description = subagent_config.get("description", f"{name} SubAgent")
            subagent_type_str = subagent_config.get("type", "general")

            # 转换 string type 到 SubAgentType enum
            try:
                subagent_type = SubAgentType(subagent_type_str)
            except ValueError:
                subagent_type = SubAgentType.GENERAL

            # 构建输入 schema
            input_schema = {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task input for the subagent",
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "summary": {
                        "type": "string",
                        "description": "Parent task summary context",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Relevant files for context",
                    },
                },
                "required": ["task"],
            }

            # 创建运行器
            if subagent_runner_factory:
                runner = subagent_runner_factory(subagent_config)
            else:
                # 默认使用 SubAgent 类
                from src.core.types.agent import SubAgentConfig

                config = SubAgentConfig(
                    name=name,
                    type=subagent_type,
                    description=description,
                    instructions=subagent_config.get("instructions", ""),
                    model=subagent_config.get("model", "deepseek-chat"),
                    temperature=subagent_config.get("temperature", 0.7),
                )
                runner = SubAgent(config)

            await self.register_subagent(name, description, input_schema, runner)
            logger.info(f"Registered SubAgent from registry: {name}")

    async def _handle_initialize(self, **params) -> dict[str, Any]:
        """处理 initialize 请求"""
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
            },
        }

    async def _handle_initialized(self, **params):
        """处理 initialized 通知"""
        logger.info("Client initialized")
        return None

    async def _handle_tools_list(self, **params) -> dict[str, Any]:
        """处理 tools/list 请求"""
        return {
            "tools": self.registry.list_tools(),
        }

    async def _handle_tools_call(self, name: str, arguments: dict, **params) -> dict[str, Any]:
        """处理 tools/call 请求"""
        try:
            result = await self.registry.execute_tool(name, arguments or {})
            return {"content": [{"type": "text", "text": str(result)}]}
        except ValueError as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
        except Exception as e:
            logger.exception(f"Tool execution error: {name}")
            return {"content": [{"type": "text", "text": str(e)}], "isError": True}

    async def handle_message(self, raw_message: str) -> Optional[str]:
        """处理单条消息"""
        message = self.protocol.parse_message(raw_message)

        # 解析错误
        if isinstance(message, JSONRPCResponse) and message.error:
            logger.error(f"Parse error: {message.error.message}")
            return self.protocol.serialize_error(message.error)

        # 处理请求
        if message.request:
            response = await self.protocol.handle_request(message.request)

            # 通知消息不需要响应
            if message.is_notification:
                return None

            return self.protocol.serialize_response(response)

        # 批量消息简化为单个响应
        if isinstance(message, JSONRPCResponse):
            return self.protocol.serialize_response(message)

        return None

    async def read_stdio(self, reader: asyncio.StreamReader) -> str:
        """从 STDIN 读取消息"""
        line = await reader.readline()
        if not line:
            return ""
        return line.decode("utf-8").strip()

    async def write_stdio(self, message: str):
        """写入 STDOUT"""
        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    async def run(self):
        """运行服务器 (STDIO 模式)"""
        await self.initialize()
        self._running = True

        loop = asyncio.get_event_loop()
        logger.info(f"{self.name} running on STDIO")

        while self._running:
            try:
                # 使用 run_in_executor 每次读取新行
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                raw_message = line.strip()
                if not raw_message:
                    continue

                # 处理消息
                response = await self.handle_message(raw_message)
                if response:
                    await self.write_stdio(response)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.exception(f"Server error: {e}")
                error_response = JSONRPCResponse.error(
                    id=None,
                    code=JSONRPCErrorCode.INTERNAL_ERROR,
                    message=str(e),
                )
                await self.write_stdio(self.protocol.serialize_response(error_response))

    def stop(self):
        """停止服务器"""
        self._running = False
        logger.info("Server stopped")


async def run_server(
    name: str = "openyoung-mcp",
    version: str = "1.0.0",
    tool_registry: Optional[MCPToolRegistry] = None,
):
    """运行 MCP 服务器

    Args:
        name: 服务器名称
        version: 服务器版本
        tool_registry: 工具注册表 (可选)
    """
    server = MCPServer(name=name, version=version, tool_registry=tool_registry)
    await server.run()


def main():
    """入口点"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
