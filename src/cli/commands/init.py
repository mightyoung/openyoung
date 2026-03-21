"""
Init Command - 初始化向导命令

提供 openyoung init 命令
"""

from pathlib import Path

import click

# Configuration path
_CONFIG_FILE = Path.home() / ".openyoung" / "config.json"


@click.command("init")
@click.option("--force", "-f", is_flag=True, help="Force reinitialize")
def init_cmd(force: bool):
    """Initialize OpenYoung configuration

    Interactive wizard to set up:
    - LLM Provider selection and API keys
    - Default channel configuration
    - Agent settings

    Example:
        openyoung init
        openyoung init --force
    """
    from src.config import load_user_config as _load_config
    from src.config import save_user_config as _save_config

    click.echo("=== OpenYoung Initialization Wizard ===\n")

    # Check if already initialized
    config = _load_config()
    if config and not force:
        click.echo("OpenYoung is already initialized!")
        click.echo(f"Config file: {_CONFIG_FILE}")
        click.echo("\nUse --force to reinitialize")
        return

    # Step 1: LLM Provider selection
    click.echo("Step 1: Select LLM Provider")
    click.echo("  1) DeepSeek (default)")
    click.echo("  2) OpenAI")
    click.echo("  3) Anthropic")
    click.echo("  4) Moonshot (Kano)")
    click.echo("  5) Qwen (Alibaba)")
    click.echo("  6) GLM (Zhipu)")

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

    # Step 3: Channel selection
    click.echo("\nStep 3: Select Channel")
    click.echo("  1) CLI (Command line)")
    click.echo("  2) Telegram")
    click.echo("  3) Discord")
    click.echo("  4) QQ (Go-CQHTTP)")
    click.echo("  5) DingTalk")
    click.echo("  6) Feishu")

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

    # Step 4: Channel-specific configuration
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

    # Save configuration
    config = {
        "provider": provider,
        "api_key": api_key,
        "channel": channel,
        "channel_config": channel_config,
    }

    # Write to .env file
    env_file = Path(".env")
    env_lines = []

    if env_file.exists():
        env_lines = env_file.read_text().splitlines()

    # Update or add provider
    env_found = False
    for i, line in enumerate(env_lines):
        if line.startswith(f"{provider.upper()}_API_KEY="):
            env_lines[i] = f"{provider.upper()}_API_KEY={api_key}"
            env_found = True
            break

    if not env_found:
        env_lines.append(f"{provider.upper()}_API_KEY={api_key}")

    env_file.write_text("\n".join(env_lines) + "\n")

    # Save to config file
    if _save_config(config):
        click.echo(f"\nConfiguration saved to {_CONFIG_FILE}")
        click.echo("API key saved to .env")
    else:
        click.echo("\nFailed to save configuration", err=True)
        return

    # Generate channels.yaml
    channels_config = {
        "channels": [
            {"platform": "cli", "enabled": True, "config": {"timeout": 300}},
        ],
        "agent": {
            "default_model": f"{provider}-chat" if provider == "deepseek" else "gpt-4o-mini",
        },
    }

    # Add selected channel
    if channel != "cli":
        channels_config["channels"].append(
            {"platform": channel, "enabled": True, "config": channel_config}
        )

    # Save channels.yaml
    channels_file = Path("config/channels.yaml")
    channels_file.parent.mkdir(parents=True, exist_ok=True)

    import yaml

    with open(channels_file, "w") as f:
        yaml.dump(channels_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"Channels config saved to {channels_file}")

    click.echo("\n=== Initialization Complete! ===")
    click.echo("\nNext steps:")
    click.echo("  1. Run: openyoung run default -i")
    click.echo("  2. Or start channel: openyoung channel start")
