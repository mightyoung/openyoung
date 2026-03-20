"""
PEAS CLI - PEAS 命令行工具

提供 openyoung peas 命令:
- peas parse <file>: 解析 Markdown 文件
- peas profile <file>: 分析文档风格
- peas drift <result_file>: 检测偏离
"""

import json
from pathlib import Path

import click

from src.peas import (
    DriftDetector,
    DriftLevel,
    FeatureStatus,
    MarkdownParser,
    ParsedDocument,
    StyleProfiler,
    StyleProfile,
    VerificationStatus,
)


@click.group(name="peas")
def peas_group():
    """PEAS - Plan-Execution Alignment System

    用于解析设计文档、分析风格和检测偏离的工具。
    """
    pass


@peas_group.command(name="parse")
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def peas_parse(file: str, output_format: str) -> None:
    """Parse a Markdown design document.

    Parses the specified Markdown file and extracts:
    - Document title
    - Section structure
    - Feature points
    - Acceptance criteria

    Example:
        openyoung peas parse design.md
        openyoung peas parse design.md --format json
    """
    parser = MarkdownParser()

    try:
        result: ParsedDocument = parser.parse_file(file)

        if output_format == "json":
            output = {
                "title": result.title,
                "sections": result.sections,
                "feature_points": [
                    {
                        "id": fp.id,
                        "title": fp.title,
                        "priority": fp.priority.name,
                        "related_section": fp.related_section,
                        "acceptance_criteria": fp.acceptance_criteria,
                    }
                    for fp in result.feature_points
                ],
                "metadata": result.metadata,
            }
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            click.echo(f"# {result.title}")
            click.echo()

            if result.sections:
                click.echo("## Sections")
                for i, section in enumerate(result.sections, 1):
                    click.echo(f"  {i}. {section}")
                click.echo()

            click.echo(f"## Feature Points ({len(result.feature_points)})")
            for fp in result.feature_points:
                priority_marker = {
                    "MUST": "[M]",
                    "SHOULD": "[S]",
                    "COULD": "[C]",
                }.get(fp.priority.name, "")
                click.echo(f"  - {fp.id}: {fp.title} {priority_marker}")
                if fp.related_section:
                    click.echo(f"    Section: {fp.related_section}")
                if fp.acceptance_criteria:
                    for criteria in fp.acceptance_criteria[:3]:
                        click.echo(f"    - {criteria[:80]}...")
            click.echo()
            click.echo(f"Metadata: {result.metadata}")

    except Exception as e:
        click.echo(f"Error parsing file: {e}", err=True)
        raise SystemExit(1)


@peas_group.command(name="profile")
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def peas_profile(file: str, output_format: str) -> None:
    """Analyze document writing style.

    Analyzes the document's writing style including:
    - Document type (spec, api, guide, etc.)
    - Tone (formal, casual, technical, etc.)
    - Language (zh, en, mixed)
    - Sentence length
    - Technical terms density

    Example:
        openyoung peas profile design.md
        openyoung peas profile design.md --format json
    """
    profiler = StyleProfiler()

    try:
        content = Path(file).read_text(encoding="utf-8")
        profile: StyleProfile = profiler.analyze(content)

        if output_format == "json":
            output = {
                "doc_type": profile.doc_type.value,
                "tone": profile.tone.value,
                "language": profile.language,
                "avg_sentence_length": profile.avg_sentence_length,
                "has_numbered_sections": profile.has_numbered_sections,
                "uses_bullet_points": profile.uses_bullet_points,
                "technical_terms_density": profile.technical_terms_density,
                "code_examples_count": profile.code_examples_count,
                "section_depth": profile.section_depth,
                "consistency_score": profile.consistency_score,
            }
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            click.echo(f"# Style Profile: {Path(file).name}")
            click.echo()
            click.echo(f"  Document Type: {profile.doc_type.value}")
            click.echo(f"  Tone: {profile.tone.value}")
            click.echo(f"  Language: {profile.language}")
            click.echo(f"  Avg Sentence Length: {profile.avg_sentence_length:.1f} chars")
            click.echo(f"  Numbered Sections: {'Yes' if profile.has_numbered_sections else 'No'}")
            click.echo(f"  Uses Bullet Points: {'Yes' if profile.uses_bullet_points else 'No'}")
            click.echo(f"  Technical Terms Density: {profile.technical_terms_density:.2%}")
            click.echo(f"  Code Examples: {profile.code_examples_count}")
            click.echo(f"  Section Depth: {profile.section_depth}")
            click.echo(f"  Consistency Score: {profile.consistency_score:.2%}")

    except Exception as e:
        click.echo(f"Error analyzing file: {e}", err=True)
        raise SystemExit(1)


@peas_group.command(name="drift")
@click.argument("result_file", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
def peas_drift(result_file: str, output_format: str) -> None:
    """Detect drift from execution results.

    Analyzes a result file (JSON) containing feature statuses and
    generates a drift report showing alignment between execution
    and planning.

    Example:
        openyoung peas drift results.json
        openyoung peas drift results.json --format json
    """
    try:
        content = Path(result_file).read_text(encoding="utf-8")
        data = json.loads(content)

        statuses: list[FeatureStatus] = []
        for item in data.get("statuses", []):
            status_enum = VerificationStatus(item.get("status", "pending"))
            statuses.append(
                FeatureStatus(
                    req_id=item.get("req_id", "unknown"),
                    status=status_enum,
                    evidence=item.get("evidence", []),
                    notes=item.get("notes"),
                )
            )

        if not statuses:
            click.echo("No feature statuses found in result file", err=True)
            raise SystemExit(1)

        detector = DriftDetector()
        report = detector.detect(statuses)

        if output_format == "json":
            output = {
                "drift_score": report.drift_score,
                "level": report.level.name,
                "verified_count": report.verified_count,
                "failed_count": report.failed_count,
                "total_count": report.total_count,
                "alignment_rate": report.alignment_rate,
                "is_aligned": report.is_aligned,
                "recommendations": report.recommendations,
            }
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            level_emoji = {
                DriftLevel.NONE: "[OK]",
                DriftLevel.MINOR: "[~]",
                DriftLevel.MODERATE: "[!]",
                DriftLevel.SEVERE: "[!!]",
                DriftLevel.CRITICAL: "[!!!]",
            }.get(report.level, "[]")

            click.echo(f"# Drift Report {level_emoji}")
            click.echo()
            click.echo(f"  Drift Score: {report.drift_score:.1f}%")
            click.echo(f"  Level: {report.level.name}")
            click.echo(f"  Alignment Rate: {report.alignment_rate:.1f}%")
            click.echo()
            click.echo(f"  Verified: {report.verified_count}")
            click.echo(f"  Failed: {report.failed_count}")
            click.echo(f"  Total: {report.total_count}")
            click.echo()
            click.echo("  Recommendations:")
            for rec in report.recommendations:
                click.echo(f"    - {rec}")

    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in result file: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error detecting drift: {e}", err=True)
        raise SystemExit(1)
