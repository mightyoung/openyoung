"""
Channel Command - 通道管理命令

提供 openyoung channel 命令
"""

import asyncio
import os
from pathlib import Path

import click
import yaml


@click.group(name="channel")
def channel_group():
    """Channel management"""
    pass


@channel_group.command(name="list")
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

    # Check config file
    channels_file = Path("config/channels.yaml")
    if channels_file.exists():
        click.echo(f"\nConfigured channels (in {channels_file}):")
        try:
            config = yaml.safe_load(channels_file.read_text())
            for ch in config.get("channels", []):
                status = "enabled" if ch.get("enabled") else "disabled"
                click.echo(f"  • {ch['platform']} [{status}]")
        except Exception as e:
            click.echo(f"  Error loading config: {e}")


@channel_group.command(name="config")
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

    # Load or create config
    config = {"channels": []}
    if channels_file.exists():
        try:
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
            status = "enabled" if ch.get("enabled") else "disabled"
            click.echo(f"Platform: {ch['platform']}")
            click.echo(f"  Status: {status}")
            if ch.get("config"):
                for k, v in ch["config"].items():
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
            click.echo(f"Error: Invalid platform. Choose from: {', '.join(valid_platforms)}", err=True)
            return

        # Check if already exists
        for ch in config["channels"]:
            if ch["platform"] == platform:
                click.echo(f"Channel '{platform}' already exists. Use 'update' or remove first.")
                return

        # Build config
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

        # Save
        channels_file.parent.mkdir(parents=True, exist_ok=True)
        with open(channels_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"Added channel: {platform}")
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

        click.echo(f"Removed channel: {platform}")
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
        click.echo(f"Channel '{platform}' {status}")


@channel_group.command(name="start")
@click.argument("platform", required=False)
@click.option("--port", "-p", default=8080, help="Server port for callback channels")
def channel_start(platform: str = None, port: int = 8080):
    """Start a channel server

    Examples:
        openyoung channel start
        openyoung channel start feishu
        openyoung channel start feishu --port 3000
    """
    asyncio.run(_start_channel(platform, port))


async def _start_channel(platform: str = None, port: int = 8080):
    from src.channels.manager import ChannelManager

    click.echo("Starting channel server...")

    # Load config
    channels_file = Path("config/channels.yaml")
    if not channels_file.exists():
        click.echo("No channel configuration found. Run 'openyoung init' first.")
        return

    try:
        config = yaml.safe_load(channels_file.read_text())
    except Exception as e:
        click.echo(f"Error loading config: {e}")
        return

    # Create ChannelManager
    manager = ChannelManager()

    # Enable configured channels
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

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        click.echo("\nStopping...")
