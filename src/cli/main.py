"""
OpenYoung CLI - 命令行入口
"""

import click
import asyncio
import sys
from pathlib import Path
from typing import Optional, List

# 添加 src 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

from src.agents.young_agent import YoungAgent
from src.core.types import (
    AgentConfig,
    AgentMode,
    PermissionConfig,
    PermissionRule,
    PermissionAction,
    SubAgentConfig,
    SubAgentType,
)
from src.package_manager.manager import PackageManager
from src.package_manager.registry import AgentRegistry
from src.evaluation import EvaluationHub


# ========================
# Agent Loader
# ========================


class AgentLoader:
    """Agent 配置加载器"""

    def __init__(self, agent_dir: Optional[str] = None):
        self.agent_dir = (
            Path(agent_dir) if agent_dir else Path(__file__).parent.parent / "agents"
        )
        self.agent_dir.mkdir(parents=True, exist_ok=True)

    def load_agent(self, name: str) -> AgentConfig:
        """加载 Agent 配置 - 支持多个目录"""
        # 1. 直接文件路径
        if Path(name).exists() and Path(name).is_file():
            return self._load_from_file(Path(name))

        # 2. src/agents/ 目录
        agent_file = self.agent_dir / f"{name}.yaml"
        if agent_file.exists():
            return self._load_from_file(agent_file)

        # 3. packages/ 目录 (agent-xxx/agent.yaml)
        packages_dir = Path("packages")
        if packages_dir.exists():
            for item in packages_dir.iterdir():
                if item.is_dir():
                    # 支持 agent-xxx 或 xxx 两种命名
                    expected = f"agent-{name}"
                    if item.name == expected or item.name == name:
                        yaml_file = item / "agent.yaml"
                        if yaml_file.exists():
                            return self._load_from_file(yaml_file)

        if name == "default":
            return self._get_default_config()

        raise ValueError(f"Agent not found: {name}")

    def _load_from_file(self, path: Path) -> AgentConfig:
        try:
            import yaml

            with open(path) as f:
                config = yaml.safe_load(f)
            return self._parse_config(config)
        except ImportError:
            return self._get_default_config()

    def _get_default_config(self) -> AgentConfig:
        return AgentConfig(
            name="default",
            mode=AgentMode.PRIMARY,
            model="deepseek-chat",
            temperature=0.7,
        )

    def _parse_config(self, config: dict) -> AgentConfig:
        """解析完整配置 - 参考 OpenCode 架构"""
        model_config = config.get("model", {})
        permission_config = config.get("permission", {})

        # 解析 permission
        permission = self._parse_permission(permission_config)

        # 解析 sub_agents
        sub_agents = self._parse_sub_agents(config.get("sub_agents", []))

        # 解析 system_prompt (支持多行字符串)
        system_prompt = config.get("system_prompt")
        if not system_prompt:
            system_prompt = "你是一个有帮助的AI助手。"

        return AgentConfig(
            name=config.get("name", "unknown"),
            mode=AgentMode.PRIMARY,
            model=model_config.get("name", model_config.get("model", "deepseek-chat")),
            temperature=model_config.get("temperature", 0.7),
            max_tokens=model_config.get("max_tokens"),
            tools=config.get("tools", []),
            permission=permission,
            skills=config.get("skills", []),
            sub_agents=sub_agents,
            system_prompt=system_prompt,
        )

    def _parse_permission(self, config: dict) -> PermissionConfig:
        """解析权限配置 - 参考 OpenCode PermissionNext"""
        # 解析全局默认
        global_action = config.get("_global", "ask")
        if isinstance(global_action, str):
            global_action = PermissionAction(global_action)

        # 解析规则
        rules = []
        for rule in config.get("rules", []):
            tool_pattern = rule.get("tool", "*")
            action_str = rule.get("action", "ask")
            action = PermissionAction(action_str) if isinstance(action_str, str) else action_str
            rules.append(PermissionRule(
                tool_pattern=tool_pattern,
                action=action
            ))

        return PermissionConfig(
            _global=global_action,
            rules=rules,
            confirm_message=config.get("confirm_message", "确认执行此操作?")
        )

    def _parse_sub_agents(self, config: list) -> List[SubAgentConfig]:
        """解析 SubAgent 配置 - 参考 Claude Code Task 协议"""
        sub_agents = []
        for item in config:
            try:
                sub_type = SubAgentType(item.get("type", "general"))
            except ValueError:
                sub_type = SubAgentType.GENERAL

            sub_agents.append(SubAgentConfig(
                name=item.get("name", sub_type.value),
                type=sub_type,
                description=item.get("description", ""),
                model=item.get("model", "default"),
                temperature=item.get("temperature", 0.7),
                instructions=item.get("instructions"),
                hidden=item.get("hidden", False),
            ))

        return sub_agents

    def list_agents(self) -> List[str]:
        agents = []
        if self.agent_dir.exists():
            for f in self.agent_dir.glob("*.yaml"):
                agents.append(f.stem)
        if "default" not in agents:
            agents.insert(0, "default")
        return agents

    def validate_config(self, config: AgentConfig) -> tuple[bool, str]:
        """Validate Agent configuration

        Returns:
            (is_valid, error_message)
        """
        # Check model is specified
        if not config.model:
            return False, "Model is required"

        # Check temperature is in valid range
        if config.temperature is not None:
            if not 0 <= config.temperature <= 2:
                return False, "Temperature must be between 0 and 2"

        # Check max_tokens is reasonable
        if config.max_tokens is not None:
            if config.max_tokens <= 0:
                return False, "max_tokens must be positive"
            if config.max_tokens > 100000:
                return False, "max_tokens exceeds maximum (100000)"

        # Check mode is valid
        if config.mode not in [AgentMode.PRIMARY, AgentMode.SUBAGENT, AgentMode.ALL]:
            return False, f"Invalid agent mode: {config.mode}"

        return True, ""

    def validate_agent_file(self, path: Path) -> tuple[bool, str]:
        """Validate an agent YAML file before loading

        Returns:
            (is_valid, error_message)
        """
        try:
            import yaml

            with open(path) as f:
                config = yaml.safe_load(f)

            if not config:
                return False, "Empty configuration file"

            # Check required fields
            if "name" not in config:
                return False, "Missing required field: name"

            # Validate model section
            model_config = config.get("model", {})
            if model_config:
                if "model" in model_config:
                    model = model_config["model"]
                    if not isinstance(model, str) or not model.strip():
                        return False, "Invalid model name"

                if "temperature" in model_config:
                    temp = model_config["temperature"]
                    if not isinstance(temp, (int, float)) or not 0 <= temp <= 2:
                        return False, "Temperature must be between 0 and 2"

            return True, ""

        except ImportError:
            return True, ""  # YAML not available, skip validation
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def load_default(self) -> AgentConfig:
        """Load default agent configuration"""
        return self._get_default_config()


