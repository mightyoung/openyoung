"""
MCP Server - STDIO MCP 服务器

提供基于 STDIO 的 MCP 服务器实现，使用 asyncio 和 JSON-RPC 2.0
"""

import asyncio
import logging
import sys
from typing import Any, Optional

from .protocol import JSONRPCProtocol, JSONRPCRequest, JSONRPCResponse, JSONRPCErrorCode
from .tools import MCPToolRegistry

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

        reader = asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

        logger.info(f"{self.name} running on STDIO")

        while self._running:
            try:
                # 异步读取
                line = await asyncio.wait_for(reader, timeout=1.0)
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
