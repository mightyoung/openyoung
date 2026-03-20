"""
Security Tests for PEAS Parsers

Tests for:
- Path traversal protection
- Content size limits (DoS prevention)
- XSS payload handling
- Catastrophic backtracking prevention
"""
import pytest
import tempfile
import os
from pathlib import Path


class TestMarkdownParserSecurity:
    """MarkdownParser安全测试"""

    @pytest.fixture
    def parser(self):
        from src.peas.understanding import MarkdownParser
        return MarkdownParser()

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    # === Path Traversal Tests ===

    def test_path_traversal_absolute_outside_allowed(self, parser, temp_dir):
        """测试绝对路径绕过allowed_dir"""
        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file("/etc/passwd", allowed_dir=temp_dir)

    def test_path_traversal_relative_dotdot(self, parser, temp_dir):
        """测试相对路径的../绕过"""
        # 创建临时目录结构
        subdir = Path(temp_dir) / "docs"
        subdir.mkdir()

        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file(str(subdir / "../../../etc/passwd"), allowed_dir=str(subdir))

    def test_path_traversal_windows_style(self, parser, temp_dir):
        """测试Windows风格路径遍历"""
        # Windows absolute path
        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file("C:\\Windows\\System32\\config\\sam", allowed_dir=temp_dir)

    def test_path_traversal_symlink_bypass(self, parser, temp_dir):
        """测试符号链接绕过 - 应该被阻止"""
        # 创建目录和符号链接
        target_dir = Path(temp_dir) / "target"
        target_dir.mkdir()

        allowed_dir = Path(temp_dir) / "allowed"
        allowed_dir.mkdir()

        # 创建一个指向目标目录的符号链接
        link_path = allowed_dir / "link"
        try:
            os.symlink(target_dir, link_path)
            # 尝试通过符号链接访问target目录下的文件
            # 这应该被阻止，因为符号链接指向allowed_dir之外
            test_file = target_dir / "test.md"
            test_file.write_text("# Test")

            # 访问符号链接应该失败（正确的安全行为）
            with pytest.raises(ValueError, match="escapes allowed directory"):
                parser.parse_file(str(link_path / "test.md"), allowed_dir=str(allowed_dir))
        except OSError:
            # Windows可能不支持符号链接，跳过
            pytest.skip("Symbolic links not supported on this platform")

    def test_path_traversal_allowed_dir_none(self, parser, temp_dir):
        """测试不限制allowed_dir时的行为"""
        # 创建测试文件
        test_file = Path(temp_dir) / "test.md"
        test_file.write_text("# Test Content")

        # 不提供allowed_dir时应该能访问
        result = parser.parse_file(str(test_file))
        assert result.title == "Test Content"

    # === Content Size Limit Tests ===

    def test_content_size_exactly_at_limit(self, parser):
        """测试刚好在限制大小的内容"""
        # 10MB exactly
        content = "# Title\n\n" + ("x" * (10 * 1024 * 1024 - 20))
        result = parser.parse(content)
        assert result.title == "Title"

    def test_content_size_over_limit(self, parser):
        """测试超过限制大小的内容"""
        content = "x" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(ValueError, match="exceeds maximum"):
            parser.parse(content)

    def test_content_size_unicode(self, parser):
        """测试Unicode内容的实际大小"""
        # 5MB的中文字符（UTF-8编码后约15MB）
        content = "x" * (5 * 1024 * 1024) + "中" * (5 * 1024 * 1024)
        with pytest.raises(ValueError, match="exceeds maximum"):
            parser.parse(content)

    # === DoS Prevention Tests ===

    def test_markdown_nested_brackets_dos(self, parser):
        """测试嵌套括号DoS攻击"""
        # 深度嵌套的列表可能导致指数级解析时间
        content = "# Title\n" + ("- " + "[" * 100 + "x" + "]" * 100 + "\n") * 10
        result = parser.parse(content)
        # 应该成功解析，不挂起
        assert result is not None

    def test_markdown_many_headings(self, parser):
        """测试大量标题DoS"""
        # 使用h2而不是h1，因为只有level > 1的标题会被提取为sections
        content = "\n".join([f"## Heading {i}" for i in range(10000)])
        result = parser.parse(content)
        assert len(result.sections) > 0

    def test_markdown_extremely_long_line(self, parser):
        """测试超长行DoS"""
        content = "# Title\n" + "x" * (1 * 1024 * 1024)  # 1MB single line
        result = parser.parse(content)
        assert result is not None

    # === XSS Prevention Tests ===

    def test_markdown_xss_script_tag(self, parser):
        """测试XSS脚本标签"""
        content = "# Title\n\n<script>alert('xss')</script>"
        result = parser.parse(content)
        # raw_content应该保留原始内容（用于调试）
        # 使用者应该自行转义
        assert "<script>" in result.raw_content

    def test_markdown_xss_event_handler(self, parser):
        """测试XSS事件处理器"""
        content = "# Title\n\n[click me](javascript:alert('xss'))"
        result = parser.parse(content)
        assert "javascript:" in result.raw_content