# ========================
# Agent Runner
# ========================


class AgentRunner:
    def __init__(self):
        self.loader = AgentLoader()
        self.package_manager = PackageManager()
        self.evaluation_hub = EvaluationHub()
        self.agent: Optional[YoungAgent] = None

    def load_agent(self, name: str) -> YoungAgent:
        config = self.loader.load_agent(name)
        self.agent = YoungAgent(config)
        return self.agent

    async def run(self, task: str) -> str:
        if not self.agent:
            raise RuntimeError("Agent not loaded")
        return await self.agent.run(task)


# ========================
# CLI Commands
# ========================


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """OpenYoung - AI Agent Platform"""
    pass


@cli.command()
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--model", "-m", help="Override model")
@click.option("--eval/--no-eval", default=False, help="Evaluate result")
@click.option("--interactive", "-i", is_flag=True, help="Force interactive mode")
def run(
    agent_name: str,
    task: Optional[str],
    model: Optional[str],
    eval: bool,
    interactive: bool,
):
    """Run an agent with a task"""
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
def agent_list():
    """List available agents"""
    loader = AgentLoader()
    agents = loader.list_agents()
    click.echo("Available agents:")
    for a in agents:
        click.echo(f"  • {a}")


@agent.command("info")
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


@agent.command("use")
@click.argument("agent_name")
def agent_use(agent_name: str):
    """Set default agent"""
    click.echo(f"Set default agent to: {agent_name}")
    # TODO: Save to config


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
        marker = (
            " (default)" if default_provider and p.name == default_provider.name else ""
        )
        click.echo(f"  • {p.name} ({p.provider_type}){marker}")
        click.echo(
            f"    Models: {', '.join(p.models[:3])}{'...' if len(p.models) > 3 else ''}"
        )


