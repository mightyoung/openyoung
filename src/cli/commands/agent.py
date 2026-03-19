"""
Agent Command - Agent 管理命令

提供 openyoung agent 命令
"""

import asyncio

import click

from src.cli.loader import AgentLoader


@click.group(name="agent")
def agent_group():
    """Agent management"""
    pass


@agent_group.command(name="list")
@click.option("--badges", is_flag=True, help="Show badges")
@click.option("--stats", is_flag=True, help="Show usage statistics")
@click.option("--all", "show_all", is_flag=True, help="Show all agents including from packages")
def agent_list(badges: bool, stats: bool, show_all: bool):
    """List available agents"""
    click.echo("Available agents:")
    loader = AgentLoader()
    agents = loader.list_agents()

    # If showing all, also get from packages directory
    if show_all:
        packages_dir = Path("packages")
        if packages_dir.exists():
            for item in packages_dir.iterdir():
                if item.is_dir():
                    yaml_file = item / "agent.yaml"
                    if yaml_file.exists():
                        name = item.name
                        if name.startswith("agent-"):
                            name = name[6:]
                        if name not in agents:
                            agents.append(name)

    # Import badge system
    from src.package_manager.badge_system import BadgeSystem

    # Get usage stats if needed
    usage_list = []
    if stats:
        try:
            from src.package_manager.registry import AgentRegistry
            registry = AgentRegistry("packages")
            usage_list = registry.get_usage_stats(100)
        except Exception as e:
            logger.warning(f"Failed to get usage stats: {e}")

    for a in agents:
        line = f"  • {a}"

        # Show badges
        if badges:
            try:
                from src.package_manager.registry import AgentRegistry
                registry = AgentRegistry("packages")
                usage_list = registry.get_usage_stats(100)
                use_count = 0
                rating = 0.0
                for item in usage_list:
                    if item.get("agent_name") == a:
                        use_count = item.get("use_count", 0)
                        rating = item.get("rating", 0.0)
                        break

                quality_score = 0
                try:
                    from src.package_manager.agent_evaluator import AgentEvaluator
                    evaluator = AgentEvaluator()
                    report = asyncio.run(evaluator.evaluate(f"packages/{a}"))
                    if report:
                        quality_score = report.overall_score
                except Exception as e:
                    logger.debug(f"Failed to get quality score for {a}: {e}")

                agent_data = {
                    "downloads": use_count,
                    "rating": rating,
                    "dimensions": {"documentation": 0.5},
                    "quality_score": quality_score,
                    "recent_downloads": use_count // 2 if use_count else 0,
                    "created_at": "",
                }
                badge_system = BadgeSystem()
                agent_badges = asyncio.run(badge_system.evaluate_badges(a, agent_data))
                if agent_badges:
                    badge_str = badge_system.format_badges(agent_badges)
                    line += f" {badge_str}"
            except Exception as e:
                logger.debug(f"Failed to show badges for {a}: {e}")

        # Show stats
        if stats:
            for item in usage_list:
                if item.get("agent_name") == a:
                    count = item.get("use_count", 0)
                    line += f" | Uses: {count}次"
                    break

        click.echo(line)


