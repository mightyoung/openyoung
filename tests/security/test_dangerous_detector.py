"""
Dangerous Code Detector Tests - Phase 2.x
Tests for DangerousCodeDetector
"""

import pytest
from src.runtime.security import (
    DangerousCodeDetector,
    DangerousCodeResult,
    DangerousLevel,
    detect_dangerous_code,
    is_code_safe,
)


class TestDangerousCodeDetector:
    """DangerousCodeDetector 测试"""

    def test_safe_code(self):
        """安全代码测试"""
        detector = DangerousCodeDetector()
        result = detector.detect("print('hello')")

        assert result.is_safe == True
        assert result.level == DangerousLevel.SAFE
        assert len(result.detected_patterns) == 0

    def test_eval_detection(self):
        """eval 检测"""
        detector = DangerousCodeDetector()
        result = detector.detect("eval('dangerous')")

        assert result.is_safe == False
        assert result.level == DangerousLevel.CRITICAL

    def test_exec_detection(self):
        """exec 检测"""
        detector = DangerousCodeDetector()
        result = detector.detect("exec('code')")

        assert result.is_safe == False
        assert result.level == DangerousLevel.CRITICAL

    def test_file_write_detection(self):
        """文件写入检测"""
        detector = DangerousCodeDetector()
        result = detector.detect("open('file.txt', 'w')")

        assert result.is_safe == False
        assert result.level == DangerousLevel.HIGH

    def test_subprocess_detection(self):
        """子进程检测"""
        detector = DangerousCodeDetector()
        result = detector.detect("subprocess.run(['ls'])")

        assert result.is_safe == False
        assert result.level == DangerousLevel.MEDIUM

    def test_os_remove_detection(self):
        """文件删除检测"""
        detector = DangerousCodeDetector()
        result = detector.detect("import os; os.remove('file.txt')")

        assert result.is_safe == False
        assert result.level == DangerousLevel.HIGH


class TestDangerousLevel:
    """危险等级测试"""

    def test_level_order(self):
        """等级顺序"""
        assert DangerousLevel.CRITICAL.value == "critical"
        assert DangerousLevel.HIGH.value == "high"
        assert DangerousLevel.MEDIUM.value == "medium"
        assert DangerousLevel.LOW.value == "low"
        assert DangerousLevel.SAFE.value == "safe"


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_detect_dangerous_code(self):
        """便捷检测函数"""
        result = detect_dangerous_code("eval('x')")
        assert result.is_safe == False
        assert result.level == DangerousLevel.CRITICAL

    def test_is_code_safe(self):
        """便捷安全检查"""
        assert is_code_safe("print('hello')") == True
        assert is_code_safe("eval('x')") == False


class TestDangerousCodeResult:
    """检测结果测试"""

    def test_result_properties(self):
        """结果属性"""
        result = DangerousCodeResult(
            is_safe=False,
            level=DangerousLevel.CRITICAL,
            detected_patterns=[{"name": "eval", "level": DangerousLevel.CRITICAL}],
            warnings=["eval() is dangerous"],
        )

        assert result.is_safe == False
        assert result.level == DangerousLevel.CRITICAL
        assert len(result.detected_patterns) == 1
        assert len(result.warnings) == 1


class TestBlockThreshold:
    """阻止阈值测试"""

    def test_block_at_critical(self):
        """critical 级别阻止"""
        detector = DangerousCodeDetector()
        assert detector.is_blocked("eval('x')", DangerousLevel.CRITICAL) == True

    def test_block_at_high(self):
        """high 级别阻止"""
        detector = DangerousCodeDetector()
        assert detector.is_blocked("open('f', 'w')", DangerousLevel.HIGH) == True
        assert detector.is_blocked("eval('x')", DangerousLevel.HIGH) == True

    def test_allow_at_medium(self):
        """medium 级别允许"""
        detector = DangerousCodeDetector()
        # open write is HIGH, should be blocked even with MEDIUM threshold
        assert detector.is_blocked("open('f', 'w')", DangerousLevel.MEDIUM) == True
        # subprocess is MEDIUM, should be allowed with HIGH threshold
        assert detector.is_blocked("subprocess.run(['ls'])", DangerousLevel.HIGH) == False


class TestCustomPatterns:
    """自定义模式测试"""

    def test_block_patterns(self):
        """自定义阻止模式"""
        detector = DangerousCodeDetector(block_patterns=[r"forbidden"])
        result = detector.detect("some forbidden code")

        assert result.is_safe == False
        assert result.level == DangerousLevel.CRITICAL

    def test_allow_patterns(self):
        """自定义允许模式"""
        detector = DangerousCodeDetector()
        result = detector.detect("print('hello')")
        assert result.is_safe == True
