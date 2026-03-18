"""
Import Command - GitHub 一键导入命令

提供 openyoung import github 命令
"""

import click

from src.package_manager.enhanced_importer import import_github_enhanced
from src.package_manager.github_importer import GitHubImporter


@click.group(name="import")
def import_group():
    """Import from external sources"""
    pass


@import_group.command(name="github")
@click.argument("github_url")
@click.argument("agent_name", required=False)
@click.option(
    "--enhanced/--basic", default=True, help="Use enhanced import with git clone + agent analysis"
)
@click.option("--lazy/--no-lazy", default=False, help="Lazy clone (faster but incomplete)")
@click.option("--validate/--no-validate", default=True, help="Validate after import")
def import_github(
    github_url: str,
    agent_name: str = None,
    enhanced: bool = True,
    lazy: bool = False,
    validate: bool = True,
):
    """Import agent from GitHub URL

    Example:
        openyoung import github https://github.com/affaan-m/everything-claude-code my-agent
        openyoung import github https://github.com/anthropics/claude-code claude-code --no-lazy
    """
    if enhanced:
        click.echo(f"[Enhanced] Importing from: {github_url}")
        if lazy:
            click.echo("[Mode] Lazy clone (fast, partial)")

        result = import_github_enhanced(
            github_url, use_git_clone=not lazy, analyze_with_agent=validate
        )

        if "error" in result:
            click.echo(f"Error: {result['error']}", err=True)
        else:
            click.echo("Successfully imported!")
            if result.get("agent"):
                click.echo(f"  Agent: {result['agent']}")
            if result.get("flowskill"):
                click.echo(f"  FlowSkill: {result['flowskill']}")
            if result.get("skills"):
                click.echo(f"  Skills: {len(result['skills'])}")
            if result.get("mcps"):
                click.echo(f"  MCPs: {len(result['mcps'])}")
            if result.get("subagents"):
                click.echo(f"  SubAgents: {len(result['subagents'])}")
    else:
        click.echo(f"Importing from: {github_url}")

        importer = GitHubImporter()
        result = importer.import_from_url(github_url, agent_name)

        if "error" in result:
            click.echo(f"Error: {result['error']}", err=True)
        else:
            click.echo("Successfully imported!")
            if result.get("agent"):
                click.echo(f"  Agent: {result['agent']}")
            if result.get("skills"):
                click.echo(f"  Skills: {', '.join(result['skills'])}")
            if result.get("mcps"):
                click.echo(f"  MCPs: {', '.join(result['mcps'])}")
