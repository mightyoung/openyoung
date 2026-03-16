"""
Config Command - 配置命令

提供配置管理命令
"""

import os
from pathlib import Path

import click


@click.group(name="config")
def config_group():
    """配置管理"""
    pass


@config_group.command(name="get")
@click.argument("key")
def config_get(key: str):
    """获取配置值"""
    from src.cli.config_manager import get_config

    value = get_config(key)
    if value is not None:
        click.echo(f"{key} = {value}")
    else:
        click.echo(f"Key '{key}' not found")


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """设置配置值"""
    from src.cli.config_manager import set_config

    set_config(key, value)
    click.echo(f"Set {key} = {value}")


@config_group.command(name="list")
def config_list():
    """列出所有配置"""
    from src.cli.config_manager import get_config

    # TODO: Implement full config listing
    click.echo("Configuration:")
    click.echo(f"  API Key: {'*' * 8 if get_config('api_key') else 'not set'}")
    click.echo(f"  Model: {get_config('model', 'default')}")


@config_group.command(name="init")
@click.option("--force", is_flag=True, help="Force reinitialize")
def config_init(force: bool):
    """初始化配置"""
    config_dir = Path.home() / ".openyoung"
    config_file = config_dir / "config.yaml"

    if config_file.exists() and not force:
        click.echo(f"Config already exists at {config_file}")
        return

    config_dir.mkdir(parents=True, exist_ok=True)
    click.echo(f"Initialized config at {config_file}")
