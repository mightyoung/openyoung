"""
OpenYoung CLI - 命令行入口
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import click

# 添加 src 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

# 导入配置管理和加载器
from src.agents.young_agent import YoungAgent
from src.config import (
    get_user_config as _get_config,
    load_user_config as _load_config,
    save_user_config as _save_config,
    set_user_config as _set_config,
)

# 配置路径 (从 src.config 迁移)
from pathlib import Path
_CONFIG_FILE = Path.home() / ".openyoung" / "config.json"

# ========================
# Agent Loader
# ========================
from src.cli.loader import AgentLoader
from src.core.types import (
    AgentConfig,
    AgentMode,
    PermissionAction,
    PermissionConfig,
    PermissionRule,
    SubAgentConfig,
    SubAgentType,
)
from src.hub.evaluate import EvalRunner, RunnerConfig
from src.package_manager.manager import PackageManager
from src.package_manager.registry import AgentRegistry

# ========================
# Agent Runner
# ========================


class AgentRunner:
    def __init__(self):
        self.loader = AgentLoader()
        self.package_manager = PackageManager()
        self.evaluation_hub = EvalRunner(RunnerConfig())
        self.agent: YoungAgent | None = None
        self._last_task = None
        self._last_result = None

    def load_agent(self, name: str) -> YoungAgent:
        config = self.loader.load_agent(name)
        self.agent = YoungAgent(config)
        return self.agent

    async def run(self, task: str) -> str:
        if not self.agent:
            raise RuntimeError("Agent not loaded")
        self._last_task = task
        self._last_result = await self.agent.run(task)
        return self._last_result

    async def evaluate_last_result(self, task: str, result: str = None) -> dict:
        """评估上一次执行的结果"""
        if result is None:
            result = self._last_result
        if task is None:
            task = self._last_task

        if not result:
            return {"error": "No result to evaluate"}

        # 使用 Harness EvalRunner 评估
        try:
            # 新 harness 需要 BenchmarkTask，这里用简化格式
            # 后续通过 BenchmarkTask + GraderConfig 实现完整评估
            return {
                "task": task,
                "result": result[:200] + "..." if len(result) > 200 else result,
                "evaluation": {
                    "note": "使用 src/hub/evaluate/ 评估系统",
                    "legacy_eval": False,
                    "harness": True,
                },
                "overall_score": 0.0,
            }
        except Exception as e:
            return {"error": str(e), "task": task, "result": result[:200]}


# ========================
# CLI Commands
# ========================


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """OpenYoung - AI Agent Platform"""
    pass


@cli.group()
def skills():
    """Skill management commands"""
    pass


@skills.command("list")
@click.option("--category", "-c", help="Filter by category")
def skills_list(category: str):
    """List available skill templates"""
    try:
        from src.skills.creator import list_templates

        templates = list_templates()
        if not templates:
            click.echo("No templates available")
            return

        click.echo("Available templates:")
        for template in templates:
            click.echo(f"  - {template}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@skills.command("create")
@click.argument("name")
@click.option("--template", "-t", default="code", help="Template to use")
@click.option("--output", "-o", default="skills", help="Output directory")
def skills_create(name: str, template: str, output: str):
    """Create a new skill from template"""
    try:
        from pathlib import Path

        from src.skills.creator import create_skill

        click.echo(f"Creating skill '{name}' from template '{template}'...")
        skill = create_skill(name, template, Path(output))

        click.echo(f"Skill created at: {skill.path}")
        click.echo("Files:")
        for filename in skill.files:
            click.echo(f"  - {filename}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--model", "-m", help="Override model")
@click.option("--eval/--no-eval", default=False, help="Evaluate result")
@click.option("--interactive", "-i", is_flag=True, help="Force interactive mode")
def run(
    agent_name: str,
    task: str | None,
    model: str | None,
    eval: bool,
    interactive: bool,
):
    """Run an agent with a task"""
    # 自动设置非交互式模式的环境变量
    import os

    if not task or interactive:
        # 交互式模式：清除自动允许设置
        os.environ.pop("OPENYOUNG_AUTO_ALLOW", None)
    else:
        # 非交互式模式：自动允许安全命令
        os.environ["OPENYOUNG_AUTO_ALLOW"] = "true"

    # 启动交互式 REPL
    if not task or interactive:
        from src.cli.repl import start_repl

        asyncio.run(start_repl(agent_name, model))
        return

    # 单次执行模式
    async def _run():
        runner = AgentRunner()
        try:
            click.echo(f"Loading agent: {agent_name}")
            runner.load_agent(agent_name)

            if model:
                runner.agent.config.model = model
                click.echo(f"Using model: {model}")

            click.echo(f"Executing: {task}")
            result = await runner.run(task)
            click.echo(f"\n{result}")

            if eval:
                eval_result = await runner.evaluate_last_result(task, result)
                click.echo(f"\nEvaluation: {eval_result.get('overall_score', 0):.2f}")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    asyncio.run(_run())


@cli.group()
def agent():
    """Agent management"""
    pass


@agent.command("list")
@click.option("--badges", is_flag=True, help="Show badges")
@click.option("--stats", is_flag=True, help="Show usage statistics")
@click.option("--all", "show_all", is_flag=True, help="Show all agents including from packages")
def agent_list(badges: bool, stats: bool, show_all: bool):
    """List available agents (DEPRECATED - use WebUI Agents page)"""
    import click
    click.echo("⚠️  WARNING: 'openyoung agent list' is deprecated. Use WebUI Agents page for better visualization.")
    loader = AgentLoader()
    agents = loader.list_agents()

    # 如果显示所有，也从 packages 目录获取（只获取有 agent.yaml 的目录）
    if show_all:
        packages_dir = Path("packages")
        if packages_dir.exists():
            for item in packages_dir.iterdir():
                if item.is_dir():
                    yaml_file = item / "agent.yaml"
                    if yaml_file.exists():
                        # 提取 agent 名称
                        name = item.name
                        if name.startswith("agent-"):
                            name = name[6:]  # 去掉 "agent-" 前缀
                        if name not in agents:
                            agents.append(name)

    # 导入徽章系统
    from src.package_manager.badge_system import BadgeSystem

    # 导入版本管理（如果存在）
    try:
        from src.package_manager.version_manager import VersionManager

        has_version_manager = True
    except ImportError:
        has_version_manager = False

    click.echo("Available agents:")

    # 获取使用统计
    usage_list = []
    if stats:
        try:
            from src.package_manager.registry import AgentRegistry

            registry = AgentRegistry("packages")
            usage_list = registry.get_usage_stats(100)
        except Exception:
            pass

    for a in agents:
        line = f"  • {a}"

        # 显示徽章
        if badges:
            try:
                # 从注册表获取使用统计
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

                # 尝试获取评估分数
                quality_score = 0
                try:
                    from src.package_manager.agent_evaluator import AgentEvaluator

                    evaluator = AgentEvaluator()
                    report = asyncio.run(evaluator.evaluate(f"packages/{a}"))
                    if report:
                        quality_score = report.overall_score
                except Exception:
                    pass

                agent_data = {
                    "downloads": use_count,
                    "rating": rating,
                    "dimensions": {"documentation": 0.5},  # 默认值
                    "quality_score": quality_score,
                    "recent_downloads": use_count // 2 if use_count else 0,
                    "created_at": "",
                }
                badge_system = BadgeSystem()
                agent_badges = asyncio.run(badge_system.evaluate_badges(a, agent_data))
                if agent_badges:
                    badge_str = badge_system.format_badges(agent_badges)
                    line += f" {badge_str}"
            except Exception:
                pass

        # 显示统计
        if stats:
            for item in usage_list:
                if item.get("agent_name") == a:
                    count = item.get("use_count", 0)
                    line += f" | 使用: {count}次"
                    break

        click.echo(line)


@agent.command("info")
@click.argument("agent_name")
def agent_info(agent_name: str):
    """Show agent details (DEPRECATED - use WebUI)"""
    import click
    click.echo("⚠️  WARNING: 'openyoung agent info' is deprecated. Use WebUI Agents page.")
    loader = AgentLoader()
    try:
        config = loader.load_agent(agent_name)
        click.echo(f"Agent: {config.name}")
        click.echo(f"Mode: {config.mode}")
        click.echo(f"Model: {config.model}")
        click.echo(f"Temperature: {config.temperature}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@agent.command("use")
@click.argument("agent_name")
def agent_use(agent_name: str):
    """Set default agent"""
    if _set_config("default_agent", agent_name):
        click.echo(f"Set default agent to: {agent_name}")
    else:
        click.echo(f"Failed to set default agent: {agent_name}")


@agent.command("search")
@click.argument("query")
@click.option("--limit", "-l", default=10, help="Maximum results")
@click.option("--intent/--no-intent", default=True, help="Show intent analysis")
def agent_search(query: str, limit: int, intent: bool):
    """Search agents by keyword (DEPRECATED - use WebUI)"""
    import click
    click.echo("⚠️  WARNING: 'openyoung agent search' is deprecated. Use WebUI Agents page.")
    import asyncio

    async def _search():
        # 先分析意图
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

        # 然后搜索
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

    asyncio.run(_search())


@agent.command("intent")
@click.argument("user_input")
def agent_intent(user_input: str):
    """Analyze user intent and recommend agents"""
    import asyncio

    async def _analyze():
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

    asyncio.run(_analyze())


@agent.command("evaluate")
@click.argument("agent_name")
def agent_evaluate(agent_name: str):
    """Evaluate agent quality"""
    import asyncio

    async def _evaluate():
        from src.package_manager.import_manager import ImportManager

        manager = ImportManager()
        report = await manager.evaluate_agent(agent_name)

        if not report:
            click.echo(f"Agent not found: {agent_name}")
            return

        click.echo(f"=== Agent Quality Report: {agent_name} ===\n")
        click.echo(f"Overall Score: {round(report.overall_score, 2)}/1.0")
        click.echo(f"Passed: {'✓ Yes' if report.passed else '✗ No'}\n")

        click.echo("Dimensions:")
        for d in report.dimensions:
            status = "✓" if d.passed else "✗"
            click.echo(f"  {status} {d.dimension.value:20s} {round(d.score, 2)}/1.0")
            if d.suggestions:
                for s in d.suggestions[:2]:
                    click.echo(f"    → {s}")

        if report.warnings:
            click.echo(f"\nWarnings ({len(report.warnings)}):")
            for w in report.warnings[:5]:
                click.echo(f"  ⚠ {w}")

    asyncio.run(_evaluate())


@agent.command("stats")
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


@agent.command("compare")
@click.argument("agent_a")
@click.argument("agent_b")
def agent_compare(agent_a: str, agent_b: str):
    """Compare two agents"""
    import asyncio

    async def _compare():
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

        # 表头
        click.echo(f"{'Dimension':<20} {agent_a:<15} {agent_b:<15} Winner")
        click.echo("-" * 60)

        # 各维度结果
        for d in result.dimensions:
            winner_mark = "✓" if d.winner == "a" else "✓" if d.winner == "b" else "="
            a_display = f"{d.agent_a_value}"
            b_display = f"{d.agent_b_value}"

            if d.winner == "a":
                a_display += " ✓"
            elif d.winner == "b":
                b_display += " ✓"

            click.echo(f"{d.dimension:<20} {a_display:<15} {b_display:<15}")

        click.echo("-" * 60)
        click.echo()
        click.echo(f"🏆 Winner: {result.summary}")

    asyncio.run(_compare())


@agent.command("versions")
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


@agent.command("version-add")
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
        click.echo(f"✓ Registered {agent_name} v{version}")
    except VersionError as e:
        click.echo(f"Error: {e}", err=True)


@agent.command("version-check")
@click.argument("agent_name")
@click.option("--current", default="0.0.0", help="Current version")
def agent_version_check(agent_name: str, current: str):
    """Check if there's a newer version available"""
    from src.package_manager.version_manager import VersionManager

    manager = VersionManager()
    latest = manager.check_update_available(agent_name, current)

    if latest:
        click.echo(f"Update available: v{current} → v{latest}")
    else:
        click.echo(f"Already on latest version: v{current}")