@agent_group.command(name="info")
@click.argument("agent_name")
def agent_info(agent_name: str):
    """Show agent details"""
    loader = AgentLoader()
    try:
        config = loader.load_agent(agent_name)
        click.echo(f"Agent: {config.name}")
        click.echo(f"Mode: {config.mode}")
        click.echo(f"Model: {config.model}")
        click.echo(f"Temperature: {config.temperature}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@agent_group.command(name="use")
@click.argument("agent_name")
def agent_use(agent_name: str):
    """Set default agent"""
    from src.config import set_user_config as _set_config
    if _set_config("default_agent", agent_name):
        click.echo(f"Set default agent to: {agent_name}")
    else:
        click.echo(f"Failed to set default agent: {agent_name}")


@agent_group.command(name="search")
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum results")
@click.option("--intent/--no-intent", default=True, help="Show intent analysis")
def agent_search(query: str, limit: int, intent: bool):
    """Search agents by keyword"""
    asyncio.run(_search(query, limit, intent))


async def _search(query: str, limit: int, intent: bool):
    # Intent analysis first
    if intent:
        from src.package_manager.intent_analyzer import IntentAnalyzer
        analyzer = IntentAnalyzer()
        intent_result = await analyzer.analyze(query)

        click.echo("=== Intent Analysis ===\n")
        click.echo(f"Query: {query}")
        click.echo(f"Intent: {intent_result.type.value} ({intent_result.confidence:.0%})")
        click.echo(f"Description: {intent_result.description}")
        click.echo(f"\nSuggested Agents: {', '.join(intent_result.suggested_agents)}")
        click.echo("\n" + "=" * 40 + "\n")

    # Then search
    from src.package_manager.import_manager import ImportManager
    manager = ImportManager()
    results = await manager.search(query, limit=limit)

    if not results:
        click.echo(f"No agents found matching: {query}")
        return

    click.echo(f"Search results for '{query}':\n")
    for r in results:
        score = r.get("quality_score", "N/A")
        if score is not None and isinstance(score, float):
            score = round(score, 2)
        click.echo(f"  • {r['name']}")
        click.echo(f"    Description: {r.get('description', 'N/A')[:60]}...")
        click.echo(f"    Version: {r.get('version', 'N/A')}")
        click.echo(f"    Quality: {score}")
        click.echo()


@agent_group.command(name="intent")
@click.argument("user_input")
def agent_intent(user_input: str):
    """Analyze user intent and recommend agents"""
    asyncio.run(_analyze_intent(user_input))


async def _analyze_intent(user_input: str):
    from src.package_manager.intent_analyzer import IntentAnalyzer
    analyzer = IntentAnalyzer()
    intent = await analyzer.analyze(user_input)

    click.echo("=== Intent Analysis ===\n")
    click.echo(f"Input: {user_input}\n")
    click.echo(f"Intent Type: {intent.type.value}")
    click.echo(f"Confidence: {intent.confidence:.0%}")
    click.echo(f"Description: {intent.description}")
    click.echo("\nSuggested Agents:")
    for agent in intent.suggested_agents:
        click.echo(f"  • {agent}")
    if intent.required_capabilities:
        click.echo("\nRequired Capabilities:")
        for cap in intent.required_capabilities:
            click.echo(f"  • {cap}")


@agent_group.command(name="evaluate")
@click.argument("agent_name")
def agent_evaluate(agent_name: str):
    """Evaluate agent quality"""
    asyncio.run(_evaluate_agent(agent_name))


async def _evaluate_agent(agent_name: str):
    from src.package_manager.import_manager import ImportManager
    manager = ImportManager()
    report = await manager.evaluate_agent(agent_name)

    if not report:
        click.echo(f"Agent not found: {agent_name}")
        return

    click.echo(f"=== Agent Quality Report: {agent_name} ===\n")
    click.echo(f"Overall Score: {round(report.overall_score, 2)}/1.0")
    click.echo(f"Passed: {'Yes' if report.passed else 'No'}\n")

    click.echo("Dimensions:")
    for d in report.dimensions:
        status = "Y" if d.passed else "N"
        click.echo(f"  [{status}] {d.dimension.value:20s} {round(d.score, 2)}/1.0")
        if d.suggestions:
            for s in d.suggestions[:2]:
                click.echo(f"    -> {s}")

    if report.warnings:
        click.echo(f"\nWarnings ({len(report.warnings)}):")
        for w in report.warnings[:5]:
            click.echo(f"  Warning: {w}")


@agent_group.command(name="stats")
@click.option("--limit", "-n", default=10, help="Number of agents to show")
def agent_stats(limit: int):
    """Show agent usage statistics"""
    from src.package_manager.registry import AgentRegistry
    registry = AgentRegistry()
    stats = registry.get_usage_stats(limit)

    if not stats:
        click.echo("No usage data yet. Agents will be tracked when used.")
        return

    click.echo("=== Agent Usage Statistics ===\n")
    for i, s in enumerate(stats, 1):
        click.echo(f"{i}. {s['agent_name']}")
        click.echo(f"   Uses: {s['use_count']} | Last used: {s['last_used'][:10]}")
    click.echo(f"\nShowing top {len(stats)} agents")


@agent_group.command(name="compare")
@click.argument("agent_a")
@click.argument("agent_b")
def agent_compare(agent_a: str, agent_b: str):
    """Compare two agents"""
    asyncio.run(_compare_agents(agent_a, agent_b))


async def _compare_agents(agent_a: str, agent_b: str):
    from src.package_manager.agent_compare import AgentComparer
    comparer = AgentComparer()
    result = await comparer.compare(agent_a, agent_b)

    if not result.dimensions:
        click.echo("Error: One or both agents not found")
        return

    click.echo("=" * 50)
    click.echo("         Agent Comparison")
    click.echo("=" * 50)
    click.echo()

    click.echo(f"{'Dimension':<20} {agent_a:<15} {agent_b:<15} Winner")
    click.echo("-" * 60)

    for d in result.dimensions:
        winner_mark = "Y" if d.winner == "a" else "Y" if d.winner == "b" else "="
        a_display = f"{d.agent_a_value}"
        b_display = f"{d.agent_b_value}"

        if d.winner == "a":
            a_display += " Y"
        elif d.winner == "b":
            b_display += " Y"

        click.echo(f"{d.dimension:<20} {a_display:<15} {b_display:<15}")

    click.echo("-" * 60)
    click.echo()
    click.echo(f"Winner: {result.summary}")


@agent_group.command(name="versions")
@click.argument("agent_name")
@click.option("--limit", default=10, help="Number of versions to show")
def agent_versions(agent_name: str, limit: int):
    """Show agent version history"""
    from src.package_manager.version_manager import VersionManager
    manager = VersionManager()
    versions = manager.list_versions(agent_name, limit)

    if not versions:
        click.echo(f"No version history for: {agent_name}")
        click.echo(f"Use 'agent version-add {agent_name} 1.0.0' to register first version")
        return

    current = manager.get_current_version(agent_name)

    click.echo(f"=== {agent_name} Versions ===")
    click.echo(f"\nCurrent: {current}")
    click.echo("\nVersion History:")

    for v in versions:
        is_current = " (latest)" if v.version == current else ""
        click.echo(f"\n  v{v.version}{is_current}")
        click.echo(f"    Released: {v.released_at[:10]}")
        if v.changelog:
            click.echo("    Changelog:")
            for line in v.changelog.split("\n"):
                if line.strip():
                    click.echo(f"      {line}")
        if v.breaking_changes:
            click.echo(f"    Breaking: {', '.join(v.breaking_changes)}")


@agent_group.command(name="version-add")
@click.argument("agent_name")
@click.argument("version")
@click.option("--changelog", default="", help="Changelog message")
@click.option("--compatible", default="*", help="Compatible version (e.g., 1.x)")
def agent_version_add(agent_name: str, version: str, changelog: str, compatible: str):
    """Add a new version for an agent"""
    from src.package_manager.version_manager import VersionError, VersionManager
    manager = VersionManager()

    try:
        v = manager.register_version(
            agent_name, version, changelog=changelog, compatible_with=compatible
        )
        click.echo(f"Registered {agent_name} v{version}")
    except VersionError as e:
        click.echo(f"Error: {e}", err=True)


@agent_group.command(name="version-check")
@click.argument("agent_name")
@click.option("--current", default="0.0.0", help="Current version")
def agent_version_check(agent_name: str, current: str):
    """Check if there's a newer version available"""
    from src.package_manager.version_manager import VersionManager
    manager = VersionManager()
    latest = manager.check_update_available(agent_name, current)

    if latest:
        click.echo(f"Update available: v{current} -> v{latest}")
    else:
        click.echo(f"Already on latest version: v{current}")
