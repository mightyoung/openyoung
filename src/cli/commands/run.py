"""
Run Command - 运行命令

提供 openyoung run 命令
"""

import asyncio

import click

from src.agents.young_agent import YoungAgent
from src.cli.loader import AgentLoader


@click.command("run")
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option(
    "--github", "-g", "github_url", default=None, help="GitHub URL to clone and analyze first"
)
@click.option("--sandbox", "-s", is_flag=True, help="Enable AI sandbox execution (subprocess-based, not Docker)")
@click.option("--allow-network", "-n", is_flag=True, help="Allow network access in sandbox")
@click.option("--max-memory", default=512, help="Max memory in MB for sandbox")
@click.option("--max-time", default=300, help="Max execution time in seconds")
def run_agent(
    agent_name: str,
    task: str = None,
    interactive: bool = False,
    github_url: str = None,
    sandbox: bool = False,
    allow_network: bool = False,
    max_memory: int = 512,
    max_time: int = 300,
):
    """Run an agent

    Examples:
        openyoung run default "Hello"
        openyoung run default -i
        openyoung run default --github https://github.com/user/repo "analyze this"
    """
    asyncio.run(
        _run(
            initial_task=task,
            agent_name=agent_name,
            interactive=interactive,
            github_url=github_url,
            sandbox=sandbox,
            allow_network=allow_network,
            max_memory=max_memory,
            max_time=max_time,
        )
    )


async def _run(
    initial_task, agent_name, interactive, github_url, sandbox, allow_network, max_memory, max_time
):
    """Internal async runner implementation"""
    user_task = initial_task or ""

    # Load agent
    loader = AgentLoader()
    try:
        config = loader.load_agent(agent_name)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    # If --github is specified, clone and analyze first
    if github_url:
        click.echo(f"[Import] Cloning {github_url}...")
        try:
            from src.package_manager.enhanced_importer import EnhancedGitHubImporter

            importer = EnhancedGitHubImporter()
            result = importer.import_from_url(github_url, agent_name or "default", validate=True)

            if result.get("agent") or result.get("config"):
                validation = result.get("validation", {})
                if validation:
                    click.echo(f"[Import] Validation score: {validation.get('score', 0):.2f}")
                    if validation.get("warnings"):
                        for warn in validation["warnings"]:
                            click.echo(f"  Warning: {warn}")
                    if not validation.get("passed"):
                        click.echo("[Import] Quality below threshold!", err=True)
                        for err in validation.get("errors", []):
                            click.echo(f"  Error: {err}", err=True)

                analysis = result.get("analysis", {})
                click.echo(f"[Import] Language: {analysis.get('language', 'unknown')}")

                clone_path = result.get("local_path")
                if clone_path and clone_path.exists():
                    click.echo("[Import] Installing dependencies...")
                    from src.tools.executor import ToolExecutor

                    executor = ToolExecutor()
                    deps_result = await executor.install_dependencies(clone_path)
                    click.echo(f"[Import] {deps_result}")

                if user_task:
                    user_task = f"分析并{user_task}"
                else:
                    user_task = "分析这个项目的结构和功能"
            else:
                click.echo("[Import] Warning: continuing without full import...")
        except Exception as e:
            click.echo(f"[Import] Error: {e}", err=True)
            return

    # Create agent
    agent = YoungAgent(config)

    # Enable sandbox if requested
    if sandbox:
        try:
            agent.enable_sandbox(
                max_memory_mb=max_memory,
                max_execution_time_seconds=max_time,
                allow_network=allow_network,
            )
            click.echo(
                f"[Sandbox] Enabled: max_memory={max_memory}MB, max_time={max_time}s, allow_network={allow_network}"
            )
        except Exception as e:
            click.echo(f"[Warning] Sandbox init failed: {e}", err=True)

    if interactive:
        click.echo(f"Interactive mode with {agent_name}. Type 'exit' to quit.")
        while True:
            try:
                user_input = input("\n> ")
            except EOFError:
                break

            if user_input.lower() in ["exit", "quit"]:
                break

            if not user_input.strip():
                continue

            result = await agent.run(user_input)
            click.echo(f"\n{result}")
    else:
        if not user_task:
            click.echo("Error: Task required (or use -i for interactive mode)", err=True)
            return

        result = await agent.run(user_task)
        click.echo(result)

        # Track agent usage
        try:
            from src.package_manager.registry import AgentRegistry

            registry = AgentRegistry("packages")
            registry.track_usage(agent_name)
        except Exception as e:
            logger.debug(f"Failed to track agent usage: {e}")

        # Show stats
        stats = agent.get_all_stats()
        click.echo("\n--- Stats ---")
        click.echo(f"Traces: {stats.get('datacenter_traces_count', 0)}")
        click.echo(f"Evaluations: {stats.get('evaluation_results_count', 0)}")
        click.echo(f"Capsules: {stats.get('evolver_capsules_count', 0)}")
