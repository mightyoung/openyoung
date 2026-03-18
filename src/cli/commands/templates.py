"""
Templates Command - 模板市场命令

提供 openyoung templates 命令
"""

import click

from src.package_manager.template_registry import add_template, get_registry


@click.group(name="templates")
def templates_group():
    """Template marketplace commands"""
    pass


@templates_group.command(name="list")
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
    registry = get_registry()
    template_list = registry.list(tags=list(tag) if tag else None, sort_by=sort)

    if not template_list:
        click.echo("No templates found")
        return

    click.echo(f"Found {len(template_list)} templates:\n")
    for t in template_list:
        click.echo(f"  {t.name}")
        click.echo(f"    Source: {t.source}")
        click.echo(f"    Rating: {'*' * int(t.rating)} ({t.rating:.1f})")
        click.echo(f"    Installs: {t.installs}")
        if t.tags:
            click.echo(f"    Tags: {', '.join(t.tags)}")
        click.echo()


@templates_group.command(name="search")
@click.argument("query")
def templates_search(query):
    """Search templates"""
    registry = get_registry()
    results = registry.search(query)

    if not results:
        click.echo(f"No templates found matching '{query}'")
        return

    click.echo(f"Found {len(results)} templates:\n")
    for t in results:
        click.echo(f"  {t.name}")
        click.echo(f"    {t.description}")
        click.echo(f"    Rating: {'*' * int(t.rating)} ({t.rating:.1f})")
        click.echo()


@templates_group.command(name="add")
@click.argument("name")
@click.argument("source")
@click.option("--description", "-d", default="", help="Template description")
@click.option("--tags", "-t", multiple=True, help="Template tags")
@click.option("--author", "-a", default="", help="Template author")
def templates_add(name, source, description, tags, author):
    """Add a template to the registry"""
    template = add_template(
        name=name,
        source=source,
        description=description,
        tags=list(tags) if tags else None,
        author=author,
    )
    click.echo(f"[OK] Added template: {name}")


@templates_group.command(name="remove")
@click.argument("name")
def templates_remove(name):
    """Remove a template from the registry"""
    registry = get_registry()
    if registry.remove(name):
        click.echo(f"[OK] Removed template: {name}")
    else:
        click.echo(f"[Error] Template not found: {name}", err=True)


@templates_group.command(name="info")
@click.argument("name")
def templates_info(name):
    """Show template details"""
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
    click.echo(f"  Rating: {'*' * int(template.rating)} ({template.rating:.1f})")
    click.echo(f"  Installs: {template.installs}")
    click.echo(f"  Tags: {', '.join(template.tags) or 'None'}")
    click.echo(f"  Added: {template.added_at}")
    click.echo(f"  Updated: {template.updated_at}")
