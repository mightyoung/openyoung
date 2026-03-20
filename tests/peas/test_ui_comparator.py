"""
Tests for UIComparator
"""
import pytest
from src.peas.verification import UIComparator
from src.peas.types import DriftLevel


class TestUIComparator:
    """UIComparator测试"""

    @pytest.fixture
    def comparator(self):
        return UIComparator()

    def test_compare_identical_html(self, comparator):
        """测试相同HTML返回匹配"""
        html = "<html><body><h1>Title</h1></body></html>"
        result = comparator.compare_html(html, html)
        assert result.is_match is True
        assert result.drift_score == 0.0
        assert result.drift_level == DriftLevel.NONE

    def test_compare_different_html(self, comparator):
        """测试不同HTML返回差异"""
        expected = "<html><body><h1>Title</h1><button>Click</button></body></html>"
        actual = "<html><body><h1>Title</h1></body></html>"
        result = comparator.compare_html(expected, actual)
        # MINOR级别的差异被视为"匹配"，但差异仍然被记录
        assert len(result.element_diffs) > 0 or len(result.structural_diffs) > 0

    def test_compare_with_missing_element(self, comparator):
        """测试缺失元素检测"""
        expected = "<html><body><div id='header'>Header</div></body></html>"
        actual = "<html><body></body></html>"
        result = comparator.compare_html(expected, actual)
        assert result.is_match is False
        # 检查是否有缺失的元素
        assert len(result.structural_diffs) > 0

    def test_compare_with_style_change(self, comparator):
        """测试样式变化检测"""
        expected = '<html><body><div id="main" class="container">Content</div></body></html>'
        actual = '<html><body><div id="main" class="container-fluid">Content</div></body></html>'
        result = comparator.compare_html(expected, actual)
        assert result.is_match is False

    def test_compare_files(self, comparator, tmp_path):
        """测试文件比较"""
        expected_file = tmp_path / "expected.html"
        actual_file = tmp_path / "actual.html"

        expected_file.write_text("<html><body><h1>Test</h1></body></html>", encoding="utf-8")
        actual_file.write_text("<html><body><h1>Test</h1></body></html>", encoding="utf-8")

        result = comparator.compare_files(str(expected_file), str(actual_file))
        assert result.is_match is True

    def test_generate_drift_report(self, comparator):
        """测试生成偏离报告"""
        html1 = "<html><body><button>Submit</button></body></html>"
        html2 = "<html><body></body></html>"

        comparison = comparator.compare_html(html1, html2)
        report = comparator.generate_drift_report(comparison, verified_count=5, total_count=10)

        assert report.drift_score >= 0
        assert report.total_count == 10
        assert len(report.recommendations) > 0


class TestUIComparatorWithPIL:
    """UIComparator PIL测试 (如果PIL可用)"""

    @pytest.fixture
    def comparator(self):
        return UIComparator()

    def test_screenshot_comparison_requires_pil(self, comparator, tmp_path):
        """测试截图比较需要PIL"""
        # 如果PIL不可用，应该抛出ImportError
        try:
            from PIL import Image
            pytest.skip("PIL is available, skipping mock test")
        except ImportError:
            pass

        # 创建临时图片文件
        img1 = tmp_path / "img1.png"
        img2 = tmp_path / "img2.png"

        # 这些文件实际上不是有效的图片，但测试应该能运行
        with pytest.raises(Exception):
            comparator.compare_screenshots(str(img1), str(img2))
