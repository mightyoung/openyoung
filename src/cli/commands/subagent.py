"""
SubAgent Command - SubAgent 管理命令

提供 openyoung subagent 命令
"""

import click

from src.cli.loader import AgentLoader
from src.package_manager.subagent_registry import SubAgentRegistry


@click.group(name="subagent")
def subagent_group():
    """SubAgent management"""
    pass


@subagent_group.command(name="list")
def subagent_list():
    """List all subagents"""
    registry = SubAgentRegistry()
    subagents = registry.discover_subagents()

    if not subagents:
        click.echo("No subagents found")
        return

    click.echo("Available subagents:")
    for sa in subagents:
        subagent = registry.load_subagent(sa)
        if subagent:
            click.echo(f"  • {sa}")
            click.echo(f"    Type: {subagent.type}")
            click.echo(f"    Description: {subagent.description}")
            click.echo(f"    Skills: {len(subagent.skills)}")
            click.echo(f"    MCPs: {len(subagent.mcps)}")


@subagent_group.command(name="info")
@click.argument("subagent_name")
def subagent_info(subagent_name: str):
    """Show subagent details"""
    registry = SubAgentRegistry()
    subagent = registry.load_subagent(subagent_name)

    if not subagent:
        click.echo(f"Subagent not found: {subagent_name}", err=True)
        return

    click.echo(f"SubAgent: {subagent.name}")
    click.echo(f"Type: {subagent.type}")
    click.echo(f"Description: {subagent.description}")
    click.echo(f"Model: {subagent.model}")
    click.echo(f"Temperature: {subagent.temperature}")
    click.echo(f"Skills: {subagent.skills}")
    click.echo(f"MCPs: {subagent.mcps}")
    click.echo(f"Evaluations: {subagent.evaluations}")


# DEPRECATED: Legacy subagent commands for backward compatibility
@click.group(name="deprecated_subagent")
def deprecated_subagent_group():
    """SubAgent management (DEPRECATED - use 'openyoung subagent' instead)"""
    click.echo("WARNING: This subagent command is deprecated. Use 'openyoung subagent' instead.")


@deprecated_subagent_group.command(name="list")
def deprecated_subagent_list():
    """List available subagents (DEPRECATED)"""
    click.echo("WARNING: This command is deprecated. Use 'openyoung subagent list' instead.")
    loader = AgentLoader()
    subagents = loader.list_subagents()

    click.echo("Available subagents:")
    for s in subagents:
        click.echo(f"  • {s}")


@deprecated_subagent_group.command(name="info")
@click.argument("subagent_name")
def deprecated_subagent_info(subagent_name: str):
    """Show subagent details (DEPRECATED)"""
    click.echo("WARNING: This command is deprecated. Use WebUI Agents page instead.")
    loader = AgentLoader()
    try:
        config = loader.load_subagent(subagent_name)
        click.echo(f"SubAgent: {config.name}")
        click.echo(f"Model: {config.model}")
        click.echo(f"Temperature: {config.temperature}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
