"""
Code-Based Grader - 确定性检查
支持: unit_test, lint, security, tool_call, state_check, file_pattern, command
"""

import re
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseGrader, GraderOutput


class CodeGrader(BaseGrader):
    """Deterministic Code-Based Grader"""

    def __init__(self, config: Any):
        # config is always a GraderConfig from BaseGrader contract
        super().__init__(config)
        code_cfg = config.code_config
        self.check_type = code_cfg.check_type
        self.command = code_cfg.command
        self.expected_pattern = code_cfg.expected_pattern
        self.required_files = code_cfg.required_files or []
        self.forbidden_patterns = code_cfg.forbidden_patterns or []
        self.params = code_cfg.params or {}

    async def grade(
        self,
        task_id: str,
        transcript: list[dict[str, Any]],
        outcome: dict[str, Any],
        context: dict[str, Any],
    ) -> GraderOutput:
        """执行确定性检查"""
        import time

        start = time.perf_counter()

        try:
            working_dir = context.get("working_dir", "")

            if self.check_type == "unit_test":
                passed, score, details = await self._check_unit_test(working_dir)
            elif self.check_type == "lint":
                passed, score, details = await self._check_lint(working_dir)
            elif self.check_type == "security":
                passed, score, details = await self._check_security(working_dir)
            elif self.check_type == "tool_call":
                passed, score, details = self._check_tool_call(transcript)
            elif self.check_type == "state_check":
                passed, score, details = self._check_state(outcome, context)
            elif self.check_type == "file_pattern":
                passed, score, details = self._check_file_pattern(working_dir)
            elif self.check_type == "command":
                passed, score, details = await self._run_command(working_dir)
            else:
                passed, score, details = False, 0.0, f"Unknown check_type: {self.check_type}"

            elapsed_ms = (time.perf_counter() - start) * 1000

            return GraderOutput(
                grader_name=self.name,
                grader_type=GraderType.CODE_BASED,
                passed=passed,
                score=score,
                details=details,
                latency_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return GraderOutput(
                grader_name=self.name,
                grader_type=GraderType.CODE_BASED,
                passed=False,
                score=0.0,
                details=f"CodeGrader error: {e}",
                error=str(e),
                latency_ms=elapsed_ms,
            )

    async def _check_unit_test(self, working_dir: str) -> tuple[bool, float, str]:
        """运行单元测试"""
        if not self.command:
            return False, 0.0, "No test command configured"

        cmd = self.command.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=working_dir or None,
            )

            output = result.stdout + result.stderr
            passed = result.returncode == 0

            # 解析测试结果
            if not passed:
                # 尝试从输出中提取失败信息
                failed_match = re.search(r"(\d+) failed", output)
                if failed_match:
                    return False, 0.3, f"Tests failed: {failed_match.group(0)}"
                return False, 0.0, f"Test command failed (exit {result.returncode})"

            # 解析通过率
            passed_match = re.search(r"(\d+) passed", output)
            if passed_match:
                num_passed = int(passed_match.group(1))
                score = min(num_passed / max(num_passed, 1) * 0.5 + 0.5, 1.0)
                return True, score, f"{num_passed} tests passed"

            return True, 0.8, "Tests passed"

        except subprocess.TimeoutExpired:
            return False, 0.0, "Test timed out (>120s)"
        except FileNotFoundError:
            return False, 0.0, f"Command not found: {cmd[0]}"
        except Exception as e:
            return False, 0.0, f"Test execution error: {e}"

    async def _check_lint(self, working_dir: str) -> tuple[bool, float, str]:
        """运行 lint 检查"""
        if not self.command:
            return False, 0.0, "No lint command configured"

        cmd = self.command.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=working_dir or None,
            )

            output = result.stdout + result.stderr
            passed = result.returncode == 0

            if passed:
                return True, 1.0, "Lint passed"

            # 解析 lint 错误
            error_count = len([l for l in output.splitlines() if l.strip()])
            score = max(0.0, 1.0 - error_count * 0.05)

            return False, score, f"Lint errors ({error_count} issues)"

        except subprocess.TimeoutExpired:
            return False, 0.0, "Lint timed out (>60s)"
        except FileNotFoundError:
            return False, 0.0, f"Linter not found: {cmd[0]}"
        except Exception as e:
            return False, 0.0, f"Lint error: {e}"

    async def _check_security(self, working_dir: str) -> tuple[bool, float, str]:
        """安全检查 - 扫描禁止模式"""
        findings = []
        search_paths = self.params.get("search_paths", ["."])
        extensions = self.params.get("extensions", [".py", ".js", ".ts", ".sh"])

        for search_path in search_paths:
            base = Path(working_dir) if working_dir else Path.cwd()
            for ext in extensions:
                for f in base.rglob(f"*{ext}"):
                    # 跳过 node_modules, .venv 等
                    if any(
                        n in f.parts
                        for n in ("node_modules", ".venv", "venv", ".git", "__pycache__")
                    ):
                        continue
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        for pattern in self.forbidden_patterns:
                            if pattern in content:
                                line_num = content[: content.index(pattern)].count("\n") + 1
                                findings.append(
                                    f"{f.relative_to(base)}:{line_num}: forbidden '{pattern}'"
                                )
                    except OSError:
                        continue

        if findings:
            return False, 0.0, "Security issues found:\n  " + "\n  ".join(findings[:10])

        return True, 1.0, "No security issues detected"

    def _check_tool_call(self, transcript: list[dict[str, Any]]) -> tuple[bool, float, str]:
        """检查 transcript 中的工具调用"""
        if not self.expected_pattern:
            return True, 1.0, "No tool call pattern specified"

        # 从 transcript 中提取所有工具调用
        all_tools = []
        for entry in transcript:
            if isinstance(entry, dict):
                tool_calls = entry.get("tool_calls", [])
                for tc in tool_calls:
                    if isinstance(tc, dict):
                        name = tc.get("name", "")
                        all_tools.append(name)

        # 检查预期的工具是否被调用
        if self.expected_pattern in all_tools:
            return True, 1.0, f"Tool '{self.expected_pattern}' was called"

        return False, 0.0, f"Tool '{self.expected_pattern}' was NOT called. Called: {all_tools}"

    def _check_state(
        self, outcome: dict[str, Any], context: dict[str, Any]
    ) -> tuple[bool, float, str]:
        """检查最终环境状态"""
        expected = self.params.get("expected_state", {})

        if not expected:
            return True, 1.0, "No state assertions"

        violations = []
        for key, expected_val in expected.items():
            actual_val = outcome.get(key)
            if actual_val != expected_val:
                violations.append(f"{key}: expected {expected_val}, got {actual_val}")

        if violations:
            return False, 0.0, f"State violations: {'; '.join(violations)}"

        return True, 1.0, "State matches expectations"

    async def _check_file_pattern(self, working_dir: str) -> tuple[bool, float, str]:
        """文件模式检查"""
        base = Path(working_dir) if working_dir else Path.cwd()
        issues = []

        # 检查必需文件
        for req in self.required_files:
            if not (base / req).exists():
                issues.append(f"Required file/dir missing: {req}")

        # 检查禁止模式
        extensions = self.params.get("extensions", [".py"])
        for ext in extensions:
            for f in base.rglob(f"*{ext}"):
                if any(n in f.parts for n in ("node_modules", ".venv", ".git", "__pycache__")):
                    continue
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    for pattern in self.forbidden_patterns:
                        if pattern in content:
                            issues.append(f"Forbidden pattern '{pattern}' in {f.relative_to(base)}")
                except OSError:
                    continue

        if issues:
            return False, 0.0, "File pattern issues:\n  " + "\n  ".join(issues[:10])

        return True, 1.0, "All file patterns satisfied"

    async def _run_command(self, working_dir: str) -> tuple[bool, float, str]:
        """运行自定义命令"""
        if not self.command:
            return False, 0.0, "No command configured"

        cmd = self.command.split()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.params.get("timeout", 60),
                cwd=working_dir or None,
            )

            output = result.stdout + result.stderr

            # 如果配置了 forbidden_patterns，检查输出
            if self.forbidden_patterns:
                for pattern in self.forbidden_patterns:
                    if pattern in output:
                        return False, 0.0, f"Command output contains forbidden: '{pattern}'"

            passed = result.returncode == 0

            if passed:
                return True, 1.0, f"Command succeeded: {self.command}"
            else:
                # 提取错误信息
                error_lines = [l for l in output.splitlines() if l.strip()][:5]
                error_msg = "; ".join(error_lines) or f"Exit code {result.returncode}"
                return False, 0.0, f"Command failed: {error_msg}"

        except subprocess.TimeoutExpired:
            return False, 0.0, f"Command timed out (> {self.params.get('timeout', 60)}s)"
        except FileNotFoundError:
            return False, 0.0, f"Command not found: {cmd[0]}"
        except Exception as e:
            return False, 0.0, f"Command error: {e}"