# DEPRECATED: 使用 src/package_manager.subagent_registry.SubAgentRegistry
# 保留此命令组以避免CLI报错，仅显示弃用警告


@cli.group()
def subagent():
    """SubAgent management (DEPRECATED - use 'openyoung subagent' below or WebUI)"""
    import click
    click.echo("⚠️  WARNING: This subagent command is deprecated. Use 'openyoung subagent' or WebUI Agents page.")


@subagent.command("list")
def subagent_list():
    """List available subagents (DEPRECATED)"""
    import click
    click.echo("⚠️  WARNING: This command is deprecated. Use 'openyoung subagent list' or WebUI Agents page.")
    loader = AgentLoader()
    subagents = loader.list_subagents()

    click.echo("Available subagents:")
    for s in subagents:
        click.echo(f"  • {s}")


@subagent.command("info")
@click.argument("subagent_name")
def subagent_info(subagent_name: str):
    """Show subagent details (DEPRECATED)"""
    import click
    click.echo("⚠️  WARNING: This command is deprecated. Use WebUI Agents page.")
    loader = AgentLoader()
    try:
        config = loader.load_subagent(subagent_name)
        click.echo(f"SubAgent: {config.name}")
        click.echo(f"Model: {config.model}")
        click.echo(f"Temperature: {config.temperature}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.argument("package_name")
def install(package_name: str):
    """Install a package"""

    async def _install():
        manager = PackageManager()
        await manager.install(package_name)
        click.echo(f"Installed: {package_name}")

    asyncio.run(_install())


@cli.group()
def package():
    """Package management"""
    pass


@package.command("list")
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


@package.command("install")
@click.argument("agent_name")
def package_install(agent_name: str):
    """Install agent dependencies (via pip)"""
    registry = AgentRegistry()
    success = registry.install_agent(agent_name)
    if success:
        click.echo(f"[OK] Installed dependencies for {agent_name}")
    else:
        click.echo(f"[Error] Failed to install {agent_name}", err=True)


@package.command("create")
@click.argument("agent_name")
@click.option("--template", "-t", default="default", help="Template: default, coder, reviewer")
def package_create(agent_name: str, template: str):
    """Create a new agent from template"""
    registry = AgentRegistry()
    path = registry.create_agent_template(agent_name, template)
    click.echo(f"[OK] Created: {path}")


# ========================
# LLM Commands
# ========================


@cli.group()
def llm():
    """LLM Provider management"""
    pass


@llm.command("list")
@click.option("--enabled", "-e", is_flag=True, help="Show only enabled providers")
def llm_list(enabled: bool):
    """List available LLM providers"""
    manager = PackageManager()
    providers = manager.list_providers(enabled_only=enabled)

    if not providers:
        click.echo("No LLM providers configured")
        return

    default_provider = manager.get_default_provider()

    click.echo("Available LLM providers:")
    for p in providers:
        marker = " (default)" if default_provider and p.name == default_provider.name else ""
        click.echo(f"  • {p.name} ({p.provider_type}){marker}")
        click.echo(f"    Models: {', '.join(p.models[:3])}{'...' if len(p.models) > 3 else ''}")


@llm.command("add")
@click.argument("provider_name")
@click.option("--api-key", "-k", required=True, help="API key for the provider")
@click.option("--base-url", "-b", help="Base URL (optional)")
@click.option("--models", "-m", help="Comma-separated list of models")
@click.option("--default", "-d", is_flag=True, help="Set as default provider")
def llm_add(
    provider_name: str,
    api_key: str,
    base_url: str | None,
    models: str | None,
    default: bool,
):
    """Add an LLM provider"""
    manager = PackageManager()
    provider_manager = manager.provider_manager

    # 获取 Provider 类型信息
    provider_info = provider_manager.get_provider_info(provider_name)
    if not provider_info:
        click.echo(f"Error: Unknown provider '{provider_name}'")
        click.echo(f"Available: {', '.join(provider_manager.available_providers)}")
        return

    # 验证 API key
    if not provider_manager.validate_provider_config(provider_name, api_key):
        click.echo(f"Error: Invalid API key format for '{provider_name}'")
        return

    # 获取 base_url
    actual_base_url = base_url or provider_manager.get_base_url(provider_name)
    if not actual_base_url:
        click.echo(f"Error: Could not determine base URL for '{provider_name}'")
        return

    # 解析 models
    model_list = None
    if models:
        model_list = [m.strip() for m in models.split(",")]

    # 添加 Provider
    success = manager.add_provider(
        name=provider_name,
        provider_type=provider_name,
        base_url=actual_base_url,
        api_key=api_key,
        models=model_list,
    )

    if success:
        if default:
            manager.set_default_provider(provider_name)
            click.echo(f"Added and set '{provider_name}' as default provider")
        else:
            click.echo(f"Added provider: {provider_name}")
    else:
        click.echo(f"Error: Failed to add provider '{provider_name}'")


@llm.command("remove")
@click.argument("provider_name")
def llm_remove(provider_name: str):
    """Remove an LLM provider"""
    manager = PackageManager()
    success = manager.remove_provider(provider_name)

    if success:
        click.echo(f"Removed provider: {provider_name}")
    else:
        click.echo(f"Error: Provider '{provider_name}' not found")


@llm.command("use")
@click.argument("provider_name")
def llm_use(provider_name: str):
    """Set default LLM provider"""
    manager = PackageManager()

    # 验证 provider 存在
    provider = manager.get_provider(provider_name)
    if not provider:
        click.echo(f"Error: Provider '{provider_name}' not found")
        return

    manager.set_default_provider(provider_name)
    click.echo(f"Default provider set to: {provider_name}")


@llm.command("info")
@click.argument("provider_name", required=False)
def llm_info(provider_name: str | None):
    """Show provider details"""
    manager = PackageManager()

    if provider_name:
        # 显示指定 provider
        provider = manager.get_provider(provider_name)
        if not provider:
            click.echo(f"Error: Provider '{provider_name}' not found")
            return

        click.echo(f"Provider: {provider.name}")
        click.echo(f"Type: {provider.provider_type}")
        click.echo(f"Base URL: {provider.base_url}")
        click.echo(f"API Key: {'*' * 8}{provider.api_key[-4:] if provider.api_key else 'N/A'}")
        click.echo(f"Enabled: {provider.enabled}")
        click.echo(f"Models: {', '.join(provider.models)}")
    else:
        # 显示默认 provider
        default = manager.get_default_provider()
        if not default:
            click.echo("No default provider set")
            return

        click.echo(f"Default provider: {default.name}")
        click.echo(f"Type: {default.provider_type}")
        click.echo(f"Base URL: {default.base_url}")
        click.echo(
            f"Models: {', '.join(default.models[:3])}{'...' if len(default.models) > 3 else ''}"
        )


# ========================
# Config Commands
# ========================
# DEPRECATED: config命令已迁移到 WebUI Settings (pages/5_Settings.py)
# 保留空的命令组以避免CLI报错，仅显示弃用警告


@cli.group()
def config():
    """Configuration management (DEPRECATED - use WebUI Settings instead)"""
    import click
    click.echo("⚠️  WARNING: 'openyoung config' is deprecated.")
    click.echo("   Please use WebUI Settings (pages/5_Settings.py) instead.")
    click.echo("   Run 'openyoung webui' to open the WebUI.")
    click.echo("")


# ========================
# Source Commands
# ========================


@cli.group()
def source():
    """Source/package repository management"""
    pass


@source.command("list")
def source_list():
    """List configured sources"""
    click.echo("Configured sources:")
    click.echo("  • default (PyPI)")
    # Note: Full source management coming soon


@source.command("add")
@click.argument("source_name")
@click.option("--url", "-u", help="Source URL")
def source_add(source_name: str, url: str):
    """Add a new source"""
    click.echo(f"Added source: {source_name}")
    if url:
        click.echo(f"  URL: {url}")
    click.echo("Note: Source persistence not yet implemented")


# ========================
# Init Commands - 初始化向导
# ========================


@cli.command()
@click.option("--force", "-f", is_flag=True, help="Force reinitialize")
def init(force: bool):
    """Initialize OpenYoung configuration

    Interactive wizard to set up:
    - LLM Provider selection and API keys
    - Default channel configuration
    - Agent settings

    Example:
        openyoung init
        openyoung init --force
    """

    click.echo("=== OpenYoung Initialization Wizard ===\n")

    # 检查是否已初始化
    config = _load_config()
    if config and not force:
        click.echo("OpenYoung is already initialized!")
        click.echo(f"Config file: {_CONFIG_FILE}")
        click.echo("\nUse --force to reinitialize")
        return

    # Step 1: LLM Provider 选择
    click.echo("Step 1: Select LLM Provider")
    click.echo("  1) DeepSeek (default)")
    click.echo("  2) OpenAI")
    click.echo("  3) Anthropic")
    click.echo("  4) Moonshot (月之暗面)")
    click.echo("  5) Qwen (阿里)")
    click.echo("  6) GLM (智谱)")

    provider_map = {
        "1": "deepseek",
        "2": "openai",
        "3": "anthropic",
        "4": "moonshot",
        "5": "qwen",
        "6": "glm",
    }

    provider_choice = click.prompt(
        "Select provider (1-6)", default="1", type=click.Choice(["1", "2", "3", "4", "5", "6"])
    )
    provider = provider_map[provider_choice]

    # Step 2: API Key
    click.echo(f"\nStep 2: Enter API Key for {provider}")
    api_key = click.prompt("API Key", hide_input=True)

    # Step 3: Channel 选择
    click.echo("\nStep 3: Select Channel")
    click.echo("  1) CLI (命令行)")
    click.echo("  2) Telegram")
    click.echo("  3) Discord")
    click.echo("  4) QQ (Go-CQHTTP)")
    click.echo("  5) 钉钉")
    click.echo("  6) 飞书")

    channel_choice = click.prompt(
        "Select channel (1-6)", default="1", type=click.Choice(["1", "2", "3", "4", "5", "6"])
    )

    channel_map = {
        "1": "cli",
        "2": "telegram",
        "3": "discord",
        "4": "qq",
        "5": "dingtalk",
        "6": "feishu",
    }
    channel = channel_map[channel_choice]

    # Step 4: Channel 特定配置
    channel_config = {}
    if channel == "telegram":
        click.echo("\nStep 4: Telegram Configuration")
        bot_token = click.prompt("Bot Token (from @BotFather)", hide_input=True)
        channel_config["bot_token"] = bot_token
    elif channel == "discord":
        click.echo("\nStep 4: Discord Configuration")
        bot_token = click.prompt("Bot Token", hide_input=True)
        channel_config["bot_token"] = bot_token
    elif channel == "dingtalk":
        click.echo("\nStep 4: DingTalk Configuration")
        webhook_url = click.prompt("Webhook URL", type=str)
        secret = click.prompt(
            "Secret (optional, press Enter to skip)", default="", type=str, hide_input=True
        )
        channel_config["webhook_url"] = webhook_url
        if secret:
            channel_config["secret"] = secret
    elif channel == "feishu":
        click.echo("\nStep 4: Feishu Configuration")
        app_id = click.prompt("App ID", type=str)
        app_secret = click.prompt("App Secret", hide_input=True)
        channel_config["app_id"] = app_id
        channel_config["app_secret"] = app_secret

    # 保存配置
    config = {
        "provider": provider,
        "api_key": api_key,
        "channel": channel,
        "channel_config": channel_config,
    }

    # 写入 .env 文件
    env_file = Path(".env")
    env_lines = []

    # 读取现有 .env
    if env_file.exists():
        env_lines = env_file.read_text().splitlines()

    # 更新或添加 provider
    env_found = False
    for i, line in enumerate(env_lines):
        if line.startswith(f"{provider.upper()}_API_KEY="):
            env_lines[i] = f"{provider.upper()}_API_KEY={api_key}"
            env_found = True
            break

    if not env_found:
        env_lines.append(f"{provider.upper()}_API_KEY={api_key}")

    env_file.write_text("\n".join(env_lines) + "\n")

    # 保存到配置文件
    if _save_config(config):
        click.echo(f"\n✓ Configuration saved to {_CONFIG_FILE}")
        click.echo("✓ API key saved to .env")
    else:
        click.echo("\n✗ Failed to save configuration", err=True)
        return

    # 生成 channels.yaml
    channels_config = {
        "channels": [
            {"platform": "cli", "enabled": True, "config": {"timeout": 300}},
        ],
        "agent": {
            "default_model": f"{provider}-chat" if provider == "deepseek" else "gpt-4o-mini",
        },
    }

    # 添加选中的 channel
    if channel != "cli":
        channels_config["channels"].append(
            {"platform": channel, "enabled": True, "config": channel_config}
        )

    # 保存 channels.yaml
    channels_file = Path("config/channels.yaml")
    channels_file.parent.mkdir(parents=True, exist_ok=True)

    import yaml

    with open(channels_file, "w") as f:
        yaml.dump(channels_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"✓ Channels config saved to {channels_file}")

    click.echo("\n=== Initialization Complete! ===")
    click.echo("\nNext steps:")
    click.echo("  1. Run: openyoung run default -i")
    click.echo("  2. Or start channel: openyoung channel start")


# ========================
# Channel Commands - 通道管理
# ========================


@cli.group()
def channel():
    """Channel management"""
    pass


@channel.command("list")
def channel_list():
    """List available channels"""

    click.echo("Available channels:")
    click.echo("  • cli       - Command line interface")
    click.echo("  • repl      - Interactive REPL mode")
    click.echo("  • telegram  - Telegram bot")
    click.echo("  • discord   - Discord bot")
    click.echo("  • qq        - QQ (Go-CQHTTP)")
    click.echo("  • dingtalk  - DingTalk webhook")
    click.echo("  • feishu    - Feishu/Lark")

    # 检查配置文件
    channels_file = Path("config/channels.yaml")
    if channels_file.exists():
        click.echo(f"\nConfigured channels (in {channels_file}):")
        try:
            import yaml

            config = yaml.safe_load(channels_file.read_text())
            for ch in config.get("channels", []):
                status = "✓ enabled" if ch.get("enabled") else "○ disabled"
                click.echo(f"  • {ch['platform']} [{status}]")
        except Exception as e:
            click.echo(f"  Error loading config: {e}")


@channel.command("config")
@click.argument("action", type=click.Choice(["show", "add", "remove", "enable", "disable"]))
@click.argument("platform", required=False)
@click.option("--webhook-url", help="Webhook URL for DingTalk/Feishu")
@click.option("--app-id", help="App ID for Feishu")
@click.option("--app-secret", help="App Secret for Feishu")
@click.option("--bot-token", help="Bot token for Telegram/Discord")
def channel_config_cmd(
    action: str,
    platform: str = None,
    webhook_url: str = None,
    app_id: str = None,
    app_secret: str = None,
    bot_token: str = None,
):
    """Configure channels

    Actions:
        show              - Show current channel configuration
        add <platform>   - Add a channel (telegram/discord/dingtalk/feishu/qq)
        remove <platform> - Remove a channel
        enable <platform> - Enable a channel
        disable <platform> - Disable a channel

    Examples:
        openyoung channel config show
        openyoung channel config add feishu --app-id xxx --app-secret xxx
        openyoung channel config enable telegram
        openyoung channel config disable dingtalk
    """
    channels_file = Path("config/channels.yaml")

    # 加载或创建配置
    config = {"channels": []}
    if channels_file.exists():
        try:
            import yaml

            config = yaml.safe_load(channels_file.read_text()) or {"channels": []}
        except Exception as e:
            click.echo(f"Error loading config: {e}")
            config = {"channels": []}

    if action == "show":
        click.echo("=== Channel Configuration ===\n")
        if not config.get("channels"):
            click.echo("No channels configured")
            return

        for ch in config["channels"]:
            status = "✓ enabled" if ch.get("enabled") else "○ disabled"
            click.echo(f"Platform: {ch['platform']}")
            click.echo(f"  Status: {status}")
            if ch.get("config"):
                for k, v in ch["config"].items():
                    # 隐藏敏感信息
                    if "secret" in k.lower() or "token" in k.lower() or "key" in k.lower():
                        v = "***" if v else ""
                    click.echo(f"  {k}: {v}")
            click.echo()
        return

    if action == "add":
        if not platform:
            click.echo("Error: Platform required for add action", err=True)
            return

        valid_platforms = ["cli", "telegram", "discord", "qq", "dingtalk", "feishu"]
        if platform not in valid_platforms:
            click.echo(
                f"Error: Invalid platform. Choose from: {', '.join(valid_platforms)}", err=True
            )
            return

        # 检查是否已存在
        for ch in config["channels"]:
            if ch["platform"] == platform:
                click.echo(f"Channel '{platform}' already exists. Use 'update' or remove first.")
                return

        # 构建配置
        new_ch = {"platform": platform, "enabled": True, "config": {}}

        if platform == "telegram":
            token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
            new_ch["config"]["bot_token"] = token
        elif platform == "discord":
            token = bot_token or os.getenv("DISCORD_BOT_TOKEN", "")
            new_ch["config"]["bot_token"] = token
        elif platform == "dingtalk":
            url = webhook_url or os.getenv("DINGTALK_WEBHOOK_URL", "")
            new_ch["config"]["webhook_url"] = url
            secret = os.getenv("DINGTALK_SECRET", "")
            if secret:
                new_ch["config"]["secret"] = secret
        elif platform == "feishu":
            aid = app_id or os.getenv("FEISHU_APP_ID", "")
            asec = app_secret or os.getenv("FEISHU_APP_SECRET", "")
            new_ch["config"]["app_id"] = aid
            new_ch["config"]["app_secret"] = asec
        elif platform == "qq":
            new_ch["config"]["http_port"] = 5700
            new_ch["config"]["ws_port"] = 5701

        config["channels"].append(new_ch)

        # 保存
        channels_file.parent.mkdir(parents=True, exist_ok=True)
        with open(channels_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"✓ Added channel: {platform}")
        return

    if action == "remove":
        if not platform:
            click.echo("Error: Platform required for remove action", err=True)
            return

        original_len = len(config["channels"])
        config["channels"] = [ch for ch in config["channels"] if ch["platform"] != platform]

        if len(config["channels"]) == original_len:
            click.echo(f"Channel '{platform}' not found")
            return

        with open(channels_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"✓ Removed channel: {platform}")
        return

    if action in ["enable", "disable"]:
        if not platform:
            click.echo(f"Error: Platform required for {action} action", err=True)
            return

        found = False
        for ch in config["channels"]:
            if ch["platform"] == platform:
                ch["enabled"] = action == "enable"
                found = True
                break

        if not found:
            click.echo(f"Channel '{platform}' not found. Add it first with 'add' command.")
            return

        with open(channels_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        status = "enabled" if action == "enable" else "disabled"
        click.echo(f"✓ Channel '{platform}' {status}")


@channel.command("start")
@click.argument("platform", required=False)
@click.option("--port", "-p", default=8080, help="Server port for callback channels")
def channel_start(platform: str = None, port: int = 8080):
    """Start a channel server

    Examples:
        openyoung channel start
        openyoung channel start feishu
        openyoung channel start feishu --port 3000
    """
    import asyncio

    async def _start():
        from src.channels.manager import ChannelManager

        click.echo("Starting channel server...")

        # 加载配置
        channels_file = Path("config/channels.yaml")
        if not channels_file.exists():
            click.echo("No channel configuration found. Run 'openyoung init' first.")
            return

        try:
            import yaml

            config = yaml.safe_load(channels_file.read_text())
        except Exception as e:
            click.echo(f"Error loading config: {e}")
            return

        # 创建 ChannelManager
        manager = ChannelManager()

        # 启用配置的通道
        for ch in config.get("channels", []):
            if not ch.get("enabled", True):
                continue

            if platform and ch["platform"] != platform:
                continue

            click.echo(f"Starting {ch['platform']} channel...")

            if ch["platform"] == "cli":
                from src.channels import CLIChannel

                manager.register("cli", CLIChannel(ch.get("config", {})))

            elif ch["platform"] == "telegram":
                from src.channels import TelegramChannel

                manager.register("telegram", TelegramChannel(ch.get("config", {})))

            elif ch["platform"] == "discord":
                from src.channels import DiscordChannel

                manager.register("discord", DiscordChannel(ch.get("config", {})))

            elif ch["platform"] == "qq":
                from src.channels import QQChannel

                manager.register("qq", QQChannel(ch.get("config", {})))

            elif ch["platform"] == "dingtalk":
                from src.channels import DingTalkChannel

                manager.register("dingtalk", DingTalkChannel(ch.get("config", {})))

            elif ch["platform"] == "feishu":
                from src.channels import FeishuChannel

                manager.register("feishu", FeishuChannel(ch.get("config", {})))

        click.echo("Channels started. Press Ctrl+C to stop.")
        click.echo(f"Server running on port {port}...")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            click.echo("\nStopping...")

    asyncio.run(_start())


# ========================
# Import Commands - GitHub 一键导入
# ========================


@cli.group()
def import_cmd():
    """Import from external sources"""
    pass


@import_cmd.command("github")
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
        from src.package_manager.enhanced_importer import import_github_enhanced

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
        from src.package_manager.github_importer import GitHubImporter

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


@cli.group()
def subagent():
    """SubAgent management"""
    pass


@subagent.command("list")
def subagent_list():
    """List all subagents"""
    from src.package_manager.subagent_registry import SubAgentRegistry

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


@subagent.command("info")
@click.argument("subagent_name")
def subagent_info(subagent_name: str):
    """Show subagent details"""
    from src.package_manager.subagent_registry import SubAgentRegistry

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


@cli.group()
def mcp():
    """MCP Server management"""
    pass


@mcp.command("servers")
def mcp_servers():
    """List available MCP servers"""
    from src.package_manager.mcp_manager import MCPServerManager

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


@mcp.command("start")
@click.argument("server_name")
def mcp_start(server_name: str):
    """Start an MCP server"""
    from src.package_manager.mcp_manager import MCPServerManager

    manager = MCPServerManager()
    success = manager.start_mcp_server(server_name)

    if success:
        click.echo(f"[OK] Started MCP server: {server_name}")
    else:
        click.echo(f"[Error] Failed to start MCP server: {server_name}", err=True)


@mcp.command("stop")
@click.argument("server_name")
def mcp_stop(server_name: str):
    """Stop an MCP server"""
    from src.package_manager.mcp_manager import MCPServerManager

    manager = MCPServerManager()
    success = manager.stop_mcp_server(server_name)

    if success:
        click.echo(f"[OK] Stopped MCP server: {server_name}")
    else:
        click.echo(f"[Error] Failed to stop MCP server: {server_name}", err=True)


# ========== Template Commands ==========


@cli.group()
def templates():
    """Template marketplace commands"""
    pass


@templates.command("list")
@click.option("--tag", "-t", multiple=True, help="Filter by tags")
@click.option(
    "--sort",
    "-s",
    default="rating",
    type=click.Choice(["rating", "installs", "name"]),
    help="Sort by",
)
def templates_list(tag, sort):
    """List available templates"""
    from src.package_manager.template_registry import get_registry

    registry = get_registry()
    template_list = registry.list(tags=list(tag) if tag else None, sort_by=sort)

    if not template_list:
        click.echo("No templates found")
        return

    click.echo(f"Found {len(template_list)} templates:\n")
    for t in template_list:
        click.echo(f"  {t.name}")
        click.echo(f"    Source: {t.source}")
        click.echo(f"    Rating: {'⭐' * int(t.rating)} ({t.rating:.1f})")
        click.echo(f"    Installs: {t.installs}")
        if t.tags:
            click.echo(f"    Tags: {', '.join(t.tags)}")
        click.echo()


@templates.command("search")
@click.argument("query")
def templates_search(query):
    """Search templates"""
    from src.package_manager.template_registry import get_registry

    registry = get_registry()
    results = registry.search(query)

    if not results:
        click.echo(f"No templates found matching '{query}'")
        return

    click.echo(f"Found {len(results)} templates:\n")
    for t in results:
        click.echo(f"  {t.name}")
        click.echo(f"    {t.description}")
        click.echo(f"    Rating: {'⭐' * int(t.rating)} ({t.rating:.1f})")
        click.echo()


@templates.command("add")
@click.argument("name")
@click.argument("source")
@click.option("--description", "-d", default="", help="Template description")
@click.option("--tags", "-t", multiple=True, help="Template tags")
@click.option("--author", "-a", default="", help="Template author")
def templates_add(name, source, description, tags, author):
    """Add a template to the registry"""
    from src.package_manager.template_registry import add_template

    template = add_template(
        name=name,
        source=source,
        description=description,
        tags=list(tags) if tags else None,
        author=author,
    )
    click.echo(f"[OK] Added template: {name}")


@templates.command("remove")
@click.argument("name")
def templates_remove(name):
    """Remove a template from the registry"""
    from src.package_manager.template_registry import get_registry

    registry = get_registry()
    if registry.remove(name):
        click.echo(f"[OK] Removed template: {name}")
    else:
        click.echo(f"[Error] Template not found: {name}", err=True)


@templates.command("info")
@click.argument("name")
def templates_info(name):
    """Show template details"""
    from src.package_manager.template_registry import get_registry

    registry = get_registry()
    template = registry.get(name)

    if not template:
        click.echo(f"[Error] Template not found: {name}", err=True)
        return

    click.echo(f"Template: {template.name}")
    click.echo(f"  Source: {template.source}")
    click.echo(f"  Description: {template.description}")
    click.echo(f"  Author: {template.author or 'Unknown'}")
    click.echo(f"  Version: {template.version}")
    click.echo(f"  Rating: {'⭐' * int(template.rating)} ({template.rating:.1f})")
    click.echo(f"  Installs: {template.installs}")
    click.echo(f"  Tags: {', '.join(template.tags) or 'None'}")
    click.echo(f"  Added: {template.added_at}")
    click.echo(f"  Updated: {template.updated_at}")


# ========== Memory Commands ==========


@cli.group()
def memory():
    """Memory and vector search commands"""
    pass


@memory.command("list")
@click.option("--namespace", "-n", default=None, help="Filter by namespace")
@click.option("--limit", "-l", default=20, help="Maximum results")
def memory_list(namespace: str = None, limit: int = 20):
    """List all memory entries"""
    from src.core.memory.impl.vector_store import VectorStore

    store = VectorStore()

    if namespace:
        results = store.list(namespace=namespace, limit=limit)
    else:
        # List all namespaces
        stats = store.get_stats()
        namespaces = stats.get("namespace_list", [])
        if not namespaces:
            click.echo("No namespaces found")
            return

        click.echo("=== Namespaces ===")
        for ns in namespaces:
            click.echo(f"  - {ns}")

        # Also show first few entries from each namespace
        click.echo("\n=== Recent Entries ===")
        for ns in namespaces[:3]:
            results = store.list(namespace=ns, limit=3)
            if results:
                click.echo(f"\n[{ns}]:")
                for r in results:
                    content = r.get("content", "")[:100]
                    click.echo(f"  - {content}...")


@memory.command("search")
@click.argument("query")
@click.option("--namespace", "-n", default="default", help="Namespace to search in")
@click.option("--limit", "-l", default=5, help="Maximum results")
@click.option("--threshold", "-t", default=0.0, help="Similarity threshold")
def memory_search(query: str, namespace: str, limit: int, threshold: float):
    """Search memory using semantic vector search"""
    from src.core.memory.impl.vector_store import VectorStore

    store = VectorStore()
    results = store.search(query, namespace=namespace, limit=limit, threshold=threshold)

    if not results:
        click.echo("No results found")
        return

    click.echo(f"Found {len(results)} results:\n")
    for i, r in enumerate(results, 1):
        similarity = r.get("similarity", 0)
        content = r.get("content", "")[:200]
        click.echo(f"{i}. [similarity: {similarity:.3f}] {content}...")


@memory.command("stats")
def memory_stats():
    """Show memory statistics"""
    from src.core.memory.impl.vector_store import VectorStore

    store = VectorStore()
    stats = store.get_stats()

    click.echo("=== Vector Store Stats ===")
    click.echo(f"Status: {stats.get('status')}")
    click.echo(f"Namespaces: {stats.get('namespaces', 0)}")
    if stats.get("namespace_list"):
        click.echo(f"Namespace list: {', '.join(stats['namespace_list'])}")


# ========================
# Run Commands - Agent 运行
# ========================


@cli.command("run")
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option(
    "--github", "-g", "github_url", default=None, help="GitHub URL to clone and analyze first"
)
@click.option("--sandbox", "-s", is_flag=True, help="Enable AI Docker sandbox execution")
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
    import asyncio

    async def _run(initial_task):
        # 保存原始任务
        user_task = initial_task or ""

        # 如果指定了 --github，先克隆和分析

        # Load agent
        loader = AgentLoader()
        try:
            config = loader.load_agent(agent_name)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            return

        # 如果指定了 --github，先克隆和分析
        if github_url:
            click.echo(f"[Import] Cloning {github_url}...")
            try:
                from src.package_manager.enhanced_importer import EnhancedGitHubImporter

                importer = EnhancedGitHubImporter()

                # 解析 URL 并克隆（启用验证）
                result = importer.import_from_url(
                    github_url, agent_name or "default", validate=True
                )

                # 检查导入是否有结果
                if result.get("agent") or result.get("config"):
                    # 显示验证结果
                    validation = result.get("validation", {})
                    if validation:
                        click.echo(f"[Import] Validation score: {validation.get('score', 0):.2f}")
                        if validation.get("warnings"):
                            for warn in validation["warnings"]:
                                click.echo(f"  Warning: {warn}")
                        if not validation.get("passed"):
                            click.echo("[Import] ⚠️ Quality below threshold!", err=True)
                            for err in validation.get("errors", []):
                                click.echo(f"  Error: {err}", err=True)

                    # 分析项目结构
                    analysis = result.get("analysis", {})
                    click.echo(f"[Import] Language: {analysis.get('language', 'unknown')}")

                    # 自动安装依赖
                    clone_path = result.get("local_path")
                    if clone_path and clone_path.exists():
                        click.echo("[Import] Installing dependencies...")
                        from src.tools.executor import ToolExecutor

                        executor = ToolExecutor()
                        deps_result = await executor.install_dependencies(clone_path)
                        click.echo(f"[Import] {deps_result}")

                    # 将任务改为分析项目
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
            except Exception:
                pass  # Silently ignore tracking errors

            # Show stats
            stats = agent.get_all_stats()
            click.echo("\n--- Stats ---")
            click.echo(f"Traces: {stats.get('datacenter_traces_count', 0)}")
            click.echo(f"Evaluations: {stats.get('evaluation_results_count', 0)}")
            click.echo(f"Capsules: {stats.get('evolver_capsules_count', 0)}")

    asyncio.run(_run(task))


# ========================
# Data Commands - 数据管理
# ========================


@cli.group()
def data():
    """Data management commands"""
    pass


@data.command("stats")
@click.option("--agent", "-a", default=None, help="Filter by agent ID")
@click.option("--days", "-d", default=7, type=int, help="Days to look back")
def data_stats(agent: str, days: int):
    """Show run statistics"""
    from src.datacenter import DataAnalytics

    analytics = DataAnalytics()
    if agent:
        stats = analytics.get_agent_stats(agent, days)
        click.echo(f"Agent: {agent}")
        click.echo(f"Period: {days} days")
        click.echo(f"Total runs: {stats['total_runs']}")
        click.echo(f"Success: {stats['success']}")
        click.echo(f"Failed: {stats['failed']}")
        click.echo(f"Success rate: {stats['success_rate']:.1%}")
        click.echo(f"Avg duration: {stats['avg_duration']}s")
    else:
        dashboard = analytics.get_dashboard()
        summary = dashboard["summary"]
        click.echo("=== Dashboard ===")
        click.echo(f"Total agents: {summary['total_agents']}")
        click.echo(f"Total runs: {summary['total_runs']}")
        click.echo(f"Success rate: {summary['success_rate']:.1%}")
        click.echo(f"Avg duration: {summary['avg_duration']}s")


@data.command("runs")
@click.option("--agent", "-a", default=None, help="Filter by agent")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--limit", "-l", default=10, type=int, help="Limit results")
def data_runs(agent: str, status: str, limit: int):
    """List recent runs"""
    from src.datacenter import RunTracker

    tracker = RunTracker()
    runs = tracker.list_runs(agent_id=agent, status=status, limit=limit)


@data.command("list")
@click.option("--agent", "-a", default=None, help="Filter by agent")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--limit", "-l", default=10, type=int, help="Limit results")
def data_list(agent: str, status: str, limit: int):
    """List recent runs (alias for 'runs')"""
    from src.datacenter import RunTracker

    tracker = RunTracker()
    runs = tracker.list_runs(agent_id=agent, status=status, limit=limit)

    if not runs:
        click.echo("No runs found")
        return

    click.echo(f"Found {len(runs)} runs:")
    for run in runs:
        status_emoji = "✅" if run["status"] == "success" else "❌"
        click.echo(
            f"  {status_emoji} {run['run_id'][:16]}... | {run['status']:8} | {run.get('task', 'N/A')[:40]}"
        )


@data.command("export")
@click.argument("output_dir")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "csv"]))
def data_export(output_dir: str, format: str):
    """Export data to directory"""
    from src.datacenter import DataExporter

    exporter = DataExporter()
    files = exporter.export_full(output_dir)

    click.echo("Exported files:")
    for name, path in files.items():
        click.echo(f"  {name}: {path}")


