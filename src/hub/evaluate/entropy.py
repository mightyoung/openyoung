"""
Entropy Management - 代码库熵管理

监控和管理代码库的"熵"(质量衰减、文档漂移、约束违反):

1. 文档一致性: CLAUDE.md / AGENTS.md 与实际代码的对齐度
2. 约束违规扫描: 文件大小限制、禁止导入等
3. 死代码检测: 未使用的导入、函数、类
4. 依赖审计: 未使用的依赖、版本过时
"""

from pathlib import Path

from .scanner import ConstraintScanner, DeadCodeScanner
from .types import EntropyIssue, EntropyReport, EntropyType, Severity


class EntropyManager:
    """
    熵管理器

    检测和追踪代码库质量衰减:
    - 文档漂移 (代码改了但文档没改)
    - 约束违反 (文件太大、禁止导入)
    - 死代码 (未使用的代码)
    - 依赖漂移 (未使用的依赖)
    """

    def __init__(
        self,
        repo_root: str = ".",
        max_file_lines: int = 400,
        forbidden_patterns: list[str] | None = None,
        exclude_dirs: list[str] | None = None,
    ):
        self.repo_root = Path(repo_root)
        self._constraint_scanner = ConstraintScanner(
            repo_root=self.repo_root,
            max_file_lines=max_file_lines,
            forbidden_patterns=forbidden_patterns,
            exclude_dirs=set(exclude_dirs or [
                ".git", ".venv", "node_modules", "__pycache__",
                ".pytest_cache", ".mypy_cache", ".ruff_cache",
                "dist", "build", ".eggs",
            ]),
        )
        self._dead_code_scanner = DeadCodeScanner(
            repo_root=self.repo_root,
            exclude_dirs=set(exclude_dirs or [
                ".git", ".venv", "node_modules", "__pycache__",
                ".pytest_cache", ".mypy_cache", ".ruff_cache",
                "dist", "build", ".eggs",
            ]),
        )

    def scan_all(self) -> EntropyReport:
        """扫描所有类型的熵问题"""
        report = EntropyReport(repo_root=str(self.repo_root))
        report.issues.extend(self._constraint_scanner.scan())
        report.total_files_scanned = self._constraint_scanner.total_files_scanned
        report.issues.extend(self._dead_code_scanner.scan())
        report.issues.extend(self._scan_doc_drift())
        report.issues.extend(self._scan_dependency_drift())
        return report

    def scan_constraints(self) -> list[EntropyIssue]:
        """仅扫描约束违规"""
        return self._constraint_scanner.scan()

    def scan_dead_code(self) -> list[EntropyIssue]:
        """仅扫描死代码"""
        return self._dead_code_scanner.scan()

    def scan_doc_drift(self) -> list[EntropyIssue]:
        """仅扫描文档漂移"""
        return self._scan_doc_drift()

    # ========== 文档漂移检测 ==========

    def _scan_doc_drift(self) -> list[EntropyIssue]:
        """检测文档与代码的不一致"""
        import re
        issues: list[EntropyIssue] = []

        claude_md = self.repo_root / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8", errors="ignore")
            file_refs = re.findall(r"`([^`]+`\.[a-z]+)`|`([\w./]+\.py)`", content)
            for match in file_refs:
                for ref in match:
                    if not ref:
                        continue
                    ref = ref.strip().lstrip("`")
                    ref_path = self.repo_root / ref
                    if not ref_path.exists() and "." in ref:
                        issues.append(EntropyIssue(
                            entropy_type=EntropyType.DOC_DRIFT,
                            severity=Severity.MEDIUM,
                            file_path="CLAUDE.md",
                            description=f"文档引用了不存在的文件: {ref}",
                            evidence=f"CLAUDE.md 引用了 {ref} 但该文件不存在",
                            recommendation="更新文档或创建缺失的文件",
                        ))

            agents_md = self.repo_root / "AGENTS.md"
            if agents_md.exists():
                agents_content = agents_md.read_text(encoding="utf-8", errors="ignore")
                agent_refs = re.findall(r"(?:src|docs)/[\w/]+\.py", agents_content)
                for ref in agent_refs:
                    ref_path = self.repo_root / ref
                    if not ref_path.exists():
                        issues.append(EntropyIssue(
                            entropy_type=EntropyType.DOC_DRIFT,
                            severity=Severity.LOW,
                            file_path="AGENTS.md",
                            description=f"AGENTS.md 引用了不存在的文件: {ref}",
                            evidence=f"AGENTS.md 引用了 {ref} 但该文件不存在",
                            recommendation="更新 AGENTS.md 以反映当前代码结构",
                        ))

        return issues

    # ========== 依赖漂移检测 ==========

    def _scan_dependency_drift(self) -> list[EntropyIssue]:
        """检测依赖与代码的不一致"""
        # Placeholder: cross-reference pyproject.toml deps with actual imports
        return []

    # ========== 报告生成 ==========

    def generate_report(self, report: EntropyReport) -> str:
        """生成熵管理报告"""
        lines = [
            f"# Entropy Report: {report.repo_root}",
            f"Scanned: {report.scanned_at.isoformat()}",
            f"Files: {report.total_files_scanned}",
            "",
            f"## Summary",
            f"- 🔴 Critical: {report.critical_count}",
            f"- 🟠 High: {report.high_count}",
            f"- 🟡 Medium: {report.medium_count}",
            f"- 🟢 Low: {report.low_count}",
            "",
            f"## Issues ({report.total_issues} total)",
        ]

        # 按类型分组
        by_type: dict[EntropyType, list[EntropyIssue]] = {}
        for issue in report.issues:
            by_type.setdefault(issue.entropy_type, []).append(issue)

        for etype, type_issues in by_type.items():
            lines.append(f"\n### {etype.value.replace('_', ' ').title()}")
            for issue in type_issues:
                severity_icon = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🟢",
                }[issue.severity]
                loc = f"{issue.file_path}"
                if issue.symbol_name:
                    loc += f"::{issue.symbol_name}"
                lines.append(f"- {severity_icon} **{issue.severity.value}**: {issue.description}")
                lines.append(f"  - Location: `{loc}`")
                lines.append(f"  - Evidence: {issue.evidence}")
                lines.append(f"  - Fix: {issue.recommendation}")

        return "\n".join(lines)
