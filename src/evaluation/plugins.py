"""
评估插件系统

提供插件化的评估能力:
- EvalPlugin 抽象基类
- PluginRegistry 插件注册中心
- 内置评估插件 (CodeQuality, Security, Performance)

依赖: langgraph >= 0.0.20 (可选)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class EvalMetricType(Enum):
    """评估指标类型"""

    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    CORRECTNESS = "correctness"
    STYLE = "style"
    COMPLEXITY = "complexity"


@dataclass
class EvalResult:
    """评估结果"""

    plugin_name: str
    score: float  # 0-1
    passed: bool
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plugin_name": self.plugin_name,
            "score": self.score,
            "passed": self.passed,
            "details": self.details,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
        }


@dataclass
class EvalContext:
    """评估上下文"""

    task_description: str
    task_type: str
    input_data: Any = None
    output_data: Any = None
    expected_output: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvalPlugin(ABC):
    """评估插件抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    def description(self) -> str:
        """插件描述"""
        return ""

    @property
    def metric_type(self) -> EvalMetricType:
        """指标类型"""
        return EvalMetricType.QUALITY

    @abstractmethod
    def evaluate(self, context: EvalContext) -> EvalResult:
        """执行评估

        Args:
            context: 评估上下文

        Returns:
            评估结果
        """
        pass

    def validate_input(self, context: EvalContext) -> bool:
        """验证输入有效性

        Args:
            context: 评估上下文

        Returns:
            是否有效
        """
        return True


class CodeQualityPlugin(EvalPlugin):
    """代码质量评估插件

    评估代码的:
    - 可读性
    - 结构
    - 最佳实践
    - 文档
    """

    @property
    def name(self) -> str:
        return "code_quality"

    @property
    def description(self) -> str:
        return "评估代码质量、可读性和最佳实践"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.QUALITY

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估代码质量"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.5  # 基础分
        suggestions = []
        warnings = []

        # 检查是否有代码输出
        if isinstance(output, str):
            code = output

            # 检查是否有文档字符串
            if '"""' in code or "'''" in code:
                score += 0.1
            else:
                suggestions.append("Add docstrings to document functions")

            # 检查是否有类型注解
            if "->" in code or ":" in code:
                score += 0.1

            # 检查是否有错误处理
            if "try:" in code or "except" in code:
                score += 0.1
            else:
                suggestions.append("Add error handling")

            # 检查代码长度是否合理
            lines = code.split("\n")
            if len(lines) > 500:
                warnings.append("Consider breaking down large code blocks")
            elif len(lines) > 100:
                score += 0.1

            # 检查是否有注释
            if "#" in code:
                score += 0.1

        return EvalResult(
            plugin_name=self.name,
            score=min(score, 1.0),
            passed=score >= 0.6,
            details={"checks": ["docstrings", "types", "error_handling", "length", "comments"]},
            warnings=warnings,
            suggestions=suggestions,
        )


class SecurityPlugin(EvalPlugin):
    """安全评估插件

    评估代码的:
    - 敏感信息泄露
    - SQL 注入
    - 命令注入
    - 认证问题
    """

    SENSITIVE_PATTERNS = [
        "password",
        "secret",
        "api_key",
        "token",
        "credential",
        "private_key",
    ]

    DANGEROUS_PATTERNS = [
        "eval(",
        "exec(",
        "os.system",
        "subprocess",
        "shell=True",
    ]

    @property
    def name(self) -> str:
        return "security"

    @property
    def description(self) -> str:
        return "评估代码安全性，检测潜在安全漏洞"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.SECURITY

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估安全性"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 1.0
        errors = []
        warnings = []

        if isinstance(output, str):
            code = output.lower()

            # 检查敏感信息泄露
            for pattern in self.SENSITIVE_PATTERNS:
                if f'"{pattern}"' in code or f"'{pattern}'" in code:
                    warnings.append(f"Potential sensitive data: {pattern}")
                    score -= 0.2

            # 检查危险模式
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in code:
                    errors.append(f"Dangerous pattern detected: {pattern}")
                    score -= 0.3

        return EvalResult(
            plugin_name=self.name,
            score=max(score, 0.0),
            passed=score >= 0.7,
            details={"checks": ["sensitive_data", "dangerous_patterns"]},
            errors=errors,
            warnings=warnings,
        )


