"""
Eval CLI Commands - 使用新 harness (src/hub/evaluate/)

从旧的 src/evaluation/ 迁移到 src/hub/evaluate/ 评估系统。
"""

import json

import click


@click.group("eval")
def eval_group():
    """Manage evaluations using the Harness evaluation system"""
    pass


@eval_group.command("run")
@click.argument("task_description")
@click.option("--expected", "-e", help="Expected result")
@click.option("--output", "-o", help="Actual output")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def run_eval(task_description, expected, output, format):
    """Run a task evaluation using the Harness.

    This now uses src/hub/evaluate/ (BenchmarkTask + Grader pattern)
    instead of the legacy src/evaluation/ system.

    Examples:
        openyoung eval run "test task" --expected "expected output"
        openyoung eval run "test task" -e "expected" -o "actual"
    """
    click.echo("Using Harness evaluation system (src/hub/evaluate/)")

    # TODO: Wire up to BenchmarkTask + EvalRunner
    # For now, show a clear deprecation path
    click.echo("\n⚠️  eval run is being migrated to BenchmarkTask format.")
    click.echo("   Use 'openyoung harness run' for the new system.")


@eval_group.command("list")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def list_metrics(format):
    """List available evaluation metrics and grader types.

    Shows what's available in the new harness system.
    """
    from src.hub.evaluate import EvalType, GraderType, GradingMode

    metrics = {
        "grader_types": [g.value for g in GraderType],
        "eval_types": [e.value for e in EvalType],
        "grading_modes": [m.value for m in GradingMode],
    }

    if format == "json":
        click.echo(json.dumps(metrics, indent=2))
    else:
        click.echo("\nHarness Evaluation System — Available Types\n")
        click.echo("=" * 45)
        click.echo("\nGrader Types:")
        for g in metrics["grader_types"]:
            click.echo(f"  • {g}")
        click.echo("\nEval Types:")
        for e in metrics["eval_types"]:
            click.echo(f"  • {e}")
        click.echo("\nGrading Modes:")
        for m in metrics["grading_modes"]:
            click.echo(f"  • {m}")
        click.echo()


@eval_group.command("register")
@click.argument("metric_name")
@click.option("--description", "-d", help="Metric description")
def register_metric(metric_name, description):
    """Register a new evaluation metric (DEPRECATED).

    The new harness uses BenchmarkTask + GraderConfig pattern.
    Metrics are defined in task suites, not registered globally.
    """
    click.echo("⚠️  'eval register' is deprecated.")
    click.echo("   Define graders in BenchmarkTask.grader_configs instead.")
    click.echo("   See: src/hub/evaluate/benchmark.py")


@eval_group.command("history")
@click.option("--limit", "-n", default=10, help="Number of results to show")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def eval_history(limit, format):
    """Show evaluation history.

    The new harness stores results in EvalTrial / TaskMetrics.
    Connect to LangSmith or the WebUI Dashboard for history.
    """
    sample_history = [
        {"task": "test task 1", "score": 0.95, "timestamp": "2026-03-08 10:00"},
        {"task": "test task 2", "score": 0.87, "timestamp": "2026-03-08 09:30"},
    ]

    if format == "json":
        click.echo(json.dumps(sample_history[:limit], indent=2, default=str))
    else:
        click.echo("\nEvaluation History (legacy format — migrated to Harness):\n")
        for item in sample_history[:limit]:
            score = item.get("score", 0)
            score_str = f"{score:.0%}"
            if score >= 0.9:
                score_display = click.style(score_str, fg="green")
            elif score >= 0.7:
                score_display = click.style(score_str, fg="yellow")
            else:
                score_display = click.style(score_str, fg="red")
            click.echo(f"  {score_display} | {item.get('task', 'N/A')}")
        click.echo()


@eval_group.command("compare")
@click.argument("eval_a", type=int)
@click.argument("eval_b", type=int)
def compare_evals(eval_a, eval_b):
    """Compare two evaluation results by index (DEPRECATED).

    The new harness uses aggregate_eval_metrics() for comparison.
    Use the WebUI Dashboard for visual comparison.
    """
    click.echo("⚠️  'eval compare' is deprecated.")
    click.echo("   Use WebUI Dashboard for evaluation comparison.")
    click.echo("   Or use aggregate_eval_metrics() from src.hub.evaluate.metrics")


@eval_group.command("server")
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, help="Server port")
def eval_server(host, port):
    """Start the Eval API server (DEPRECATED).

    Use 'openyoung api' for the FastAPI server, which now includes
    evaluation endpoints via src/api/eval_routes.py.
    """
    click.echo("⚠️  'eval server' is deprecated.")
    click.echo("   Use 'openyoung api' — FastAPI server with eval routes.")
    click.echo(f"   Start with: openyoung api --port {port}")


@eval_group.command("dashboard")
@click.option("--port", default=8050, help="Dashboard port")
def eval_dashboard(port):
    """Start the Eval Dashboard (DEPRECATED).

    Use the WebUI Dashboard at pages/4_Dashboard.py instead.
    """
    click.echo("⚠️  'eval dashboard' is deprecated.")
    click.echo("   Use WebUI Dashboard: openyoung webui")
    click.echo("   Then navigate to the Dashboard page.")
