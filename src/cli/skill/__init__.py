"""
Skill CLI Commands - skill 子命令

管理 OpenYoung 技能
"""

import click

from src.skills import SkillLoader


@click.group("skill")
def skill_group():
    """Manage skills"""
    pass


@skill_group.command("list")
@click.option("--format", "-f", type=click.Choice(["table", "json"]), default="table")
def list_skills(format):
    """List all available skills"""
    loader = SkillLoader()

    try:
        # 初始化加载器
        import asyncio
        asyncio.run(loader.initialize())

        # 获取所有 skill
        all_metadata = loader.list_all_metadata()

        if not all_metadata:
            click.echo("No skills found.")
            return

        if format == "json":
            import json
            click.echo(json.dumps(all_metadata, indent=2, default=str))
        else:
            _display_skills_table(all_metadata)

    except Exception as e:
        click.echo(f"Error listing skills: {e}", err=True)


@skill_group.command("add")
@click.argument("skill_path")
@click.option("--name", "-n", help="Skill name")
def add_skill(skill_path, name):
    """Add a skill from path or URL

    Examples:
        openyoung skill add ./my-skill
        openyoung skill add https://github.com/user/skill
    """
    loader = SkillLoader()

    try:
        import asyncio
        asyncio.run(loader.add_skill_path(skill_path, name))

        click.echo(f"✅ Skill added: {name or skill_path}")

    except Exception as e:
        click.echo(f"❌ Error adding skill: {e}", err=True)


@skill_group.command("remove")
@click.argument("skill_name")
@click.confirmation_option(prompt="Are you sure you want to remove this skill?")
def remove_skill(skill_name):
    """Remove a skill

    Example:
        openyoung skill remove my-skill
    """
    loader = SkillLoader()

    try:
        import asyncio
        asyncio.run(loader.remove_skill(skill_name))

        click.echo(f"✅ Skill removed: {skill_name}")

    except Exception as e:
        click.echo(f"❌ Error removing skill: {e}", err=True)


@skill_group.command("search")
@click.argument("query")
@click.option("--limit", "-n", default=5)
def search_skills(query, limit):
    """Search skills by name or description

    Example:
        openyoung skill search "code review"
    """
    loader = SkillLoader()

    try:
        import asyncio
        asyncio.run(loader.initialize())

        # 搜索 skills
        skills = asyncio.run(loader.find_skills_for_task(query))

        if not skills:
            click.echo(f"No skills found matching: {query}")
            return

        click.echo(f"\nFound {len(skills)} skills:\n")

        for skill in skills[:limit]:
            name = skill.get("name", "unknown")
            description = skill.get("description", "")[:60]
            click.echo(f"  • {name}")
            if description:
                click.echo(f"    {description}...")

    except Exception as e:
        click.echo(f"Error searching skills: {e}", err=True)


@skill_group.command("info")
@click.argument("skill_name")
def skill_info(skill_name):
    """Show detailed information about a skill

    Example:
        openyoung skill info my-skill
    """
    loader = SkillLoader()

    try:
        import asyncio
        asyncio.run(loader.initialize())

        # 获取 skill 元数据
        metadata = asyncio.run(loader.get_metadata(skill_name))

        if not metadata:
            click.echo(f"Skill not found: {skill_name}")
            return

        # 显示信息
        click.echo(f"\nSkill: {metadata.get('name', skill_name)}")
        click.echo("=" * 40)

        if metadata.get("description"):
            click.echo(f"\nDescription: {metadata.get('description')}")

        if metadata.get("version"):
            click.echo(f"Version: {metadata.get('version')}")

        if metadata.get("author"):
            click.echo(f"Author: {metadata.get('author')}")

        if metadata.get("tags"):
            click.echo(f"Tags: {', '.join(metadata.get('tags', []))}")

        if metadata.get("commands"):
            click.echo("\nCommands:")
            for cmd in metadata.get("commands", []):
                click.echo(f"  • {cmd}")

    except Exception as e:
        click.echo(f"Error getting skill info: {e}", err=True)


def _display_skills_table(skills):
    """以表格形式显示 skills"""
    if not skills:
        click.echo("No skills found.")
        return

    click.echo(f"\nAvailable Skills ({len(skills)}):\n")

    for skill in skills:
        name = skill.get("name", "unknown")
        version = skill.get("version", "N/A")
        description = skill.get("description", "")[:50]

        click.echo(f"  {name} (v{version})")
        if description:
            click.echo(f"    {description}")
        click.echo()