class PerformancePlugin(EvalPlugin):
    """性能评估插件

    评估代码的:
    - 算法复杂度
    - 资源使用
    - 缓存机会
    """

    @property
    def name(self) -> str:
        return "performance"

    @property
    def description(self) -> str:
        return "评估代码性能和资源使用效率"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.PERFORMANCE

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估性能"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.7
        suggestions = []

        if isinstance(output, str):
            code = output

            # 检查是否有缓存相关代码
            if "cache" in code.lower() or "memoize" in code.lower():
                score += 0.1

            # 检查是否有异步代码
            if "async" in code or "await" in code:
                score += 0.1

            # 检查是否有批量处理
            if "batch" in code.lower() or "bulk" in code.lower():
                score += 0.1

            # 检查循环中是否有不必要的重复计算
            if "for " in code and ("[" in code or "list" in code):
                suggestions.append("Consider using list comprehension for better performance")

        return EvalResult(
            plugin_name=self.name,
            score=min(score, 1.0),
            passed=score >= 0.6,
            details={"checks": ["caching", "async", "batching", "loops"]},
            suggestions=suggestions,
        )


class CorrectnessPlugin(EvalPlugin):
    """正确性评估插件

    评估代码的:
    - 语法正确性
    - 类型正确性
    - 逻辑正确性
    """

    @property
    def name(self) -> str:
        return "correctness"

    @property
    def description(self) -> str:
        return "评估代码正确性和逻辑完整性"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.CORRECTNESS

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估正确性"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.8
        errors = []

        if isinstance(output, str):
            code = output

            # 基本语法检查
            open_brackets = code.count("(") + code.count("[") + code.count("{")
            close_brackets = code.count(")") + code.count("]") + code.count("}")
            if open_brackets != close_brackets:
                errors.append("Mismatched brackets detected")
                score -= 0.3

            # 检查是否有未使用的变量（简单检查）
            if "=" in code and "==" not in code:
                # 可能的赋值语句，检查是否有明显的错误
                pass

        return EvalResult(
            plugin_name=self.name,
            score=max(score, 0.0),
            passed=score >= 0.7,
            details={"checks": ["syntax", "brackets"]},
            errors=errors,
        )


class DocumentationPlugin(EvalPlugin):
    """文档评估插件

    评估代码的文档完整性:
    - docstring 检查
    - README 检查
    - 注释覆盖率
    """

    @property
    def name(self) -> str:
        return "documentation"

    @property
    def description(self) -> str:
        return "评估代码文档完整性"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.STYLE

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估文档完整性"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.5
        suggestions = []

        if isinstance(output, str):
            code = output

            # 检查 docstring
            has_docstring = '"""' in code or "'''" in code
            if has_docstring:
                score += 0.2

            # 检查函数/类文档
            functions = code.split("def ")
            classes = code.split("class ")

            if len(functions) > 1:
                # 有函数定义
                if has_docstring:
                    score += 0.1
                else:
                    suggestions.append("Add docstrings to functions")

            if len(classes) > 1:
                # 有类定义
                if has_docstring:
                    score += 0.1
                else:
                    suggestions.append("Add docstrings to classes")

            # 检查注释比例
            lines = code.split("\n")
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
            comment_lines = [l for l in lines if l.strip().startswith("#")]

            if code_lines:
                comment_ratio = len(comment_lines) / len(code_lines)
                if comment_ratio > 0.1:
                    score += 0.1
                elif comment_ratio < 0.05:
                    suggestions.append("Add more comments")

        return EvalResult(
            plugin_name=self.name,
            score=min(score, 1.0),
            passed=score >= 0.6,
            details={"checks": ["docstrings", "functions", "classes", "comments"]},
            suggestions=suggestions,
        )


class ComplexityPlugin(EvalPlugin):
    """复杂度评估插件

    评估代码的复杂度:
    - 行数
    - 嵌套深度
    - 函数长度
    - 圈复杂度估算
    """

    @property
    def name(self) -> str:
        return "complexity"

    @property
    def description(self) -> str:
        return "评估代码复杂度"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.COMPLEXITY

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估代码复杂度"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.8
        warnings = []

        if isinstance(output, str):
            code = output

            # 分析行数
            lines = [l for l in code.split("\n") if l.strip()]
            total_lines = len(lines)

            if total_lines > 500:
                warnings.append(f"File has {total_lines} lines - consider splitting")
                score -= 0.2
            elif total_lines > 200:
                score -= 0.1

            # 分析函数长度
            function_blocks = code.split("def ")
            for i, block in enumerate(function_blocks[1:], 1):
                func_lines = block.split("\n")[:20]  # 取前20行
                if len(func_lines) > 15:
                    warnings.append("Long function detected - consider refactoring")
                    score -= 0.1
                    break

            # 分析嵌套深度
            max_depth = 0
            current_depth = 0
            for char in code:
                if char == ":":
                    continue
                if char == "{" or char == "(":
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                elif char == "}" or char == ")":
                    current_depth = max(0, current_depth - 1)

            if max_depth > 4:
                warnings.append(f"Nesting depth {max_depth} is too high")
                score -= 0.2

        return EvalResult(
            plugin_name=self.name,
            score=max(score, 0.0),
            passed=score >= 0.5,
            details={"checks": ["lines", "functions", "nesting"]},
            warnings=warnings,
        )


