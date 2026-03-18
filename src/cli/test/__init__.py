"""
Test CLI Commands - test 子命令

运行 Agent 测试 (DEPRECATED — 迁移到 Harness 评估系统)

测试功能已整合到 src/hub/evaluate/ 评估系统中。
"""

import click


@click.group("test")
def test_group():
    """Manage and run agent tests (DEPRECATED).

    Test functionality has migrated to the Harness evaluation system.
    Use 'openyoung harness run' for running task evaluations.
    """
    pass


@test_group.command("run")
@click.option("--suite", "-s", default="unit", help="Test suite (unit, integration, e2e)")
@click.option("--dataset", "-d", default="default", help="Test dataset name")
@click.option("--agent", "-a", default="default", help="Agent name to test")
@click.option("--parallel/--no-parallel", default=True, help="Run tests in parallel")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_tests(suite, dataset, agent_name, parallel, verbose):
    """Run agent tests (DEPRECATED).

    Use 'openyoung harness run' for the new evaluation system.
    The Harness system supports BenchmarkTask + Grader patterns.
    """
    click.echo("⚠️  'test run' is deprecated.")
    click.echo("   Use 'openyoung harness run' for task evaluation.")
    click.echo("   See: src/hub/evaluate/ for the new harness system.")


@test_group.command("list")
@click.option("--dataset", "-d", default="default", help="Dataset name")
def list_tests(dataset):
    """List available tests (DEPRECATED).

    Use the WebUI Dashboard to browse evaluation suites.
    """
    click.echo("⚠️  'test list' is deprecated.")
    click.echo("   Use WebUI Dashboard to browse evaluation suites.")
    click.echo("   Or use 'openyoung harness list' when implemented.")


@test_group.command("suites")
def list_suites():
    """List available test suites (DEPRECATED).

    Use the WebUI Dashboard to browse test suites.
    """
    click.echo("⚠️  'test suites' is deprecated.")
    click.echo("   Use WebUI Dashboard to browse suites.")
    click.echo("   Test suites are defined via BenchmarkTask in src/hub/evaluate/")


@test_group.command("case")
@click.argument("case_id")
@click.option("--agent", "-a", default="default", help="Agent name")
def run_case(case_id, agent_name):
    """Run a single test case (DEPRECATED).

    Use 'openyoung harness run --task <case_id>' for the new system.
    """
    click.echo("⚠️  'test case' is deprecated.")
    click.echo("   Use 'openyoung harness run' for individual task evaluation.")
    click.echo(f"   See: src/hub/evaluate/ for BenchmarkTask format.")
