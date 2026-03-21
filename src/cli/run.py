"""
Run Command - run 子命令

负责执行 Agent 任务
"""

import asyncio

import click

from src.agents.young_agent import YoungAgent


@click.command("run")
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
@click.option(
    "--github", "-g", "github_url", default=None, help="GitHub URL to clone and analyze first"
)
@click.option("--eval/--no-eval", default=True, help="Enable evaluation")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_agent(
    agent_name: str, task: str, interactive: bool, github_url: str, eval: bool, verbose: bool
):
    """Run an agent

    Examples:
        openyoung run default "Hello"
        openyoung run default -i
        openyoung run default --github https://github.com/user/repo "analyze this"
    """
    asyncio.run(_run_agent(agent_name, task, interactive, github_url, eval, verbose))


async def _run_agent(
    agent_name: str, task: str, interactive: bool, github_url: str, eval: bool, verbose: bool
):
    """Async implementation of run command"""
    # 保存原始任务
    user_task = task or ""

    # 如果指定了 --github，先克隆和分析
    if github_url:
        await _handle_github_import(github_url, agent_name)

    # Load agent
    try:
        config = _load_agent_config(agent_name)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    # 创建 Agent
    agent = YoungAgent(config)

    # 执行任务
    if interactive:
        await _run_interactive(agent, verbose)
    else:
        await _run_task(agent, user_task, eval, verbose)


async def _handle_github_import(github_url: str, agent_name: str):
    """处理 GitHub 导入"""
    click.echo(f"[Import] Cloning {github_url}...")

    try:
        from src.package_manager.enhanced_importer import EnhancedGitHubImporter

        importer = EnhancedGitHubImporter()

        # 解析 URL 并克隆（启用验证）
        result = importer.import_from_url(github_url, agent_name or "default", validate=True)

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
        else:
            click.echo("[Import] ⚠️ No agent found in repository", err=True)

    except Exception as e:
        click.echo(f"[Import] Error: {e}", err=True)


def _load_agent_config(agent_name: str):
    """加载 Agent 配置"""
    from src.hub.registry import AgentRegistry

    registry = AgentRegistry()
    config = registry.get(agent_name)

    if not config:
        raise ValueError(f"Agent not found: {agent_name}")

    return config


async def _run_task(agent: YoungAgent, task: str, eval: bool, verbose: bool):
    """运行单个任务"""
    if not task:
        click.echo("Error: No task specified", err=True)
        return

    if verbose:
        click.echo(f"[Agent] Running: {agent.config.name}")
        click.echo(f"[Task] {task}")

    try:
        # 执行任务
        result = await agent.run(task)

        if verbose:
            click.echo(f"[Result] {result}")

        click.echo("✅ Task completed successfully")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


async def _run_interactive(agent: YoungAgent, verbose: bool):
    """交互式运行"""
    click.echo("Interactive mode. Type 'exit' to quit.")

    while True:
        try:
            task = input("\n> ")
            if task.lower() in ("exit", "quit", "q"):
                break

            if not task.strip():
                continue

            if verbose:
                click.echo(f"[Executing] {task}")

            result = await agent.run(task)
            click.echo(f"\n{result}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"Error: {e}", err=True)

    click.echo("\nGoodbye!")


# 便捷函数 - 供其他模块调用
async def run(agent_name: str, task: str, **options) -> dict:
    """Programmatic API for running agents

    Args:
        agent_name: Name of the agent to run
        task: Task description
        **options: Additional options

    Returns:
        dict: Execution result
    """
    config = _load_agent_config(agent_name)
    agent = YoungAgent(config)
    return await agent.run(task)
