"""
UI Comparator - 视觉对比功能

M2.1: UIComparator组件
支持:
- HTML结构对比
- 截图对比 (需要PIL)
- 差异报告生成
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Try to import PIL for image comparison
try:
    from PIL import Image, ImageChops, ImageStat

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from ..types import DriftLevel, DriftReport


@dataclass
class UIElement:
    """UI元素"""

    tag: str
    id: Optional[str] = None
    class_name: Optional[str] = None
    text: Optional[str] = None
    attributes: dict = field(default_factory=dict)
    children: list["UIElement"] = field(default_factory=list)


@dataclass
class VisualDiff:
    """视觉差异"""

    element_path: str
    diff_type: str  # "missing", "added", "changed", "style_changed"
    expected: Optional[str] = None
    actual: Optional[str] = None
    severity: DriftLevel = DriftLevel.MINOR


@dataclass
class ComparisonResult:
    """对比结果"""

    is_match: bool
    drift_score: float  # 0-100
    drift_level: DriftLevel
    element_diffs: list[VisualDiff] = field(default_factory=list)
    structural_diffs: list[VisualDiff] = field(default_factory=list)
    image_diff_percentage: Optional[float] = None
    metadata: dict = field(default_factory=dict)


class UIComparator:
    """UI比较器

    比较两个HTML文档或UI设计的差异:
    - HTML结构对比
    - CSS样式对比
    - 截图像素对比 (如果PIL可用)
    """

    def __init__(self, *, strict_mode: bool = False):
        """
        初始化比较器

        Args:
            strict_mode: 严格模式，任何差异都报告
        """
        self.strict_mode = strict_mode

    def compare_html(
        self,
        expected_html: str,
        actual_html: str,
    ) -> ComparisonResult:
        """比较两个HTML文档

        Args:
            expected_html: 期望的HTML内容
            actual_html: 实际的HTML内容

        Returns:
            ComparisonResult: 对比结果
        """
        # 解析HTML结构
        expected_elements = self._parse_html_elements(expected_html)
        actual_elements = self._parse_html_elements(actual_html)

        # 结构对比
        structural_diffs = self._compare_structure(expected_elements, actual_elements)

        # 元素对比
        element_diffs = self._compare_elements(expected_elements, actual_elements)

        # 计算漂移分数
        drift_score = self._calculate_drift_score(
            structural_diffs, element_diffs, expected_elements
        )

        # 确定漂移级别
        drift_level = self._calculate_drift_level(drift_score)

        is_match = drift_level in (DriftLevel.NONE, DriftLevel.MINOR)

        return ComparisonResult(
            is_match=is_match,
            drift_score=drift_score,
            drift_level=drift_level,
            element_diffs=element_diffs,
            structural_diffs=structural_diffs,
            metadata={
                "expected_elements": len(expected_elements),
                "actual_elements": len(actual_elements),
            },
        )

    def compare_files(
        self,
        expected_path: str,
        actual_path: str,
    ) -> ComparisonResult:
        """比较两个HTML文件

        Args:
            expected_path: 期望的HTML文件路径
            actual_path: 实际的HTML文件路径

        Returns:
            ComparisonResult: 对比结果
        """
        expected_html = Path(expected_path).read_text(encoding="utf-8")
        actual_html = Path(actual_path).read_text(encoding="utf-8")
        return self.compare_html(expected_html, actual_html)

    def compare_screenshots(
        self,
        expected_image_path: str,
        actual_image_path: str,
        *,
        threshold: float = 0.1,
    ) -> ComparisonResult:
        """比较两张截图

        Args:
            expected_image_path: 期望的截图路径
            actual_image_path: 实际的截图路径
            threshold: 差异阈值 (0-1)

        Returns:
            ComparisonResult: 对比结果

        Raises:
            ImportError: 如果PIL未安装
        """
        if not HAS_PIL:
            raise ImportError(
                "PIL (Pillow) is required for screenshot comparison. "
                "Install with: pip install Pillow"
            )

        # 加载图片
        expected_img = Image.open(expected_image_path)
        actual_img = Image.open(actual_image_path)

        # 确保图片尺寸相同
        if expected_img.size != actual_img.size:
            # 调整大小
            actual_img = actual_img.resize(expected_img.size, Image.LANCZOS)

        # 计算差异
        diff_img = ImageChops.difference(expected_img, actual_img)
        stat = ImageStat.Stat(diff_img)
        diff_percentage = sum(stat.mean) / (len(stat.mean) * 255) * 100

        # 判断是否匹配
        is_match = diff_percentage <= (threshold * 100)
        drift_score = min(100.0, diff_percentage * 2)  # 放大差异分数
        drift_level = self._calculate_drift_level(drift_score)

        return ComparisonResult(
            is_match=is_match,
            drift_score=drift_score,
            drift_level=drift_level,
            image_diff_percentage=diff_percentage,
            metadata={
                "expected_size": expected_img.size,
                "actual_size": actual_img.size,
                "threshold": threshold,
            },
        )

    def generate_drift_report(
        self,
        comparison_result: ComparisonResult,
        verified_count: int = 0,
        total_count: int = 0,
    ) -> DriftReport:
        """生成偏离报告

        Args:
            comparison_result: 对比结果
            verified_count: 已验证的功能点数
            total_count: 总功能点数

        Returns:
            DriftReport: 偏离报告
        """
        # 统计差异
        all_diffs = comparison_result.element_diffs + comparison_result.structural_diffs

        # 按严重程度分类
        critical_diffs = [d for d in all_diffs if d.severity == DriftLevel.CRITICAL]
        severe_diffs = [d for d in all_diffs if d.severity == DriftLevel.SEVERE]
        moderate_diffs = [d for d in all_diffs if d.severity == DriftLevel.MODERATE]

        # 生成建议
        recommendations = []
        if critical_diffs:
            recommendations.append(f"发现 {len(critical_diffs)} 个关键差异，需要立即修复")
        if severe_diffs:
            recommendations.append(f"发现 {len(severe_diffs)} 个严重差异，建议下一版本修复")
        if moderate_diffs:
            recommendations.append(f"发现 {len(moderate_diffs)} 个中等差异，可视情况修复")
        if not all_diffs:
            recommendations.append("UI完全匹配，无需修改")

        failed_count = len(critical_diffs) + len(severe_diffs)

        return DriftReport(
            drift_score=comparison_result.drift_score,
            level=comparison_result.drift_level,
            verified_count=verified_count,
            failed_count=failed_count,
            total_count=total_count,
            recommendations=recommendations,
        )

    def _parse_html_elements(self, html: str) -> list[UIElement]:
        """解析HTML为元素列表"""
        from html.parser import HTMLParser

        class SimpleHTMLParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.elements: list[UIElement] = []
                self.tag_stack = []

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                element = UIElement(
                    tag=tag,
                    id=attrs_dict.get("id"),
                    class_name=attrs_dict.get("class"),
                    text="",
                    attributes=attrs_dict,
                )
                self.elements.append(element)
                if tag not in ("img", "input", "br", "hr", "meta", "link"):
                    self.tag_stack.append(element)

            def handle_data(self, data):
                if self.tag_stack:
                    self.tag_stack[-1].text += data

        parser = SimpleHTMLParser()
        parser.feed(html)
        return parser.elements

    def _compare_structure(
        self,
        expected: list[UIElement],
        actual: list[UIElement],
    ) -> list[VisualDiff]:
        """比较HTML结构"""
        diffs = []

        expected_tags = [e.tag for e in expected]
        actual_tags = [a.tag for a in actual]

        # 检查缺失的元素
        for tag in expected_tags:
            if tag not in actual_tags:
                diffs.append(
                    VisualDiff(
                        element_path=tag,
                        diff_type="missing",
                        expected=tag,
                        actual=None,
                        severity=DriftLevel.MODERATE,
                    )
                )

        # 检查新增的元素
        for tag in actual_tags:
            if tag not in expected_tags:
                diffs.append(
                    VisualDiff(
                        element_path=tag,
                        diff_type="added",
                        expected=None,
                        actual=tag,
                        severity=DriftLevel.MINOR,
                    )
                )

        return diffs

    def _compare_elements(
        self,
        expected: list[UIElement],
        actual: list[UIElement],
    ) -> list[VisualDiff]:
        """比较元素属性"""
        diffs = []

        # 创建ID索引
        expected_by_id = {e.id: e for e in expected if e.id}
        actual_by_id = {a.id: a for a in actual if a.id}

        # 检查缺失的ID元素
        for elem_id, expected_elem in expected_by_id.items():
            if elem_id not in actual_by_id:
                diffs.append(
                    VisualDiff(
                        element_path=f"#{elem_id}",
                        diff_type="missing",
                        expected=expected_elem.tag,
                        actual=None,
                        severity=DriftLevel.SEVERE,
                    )
                )

        # 检查属性变化
        for elem_id, actual_elem in actual_by_id.items():
            if elem_id in expected_by_id:
                expected_elem = expected_by_id[elem_id]

                # 比较class
                if expected_elem.class_name != actual_elem.class_name:
                    diffs.append(
                        VisualDiff(
                            element_path=f"#{elem_id}.class",
                            diff_type="changed",
                            expected=expected_elem.class_name,
                            actual=actual_elem.class_name,
                            severity=DriftLevel.MODERATE,
                        )
                    )

                # 比较文本
                if expected_elem.text and actual_elem.text:
                    if expected_elem.text.strip() != actual_elem.text.strip():
                        diffs.append(
                            VisualDiff(
                                element_path=f"#{elem_id} text",
                                diff_type="changed",
                                expected=expected_elem.text[:50],
                                actual=actual_elem.text[:50],
                                severity=DriftLevel.MINOR,
                            )
                        )

        return diffs

    def _calculate_drift_score(
        self,
        structural_diffs: list[VisualDiff],
        element_diffs: list[VisualDiff],
        expected_elements: list[UIElement],
    ) -> float:
        """计算漂移分数"""
        if not expected_elements:
            return 0.0

        # 权重
        STRUCTURAL_WEIGHT = 0.3
        ELEMENT_WEIGHT = 0.7

        # 结构漂移
        structural_score = len(structural_diffs) * 10 if structural_diffs else 0

        # 元素漂移
        element_score = len(element_diffs) * 15 if element_diffs else 0

        # 归一化到0-100
        total_score = structural_score * STRUCTURAL_WEIGHT + element_score * ELEMENT_WEIGHT

        return min(100.0, total_score)

    def _calculate_drift_level(self, drift_score: float) -> DriftLevel:
        """计算漂移级别"""
        if drift_score == 0:
            return DriftLevel.NONE
        elif drift_score < 10:
            return DriftLevel.MINOR
        elif drift_score < 30:
            return DriftLevel.MODERATE
        elif drift_score < 60:
            return DriftLevel.SEVERE
        else:
            return DriftLevel.CRITICAL


# 便捷函数
def compare_ui(expected: str, actual: str) -> ComparisonResult:
    """比较两个UI的便捷函数"""
    comparator = UIComparator()
    return comparator.compare_html(expected, actual)


def compare_screenshots(
    expected: str,
    actual: str,
    threshold: float = 0.1,
) -> ComparisonResult:
    """比较两张截图的便捷函数"""
    comparator = UIComparator()
    return comparator.compare_screenshots(expected, actual, threshold=threshold)
