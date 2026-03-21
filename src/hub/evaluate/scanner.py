"""
Entropy Scanners - 熵检测扫描器

各类型熵问题的专用扫描器:
- constraint_scanner: 文件大小、禁止模式
- dead_code_scanner: 未使用的导入、函数、类
- doc_drift_scanner: 文档与代码不一致
- dependency_scanner: 依赖漂移
"""

import re
from pathlib import Path

from .types import EntropyIssue, EntropyType, Severity


class ConstraintScanner:
    """约束违规扫描器"""

    def __init__(
        self,
        repo_root: Path,
        max_file_lines: int = 400,
        forbidden_patterns: list[str] | None = None,
        exclude_dirs: set[str] | None = None,
    ):
        self.repo_root = repo_root
        self.max_file_lines = max_file_lines
        self.total_files_scanned = 0
        self.forbidden_patterns = forbidden_patterns or [
            "eval(",
            "exec(",
            "os.system(",
            "subprocess.run(shell=True)",
            r'password\s*=\s*"',
            r'api_key\s*=\s*"',
            r"api_key\s*=\s*\'",
            r'secret\s*=\s*"',
            r'token\s*=\s*"',
            "SECRET",
        ]
        self.exclude_dirs = exclude_dirs or {
            ".git",
            ".venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".eggs",
        }

    def scan(self) -> list[EntropyIssue]:
        """扫描所有文件"""
        issues: list[EntropyIssue] = []
        py_files = list(self.repo_root.rglob("*.py"))
        self.total_files_scanned = len(py_files)

        for fpath in py_files:
            if any(ex in fpath.parts for ex in self.exclude_dirs):
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                rel_path = str(fpath.relative_to(self.repo_root))

                # 文件大小检查
                if len(lines) > self.max_file_lines:
                    issues.append(
                        EntropyIssue(
                            entropy_type=EntropyType.CONSTRAINT_VIOLATION,
                            severity=Severity.HIGH,
                            file_path=rel_path,
                            description=f"文件超过 {self.max_file_lines} 行限制",
                            evidence=f"当前 {len(lines)} 行",
                            recommendation=f"拆分文件，或将限制提升至 {self.max_file_lines}",
                        )
                    )

                # 禁止模式检查
                issues.extend(self._scan_forbidden(rel_path, content))

            except Exception as e:
                logger.warning(f"Failed to scan file {rel_path}: {e}")

        return issues

    def _scan_forbidden(self, rel_path: str, content: str) -> list[EntropyIssue]:
        """检查禁止模式"""
        issues: list[EntropyIssue] = []
        # 预处理: 移除 docstrings, comments, string literals
        stripped = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
        stripped = re.sub(r"'''.*?'''", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"#.*$", "", stripped, flags=re.MULTILINE)
        stripped = re.sub(r'"[^"]*"', "", stripped)
        stripped = re.sub(r"'[^']*'", "", stripped)

        for pattern in self.forbidden_patterns:
            if re.search(pattern, stripped):
                issues.append(
                    EntropyIssue(
                        entropy_type=EntropyType.CONSTRAINT_VIOLATION,
                        severity=Severity.CRITICAL,
                        file_path=rel_path,
                        description=f"禁止模式: {pattern}",
                        evidence=f"在 {rel_path} 中发现",
                        recommendation="移除或替换为安全替代方案",
                    )
                )
        return issues


class DeadCodeScanner:
    """死代码扫描器"""

    def __init__(self, repo_root: Path, exclude_dirs: set[str] | None = None):
        self.repo_root = repo_root
        self.exclude_dirs = exclude_dirs or {
            ".git",
            ".venv",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "dist",
            "build",
            ".eggs",
        }

    def scan(self) -> list[EntropyIssue]:
        """检测死代码"""
        issues: list[EntropyIssue] = []

        # 收集所有导入和定义
        all_imports: dict[str, dict[str, set[str]]] = {}
        all_definitions: dict[str, set[str]] = {}

        for fpath in self.repo_root.rglob("*.py"):
            if any(ex in fpath.parts for ex in self.exclude_dirs):
                continue
            if fpath.name.startswith("_"):
                continue

            rel = str(fpath.relative_to(self.repo_root))

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                all_imports[rel] = self._extract_imports(content)
                all_definitions[rel] = self._extract_definitions(content)
            except Exception as e:
                logger.debug(f"Failed to read file {rel}: {e}")

        # 检测未使用的导入
        for fpath_str, imports in all_imports.items():
            for module, names in imports.items():
                for name in names:
                    if name.startswith("_"):
                        continue
                    if not self._check_name_used(name, all_imports, all_definitions):
                        issues.append(
                            EntropyIssue(
                                entropy_type=EntropyType.DEAD_CODE,
                                severity=Severity.LOW,
                                file_path=fpath_str,
                                symbol_name=name,
                                description=f"可能未使用的导入: {module}.{name}",
                                recommendation="移除未使用的导入",
                            )
                        )

        return issues

    def _extract_imports(self, content: str) -> dict[str, set[str]]:
        imports: dict[str, set[str]] = {}
        stripped = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
        stripped = re.sub(r"'''.*?'''", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"#.*$", "", stripped, flags=re.MULTILINE)

        from_pat = re.compile(r"^from\s+([\w.]+)\s+import\s+(.+)$", re.MULTILINE)
        for m in from_pat.finditer(stripped):
            module = m.group(1)
            names_str = m.group(2)
            names = set(re.split(r"[,\s]+", names_str))
            names.discard("")
            imports[module] = names

        import_pat = re.compile(r"^import\s+([\w.]+)", re.MULTILINE)
        for m in import_pat.finditer(stripped):
            module = m.group(1)
            imports[module] = {module.split(".")[-1]}

        return imports

    def _extract_definitions(self, content: str) -> set[str]:
        definitions: set[str] = set()
        stripped = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
        stripped = re.sub(r"'''.*?'''", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"#.*$", "", stripped, flags=re.MULTILINE)

        func_pat = re.compile(r"^def\s+(\w+)\s*\(", re.MULTILINE)
        for m in func_pat.finditer(stripped):
            if not m.group(1).startswith("_"):
                definitions.add(m.group(1))

        class_pat = re.compile(r"^class\s+(\w+)", re.MULTILINE)
        for m in class_pat.finditer(stripped):
            if not m.group(1).startswith("_"):
                definitions.add(m.group(1))

        return definitions

    def _check_name_used(self, name: str, all_imports: dict, all_definitions: dict) -> bool:
        for imports in all_imports.values():
            for names in imports.values():
                if name in names:
                    return True
        return False