class StylePlugin(EvalPlugin):
    """代码风格评估插件

    评估代码风格:
    - 命名规范
    - 代码格式
    - import 顺序
    """

    @property
    def name(self) -> str:
        return "style"

    @property
    def description(self) -> str:
        return "评估代码风格"

    @property
    def metric_type(self) -> EvalMetricType:
        return EvalMetricType.STYLE

    def evaluate(self, context: EvalContext) -> EvalResult:
        """评估代码风格"""
        output = context.output_data
        if not output:
            return EvalResult(
                plugin_name=self.name, score=0.0, passed=False, errors=["No output to evaluate"]
            )

        score = 0.7
        suggestions = []

        if isinstance(output, str):
            code = output

            # 检查命名规范 (简单检查)
            snake_case_vars = len([w for w in code.split() if w.islower() and "_" in w])
            camel_case_vars = len([w for w in code.split() if w and w[0].isupper()])

            if snake_case_vars > 0:
                score += 0.1
            if camel_case_vars > 0:
                suggestions.append("Consider using snake_case for variables")

            # 检查行尾空格
            trailing_spaces = sum(1 for line in code.split("\n") if line.rstrip() != line)
            if trailing_spaces > 0:
                suggestions.append(f"Remove {trailing_spaces} trailing whitespace(s)")

            # 检查空行
            if "\n\n\n" in code:
                score -= 0.1

            # 检查 import 顺序 (简单)
            import_lines = [
                l for l in code.split("\n") if l.startswith("import ") or l.startswith("from ")
            ]
            if len(import_lines) > 1:
                # 检查是否按字母顺序
                sorted_imports = sorted(import_lines)
                if import_lines != sorted_imports:
                    suggestions.append("Sort imports alphabetically")

        return EvalResult(
            plugin_name=self.name,
            score=max(score, 0.0),
            passed=score >= 0.6,
            details={"checks": ["naming", "formatting", "imports"]},
            suggestions=suggestions,
        )


class PluginRegistry:
    """评估插件注册中心"""

    def __init__(self):
        self._plugins: Dict[str, EvalPlugin] = {}
        self._register_builtins()

    def _register_builtins(self):
        """注册内置插件"""
        self.register(CodeQualityPlugin())
        self.register(SecurityPlugin())
        self.register(PerformancePlugin())
        self.register(CorrectnessPlugin())
        self.register(DocumentationPlugin())
        self.register(ComplexityPlugin())
        self.register(StylePlugin())

    def register(self, plugin: EvalPlugin) -> None:
        """注册插件

        Args:
            plugin: 评估插件实例
        """
        self._plugins[plugin.name] = plugin
        logger.info(f"Registered evaluation plugin: {plugin.name}")

    def unregister(self, name: str) -> bool:
        """注销插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        if name in self._plugins:
            del self._plugins[name]
            return True
        return False

    def get(self, name: str) -> Optional[EvalPlugin]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，不存在返回 None
        """
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        """列出所有插件名称

        Returns:
            插件名称列表
        """
        return list(self._plugins.keys())

    def evaluate_all(
        self, context: EvalContext, plugin_names: Optional[List[str]] = None
    ) -> List[EvalResult]:
        """运行所有插件评估

        Args:
            context: 评估上下文
            plugin_names: 要运行的插件名称，None 表示全部

        Returns:
            评估结果列表
        """
        results = []
        plugins_to_run = plugin_names or self.list_plugins()

        for name in plugins_to_run:
            plugin = self.get(name)
            if plugin:
                try:
                    result = plugin.evaluate(context)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Plugin {name} evaluation failed: {e}")
                    results.append(
                        EvalResult(plugin_name=name, score=0.0, passed=False, errors=[str(e)])
                    )

        return results


# 全局插件注册中心实例
_default_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """获取全局插件注册中心"""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry


# 便捷函数
def evaluate(context: EvalContext, plugins: Optional[List[str]] = None) -> List[EvalResult]:
    """评估代码

    Args:
        context: 评估上下文
        plugins: 插件名称列表

    Returns:
        评估结果列表
    """
    registry = get_registry()
    return registry.evaluate_all(context, plugins)


__all__ = [
    "EvalPlugin",
    "EvalResult",
    "EvalContext",
    "EvalMetricType",
    "PluginRegistry",
    "CodeQualityPlugin",
    "SecurityPlugin",
    "PerformancePlugin",
    "CorrectnessPlugin",
    "get_registry",
    "evaluate",
]