class TestHTMLParserSecurity:
    """HTMLParser安全测试"""

    @pytest.fixture
    def parser(self):
        from src.peas.understanding import HTMLParser
        return HTMLParser()

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    # === Path Traversal Tests ===

    def test_path_traversal_absolute_outside_allowed(self, parser, temp_dir):
        """测试绝对路径绕过allowed_dir"""
        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file("/etc/passwd", allowed_dir=temp_dir)

    def test_path_traversal_relative_dotdot(self, parser, temp_dir):
        """测试相对路径的../绕过"""
        subdir = Path(temp_dir) / "docs"
        subdir.mkdir()

        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file(str(subdir / "../../../etc/passwd"), allowed_dir=str(subdir))

    def test_path_traversal_windows_style(self, parser, temp_dir):
        """测试Windows风格路径遍历"""
        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file("C:\\Windows\\System32\\config\\sam", allowed_dir=temp_dir)

    def test_path_traversal_allowed_dir_none(self, parser, temp_dir):
        """测试不限制allowed_dir"""
        test_file = Path(temp_dir) / "test.html"
        test_file.write_text("<html><head><title>Test</title></head></html>")

        result = parser.parse_file(str(test_file))
        assert result.title == "Test"

    # === Content Size Limit Tests ===

    def test_content_size_exactly_at_limit(self, parser):
        """测试刚好在限制大小的内容"""
        content = "<html><body>" + ("x" * (10 * 1024 * 1024 - 50)) + "</body></html>"
        result = parser.parse(content)
        assert result is not None

    def test_content_size_over_limit(self, parser):
        """测试超过限制大小的内容"""
        content = "x" * (11 * 1024 * 1024)
        with pytest.raises(ValueError, match="exceeds maximum"):
            parser.parse(content)

    # === DoS Prevention Tests ===

    def test_html_deeply_nested_tags(self, parser):
        """测试深度嵌套标签DoS"""
        content = "<html><body>" + ("<div>" * 10000) + "</div>" * 10000 + "</body></html>"
        result = parser.parse(content)
        assert result is not None

    def test_html_many_attributes(self, parser):
        """测试大量属性DoS"""
        attrs = " ".join([f'data-{i}="{i}"' for i in range(1000)])
        content = f"<html><body><div {attrs}>Content</div></body></html>"
        result = parser.parse(content)
        assert result is not None

    def test_html_large_comment(self, parser):
        """测试大注释DoS"""
        content = "<html><body><!--" + ("x" * (1 * 1024 * 1024)) + "--></body></html>"
        result = parser.parse(content)
        assert result is not None

    # === XSS Prevention Tests ===

    def test_html_xss_script_tag(self, parser):
        """测试XSS脚本标签"""
        content = "<html><body><script>alert('xss')</script></body></html>"
        result = parser.parse(content)
        assert "<script>" in result.raw_content

    def test_html_xss_event_handler(self, parser):
        """测试XSS事件处理器"""
        content = '<html><body><img src=x onerror="alert(1)"></body></html>'
        result = parser.parse(content)
        assert "onerror" in result.raw_content

    def test_html_xss_javascript_uri(self, parser):
        """测试JavaScript URI"""
        content = '<html><body><a href="javascript:alert(1)">click</a></body></html>'
        result = parser.parse(content)
        assert "javascript:" in result.raw_content

    def test_html_xss_data_uri(self, parser):
        """测试Data URI"""
        content = '<html><body><img src="data:text/html,<script>alert(1)</script>">'
        result = parser.parse(content)
        assert "data:" in result.raw_content


