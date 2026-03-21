"""
危险代码检测器

检测代码中的危险操作
"""

import re
from dataclasses import dataclass
from enum import Enum


class DangerousLevel(str, Enum):
    """危险等级"""

    SAFE = "safe"  # 安全
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险
    CRITICAL = "critical"  # 极高风险


@dataclass
class DangerousCodeResult:
    """危险代码检测结果"""

    is_safe: bool
    level: DangerousLevel
    detected_patterns: list[dict]
    warnings: list[str]


class DangerousCodeDetector:
    """危险代码检测器

    检测代码中的危险操作，如 eval、exec、文件系统操作等
    """

    # 危险模式定义
    PATTERNS: list[dict] = [
        # 极高风险
        {
            "name": "eval_usage",
            "pattern": r"\beval\s*\(",
            "level": DangerousLevel.CRITICAL,
            "message": "eval() allows arbitrary code execution",
        },
        {
            "name": "exec_usage",
            "pattern": r"\bexec\s*\(",
            "level": DangerousLevel.CRITICAL,
            "message": "exec() allows arbitrary code execution",
        },
        {
            "name": "compile_usage",
            "pattern": r"\bcompile\s*\(",
            "level": DangerousLevel.CRITICAL,
            "message": "compile() can execute arbitrary code",
        },
        # 高风险 - 文件系统
        {
            "name": "os_remove",
            "pattern": r"os\.remove\s*\(|os\.unlink\s*\(",
            "level": DangerousLevel.HIGH,
            "message": "File deletion detected",
        },
        {
            "name": "shutil_rmtree",
            "pattern": r"shutil\.rmtree\s*\(",
            "level": DangerousLevel.HIGH,
            "message": "Recursive directory deletion detected",
        },
        {
            "name": "os_rename",
            "pattern": r"os\.rename\s*\(|os\.replace\s*\(",
            "level": DangerousLevel.HIGH,
            "message": "File rename detected",
        },
        {
            "name": "open_write",
            "pattern": r"open\s*\([^)]*,\s*['\"]w['\"]",
            "level": DangerousLevel.HIGH,
            "message": "File write operation detected",
        },
        # 中风险 - 网络/进程
        {
            "name": "subprocess_call",
            "pattern": r"subprocess\.(call|run|Popen)\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "Subprocess execution detected",
        },
        {
            "name": "os_system",
            "pattern": r"os\.system\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "Shell command execution detected",
        },
        {
            "name": "urllib_request",
            "pattern": r"urllib\.(request\.urlopen|request\.Request)",
            "level": DangerousLevel.MEDIUM,
            "message": "Network request detected",
        },
        {
            "name": "requests_post",
            "pattern": r"requests\.(post|get)\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "HTTP request detected",
        },
        {
            "name": "os_chmod",
            "pattern": r"os\.chmod\s*\(|os\.chown\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "File permission change detected",
        },
        # 低风险
        {
            "name": "import_os",
            "pattern": r"^import\s+os\b",
            "level": DangerousLevel.LOW,
            "message": "os module imported",
        },
        {
            "name": "import_subprocess",
            "pattern": r"^import\s+subprocess\b",
            "level": DangerousLevel.LOW,
            "message": "subprocess module imported",
        },
        {
            "name": "pickle_load",
            "pattern": r"pickle\.loads?\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "Pickle deserialization can be dangerous",
        },
        {
            "name": "marshal_load",
            "pattern": r"marshal\.loads?\s*\(",
            "level": DangerousLevel.MEDIUM,
            "message": "Marshal deserialization can be dangerous",
        },
    ]

    def __init__(
        self,
        allow_patterns: list[str] = None,
        block_patterns: list[str] = None,
    ):
        """
        初始化检测器

        Args:
            allow_patterns: 允许的模式（白名单）
            block_patterns: 阻止的模式（黑名单）
        """
        self._allow_patterns = allow_patterns or []
        self._block_patterns = block_patterns or []
        self._compiled_patterns = [
            (p["name"], re.compile(p["pattern"]), p["level"], p["message"]) for p in self.PATTERNS
        ]

    def detect(self, code: str) -> DangerousCodeResult:
        """
        检测危险代码

        Args:
            code: 待检测的代码

        Returns:
            DangerousCodeResult: 检测结果
        """
        detected = []

        # 检查自定义黑名单
        for pattern in self._block_patterns:
            if re.search(pattern, code):
                detected.append(
                    {
                        "name": "custom_blocked",
                        "level": DangerousLevel.CRITICAL,
                        "message": f"Code matches blocked pattern: {pattern}",
                    }
                )

        # 检查预定义危险模式
        for name, pattern, level, message in self._compiled_patterns:
            if pattern.search(code):
                detected.append(
                    {
                        "name": name,
                        "level": level,
                        "message": message,
                    }
                )

        # 确定最高危险等级
        level_order = [
            DangerousLevel.CRITICAL,
            DangerousLevel.HIGH,
            DangerousLevel.MEDIUM,
            DangerousLevel.LOW,
            DangerousLevel.SAFE,
        ]

        max_level = DangerousLevel.SAFE
        for d in detected:
            level = d["level"]
            if level_order.index(level) < level_order.index(max_level):
                max_level = level

        # 警告列表
        warnings = [d["message"] for d in detected]

        return DangerousCodeResult(
            is_safe=len(detected) == 0,
            level=max_level,
            detected_patterns=detected,
            warnings=warnings,
        )

    def is_blocked(self, code: str, threshold: DangerousLevel = DangerousLevel.HIGH) -> bool:
        """
        检查代码是否应被阻止

        Args:
            code: 待检测的代码
            threshold: 阻止阈值

        Returns:
            是否应阻止
        """
        result = self.detect(code)

        level_order = [
            DangerousLevel.CRITICAL,
            DangerousLevel.HIGH,
            DangerousLevel.MEDIUM,
            DangerousLevel.LOW,
            DangerousLevel.SAFE,
        ]

        return level_order.index(result.level) <= level_order.index(threshold)


# ========== Convenience Functions ==========


def detect_dangerous_code(code: str) -> DangerousCodeResult:
    """便捷函数：检测危险代码"""
    detector = DangerousCodeDetector()
    return detector.detect(code)


def is_code_safe(code: str, threshold: DangerousLevel = DangerousLevel.HIGH) -> bool:
    """便捷函数：检查代码是否安全"""
    detector = DangerousCodeDetector()
    return not detector.is_blocked(code, threshold)
