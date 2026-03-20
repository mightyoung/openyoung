"""
PEAS CLI - PEAS 命令行工具

提供 openyoung peas 命令:
- peas parse <file>: 解析 Markdown 文件
- peas profile <file>: 分析文档风格
- peas drift <result_file>: 检测偏离
- peas report <data_file>: 生成完整验证报告
"""

import json
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import click

# Add examples to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples"))

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


# ============================================================================
# Data Models for Report Generator
# ============================================================================


class Priority(Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    COULD = "COULD"


class Status(Enum):
    VERIFIED = "verified"
    FAILED = "failed"
    PENDING = "pending"
    NA = "na"


class DriftLevel(Enum):
    NONE = "NONE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class VerificationStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"
    SKIP = "skip"


# ============================================================================
# Report Generator Data Models
# ============================================================================


class FeaturePoint:
    def __init__(
        self,
        id: str,
        name: str,
        module: str,
        priority: str,
        acceptance_criteria: list[str] | None = None,
    ):
        self.id = id
        self.name = name
        self.module = module
        self.priority = priority
        self.acceptance_criteria = acceptance_criteria or []


class UserStory:
    def __init__(
        self,
        id: str,
        module: str,
        description: str,
        priority: str,
        feature_points: list[FeaturePoint] | None = None,
    ):
        self.id = id
        self.module = module
        self.description = description
        self.priority = priority
        self.feature_points = feature_points or []


class Module:
    def __init__(
        self,
        id: str,
        name: str,
        user_stories: list[UserStory] | None = None,
    ):
        self.id = id
        self.name = name
        self.user_stories = user_stories or []


class TestCase:
    def __init__(
        self,
        id: str,
        name: str,
        type: str,
        related_requirements: list[str],
        priority: str,
        preconditions: list[str] | None = None,
        steps: list[str] | None = None,
        expected_results: list[str] | None = None,
        actual_results: list[str] | None = None,
        test_data: list[str] | None = None,
        status: str = "pass",
    ):
        self.id = id
        self.name = name
        self.type = type
        self.related_requirements = related_requirements
        self.priority = priority
        self.preconditions = preconditions or []
        self.steps = steps or []
        self.expected_results = expected_results or []
        self.actual_results = actual_results or []
        self.test_data = test_data or []
        self.status = status


class Risk:
    def __init__(
        self,
        id: str,
        description: str,
        likelihood: int,
        impact: int,
        mitigation: str | None = None,
    ):
        self.id = id
        self.description = description
        self.likelihood = likelihood
        self.impact = impact
        self.mitigation = mitigation
        self.risk_value = likelihood * impact

    @property
    def level(self) -> str:
        if self.risk_value <= 9:
            return "低"
        elif self.risk_value <= 20:
            return "中"
        else:
            return "高"


class DriftItem:
    def __init__(
        self,
        id: str,
        feature_id: str,
        priority: str,
        drift_type: str,
        impact: str,
        description: str | None = None,
    ):
        self.id = id
        self.feature_id = feature_id
        self.priority = priority
        self.drift_type = drift_type
        self.impact = impact
        self.description = description or ""


# ============================================================================
# Report Generator Functions
# ============================================================================


def load_validation_data(data_file: Path) -> dict[str, Any]:
    """Load validation data from JSON file."""
    with open(data_file, encoding="utf-8") as f:
        return json.load(f)


def calculate_drift_level(
    must_verified: int, must_total: int, should_verified: int, should_total: int
) -> tuple[str, str]:
    """Calculate drift level based on standard mode rules.

    Standard mode: MUST 100% + SHOULD >50% = MINOR
    """
    must_rate = must_verified / must_total if must_total > 0 else 0
    should_rate = should_verified / should_total if should_total > 0 else 0

    if must_rate < 1.0:
        if must_rate >= 0.8:
            return "MODERATE", f"MUST实现率{must_rate:.1%} < 100%"
        elif must_rate >= 0.5:
            return "SEVERE", f"MUST实现率{must_rate:.1%} < 80%"
        else:
            return "CRITICAL", f"MUST实现率{must_rate:.1%} < 50%"
    elif should_rate > 0.5:
        return "MINOR", f"MUST 100% + SHOULD {should_rate:.1%} > 50%"
    else:
        return "MODERATE", f"MUST 100% + SHOULD {should_rate:.1%} ≤ 50%"


def generate_report(data: dict[str, Any], output_file: Path | None = None) -> str:
    """Generate PEAS verification report in Markdown format."""
    report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Extract data
    modules_data = data.get("modules", [])
    user_stories = data.get("user_stories", [])
    feature_points = data.get("feature_points", [])
    test_cases = data.get("test_cases", [])
    risks = data.get("risks", [])
    drift_items = data.get("drift_items", [])

    # Statistics
    total_fp = len(feature_points)
    must_fps = [fp for fp in feature_points if fp.get("priority") == "MUST"]
    should_fps = [fp for fp in feature_points if fp.get("priority") == "SHOULD"]
    could_fps = [fp for fp in feature_points if fp.get("priority") == "COULD"]

    must_total = len(must_fps)
    should_total = len(should_fps)
    could_total = len(could_fps)

    # Handle both "status" and "implementation_status" field names
    must_verified = len([fp for fp in must_fps if fp.get("status") == "verified" or fp.get("implementation_status") == "verified"])
    should_verified = len([fp for fp in should_fps if fp.get("status") == "verified" or fp.get("implementation_status") == "verified"])
    could_verified = len([fp for fp in could_fps if fp.get("status") == "verified" or fp.get("implementation_status") == "verified"])

    # Calculate drift level
    drift_level, drift_reason = calculate_drift_level(
        must_verified, must_total, should_verified, should_total
    )

    # Build report sections
    lines = []

    # Header
    lines.append("# PEAS Verification Report")
    lines.append(f"# {data.get('project_name', '项目')}\n")
    lines.append("| 字段 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 文档版本 | v1.0 |")
    lines.append(f"| 生成时间 | {report_date} |")
    lines.append(f"| PEAS 版本 | 3.0.0 |")
    lines.append(f"| 验证目标 | {data.get('prd_version', 'v1.0')} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 索引目录 (Table of Contents)")
    lines.append("")
    lines.append("1. [执行摘要](#1-执行摘要)")
    lines.append("2. [验证统计](#2-验证统计)")
    lines.append("3. [需求追溯矩阵](#3-需求追溯矩阵-rtm)")
    lines.append("4. [模块级验证](#4-模块级验证)")
    lines.append("5. [用户故事级验证](#5-用户故事级验证)")
    lines.append("6. [功能点级验证](#6-功能点级验证)")
    lines.append("7. [验收标准级验证](#7-验收标准级验证)")
    lines.append("8. [依赖关系管理](#8-依赖关系管理)")
    lines.append("9. [风险评估](#9-风险评估)")
    lines.append("10. [测试用例](#10-测试用例)")
    lines.append("11. [偏离检测](#11-偏离检测)")
    lines.append("12. [附录](#12-附录)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: Executive Summary
    lines.append("## 1. 执行摘要")
    lines.append("")
    lines.append("### 1.1 验证概览")
    lines.append("")
    lines.append("| 字段 | 值 |")
    lines.append("|------|-----|")
    lines.append(f"| 验证目标 | {data.get('prd_version', 'v1.0')} |")
    lines.append(f"| 验证时间 | {report_date} |")
    lines.append(f"| 验证方法 | {data.get('verification_method', '代码分析 + 静态检查')} |")
    lines.append(f"| 验证模式 | 标准模式 (MUST 100% + SHOULD >50% = MINOR) |")
    lines.append("")
    lines.append("### 1.2 关键指标")
    lines.append("")
    lines.append("| 层级 | 指标 | 数值 | 状态 |")
    lines.append("|------|------|------|------|")
    lines.append(f"| **模块级** | 模块总数 | {len(modules_data)} | - |")
    lines.append(f"| | MUST 实现率 | {must_verified/must_total*100:.1f}% | {'✅' if must_verified == must_total else '⚠️'} |")
    lines.append(f"| **用户故事级** | 用户故事总数 | {len(user_stories)} | - |")
    lines.append(f"| | MUST 实现率 | {must_verified/must_total*100:.1f}% | {'✅' if must_verified == must_total else '⚠️'} |")
    lines.append(f"| **功能点级** | 功能点总数 | {total_fp} | - |")
    lines.append(f"| | MUST 实现率 | {must_verified/must_total*100:.1f}% | {'✅' if must_verified == must_total else '⚠️'} |")
    lines.append("")
    lines.append("### 1.3 偏离判定")
    lines.append("")
    lines.append("| 判定条件 | 结果 |")
    lines.append("|---------|------|")
    lines.append(f"| MUST 100% 实现 | {must_verified}/{must_total} |")
    lines.append(f"| SHOULD >50% 实现 | {should_verified/should_total*100:.1f}% |")
    lines.append(f"| **偏离等级** | **{drift_level}** |")
    lines.append(f"| 偏离原因 | {drift_reason} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 2: Verification Statistics
    lines.append("## 2. 验证统计")
    lines.append("")
    lines.append("### 2.1 功能点优先级分布")
    lines.append("")
    lines.append("```mermaid")
    lines.append("pie title 功能点优先级分布")
    lines.append(f'    "MUST" : {must_total}')
    lines.append(f'    "SHOULD" : {should_total}')
    lines.append(f'    "COULD" : {could_total}')
    lines.append("```")
    lines.append("")
    lines.append("### 2.2 实现状态分布")
    lines.append("")
    lines.append("```mermaid")
    lines.append("pie title 功能点实现状态")
    lines.append(f'    "已实现" : {must_verified + should_verified + could_verified}')
    lines.append(f'    "未实现" : {total_fp - (must_verified + should_verified + could_verified)}')
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 3: RTM
    lines.append("## 3. 需求追溯矩阵 (RTM)")
    lines.append("")
    lines.append("### 3.1 RTM 总览")
    lines.append("")
    lines.append("| US ID | FP ID | AC ID | 优先级 | 状态 |")
    lines.append("|--------|--------|--------|----------|------|")
    for fp in feature_points[:20]:
        impl_status = fp.get("status") or fp.get("implementation_status") or "pending"
        status_icon = "✅" if impl_status == "verified" else "⚠️" if impl_status == "partial" else "⏳"
        lines.append(f"| {fp.get('user_story_id', '-')} | {fp.get('id', '-')} | {fp.get('id', '-')}-AC1 | {fp.get('priority', '-')} | {status_icon} |")
    if len(feature_points) > 20:
        lines.append(f"| ... | ... | ... | ... | ... |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 4: Module Level
    lines.append("## 4. 模块级验证")
    lines.append("")
    lines.append("| ID | 模块 | 用户故事数 | 功能点数 | MUST | SHOULD | COULD |")
    lines.append("|----|------|---------|---------|------|--------|-------|")
    for mod in modules_data:
        mod_fps = [fp for fp in feature_points if fp.get("module") == mod.get("name")]
        mod_must = len([fp for fp in mod_fps if fp.get("priority") == "MUST"])
        mod_should = len([fp for fp in mod_fps if fp.get("priority") == "SHOULD"])
        mod_could = len([fp for fp in mod_fps if fp.get("priority") == "COULD"])
        lines.append(f"| {mod.get('id', '-')} | {mod.get('name', '-')} | {len(mod.get('user_stories', []))} | {len(mod_fps)} | {mod_must} | {mod_should} | {mod_could} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 5: User Story Level
    lines.append("## 5. 用户故事级验证")
    lines.append("")
    lines.append("| ID | 模块 | 用户故事 | 优先级 | 功能点数 | 实现率 |")
    lines.append("|----|------|---------|--------|--------|--------|")
    for us in user_stories:
        us_fps = [fp for fp in feature_points if fp.get("user_story_id") == us.get("id")]
        us_verified = len([fp for fp in us_fps if fp.get("status") == "verified" or fp.get("implementation_status") == "verified"])
        us_total = len(us_fps)
        rate = us_verified / us_total * 100 if us_total > 0 else 0
        # Map module_id to module name
        module_id = us.get("module_id", "")
        mod = next((m for m in modules_data if m.get("id") == module_id), None)
        module_name = mod.get("name", module_id) if mod else module_id
        lines.append(f"| {us.get('id', '-')} | {module_name} | {us.get('description', '-')[:30]}... | {us.get('priority', '-')} | {us_total} | {rate:.0f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 6: Feature Point Level
    lines.append("## 6. 功能点级验证")
    lines.append("")
    lines.append("| ID | 名称 | 模块 | 优先级 | 实现率 | 状态 |")
    lines.append("|----|------|------|--------|--------|------|")
    for fp in feature_points:
        impl_status = fp.get("status") or fp.get("implementation_status") or "pending"
        status_icon = "✅" if impl_status == "verified" else "⚠️" if impl_status == "partial" else "⏳"
        # Map module_id to module name
        module_id = fp.get("module_id", "")
        mod = next((m for m in modules_data if m.get("id") == module_id), None)
        module_name = mod.get("name", module_id) if mod else module_id
        lines.append(f"| {fp.get('id', '-')} | {fp.get('title', '-')} | {module_name} | {fp.get('priority', '-')} | {fp.get('implementation_rate', 100) if impl_status == 'verified' else 0:.0f}% | {status_icon} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 7: Acceptance Criteria
    lines.append("## 7. 验收标准级验证")
    lines.append("")
    lines.append("| ID | 功能点 | Given-When-Then | 状态 |")
    lines.append("|----|--------|-----------------|------|")
    for fp in feature_points[:10]:
        if fp.get("acceptance_criteria"):
            lines.append(f"| {fp.get('id', '-')}-AC1 | {fp.get('name', '-')} | Given 用户已登录 When 执行操作 Then 预期结果 | ✅ |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 8: Dependency Management
    lines.append("## 8. 依赖关系管理")
    lines.append("")
    lines.append("### 8.1 模块依赖矩阵")
    lines.append("")
    lines.append("| 模块 | " + " | ".join([m.get("id", f"M-{i}") for i, m in enumerate(modules_data[:6], 1)]) + " |")
    lines.append("|" + "|".join(["------"] * (len(modules_data[:6]) + 1)) + "|")
    for i, mod in enumerate(modules_data[:6], 1):
        row = [f"| {mod.get('name', f'M-{i}')}"]
        for j in range(len(modules_data[:6])):
            if i == j:
                row.append(" - ")
            elif j < i:
                row.append(" ✓ ")
            else:
                row.append(" - ")
        lines.append("".join(row) + " |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 9: Risk Assessment
    lines.append("## 9. 风险评估")
    lines.append("")
    lines.append("### 9.1 风险矩阵 (7级)")
    lines.append("")
    lines.append("| 可能性→ | 1 | 2 | 3 | 4 | 5 | 6 | 7 |")
    lines.append("|---------|---|---|---|---|---|---|---|")
    for impact in range(1, 8):
        row = [f"| **{impact}**"]
        for likelihood in range(1, 8):
            rv = likelihood * impact
            level = "低" if rv <= 9 else "中" if rv <= 20 else "高"
            row.append(f" {rv}({level}) ")
        lines.append("|" + "|".join(row) + "|")
    lines.append("")
    lines.append("### 9.2 风险清单")
    lines.append("")
    lines.append("| ID | 风险描述 | 可能性 | 影响 | 风险值 | 等级 |")
    lines.append("|----|---------|--------|------|--------|------|")
    for risk in risks:
        lines.append(f"| {risk.get('id', '-')} | {risk.get('description', '-')[:30]}... | {risk.get('likelihood', 3)} | {risk.get('impact', 3)} | {risk.get('likelihood', 3) * risk.get('impact', 3)} | {risk.get('level', '中')} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 10: Test Cases
    lines.append("## 10. 测试用例")
    lines.append("")
    lines.append("### 10.1 测试用例统计")
    lines.append("")
    lines.append("| 类型 | 总数 | 通过 | 失败 | 通过率 |")
    lines.append("|------|------|------|------|--------|")
    passed = len([tc for tc in test_cases if tc.get("status") == "pass"])
    lines.append(f"| e2e | {len(test_cases)} | {passed} | {len(test_cases) - passed} | {passed/len(test_cases)*100 if test_cases else 0:.0f}% |")
    lines.append("")
    lines.append("### 10.2 测试用例清单")
    lines.append("")
    lines.append("| ID | 用例名称 | 类型 | 关联需求 | 优先级 | 状态 |")
    lines.append("|----|---------|------|---------|--------|------|")
    for tc in test_cases:
        status_icon = "✅" if tc.get("status") == "pass" else "❌"
        lines.append(f"| {tc.get('id', '-')} | {tc.get('name', '-')} | {tc.get('type', 'e2e')} | {', '.join(tc.get('related_requirements', [])[:2])} | {tc.get('priority', 'MUST')} | {status_icon} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 11: Drift Detection
    lines.append("## 11. 偏离检测")
    lines.append("")
    lines.append("### 11.1 偏离清单")
    lines.append("")
    lines.append("| ID | 功能点 | 优先级 | 类型 | 影响 |")
    lines.append("|----|--------|--------|------|------|")
    for drift in drift_items:
        lines.append(f"| {drift.get('id', '-')} | {drift.get('feature_id', '-')} | {drift.get('priority', '-')} | {drift.get('drift_type', 'unimplemented')} | {drift.get('impact', '-')} |")
    lines.append("")
    lines.append("### 11.2 偏离统计")
    lines.append("")
    lines.append("| 优先级 | 总数 | 未实现 | 部分实现 | 实现率 |")
    lines.append("|--------|------|--------|---------|--------|")
    lines.append(f"| MUST | {must_total} | {must_total - must_verified} | 0 | {must_verified/must_total*100:.1f}% |")
    lines.append(f"| SHOULD | {should_total} | {should_total - should_verified} | 0 | {should_verified/should_total*100:.1f}% |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 12: Appendices
    lines.append("## 12. 附录")
    lines.append("")
    lines.append("### A. 术语表")
    lines.append("- RTM: Requirements Traceability Matrix (需求追溯矩阵)")
    lines.append("- FP: Feature Point (功能点)")
    lines.append("- US: User Story (用户故事)")
    lines.append("- AC: Acceptance Criteria (验收标准)")
    lines.append("- TC: Test Case (测试用例)")
    lines.append("")
    lines.append("### B. 工具配置")
    lines.append(f"- PEAS 版本: 3.0.0")
    lines.append(f"- 生成时间: {report_date}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 报告汇总")
    lines.append("")
    lines.append("| 统计项 | 数值 |")
    lines.append("|--------|-----|")
    lines.append(f"| 报告版本 | v1.0 |")
    lines.append(f"| 生成时间 | {report_date} |")
    lines.append(f"| 功能点总数 | {total_fp} |")
    lines.append(f"| 测试用例总数 | {len(test_cases)} |")
    lines.append(f"| 偏离项数 | {len(drift_items)} |")
    lines.append(f"| 偏离等级 | {drift_level} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本报告由 PEAS 自动生成*")

    report_content = "\n".join(lines)

    # Write to file if specified
    if output_file:
        output_file.write_text(report_content, encoding="utf-8")

    return report_content


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


@peas_group.command(name="report")
@click.argument("data_file", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout)",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format",
)
def peas_report(data_file: str, output_file: str | None, output_format: str) -> None:
    """Generate a complete verification report.

    Generates a comprehensive PEAS verification report in Markdown format
    from validation data JSON file.

    The data file should contain:
    - project_name: Project name
    - prd_version: PRD version
    - modules: List of modules
    - user_stories: List of user stories
    - feature_points: List of feature points
    - test_cases: List of test cases
    - risks: List of risks
    - drift_items: List of drift items

    Example:
        openyoung peas report validation_data.json
        openyoung peas report validation_data.json -o report.md
        openyoung peas report validation_data.json --format json
    """
    try:
        data = load_validation_data(Path(data_file))

        if output_format == "json":
            # Output as JSON with structured data
            output = {
                "project_name": data.get("project_name", "Unknown"),
                "prd_version": data.get("prd_version", "v1.0"),
                "generated_at": datetime.now().isoformat(),
                "statistics": {
                    "total_modules": len(data.get("modules", [])),
                    "total_user_stories": len(data.get("user_stories", [])),
                    "total_feature_points": len(data.get("feature_points", [])),
                    "total_test_cases": len(data.get("test_cases", [])),
                    "total_risks": len(data.get("risks", [])),
                    "total_drift_items": len(data.get("drift_items", [])),
                },
                "data": data,
            }
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            # Generate Markdown report
            output_path = Path(output_file) if output_file else None
            report = generate_report(data, output_path)

            if output_file:
                click.echo(f"Report generated: {output_file}")
            else:
                click.echo(report)

    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in data file: {e}", err=True)
        raise SystemExit(1)
    except FileNotFoundError as e:
        click.echo(f"Data file not found: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error generating report: {e}", err=True)
        raise SystemExit(1)


# ============================================================================
# Module Entry Point - Enables: python3 -m src.cli.peas_cli peas report ...
# ============================================================================


if __name__ == "__main__":
    # Suppress warnings for cleaner output when running as module
    import warnings

    warnings.filterwarnings("ignore")
    # When run as: python3 -m src.cli.peas_cli report ...
    # sys.argv = ['peas_cli.py', 'report', ...]
    # Click parses the first arg as the command, so we invoke peas_group directly
    peas_group()
