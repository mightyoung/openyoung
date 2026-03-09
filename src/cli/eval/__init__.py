"""
Eval CLI Commands - eval 子命令

管理评估任务
"""

import click

from src.evaluation.hub import EvaluationHub
from src.evaluation.task_eval import TaskCompletionEval


@click.group("eval")
def eval_group():
    """Manage evaluations"""
    pass


@eval_group.command("run")
@click.argument("task_description")
@click.option("--expected", "-e", help="Expected result")
@click.option("--output", "-o", help="Actual output")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def run_eval(task_description, expected, output, format):
    """Run a task evaluation

    Examples:
        openyoung eval run "test task" --expected "expected output"
        openyoung eval run "test task" -e "expected" -o "actual"
    """
    import asyncio

    async def _run():
        eval = TaskCompletionEval()

        # 如果没有提供 expected，使用 task_description
        actual = output or task_description
        exp = expected or "completed"

        result = await eval.evaluate(
            task_description=task_description,
            expected_result=exp,
            actual_result=actual,
        )

        if format == "json":
            import json
            click.echo(json.dumps(result, indent=2, default=str))
        else:
            _display_eval_result(result)

    asyncio.run(_run())


@eval_group.command("list")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def list_metrics(format):
    """List all available evaluation metrics"""
    hub = EvaluationHub()

    metrics = list(hub._evaluators.keys())

    if not metrics:
        click.echo("No evaluation metrics found.")
        return

    if format == "json":
        import json
        click.echo(json.dumps(metrics, indent=2))
    else:
        click.echo("\nAvailable Evaluation Metrics:\n")
        for metric in metrics:
            click.echo(f"  • {metric}")
        click.echo()


@eval_group.command("register")
@click.argument("metric_name")
@click.option("--description", "-d", help="Metric description")
def register_metric(metric_name, description):
    """Register a new evaluation metric

    Example:
        openyoung eval register my-metric --description "My custom metric"
    """
    hub = EvaluationHub()

    # 创建一个简单的指标
    async def custom_metric(data):
        return 0.8  # 默认值

    try:
        hub.register_metric(metric_name, custom_metric)
        click.echo(f"✅ Metric registered: {metric_name}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)


@eval_group.command("history")
@click.option("--limit", "-n", default=10, help="Number of results to show")
@click.option("--format", "-f", type=click.Choice(["text", "json"]), default="text")
def eval_history(limit, format):
    """Show evaluation history

    Example:
        openyoung eval history --limit 20
    """
    # TODO: 从数据中心获取历史
    # 目前显示模拟数据

    sample_history = [
        {"task": "test task 1", "score": 0.95, "timestamp": "2026-03-08 10:00"},
        {"task": "test task 2", "score": 0.87, "timestamp": "2026-03-08 09:30"},
    ]

    if format == "json":
        import json
        click.echo(json.dumps(sample_history[:limit], indent=2, default=str))
    else:
        click.echo("\nEvaluation History:\n")
        for item in sample_history[:limit]:
            score = item.get("score", 0)
            score_str = f"{score:.0%}"

            # 颜色编码
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
    """Compare two evaluation results by index

    Example:
        openyoung eval compare 0 1
    """
    from src.evaluation.dashboard import EvalDashboard
    from src.evaluation.hub import EvaluationHub

    hub = EvaluationHub()
    dashboard = EvalDashboard(hub)

    results = hub.get_results()

    if not results:
        click.echo("❌ No evaluation results found.")
        click.echo("Run some evaluations first!")
        return

    # 检查索引是否有效
    max_id = len(results) - 1
    if eval_a < 0 or eval_a > max_id:
        click.echo(f"❌ Invalid index: {eval_a} (valid: 0-{max_id})")
        return
    if eval_b < 0 or eval_b > max_id:
        click.echo(f"❌ Invalid index: {eval_b} (valid: 0-{max_id})")
        return

    # 执行对比
    try:
        report = dashboard.export_comparison_report(eval_a, eval_b, format="text")
        click.echo(report)
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@eval_group.command("server")
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, help="Server port")
def eval_server(host, port):
    """Start the EvalHub server

    Example:
        openyoung eval server --host 0.0.0.0 --port 8000
    """
    import asyncio

    from src.evaluation.api import run_server

    click.echo(f"Starting EvalHub server on {host}:{port}")
    asyncio.run(run_server(host, port))


@eval_group.command("dashboard")
@click.option("--port", default=8050, help="Dashboard port")
def eval_dashboard(port):
    """Start the EvalHub dashboard (coming soon)

    Example:
        openyoung eval dashboard --port 8050
    """
    click.echo("\n📊 Evaluation Dashboard")
    click.echo("=" * 40)
    click.echo(f"Port: {port}")
    click.echo("\n⚠️  Dashboard feature coming soon!")
    click.echo("\nUse 'eval history' to view recent results.")
    click.echo("Use 'eval compare <id1> <id2>' to compare results.")


def _display_eval_result(result):
    """显示评估结果"""
    if not result:
        click.echo("No evaluation result.")
        return

    success = result.get("success", False)
    completion_rate = result.get("completion_rate", 0)

    # 颜色编码
    if success:
        status = click.style("✅ PASSED", fg="green")
    else:
        status = click.style("❌ FAILED", fg="red")

    click.echo(f"\nEvaluation Result: {status}")
    click.echo("=" * 40)
    click.echo(f"Completion Rate: {completion_rate:.0%}")

    if "scores" in result:
        click.echo("\nScores:")
        for key, value in result.get("scores", {}).items():
            click.echo(f"  {key}: {value:.2f}")

    if "feedback" in result:
        click.echo(f"\nFeedback: {result.get('feedback')}")