class TestSecurityConstants:
    """安全常量测试"""

    def test_max_content_size_value(self):
        """测试最大内容大小常量"""
        from src.peas.understanding.markdown_parser import MAX_CONTENT_SIZE as MD_MAX
        from src.peas.understanding.html_parser import MAX_CONTENT_SIZE as HTML_MAX

        # 两者应该相同
        assert MD_MAX == HTML_MAX == 10 * 1024 * 1024

    def test_max_content_size_bytes(self):
        """测试10MB = 10,485,760字节"""
        from src.peas.understanding.markdown_parser import MAX_CONTENT_SIZE
        assert MAX_CONTENT_SIZE == 10_485_760


class TestSecurityIntegration:
    """集成安全测试"""

    def test_both_parsers_enforce_same_limits(self):
        """测试两个解析器执行相同限制"""
        from src.peas.understanding import MarkdownParser, HTMLParser

        md_parser = MarkdownParser()
        html_parser = HTMLParser()

        large_content = "x" * (11 * 1024 * 1024)

        # 两个解析器都应该抛出相同类型的异常
        with pytest.raises(ValueError):
            md_parser.parse(large_content)

        with pytest.raises(ValueError):
            html_parser.parse(large_content)

    def test_path_traversal_consistency(self):
        """测试路径遍历保护一致性"""
        from src.peas.understanding import MarkdownParser, HTMLParser

        md_parser = MarkdownParser()
        html_parser = HTMLParser()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 两个解析器对相同攻击应该表现一致
            for parser in [md_parser, html_parser]:
                with pytest.raises(ValueError, match="escapes allowed directory"):
                    parser.parse_file("/etc/passwd", allowed_dir=tmpdir)


class TestOutputEscaping:
    """输出转义测试"""

    def test_parsed_document_title_escaped(self):
        """测试ParsedDocument的title_escaped属性"""
        from src.peas.types import ParsedDocument, Priority, FeaturePoint

        doc = ParsedDocument(
            title='<script>alert(1)</script>',
            sections=[],
            feature_points=[],
            raw_content=""
        )

        # 原始内容应该保留
        assert '<script>' in doc.title
        # 转义后应该安全
        assert doc.title_escaped == '&lt;script&gt;alert(1)&lt;/script&gt;'

    def test_parsed_document_raw_content_escaped(self):
        """测试ParsedDocument的raw_content_escaped属性"""
        from src.peas.types import ParsedDocument

        doc = ParsedDocument(
            title="Test",
            sections=[],
            feature_points=[],
            raw_content='<img src=x onerror="alert(1)">'
        )

        # 原始内容应该保留
        assert 'onerror' in doc.raw_content
        # HTML标签应该被转义
        assert '&lt;img' in doc.raw_content_escaped
        assert '&gt;' in doc.raw_content_escaped
        # 转义后不再包含原始的<和>标签
        assert '<img' not in doc.raw_content_escaped

    def test_feature_point_title_escaped(self):
        """测试FeaturePoint的title_escaped属性"""
        from src.peas.types import FeaturePoint, Priority

        fp = FeaturePoint(
            id="FP-001",
            title='<img src=x onerror="alert(1)">',
            description="test",
            priority=Priority.MUST
        )

        # 原始内容应该保留
        assert 'onerror' in fp.title
        # 转义后应该安全
        assert fp.title_escaped == '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;'

    def test_feature_point_description_escaped(self):
        """测试FeaturePoint的description_escaped属性"""
        from src.peas.types import FeaturePoint, Priority

        fp = FeaturePoint(
            id="FP-001",
            title="Test",
            description='<script>alert("xss")</script>',
            priority=Priority.MUST
        )

        assert fp.description_escaped == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'

    def test_html_parser_escaped_content(self):
        """测试HTMLParser返回的ParsedDocument包含转义属性"""
        from src.peas.understanding import HTMLParser

        parser = HTMLParser()
        doc = parser.parse("<title>Test & Title</title>")

        # 使用ParsedDocument的转义属性
        assert "Test &amp; Title" in doc.title_escaped
