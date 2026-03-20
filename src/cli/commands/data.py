"""
Data Command - 数据管理命令

提供 openyoung data 命令
"""

import json

import click

from src.datacenter import (
    AccessLog,
    DataAnalytics,
    DataExporter,
    DataLicenseManager,
    RunTracker,
    StepRecorder,
    TeamShareManager,
)


@click.group(name="data")
def data_group():
    """Data management commands"""
    pass


@data_group.command(name="stats")
@click.option("--agent", "-a", default=None, help="Filter by agent ID")
@click.option("--days", "-d", default=7, type=int, help="Days to look back")
def data_stats(agent: str, days: int):
    """Show run statistics"""
    analytics = DataAnalytics()
    if agent:
        stats = analytics.get_agent_stats(agent, days)
        click.echo(f"Agent: {agent}")
        click.echo(f"Period: {days} days")
        click.echo(f"Total runs: {stats['total_runs']}")
        click.echo(f"Success: {stats['success']}")
        click.echo(f"Failed: {stats['failed']}")
        click.echo(f"Success rate: {stats['success_rate']:.1%}")
        click.echo(f"Avg duration: {stats['avg_duration']}s")
    else:
        dashboard = analytics.get_dashboard()
        summary = dashboard["summary"]
        click.echo("=== Dashboard ===")
        click.echo(f"Total agents: {summary['total_agents']}")
        click.echo(f"Total runs: {summary['total_runs']}")
        click.echo(f"Success rate: {summary['success_rate']:.1%}")
        click.echo(f"Avg duration: {summary['avg_duration']}s")


@data_group.command(name="runs")
@click.option("--agent", "-a", default=None, help="Filter by agent")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--limit", "-l", default=10, type=int, help="Limit results")
def data_runs(agent: str, status: str, limit: int):
    """List recent runs"""
    tracker = RunTracker()
    runs = tracker.list_runs(agent_id=agent, status=status, limit=limit)


@data_group.command(name="list")
@click.option("--agent", "-a", default=None, help="Filter by agent")
@click.option("--status", "-s", default=None, help="Filter by status")
@click.option("--limit", "-l", default=10, type=int, help="Limit results")
def data_list(agent: str, status: str, limit: int):
    """List recent runs (alias for 'runs')"""
    tracker = RunTracker()
    runs = tracker.list_runs(agent_id=agent, status=status, limit=limit)

    if not runs:
        click.echo("No runs found")
        return

    click.echo(f"Found {len(runs)} runs:")
    for run in runs:
        status_emoji = "Y" if run["status"] == "success" else "N"
        click.echo(
            f"  [{status_emoji}] {run['run_id'][:16]}... | {run['status']:8} | {run.get('task', 'N/A')[:40]}"
        )


@data_group.command(name="export")
@click.argument("output_dir")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "csv"]))
def data_export(output_dir: str, format: str):
    """Export data to directory"""
    exporter = DataExporter()
    files = exporter.export_full(output_dir)

    click.echo("Exported files:")
    for name, path in files.items():
        click.echo(f"  {name}: {path}")


@data_group.command(name="dashboard")
def data_dashboard():
    """Show dashboard data"""
    analytics = DataAnalytics()
    dashboard = analytics.get_dashboard()
    click.echo(json.dumps(dashboard, indent=2, default=str))


@data_group.command(name="steps")
@click.option("--run", "-r", required=True, help="Run ID")
@click.option("--limit", "-l", default=50, type=int, help="Limit results")
def data_steps(run: str, limit: int):
    """List steps for a run"""
    recorder = StepRecorder()
    steps = recorder.list_steps(run)

    if not steps:
        click.echo("No steps found")
        return

    click.echo(f"Found {len(steps)} steps:")
    for step in steps:
        status_emoji = (
            "Y" if step["status"] == "success" else "N" if step["status"] == "failed" else "R"
        )
        click.echo(
            f"  {status_emoji} {step['step_name']:20} | {step['status']:8} | {step.get('latency_ms', 0)}ms"
        )


@data_group.command(name="license")
@click.option("--list", "list_licenses", is_flag=True, help="List all licenses")
@click.option("--create", is_flag=True, help="Create a new license")
@click.option("--owner", "-o", default=None, help="Owner ID")
@click.option(
    "--type",
    "-t",
    "license_type",
    default="private",
    type=click.Choice(["public", "private", "team"]),
    help="License type",
)
def data_license(list_licenses: bool, create: bool, owner: str, license_type: str):
    """Manage data licenses"""
    mgr = DataLicenseManager()

    if list_licenses:
        licenses = mgr.list_licenses(
            owner_id=owner, license_type=license_type if license_type != "private" else None
        )
        if not licenses:
            click.echo("No licenses found")
            return
        click.echo(f"Found {len(licenses)} licenses:")
        for lic in licenses:
            click.echo(
                f"  {lic['license_id'][:16]}... | {lic['license_type']:8} | {lic['owner_id']}"
            )

    elif create:
        if not owner:
            click.echo("Error: --owner is required when creating a license", err=True)
            raise SystemExit(1)
        license_id = mgr.create_license(owner, license_type)
        click.echo(f"Created license: {license_id}")


@data_group.command(name="team")
@click.option("--list", "list_teams", is_flag=True, help="List teams")
@click.option("--members", is_flag=True, help="List team members")
@click.option("--team-id", "-t", default=None, help="Team ID")
@click.option("--create", is_flag=True, help="Create a team")
@click.option("--name", "-n", default=None, help="Team name")
@click.option("--owner", "-o", default=None, help="Team owner")
def data_team(list_teams: bool, members: bool, team_id: str, create: bool, name: str, owner: str):
    """Manage teams"""
    mgr = TeamShareManager()

    if list_teams:
        teams = mgr.list_teams(user_id=owner)
        if not teams:
            click.echo("No teams found")
            return
        click.echo(f"Found {len(teams)} teams:")
        for team in teams:
            click.echo(f"  {team['team_id']:20} | {team['name']:20} | {team['owner_id']}")

    elif members:
        if not team_id:
            click.echo("Error: --team-id is required", err=True)
            raise SystemExit(1)
        members_list = mgr.list_members(team_id)
        if not members_list:
            click.echo("No members found")
            return
        click.echo(f"Found {len(members_list)} members:")
        for member in members_list:
            click.echo(f"  {member['user_id']:20} | {member['role']}")

    elif create:
        if not team_id or not name or not owner:
            click.echo("Error: --team-id, --name, and --owner are required", err=True)
            raise SystemExit(1)
        mgr.create_team(team_id, name, owner)
        click.echo(f"Created team: {team_id}")


@data_group.command(name="access")
@click.option("--data-id", "-d", required=True, help="Data ID")
@click.option("--user", "-u", required=True, help="User ID")
@click.option("--type", "-t", default="read", help="Access type")
@click.option("--purpose", "-p", default="", help="Purpose")
def data_access(data_id: str, user: str, type: str, purpose: str):
    """Log data access"""
    log = AccessLog()
    log_id = log.log_access(data_id, user, type, purpose)
    click.echo(f"Logged access: {log_id}")
