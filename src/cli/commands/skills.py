"""
Skills Command - Skill 管理命令

提供 openyoung skills 命令
"""

from pathlib import Path

import click

from src.skills.creator import create_skill, list_templates


@click.group(name="skills")
def skills_group():
    """Skill management commands"""
    pass


@skills_group.command(name="list")
@click.option("--category", "-c", help="Filter by category")
def skills_list(category: str):
    """List available skill templates"""
    try:
        templates = list_templates()
        if not templates:
            click.echo("No templates available")
            return

        click.echo("Available templates:")
        for template in templates:
            click.echo(f"  - {template}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@skills_group.command(name="create")
@click.argument("name")
@click.option("--template", "-t", default="code", help="Template to use")
@click.option("--output", "-o", default="skills", help="Output directory")
def skills_create(name: str, template: str, output: str):
    """Create a new skill from template"""
    try:
        click.echo(f"Creating skill '{name}' from template '{template}'...")
        skill = create_skill(name, template, Path(output))

        click.echo(f"Skill created at: {skill.path}")
        click.echo("Files:")
        for filename in skill.files:
            click.echo(f"  - {filename}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