@llm.command("add")
@click.argument("provider_name")
@click.option("--api-key", "-k", required=True, help="API key for the provider")
@click.option("--base-url", "-b", help="Base URL (optional)")
@click.option("--models", "-m", help="Comma-separated list of models")
@click.option("--default", "-d", is_flag=True, help="Set as default provider")
def llm_add(
    provider_name: str,
    api_key: str,
    base_url: Optional[str],
    models: Optional[str],
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
def llm_info(provider_name: Optional[str]):
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
        click.echo(
            f"API Key: {'*' * 8}{provider.api_key[-4:] if provider.api_key else 'N/A'}"
        )
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


@cli.group()
def config():
    """Configuration management"""
    pass


@config.command("list")
def config_list():
    """List all configuration settings"""
    from src.config.loader import ConfigLoader

    loader = ConfigLoader()
    config = loader.load_all()

    click.echo("Current configuration:")
    click.echo(f"  Default LLM: {config.get('llm', {}).get('model', 'not set')}")
    click.echo(f"  Temperature: {config.get('llm', {}).get('temperature', 'not set')}")
    click.echo(f"  Max Tokens: {config.get('llm', {}).get('max_tokens', 'not set')}")


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a configuration value"""
    from src.config.loader import ConfigLoader

    loader = ConfigLoader()
    config = loader.load_all()

    parts = key.split(".")
    value = config
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = None
            break

    if value is not None:
        click.echo(f"{key}: {value}")
    else:
        click.echo(f"Key not found: {key}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value"""
    click.echo(f"Set {key} = {value}")
    click.echo("Note: Config persistence not yet implemented")


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
    click.echo("Note: Source configuration not yet implemented")


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
# Import Commands - GitHub 一键导入
# ========================


@cli.group()
def import_cmd():
    """Import from external sources"""
    pass


@import_cmd.command("github")
@click.argument("github_url")
@click.option("--name", "-n", default=None, help="Agent name (default: auto-detect)")
def import_github(github_url: str, name: str = None):
    """Import agent from GitHub URL

    Example:
        openyoung import github https://github.com/affaan-m/everything-claude-code
    """
    from src.package_manager.github_importer import GitHubImporter

    click.echo(f"Importing from: {github_url}")

    importer = GitHubImporter()
    result = importer.import_from_url(github_url)

    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
    else:
        click.echo(f"Successfully imported!")
        if result.get("agent"):
            click.echo(f"  Agent: {result['agent']}")
        if result.get("skills"):
            click.echo(f"  Skills: {', '.join(result['skills'])}")
        if result.get("mcps"):
            click.echo(f"  MCPs: {', '.join(result['mcps'])}")


# ========================
# Run Commands - Agent 运行
# ========================


@cli.command("run")
@click.argument("agent_name", default="default")
@click.argument("task", required=False)
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode")
def run_agent(agent_name: str, task: str = None, interactive: bool = False):
    """Run an agent

    Examples:
        openyoung run agent-coder "Hello"
        openyoung run agent-coder -i
    """
    import asyncio

    async def _run():
        # Load agent
        loader = AgentLoader()
        try:
            config = loader.load_agent(agent_name)
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)
            return

        # Create agent
        agent = YoungAgent(config)

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
            if not task:
                click.echo("Error: Task required (or use -i for interactive mode)", err=True)
                return

            result = await agent.run(task)
            click.echo(result)

            # Show stats
            stats = agent.get_all_stats()
            click.echo(f"\n--- Stats ---")
            click.echo(f"Traces: {stats.get('datacenter_traces_count', 0)}")
            click.echo(f"Evaluations: {stats.get('evaluation_results_count', 0)}")
            click.echo(f"Capsules: {stats.get('evolver_capsules_count', 0)}")

    asyncio.run(_run())


def main():
    cli()


if __name__ == "__main__":
    main()
