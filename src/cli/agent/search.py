"""
Agent Search Command - agent search 子命令
"""

import click

from src.hub.discover.retriever import AgentRetriever


@click.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=10, help="Maximum results")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def search_agents(query, limit, format):
    """Search agents using semantic search"""
    retriever = AgentRetriever()

    results = retriever.search(query, limit=limit)

    if not results:
        click.echo(f"No agents found matching: {query}")
        return

    if format == "json":
        import json

        click.echo(json.dumps(results, indent=2, default=str))
    else:
        _display_search_results(results)


def _display_search_results(results):
    """显示搜索结果"""
    click.echo(f"\nFound {len(results)} matching agents:\n")

    for i, result in enumerate(results, 1):
        name = result.get("name", "unknown")
        score = result.get("score", 0)
        description = result.get("description", "")[:60]

        click.echo(f"{i}. {name}")
        click.echo(f"   Score: {score:.2f}")
        if description:
            click.echo(f"   {description}...")
        click.echo()
