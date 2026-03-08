"""
Test Reporter - 测试报告生成器

生成可读的测试报告
支持多种格式：text, json, html
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

from .models import TestReport, TestResult


class TestReporter:
    """测试报告生成器"""

    def __init__(self):
        pass

    def generate_text(self, report: TestReport) -> str:
        """生成文本格式报告"""
        lines = []
        lines.append("=" * 60)
        lines.append("AGENT TEST REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        lines.append("📊 SUMMARY")
        lines.append("-" * 40)
        lines.append(f"  Timestamp:    {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Agent:        {report.agent_name}")
        lines.append(f"  Dataset:      {report.dataset_name}")
        lines.append(f"  Total:        {report.total_tests}")
        lines.append(f"  Passed:       {report.passed} ✅")
        lines.append(f"  Failed:       {report.failed} ❌")
        lines.append(f"  Pass Rate:    {report.pass_rate:.1%}")
        lines.append(f"  Duration:     {report.duration_ms}ms")
        lines.append("")

        # Scores
        lines.append("📈 SCORES")
        lines.append("-" * 40)
        lines.append(f"  Input Understanding: {report.input_understanding_score:.2f}")
        lines.append(f"  Output Quality:      {report.output_quality_score:.2f}")
        lines.append("")

        # Status
        status = "✅ PASSED" if report.success else "❌ FAILED"
        lines.append(f"Overall Status: {status}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_json(self, report: TestReport) -> str:
        """生成 JSON 格式报告"""
        data = {
            "timestamp": report.timestamp.isoformat(),
            "summary": {
                "total": report.total_tests,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
                "pass_rate": report.pass_rate,
                "success": report.success,
            },
            "scores": {
                "input_understanding": report.input_understanding_score,
                "output_quality": report.output_quality_score,
            },
            "metadata": {
                "agent_name": report.agent_name,
                "dataset_name": report.dataset_name,
                "duration_ms": report.duration_ms,
            },
            "results": [
                {
                    "test_id": r.test_id,
                    "test_type": r.test_type.value,
                    "dimension": r.dimension.value,
                    "passed": r.passed,
                    "score": r.score,
                    "duration_ms": r.duration_ms,
                }
                for r in report.results
            ],
        }

        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_html(self, report: TestReport) -> str:
        """生成 HTML 格式报告"""
        pass_rate = report.pass_rate * 100
        status_color = "green" if report.success else "red"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Agent Test Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .score {{ font-size: 48px; font-weight: bold; color: {status_color}; }}
        .metric {{ display: inline-block; margin: 10px 20px; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
    </style>
</head>
<body>
    <h1>🤖 Agent Test Report</h1>

    <div class="summary">
        <div class="score">{pass_rate:.1f}%</div>
        <div>{report.passed}/{report.total_tests} tests passed</div>
        <div>Duration: {report.duration_ms}ms</div>
    </div>

    <h2>📊 Metrics</h2>
    <div>
        <div class="metric">
            <div class="metric-label">Input Understanding</div>
            <div class="metric-value">{report.input_understanding_score:.2f}</div>
        </div>
        <div class="metric">
            <div class="metric-label">Output Quality</div>
            <div class="metric-value">{report.output_quality_score:.2f}</div>
        </div>
    </div>

    <h2>📋 Test Results</h2>
    <table>
        <thead>
            <tr>
                <th>Test ID</th>
                <th>Type</th>
                <th>Dimension</th>
                <th>Score</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""

        for result in report.results:
            status_class = "passed" if result.passed else "failed"
            status_symbol = "✅" if result.passed else "❌"
            html += f"""
            <tr>
                <td>{result.test_id}</td>
                <td>{result.test_type.value}</td>
                <td>{result.dimension.value}</td>
                <td>{result.score:.2f}</td>
                <td class="{status_class}">{status_symbol}</td>
            </tr>
"""

        html += """
        </tbody>
    </table>
</body>
</html>
"""
        return html

    def save_report(
        self,
        report: TestReport,
        format: str = "text",
        filepath: Optional[str] = None,
    ) -> str:
        """保存报告到文件"""
        if format == "json":
            content = self.generate_json(report)
        elif format == "html":
            content = self.generate_html(report)
        else:
            content = self.generate_text(report)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        return content


class MetricsCalculator:
    """测试指标计算器

    计算各种测试指标
    """

    @staticmethod
    def calculate_percentile(values: list[float], percentile: int) -> float:
        """计算百分位数"""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    @staticmethod
    def calculate_trend(history: list[TestReport]) -> dict:
        """计算趋势

        Args:
            history: 历史报告列表

        Returns:
            dict: 趋势数据
        """
        if len(history) < 2:
            return {"trend": "insufficient_data"}

        # 提取指标
        pass_rates = [r.pass_rate for r in history]
        input_scores = [r.input_understanding_score for r in history]
        output_scores = [r.output_quality_score for r in history]

        # 计算趋势
        def calc_trend(values):
            first = values[0]
            last = values[-1]
            diff = last - first

            if diff > 0.1:
                return "improving"
            elif diff < -0.1:
                return "declining"
            else:
                return "stable"

        return {
            "pass_rate": {
                "current": pass_rates[-1],
                "trend": calc_trend(pass_rates),
                "change": pass_rates[-1] - pass_rates[0],
            },
            "input_score": {
                "current": input_scores[-1],
                "trend": calc_trend(input_scores),
                "change": input_scores[-1] - input_scores[0],
            },
            "output_score": {
                "current": output_scores[-1],
                "trend": calc_trend(output_scores),
                "change": output_scores[-1] - output_scores[0],
            },
        }
