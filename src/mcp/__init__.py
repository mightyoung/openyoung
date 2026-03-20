"""
MCP Server - Model Context Protocol 服务器

提供 STDIO 传输的 MCP 服务器实现，支持 JSON-RPC 2.0 协议
"""

from .protocol import JSONRPCMessage, JSONRPCRequest, JSONRPCResponse, JSONRPCError
from .tools import MCPTool, MCPToolRegistry, mcp_tool
from .server import MCPServer, run_server

__all__ = [
    "JSONRPCMessage",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MCPTool",
    "MCPToolRegistry",
    "mcp_tool",
    "MCPServer",
    "run_server",
]
