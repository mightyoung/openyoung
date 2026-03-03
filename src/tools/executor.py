"""
Tool Executor
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    result: str
    error: Optional[str] = None


class ToolExecutor:
    def __init__(self, workspace: str = None, permission_evaluator=None):
        self.workspace = workspace or "/Users/muyi/Downloads/dev/openyoung"
        self.permission_evaluator = permission_evaluator  # 权限评估器
        self.tools = {
            "bash": self.execute_bash,
            "write": self.execute_write,
            "edit": self.execute_edit,
            "read": self.execute_read,
            "glob": self.execute_glob,
            "grep": self.execute_grep,
        }

    def get_tool_schemas(self) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "执行命令行命令",
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
                    "description": "创建或覆盖文件",
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
                    "description": "编辑文件",
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
                    "description": "读取文件",
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
                    "description": "查找文件",
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
                    "description": "搜索内容",
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
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        # 权限检查 - 参考 OpenCode
        if self.permission_evaluator:
            from src.core.types import PermissionAction
            action = await self.permission_evaluator.check(tool_name, arguments)

            if action == PermissionAction.DENY:
                return ToolResult(
                    success=False,
                    result="",
                    error=f"Permission denied: {tool_name} is not allowed"
                )

            if action == PermissionAction.ASK:
                # TODO: 实现用户确认流程
                print(f"[Permission] {tool_name} requires confirmation")

        tool = self.tools.get(tool_name)
        if not tool:
            return ToolResult(
                success=False, result="", error=f"Unknown tool: {tool_name}"
            )
        try:
            result = await tool(**arguments)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result="", error=str(e))

    async def execute_bash(self, command: str, description: str = "") -> str:
        proc = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode() if stdout else ""
        err = stderr.decode() if stderr else ""
        if err:
            output += f"\n[stderr]: {err}"
        return output or "[命令执行完成]"

    async def execute_write(self, filePath: str, content: str) -> str:
        import os

        dir_name = os.path.dirname(filePath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入文件: {filePath}"

    async def execute_edit(
        self, filePath: str, old_content: str, new_content: str
    ) -> str:
        with open(filePath, "r", encoding="utf-8") as f:
            content = f.read()
        if old_content not in content:
            return f"错误: 未找到内容"
        new_content_file = content.replace(old_content, new_content)
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(new_content_file)
        return f"已编辑文件: {filePath}"

    async def execute_read(
        self, filePath: str, limit: int = None, offset: int = None
    ) -> str:
        with open(filePath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if offset:
            lines = lines[offset - 1 :]
        if limit:
            lines = lines[:limit]
        return "".join(lines)

    async def execute_glob(self, pattern: str) -> str:
        import glob as g

        files = g.glob(pattern, recursive=True)
        return "\n".join(files) if files else "未找到文件"

    async def execute_grep(
        self, pattern: str, path: str = ".", include: str = None
    ) -> str:
        import re, os

        results = []
        for root, _, files in os.walk(path):
            for f in files:
                if include and not f.endswith(include.replace("*", "")):
                    continue
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        for i, line in enumerate(file, 1):
                            if re.search(pattern, line):
                                results.append(f"{filepath}:{i}: {line.rstrip()}")
                except:
                    pass
        return "\n".join(results[:50]) if results else "未找到内容"
