"""
MCP Command - MCP Server 管理命令

提供 openyoung mcp 命令
"""

import click

from src.package_manager.mcp_manager import MCPServerManager


@click.group(name="mcp")
def mcp_group():
    """MCP Server management"""
    pass


@mcp_group.command(name="servers")
def mcp_servers():
    """List available MCP servers"""
    manager = MCPServerManager()
    servers = manager.discover_mcp_servers()

    if not servers:
        click.echo("No MCP servers found")
        return

    click.echo("Available MCP servers:")
    for name, configs in servers.items():
        for config in configs:
            click.echo(f"  • {name}")
            click.echo(f"    Command: {config.command}")


@mcp_group.command(name="start")
@click.argument("server_name")
def mcp_start(server_name: str):
    """Start an MCP server"""
    manager = MCPServerManager()
    success = manager.start_mcp_server(server_name)

    if success:
        click.echo(f"[OK] Started MCP server: {server_name}")
    else:
        click.echo(f"[Error] Failed to start MCP server: {server_name}", err=True)


@mcp_group.command(name="stop")
@click.argument("server_name")
def mcp_stop(server_name: str):
    """Stop an MCP server"""
    manager = MCPServerManager()
    success = manager.stop_mcp_server(server_name)

    if success:
        click.echo(f"[OK] Stopped MCP server: {server_name}")
    else:
        click.echo(f"[Error] Failed to stop MCP server: {server_name}", err=True)