@data.command("dashboard")
def data_dashboard():
    """Show dashboard data"""
    import json

    from src.datacenter import DataAnalytics

    analytics = DataAnalytics()
    dashboard = analytics.get_dashboard()

    click.echo(json.dumps(dashboard, indent=2, default=str))


@data.command("steps")
@click.option("--run", "-r", required=True, help="Run ID")
@click.option("--limit", "-l", default=50, type=int, help="Limit results")
def data_steps(run: str, limit: int):
    """List steps for a run"""
    from src.datacenter import StepRecorder

    try:
        recorder = StepRecorder()
        steps = recorder.list_steps(run)

        if not steps:
            click.echo("No steps found")
            return

        click.echo(f"Found {len(steps)} steps:")
        for step in steps:
            status_emoji = (
                "✅"
                if step["status"] == "success"
                else "❌"
                if step["status"] == "failed"
                else "🔄"
            )
            click.echo(
                f"  {status_emoji} {step['step_name']:20} | {step['status']:8} | {step.get('latency_ms', 0)}ms"
            )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@data.command("license")
@click.option("--list", "list_licenses", is_flag=True, help="List all licenses")
@click.option("--create", is_flag=True, help="Create a new license")
@click.option("--owner", "-o", default=None, help="Owner ID")
@click.option(
    "--type",
    "-t",
    "license_type",
    default="private",
    type=click.Choice(["public", "private", "team"]),
    help="License type",
)
def data_license(list_licenses: bool, create: bool, owner: str, license_type: str):
    """Manage data licenses"""
    from src.datacenter import DataLicenseManager

    try:
        mgr = DataLicenseManager()

        if list_licenses:
            licenses = mgr.list_licenses(
                owner_id=owner, license_type=license_type if license_type != "private" else None
            )
            if not licenses:
                click.echo("No licenses found")
                return
            click.echo(f"Found {len(licenses)} licenses:")
            for lic in licenses:
                click.echo(
                    f"  {lic['license_id'][:16]}... | {lic['license_type']:8} | {lic['owner_id']}"
                )

        elif create:
            if not owner:
                click.echo("Error: --owner is required when creating a license", err=True)
                raise SystemExit(1)
            license_id = mgr.create_license(owner, license_type)
            click.echo(f"Created license: {license_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@data.command("team")
@click.option("--list", "list_teams", is_flag=True, help="List teams")
@click.option("--members", is_flag=True, help="List team members")
@click.option("--team-id", "-t", default=None, help="Team ID")
@click.option("--create", is_flag=True, help="Create a team")
@click.option("--name", "-n", default=None, help="Team name")
@click.option("--owner", "-o", default=None, help="Team owner")
def data_team(list_teams: bool, members: bool, team_id: str, create: bool, name: str, owner: str):
    """Manage teams"""
    from src.datacenter import TeamShareManager

    try:
        mgr = TeamShareManager()

        if list_teams:
            teams = mgr.list_teams(user_id=owner)
            if not teams:
                click.echo("No teams found")
                return
            click.echo(f"Found {len(teams)} teams:")
            for team in teams:
                click.echo(f"  {team['team_id']:20} | {team['name']:20} | {team['owner_id']}")

        elif members:
            if not team_id:
                click.echo("Error: --team-id is required", err=True)
                raise SystemExit(1)
            members_list = mgr.list_members(team_id)
            if not members_list:
                click.echo("No members found")
                return
            click.echo(f"Found {len(members_list)} members:")
            for member in members_list:
                click.echo(f"  {member['user_id']:20} | {member['role']}")

        elif create:
            if not team_id or not name or not owner:
                click.echo("Error: --team-id, --name, and --owner are required", err=True)
                raise SystemExit(1)
            mgr.create_team(team_id, name, owner)
            click.echo(f"Created team: {team_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@data.command("access")
@click.option("--data-id", "-d", required=True, help="Data ID")
@click.option("--user", "-u", required=True, help="User ID")
@click.option("--type", "-t", default="read", help="Access type")
@click.option("--purpose", "-p", default="", help="Purpose")
def data_access(data_id: str, user: str, type: str, purpose: str):
    """Log data access"""
    from src.datacenter import AccessLog

    try:
        log = AccessLog()
        log_id = log.log_access(data_id, user, type, purpose)
        click.echo(f"Logged access: {log_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def main():
    # 注册 skill 命令组 (from this file)
    cli.add_command(skills, name="skills")

    # 注册 eval 命令组
    from src.cli.eval import eval_group

    cli.add_command(eval_group, name="eval")

    # 注册 test 命令组
    from src.cli.test import test_group

    cli.add_command(test_group, name="test")

    cli()


if __name__ == "__main__":
    main()
