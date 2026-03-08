"""
MCP Module Tests
"""

import pytest

from src.mcp import MCPClient, MCPConnectionStatus, MCPServer, MCPTool, MCPToolMapper


class TestMCPServer:
    """Test MCPServer"""

    def test_mcp_server_creation(self):
        """Test creating MCP server"""
        server = MCPServer("http://localhost:8080", "test_server")

        assert server.url == "http://localhost:8080"
        assert server.name == "test_server"

    def test_mcp_server_default_name(self):
        """Test MCP server default name"""
        server = MCPServer("http://localhost:8080")

        assert server.name == "http://localhost:8080"


class TestMCPClient:
    """Test MCPClient"""

    def test_client_initialization(self):
        """Test MCP client initialization"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        assert client.server is server
        assert client.status == MCPConnectionStatus.DISCONNECTED
        assert client._connected is False

    def test_connect(self):
        """Test connecting to MCP server"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        result = client.connect()

        assert result is True
        assert client.status == MCPConnectionStatus.CONNECTED
        assert client.is_connected() is True

    def test_disconnect(self):
        """Test disconnecting from MCP server"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        client.disconnect()

        assert client.status == MCPConnectionStatus.DISCONNECTED
        assert client.is_connected() is False

    def test_is_connected_after_init(self):
        """Test is_connected returns False initially"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        assert client.is_connected() is False

    def test_list_tools_empty(self):
        """Test listing tools when none registered"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        tools = client.list_tools()

        assert tools == []

    def test_register_tool(self):
        """Test registering a tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        tool = MCPTool(
            name="test_tool", description="A test tool", input_schema={"type": "object"}
        )
        client.register_tool(tool)

        tools = client.list_tools()

        assert len(tools) == 1
        assert tools[0].name == "test_tool"

    def test_call_tool_success(self):
        """Test calling a registered tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        tool = MCPTool(name="echo", description="Echo tool", input_schema={})
        client.register_tool(tool)

        result = client.call_tool("echo", {"message": "hello"})

        assert result is not None
        assert "result" in result

    def test_call_tool_not_connected(self):
        """Test calling tool without connection raises error"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        with pytest.raises(ConnectionError, match="Not connected"):
            client.call_tool("echo", {})

    def test_call_nonexistent_tool(self):
        """Test calling nonexistent tool raises error"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        with pytest.raises(ValueError, match="not found"):
            client.call_tool("nonexistent", {})

    def test_get_tool(self):
        """Test getting a specific tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        tool = MCPTool(name="getme", description="Get me", input_schema={})
        client.register_tool(tool)

        retrieved = client.get_tool("getme")

        assert retrieved is not None
        assert retrieved.name == "getme"

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool returns None"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)

        retrieved = client.get_tool("nonexistent")

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_call_tool_async(self):
        """Test async tool calling"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        tool = MCPTool(name="async_tool", description="Async", input_schema={})
        client.register_tool(tool)

        result = await client.call_tool_async("async_tool", {"data": "test"})

        assert result is not None


class TestMCPTool:
    """Test MCPTool"""

    def test_mcp_tool_creation(self):
        """Test creating MCP tool"""
        tool = MCPTool(
            name="my_tool",
            description="My tool description",
            input_schema={"type": "object", "properties": {"x": {"type": "string"}}},
        )

        assert tool.name == "my_tool"
        assert tool.description == "My tool description"
        assert tool.input_schema["type"] == "object"


class TestMCPToolMapper:
    """Test MCPToolMapper"""

    def test_mapper_initialization(self):
        """Test tool mapper initialization"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        assert mapper.client is client
        assert mapper._mappings == {}

    def test_map_tool(self):
        """Test mapping tool names"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        mapper.map_tool("local_name", "remote_name")

        assert mapper._mappings["local_name"] == "remote_name"

    def test_unmap_tool(self):
        """Test unmapping tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        mapper.map_tool("local", "remote")
        result = mapper.unmap_tool("local")

        assert result is True
        assert "local" not in mapper._mappings

    def test_unmap_nonexistent(self):
        """Test unmapping nonexistent tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        result = mapper.unmap_tool("nonexistent")

        assert result is False

    def test_get_remote_name_mapped(self):
        """Test getting remote name for mapped tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        mapper.map_tool("local_echo", "remote_echo")

        assert mapper.get_remote_name("local_echo") == "remote_echo"

    def test_get_remote_name_unmapped(self):
        """Test getting remote name for unmapped tool returns local"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        mapper = MCPToolMapper(client)

        assert mapper.get_remote_name("unmapped") == "unmapped"

    def test_call_local_tool(self):
        """Test calling local mapped tool"""
        server = MCPServer("http://localhost:8080")
        client = MCPClient(server)
        client.connect()

        tool = MCPTool(name="remote_test", description="Test", input_schema={})
        client.register_tool(tool)

        mapper = MCPToolMapper(client)
        mapper.map_tool("local_test", "remote_test")

        result = mapper.call_local_tool("local_test", {"key": "value"})

        assert result is not None
