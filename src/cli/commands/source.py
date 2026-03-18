"""
Source Command - 源/包仓库管理命令

提供 openyoung source 命令
"""

import click


@click.group(name="source")
def source_group():
    """Source/package repository management"""
    pass


@source_group.command(name="list")
def source_list():
    """List configured sources"""
    click.echo("Configured sources:")
    click.echo("  • default (PyPI)")
    # Note: Full source management coming soon


@source_group.command(name="add")
@click.argument("source_name")
@click.option("--url", "-u", help="Source URL")
def source_add(source_name: str, url: str):
    """Add a new source"""
    click.echo(f"Added source: {source_name}")
    if url:
        click.echo(f"  URL: {url}")
    click.echo("Note: Source persistence not yet implemented")
