"""
Agent List Command - agent list 子命令
"""

import click

from src.hub.registry import AgentRegistry


@click.command("list")
@click.option("--all", "-a", is_flag=True, help="List all agents")
@click.option("--badges", "-b", is_flag=True, help="Show badges")
@click.option("--stats", "-s", is_flag=True, help="Show statistics")
@click.option("--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table")
def list_agents(all, badges, stats, format):
    """List all available agents"""
    registry = AgentRegistry()

    if all:
        agents = registry.list_all()
    else:
        agents = registry.list()

    if not agents:
        click.echo("No agents found.")
        return

    if format == "json":
        import json
        click.echo(json.dumps(agents, indent=2, default=str))
    elif format == "yaml":
        import yaml
        click.echo(yaml.dump(agents, default_flow_style=False))
    else:
        # Table format
        _display_agents_table(agents, badges=badges, stats=stats)


def _display_agents_table(agents, badges=False, stats=False):
    """以表格形式显示 agents"""
    # 使用 click 的表格格式
    rows = []
    for agent in agents:
        row = [agent.get("name", "unknown")]
        if badges and "badges" in agent:
            row.append(", ".join(agent.get("badges", [])))
        if stats:
            row.append(str(agent.get("usage_count", 0)))
            row.append(agent.get("rating", "N/A"))
        rows.append(row)

    headers = ["Name"]
    if badges:
        headers.append("Badges")
    if stats:
        headers.extend(["Usage", "Rating"])

    click.echo(click.format_table(rows, headers=headers))
