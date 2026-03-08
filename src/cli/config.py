"""
Config Command - config 子命令

管理 OpenYoung 配置
"""

import json
import click

from .context import CLIContext


@click.group("config")
def config_group():
    """Manage configuration"""
    pass


@config_group.command("get")
@click.argument("key", required=False)
@click.pass_obj
def config_get(obj, key):
    """Get configuration value(s)

    Examples:
        openyoung config get
        openyoung config get model
    """
    ctx = obj if obj else CLIContext()
    config = ctx.load_config()

    if not config:
        click.echo("No configuration found.")
        return

    if key:
        # 获取特定 key
        value = config.get(key)
        if value is None:
            click.echo(f"Key not found: {key}")
        else:
            click.echo(f"{key} = {value}")
    else:
        # 显示所有配置
        click.echo("Current configuration:")
        for k, v in config.items():
            click.echo(f"  {k} = {v}")


@config_group.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_obj
def config_set(obj, key, value):
    """Set configuration value

    Examples:
        openyoung config set model gpt-4
        openyoung config set temperature 0.7
    """
    ctx = obj if obj else CLIContext()
    config = ctx.load_config()

    # 尝试智能解析 value
    parsed_value = _parse_value(value)
    config[key] = parsed_value

    if ctx.save_config(config):
        click.echo(f"✅ Set {key} = {parsed_value}")
    else:
        click.echo(f"❌ Failed to save configuration", err=True)


@config_group.command("unset")
@click.argument("key")
@click.pass_obj
def config_unset(obj, key):
    """Unset configuration value

    Examples:
        openyoung config unset model
    """
    ctx = obj if obj else CLIContext()
    config = ctx.load_config()

    if key in config:
        del config[key]
        if ctx.save_config(config):
            click.echo(f"✅ Removed {key}")
        else:
            click.echo(f"❌ Failed to save configuration", err=True)
    else:
        click.echo(f"Key not found: {key}")


@config_group.command("list")
@click.pass_obj
def config_list(obj):
    """List all configuration values

    Example:
        openyoung config list
    """
    ctx = obj if obj else CLIContext()
    config = ctx.load_config()

    if not config:
        click.echo("No configuration found.")
        return

    click.echo("OpenYoung Configuration:")
    click.echo("=" * 40)

    for key in sorted(config.keys()):
        value = config[key]
        # 敏感信息脱敏
        if _is_sensitive(key):
            value = "***"
        click.echo(f"  {key}: {value}")


@config_group.command("reset")
@click.confirmation_option(prompt="Are you sure you want to reset all configuration?")
@click.pass_obj
def config_reset(obj):
    """Reset all configuration to defaults

    Example:
        openyoung config reset
    """
    ctx = obj if obj else CLIContext()

    if ctx.save_config({}):
        click.echo("✅ Configuration reset to defaults")
    else:
        click.echo(f"❌ Failed to reset configuration", err=True)


def _parse_value(value: str):
    """智能解析配置值"""
    # 布尔值
    if value.lower() in ("true", "yes", "on", "1"):
        return True
    if value.lower() in ("false", "no", "off", "0"):
        return False

    # 数字
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # JSON
    if value.startswith("{") or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    # 字符串
    return value


def _is_sensitive(key: str) -> bool:
    """检查是否为敏感配置"""
    sensitive_keys = {"api_key", "secret", "password", "token", "key"}
    return any(s in key.lower() for s in sensitive_keys)
