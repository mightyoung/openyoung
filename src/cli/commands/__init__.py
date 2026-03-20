"""
CLI Commands Package - 模块化 CLI 命令

将 CLI 命令拆分为独立模块:
- run: 运行命令
- config: 配置命令
- agent: Agent 管理命令
- eval: 评估命令
- package: Package 管理命令
- llm: LLM Provider 管理命令
- channel: 通道管理命令
- import: 导入命令
- subagent: SubAgent 管理命令
- mcp: MCP Server 管理命令
- templates: 模板市场命令
- memory: 记忆命令
- data: 数据管理命令
- init: 初始化命令
- source: 源管理命令
- skills: Skill 管理命令
"""

from .agent import agent_group
from .channel import channel_group
from .config import config_group
from .data import data_group
from .eval import eval_group
from .import_cmd import import_group
from .init import init_cmd
from .llm import llm_group
from .mcp import mcp_group
from .memory import memory_group
from .package import install, package_group
from .peas import peas_group
from .run import run_agent
from .skills import skills_group
from .source import source_group
from .subagent import deprecated_subagent_group, subagent_group
from .templates import templates_group

__all__ = [
    # Command groups
    "agent_group",
    "channel_group",
    "config_group",
    "data_group",
    "eval_group",
    "import_group",
    "init_cmd",
    "llm_group",
    "mcp_group",
    "memory_group",
    "package_group",
    "peas_group",
    "run_agent",
    "skills_group",
    "source_group",
    "subagent_group",
    "deprecated_subagent_group",
    "templates_group",
    # Standalone commands
    "install",
]
