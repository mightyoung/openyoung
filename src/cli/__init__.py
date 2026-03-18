"""
CLI Package - 命令行工具
"""

from src.cli.commands import (
    agent_group,
    channel_group,
    config_group,
    data_group,
    eval_group,
    import_group,
    init_cmd,
    install,
    llm_group,
    mcp_group,
    memory_group,
    package_group,
    run_agent,
    skills_group,
    source_group,
    subagent_group,
    templates_group,
)
from src.cli.loader import AgentLoader
from src.cli.main import cli, main

__all__ = [
    "cli",
    "main",
    "AgentLoader",
    # Command groups
    "agent_group",
    "channel_group",
    "config_group",
    "data_group",
    "eval_group",
    "import_group",
    "init_cmd",
    "install",
    "llm_group",
    "mcp_group",
    "memory_group",
    "package_group",
    "run_agent",
    "skills_group",
    "source_group",
    "subagent_group",
    "templates_group",
]
