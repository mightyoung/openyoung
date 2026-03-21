"""
Tool Schemas - Tool definitions for ToolExecutor

Contains the schema definitions for all available tools.
"""


def get_tool_schemas() -> list:
    """Returns tool schemas for all available tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Execute shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["command"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write",
                "description": "Create or overwrite file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filePath": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["filePath", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "edit",
                "description": "Edit file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filePath": {"type": "string"},
                        "old_content": {"type": "string"},
                        "new_content": {"type": "string"},
                    },
                    "required": ["filePath", "old_content", "new_content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filePath": {"type": "string"},
                        "limit": {"type": "integer"},
                        "offset": {"type": "integer"},
                    },
                    "required": ["filePath"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "glob",
                "description": "Find files",
                "parameters": {
                    "type": "object",
                    "properties": {"pattern": {"type": "string"}},
                    "required": ["pattern"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "grep",
                "description": "Search content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "path": {"type": "string"},
                        "include": {"type": "string"},
                    },
                    "required": ["pattern"],
                },
            },
        },
        # MCP tools
        {
            "type": "function",
            "function": {
                "name": "mcp_list",
                "description": "List available MCP services",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mcp_call",
                "description": "Call MCP service method",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "server": {"type": "string", "description": "MCP server name"},
                        "method": {"type": "string", "description": "Method to call"},
                        "params": {"type": "object", "description": "Method parameters"},
                    },
                    "required": ["server", "method"],
                },
            },
        },
        # Enhanced tools
        {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Fetch web content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "selector": {"type": "string", "description": "CSS selector (optional)"},
                    },
                    "required": ["url"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "git",
                "description": "Execute Git command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "git command (without git prefix)"},
                        "repo_path": {"type": "string", "description": "Repository path"},
                    },
                    "required": ["command"],
                },
            },
        },
    ]


__all__ = ["get_tool_schemas"]
