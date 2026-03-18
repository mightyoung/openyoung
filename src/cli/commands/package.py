"""
Package Command - Package 管理命令

提供 openyoung package 命令
"""

import asyncio

import click

from src.package_manager.manager import PackageManager
from src.package_manager.registry import AgentRegistry


@click.group(name="package")
def package_group():
    """Package management"""
    pass


@package_group.command(name="list")
def package_list():
    """List available agents (from packages/)"""
    registry = AgentRegistry()
    agents = registry.discover_agents()
    if agents:
        click.echo("Available agents:")
        for a in agents:
            click.echo(f"  • {a.name} ({a.version}) - {a.description}")
            click.echo(f"    model: {a.model}, tools: {len(a.tools)}")
    else:
        click.echo("No agents found in packages/")


@package_group.command(name="install")
@click.argument("agent_name")
def package_install(agent_name: str):
    """Install agent dependencies (via pip)"""
    registry = AgentRegistry()
    success = registry.install_agent(agent_name)
    if success:
        click.echo(f"[OK] Installed dependencies for {agent_name}")
    else:
        click.echo(f"[Error] Failed to install {agent_name}", err=True)


@package_group.command(name="create")
@click.argument("agent_name")
@click.option("--template", "-t", default="default", help="Template: default, coder, reviewer")
def package_create(agent_name: str, template: str):
    """Create a new agent from template"""
    registry = AgentRegistry()
    path = registry.create_agent_template(agent_name, template)
    click.echo(f"[OK] Created: {path}")


@click.command("install")
@click.argument("package_name")
def install(package_name: str):
    """Install a package"""
    asyncio.run(_install(package_name))


async def _install(package_name: str):
    manager = PackageManager()
    await manager.install(package_name)
    click.echo(f"Installed: {package_name}")
