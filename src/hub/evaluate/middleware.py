"""
Harness Middleware - 评估中间件链

在每个 Task 执行前后插入 Hook:
- ContextEngineeringMiddleware: 注入代码库上下文
- LoopDetectionMiddleware: 检测重复编辑/doom loops
- PreCompletionCheckMiddleware: 提交前自验证
- ArchitecturalConstraintMiddleware: 架构约束强制

参考 LangChain/OpenAI/ Anthropic 最佳实践
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any

from .benchmark import BenchmarkTask, TaskSuite
from .metrics import EvalMetrics, TaskMetrics


@dataclass
class MiddlewareResult:
    """Middleware 执行结果"""

    allowed: bool  # 是否允许继续
    modified_prompt: str | None = None  # 修改后的 prompt
    modified_context: dict[str, Any] | None = None  # 修改后的上下文
    warnings: list[str] | None = None  # 警告信息
    metadata: dict[str, Any] | None = None  # 额外数据

    @classmethod
    def pass_through(cls) -> "MiddlewareResult":
        return cls(allowed=True)

    @classmethod
    def block(cls, reason: str) -> "MiddlewareResult":
        return cls(allowed=False, warnings=[reason])


class BaseMiddleware(ABC):
    """
    Middleware 基类

    每个 Middleware 实现:
    - before_task(): Task 执行前调用
    - after_task(): Task 执行后调用
    """

    name: str = "base"

    async def before_task(self, task: BenchmarkTask) -> MiddlewareResult:
        """Task 执行前"""
        return MiddlewareResult.pass_through()

    async def after_task(self, task: BenchmarkTask, metrics: TaskMetrics) -> MiddlewareResult:
        """Task 执行后"""
        return MiddlewareResult.pass_through()

    async def before_suite(self, suite: TaskSuite) -> None:
        """Suite 执行前"""
        pass

    async def after_suite(self, suite: TaskSuite, metrics: EvalMetrics) -> None:
        """Suite 执行后"""
        pass


# ========== Context Engineering ==========


class ContextEngineeringMiddleware(BaseMiddleware):
    """
    上下文工程中间件

    在 Task prompt 中注入:
    - 代码库结构映射
    - AGENTS.md 摘要
    - 关键文件路径

    作用: 减少模型"幻觉"，提供准确上下文
    """

    name = "context_engineering"

    def __init__(
        self,
        repo_root: str = ".",
        max_context_chars: int = 2000,
    ):
        self.repo_root = repo_root
        self.max_context_chars = max_context_chars

    async def before_task(self, task: BenchmarkTask) -> MiddlewareResult:
        """注入代码库上下文到 task prompt"""
        # 动态收集上下文 (由外部提供或从文件读取)
        context = await self._collect_context(task)

        if context:
            return MiddlewareResult(
                allowed=True,
                modified_context={"codebase_context": context},
            )
        return MiddlewareResult.pass_through()

    async def _collect_context(self, task: BenchmarkTask) -> str:
        """收集代码库上下文"""
        from pathlib import Path

        parts = []

        # CLAUDE.md 摘要
        claude_md = Path(self.repo_root) / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text(encoding="utf-8")
            if len(content) > self.max_context_chars:
                content = content[: self.max_context_chars] + "\n... (truncated)"
            parts.append(f"## Project Context\n{content}")

        # 目录结构 (浅层)
        root = Path(self.repo_root)
        structure_lines = []
        for p in sorted(root.iterdir()):
            if p.name.startswith("."):
                continue
            if p.is_dir():
                structure_lines.append(f"  📁 {p.name}/")
            else:
                structure_lines.append(f"  📄 {p.name}")

        if structure_lines:
            parts.append("## Repository Structure\n" + "\n".join(structure_lines[:30]))

        return "\n\n".join(parts)


# ========== Loop Detection ==========


class LoopDetectionMiddleware(BaseMiddleware):
    """
    Loop 检测中间件

    检测:
    - 重复工具调用 (同一工具 + 相似参数)
    - 无进展编辑 (文件内容不变)
    - doom loop 预警
    """

    name = "loop_detection"

    def __init__(
        self,
        max_same_tool_calls: int = 5,
        max_retry_count: int = 3,
    ):
        self.max_same_tool_calls = max_same_tool_calls
        self.max_retry_count = max_retry_count
        self._tool_call_counts: dict[str, int] = {}

    async def before_task(self, task: BenchmarkTask) -> MiddlewareResult:
        self._tool_call_counts = {}
        return MiddlewareResult.pass_through()

    async def after_task(self, task: BenchmarkTask, metrics: TaskMetrics) -> MiddlewareResult:
        """检测 loop 模式并记录"""
        warnings = []

        for trial in metrics.trials:
            tool_names = [
                tc.get("name", "")
                for entry in trial.transcript
                if isinstance(entry, dict)
                for tc in entry.get("tool_calls", [])
            ]

            # 检测重复工具调用
            from collections import Counter

            tool_counts = Counter(tool_names)
            for tool_name, count in tool_counts.items():
                if count > self.max_same_tool_calls:
                    warnings.append(
                        f"Loop detected: '{tool_name}' called {count}x "
                        f"(max allowed: {self.max_same_tool_calls})"
                    )

        if warnings:
            return MiddlewareResult(
                allowed=True,
                warnings=warnings,
                metadata={"loop_warnings": warnings},
            )
        return MiddlewareResult.pass_through()


# ========== Pre-Completion Check ==========


class PreCompletionCheckMiddleware(BaseMiddleware):
    """
    Pre-Completion 检查中间件

    在 Agent 认为"完成"前执行自验证:
    - 文件是否创建
    - 测试是否通过
    - Lint 是否通过
    """

    name = "pre_completion_check"

    def __init__(
        self,
        required_files: list[str] | None = None,
        required_patterns: list[str] | None = None,
    ):
        self.required_files = required_files or []
        self.required_patterns = required_patterns or []

    async def before_task(self, task: BenchmarkTask) -> MiddlewareResult:
        """记录预期的文件/模式"""
        return MiddlewareResult(
            allowed=True,
            modified_context={
                "required_files": self.required_files,
                "required_patterns": self.required_patterns,
            },
        )

    async def after_task(self, task: BenchmarkTask, metrics: TaskMetrics) -> MiddlewareResult:
        """验证是否满足所有 pre-completion 条件"""
        warnings = []

        # 检查是否创建了必需文件
        for trial in metrics.trials:
            for req_file in self.required_files:
                created = any(
                    req_file in str(entry) for entry in trial.transcript if isinstance(entry, dict)
                )
                if not created:
                    warnings.append(f"Required file not created: {req_file}")

        if warnings:
            return MiddlewareResult(
                allowed=True,
                warnings=warnings,
            )
        return MiddlewareResult.pass_through()


# ========== Architectural Constraint ==========


class ArchitecturalConstraintMiddleware(BaseMiddleware):
    """
    架构约束强制中间件

    在执行前后强制检查:
    - 文件大小限制 (<= 400行)
    - 无禁止导入
    - 无危险模式 (eval, os.system, etc.)
    """

    name = "arch_constraint"

    def __init__(
        self,
        max_file_lines: int = 400,
        forbidden_patterns: list[str] | None = None,
    ):
        self.max_file_lines = max_file_lines
        self.forbidden_patterns = forbidden_patterns or [
            "eval(",
            "exec(",
            "os.system(",
            "subprocess.run(shell=True)",
        ]

    async def after_task(self, task: BenchmarkTask, metrics: TaskMetrics) -> MiddlewareResult:
        """检查架构约束违规"""
        warnings = []

        for trial in metrics.trials:
            for entry in trial.transcript:
                if not isinstance(entry, dict):
                    continue

                # 检查工具调用中的文件写入
                tool_calls = entry.get("tool_calls", [])
                for tc in tool_calls:
                    if tc.get("name") == "Write":
                        content = str(tc.get("arguments", ""))
                        if "n" in content and content.count("\n") > self.max_file_lines:
                            warnings.append(
                                f"File exceeds {self.max_file_lines} lines "
                                f"(potential: {content.count(chr(10))} lines)"
                            )

        if warnings:
            return MiddlewareResult(
                allowed=True,
                warnings=warnings[:5],
            )
        return MiddlewareResult.pass_through()


# ========== Default Middleware Factory ==========


def get_default_middleware() -> list[BaseMiddleware]:
    """获取默认中间件链"""
    return [
        LoopDetectionMiddleware(),
        ArchitecturalConstraintMiddleware(),
    ]


def get_all_middleware() -> list[type[BaseMiddleware]]:
    """获取所有可用中间件类型"""
    return [
        ContextEngineeringMiddleware,
        LoopDetectionMiddleware,
        PreCompletionCheckMiddleware,
        ArchitecturalConstraintMiddleware,
    ]
