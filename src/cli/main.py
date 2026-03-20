"""
OpenYoung CLI - 命令行入口

提供 openyoung 命令行工具的入口点
"""

import asyncio
import sys
from pathlib import Path

import click

# 添加 src 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

# ========================
# CLI 入口定义
# ========================


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """OpenYoung - AI Agent Platform"""
    pass


# ========================
# 注册命令组
# ========================


def register_commands():
    """Register all command groups with the CLI"""
    # Import all command groups
    from src.cli.commands import (
        agent_group,
        channel_group,
        config_group,
        data_group,
        deprecated_subagent_group,
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

    # Register main command groups
    cli.add_command(run_agent, name="run")
    cli.add_command(skills_group, name="skills")
    cli.add_command(agent_group, name="agent")
    cli.add_command(package_group, name="package")
    cli.add_command(llm_group, name="llm")
    cli.add_command(source_group, name="source")
    cli.add_command(channel_group, name="channel")
    cli.add_command(import_group, name="import")
    cli.add_command(subagent_group, name="subagent")
    cli.add_command(mcp_group, name="mcp")
    cli.add_command(templates_group, name="templates")
    cli.add_command(memory_group, name="memory")
    cli.add_command(data_group, name="data")
    cli.add_command(init_cmd, name="init")

    # Register eval command group
    cli.add_command(eval_group, name="eval")

    # Register test command group
    from src.cli.test import test_group

    cli.add_command(test_group, name="test")

    # Register standalone commands
    cli.add_command(install)
    cli.add_command(deprecated_subagent_group, name="deprecated_subagent")


def main():
    """Main entry point"""
    register_commands()
    cli()


if __name__ == "__main__":
    main()
