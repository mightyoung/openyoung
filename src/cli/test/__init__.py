"""
Test CLI Commands - test 子命令

运行 Agent 测试
"""

import asyncio

import click

from src.evaluation.test_framework import (
    AgentTestRunner,
    InputTester,
    OutputTester,
    RunnerConfig,
    TestDataManager,
)


@click.group("test")
def test_group():
    """Manage and run agent tests"""
    pass


@test_group.command("run")
@click.option("--suite", "-s", default="unit", help="Test suite (unit, integration, e2e)")
@click.option("--dataset", "-d", default="default", help="Test dataset name")
@click.option("--agent", "-a", default="default", help="Agent name to test")
@click.option("--parallel/--no-parallel", default=True, help="Run tests in parallel")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run_tests(suite, dataset, agent_name, parallel, verbose):
    """Run agent tests

    Examples:
        openyoung test run --suite unit
        openyoung test run -s integration -v
    """

    async def _run():
        from src.agents.young_agent import YoungAgent
        from src.config.loader import ConfigLoader

        # Load agent config
        try:
            loader = ConfigLoader()
            config = loader.load_agent(agent_name)
        except Exception as e:
            click.echo(f"Error loading agent: {e}", err=True)
            return

        # Create agent
        agent = YoungAgent(config)

        # Create testers
        input_tester = InputTester(agent)
        output_tester = OutputTester(agent)

        # Create runner
        config = RunnerConfig(
            parallel=parallel,
            verbose=verbose,
            timeout_seconds=60,
        )
        runner = AgentTestRunner(agent, config)

        # Load test data
        dm = TestDataManager()
        test_suite = dm.load_suite(suite, dataset)

        click.echo(f"[Test] Running suite: {suite}")
        click.echo(f"[Test] Test cases: {test_suite.size}")

        # Run tests
        report = await runner.run_suite(
            test_suite,
            input_tester=input_tester,
            output_tester=output_tester,
        )

        # Display results
        _display_report(report, verbose)

    asyncio.run(_run())


@test_group.command("list")
@click.option("--dataset", "-d", default="default", help="Dataset name")
def list_tests(dataset):
    """List available tests

    Example:
        openyoung test list
    """
    dm = TestDataManager()
    stats = dm.get_stats(dataset)

    click.echo(f"\nTest Dataset: {dataset}")
    click.echo(f"Total test cases: {stats['total']}\n")

    click.echo("By Task Type:")
    for task_type, count in stats["by_type"].items():
        click.echo(f"  {task_type}: {count}")

    click.echo("\nBy Difficulty:")
    for difficulty, count in stats["by_difficulty"].items():
        click.echo(f"  {difficulty}: {count}")


@test_group.command("suites")
def list_suites():
    """List available test suites"""
    dm = TestDataManager()

    click.echo("\nAvailable Test Suites:\n")

    for suite_name in ["unit", "integration", "e2e"]:
        suite = dm.load_suite(suite_name)
        click.echo(f"  {suite_name}: {suite.size} cases")


@test_group.command("case")
@click.argument("case_id")
@click.option("--agent", "-a", default="default", help="Agent name")
def run_case(case_id, agent_name):
    """Run a single test case

    Example:
        openyoung test case code_gen_001
    """

    async def _run():
        from src.agents.young_agent import YoungAgent
        from src.config.loader import ConfigLoader

        # Load agent
        loader = ConfigLoader()
        config = loader.load_agent(agent_name)
        agent = YoungAgent(config)

        # Load test case
        dm = TestDataManager()
        cases = dm.load_dataset()

        test_case = None
        for tc in cases:
            if tc.id == case_id:
                test_case = tc
                break

        if not test_case:
            click.echo(f"Test case not found: {case_id}")
            return

        # Run test
        input_tester = InputTester(agent)
        output_tester = OutputTester(agent)
        runner = AgentTestRunner(agent)

        result = await runner.run_case(
            test_case,
            input_tester=input_tester,
            output_tester=output_tester,
        )

        # Display result
        _display_result(result)

    asyncio.run(_run())


def _display_report(report, verbose=False):
    """Display test report"""
    click.echo("\n" + "=" * 50)
    click.echo("TEST REPORT")
    click.echo("=" * 50)

    # Summary
    pass_rate = report.pass_rate * 100
    status = "✅ PASSED" if report.success else "❌ FAILED"

    click.echo(f"\nStatus: {status}")
    click.echo(f"Pass Rate: {pass_rate:.1f}% ({report.passed}/{report.total_tests})")
    click.echo(f"Duration: {report.duration_ms}ms")

    # Scores
    click.echo("\nScores:")
    click.echo(f"  Input Understanding: {report.input_understanding_score:.2f}")
    click.echo(f"  Output Quality: {report.output_quality_score:.2f}")

    if verbose and report.results:
        click.echo("\nDetailed Results:")
        for result in report.results[:10]:  # Show first 10
            status = "✅" if result.passed else "❌"
            click.echo(f"  {status} {result.test_id}: {result.score:.2f}")


def _display_result(result):
    """Display single test result"""
    status = "✅ PASSED" if result.passed else "❌ FAILED"

    click.echo(f"\nTest: {result.test_id}")
    click.echo(f"Status: {status}")
    click.echo(f"Score: {result.score:.2f}")
    click.echo(f"Duration: {result.duration_ms}ms")

    if result.details:
        click.echo("\nDetails:")
        for key, value in result.details.items():
            if key != "output":  # Skip full output
                click.echo(f"  {key}: {value}")
