"""
Tests for HTMLParser
"""
import pytest
from src.peas.understanding import HTMLParser
from src.peas.types import Priority, FeaturePoint


class TestHTMLParser:
    """HTMLParser测试"""

    @pytest.fixture
    def parser(self):
        return HTMLParser()

    @pytest.fixture
    def sample_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <title>用户管理系统 - HTML原型</title>
</head>
<body>
    <h1>用户管理系统</h1>

    <nav id="main-nav">
        <!-- Feature: 顶部导航栏 -->
    </nav>

    <section id="login-form">
        <h2>用户登录</h2>
        <form id="loginForm">
            <!-- Feature: 邮箱登录表单 -->
            <input type="email" id="email" placeholder="请输入邮箱" data-feature="邮箱输入框" required>
            <input type="password" id="password" placeholder="请输入密码" required>
            <!-- Must: 登录按钮 -->
            <button type="submit" id="loginBtn">登录</button>
        </form>

        <div class="remember-me">
            <input type="checkbox" id="remember">
            <label for="remember">记住我</label>
        </div>
    </section>

    <section id="user-list">
        <h2>用户列表</h2>
        <!-- Feature: 用户列表展示 -->
        <table id="userTable">
            <thead>
                <tr><th>ID</th><th>用户名</th><th>邮箱</th><th>操作</th></tr>
            </thead>
            <tbody>
                <!-- Should: 分页显示 -->
            </tbody>
        </table>
    </section>
</body>
</html>"""

    def test_extract_title_from_title_tag(self, parser):
        """测试从title标签提取标题"""
        html = "<html><head><title>Test Page</title></head></html>"
        result = parser.parse(html)
        assert result.title == "Test Page"

    def test_extract_title_from_h1(self, parser):
        """测试从h1标签提取标题"""
        html = "<html><body><h1>Main Title</h1></body></html>"
        result = parser.parse(html)
        assert result.title == "Main Title"

    def test_extract_sections(self, parser, sample_html):
        """测试章节提取"""
        result = parser.parse(sample_html)
        # h2 become sections
        assert any("用户登录" in s for s in result.sections)
        assert any("用户列表" in s for s in result.sections)

    def test_extract_feature_points_from_comments(self, parser):
        """测试从HTML注释提取功能点"""
        html = """<html>
<body>
<!-- Feature: 用户注册功能 -->
<!-- Must: 用户名必填 -->
<!-- Should: 显示用户协议 -->
</body>
</html>"""
        result = parser.parse(html)
        assert len(result.feature_points) >= 3

    def test_extract_button_elements(self, parser, sample_html):
        """测试提取按钮元素"""
        result = parser.parse(sample_html)

        # 查找登录按钮
        button_fps = [fp for fp in result.feature_points if "登录" in fp.title or "button" in fp.title.lower()]
        assert len(button_fps) > 0

    def test_extract_form_elements(self, parser, sample_html):
        """测试提取表单元素"""
        result = parser.parse(sample_html)

        # 查找表单相关功能点
        form_fps = [fp for fp in result.feature_points
                   if "邮箱" in fp.title or "密码" in fp.title or "form" in fp.description.lower()]
        assert len(form_fps) > 0

    def test_priority_detection_must(self, parser):
        """测试Must优先级检测"""
        html = """<html>
<body>
<!-- Must: 必须完成的功能 -->
</body>
</html>"""
        result = parser.parse(html)
        assert len(result.feature_points) >= 1
        must_fps = [fp for fp in result.feature_points if fp.priority == Priority.MUST]
        assert len(must_fps) >= 1

    def test_priority_detection_should(self, parser):
        """测试Should优先级检测"""
        html = """<html>
<body>
<!-- Should: 建议实现的功能 -->
</body>
</html>"""
        result = parser.parse(html)
        assert len(result.feature_points) >= 1

    def test_empty_html(self, parser):
        """测试空HTML"""
        result = parser.parse("")
        assert result.title == "Untitled HTML Document"
        assert result.feature_points == []

    def test_minimal_html(self, parser):
        """测试最小HTML"""
        result = parser.parse("<html><body></body></html>")
        assert result.title == "Untitled HTML Document"

    def test_structural_extraction(self, parser):
        """测试结构化提取"""
        html = """<html>
<head><title>My App</title></head>
<body>
    <h1>Dashboard</h1>
    <h2>Settings</h2>
    <h2>Profile</h2>
    <form id="settings">
        <input type="text" id="username">
    </form>
</body>
</html>"""
        result = parser.parse(html)

        assert result.title == "My App"
        assert "Settings" in result.sections
        assert "Profile" in result.sections
        # 表单元素应被提取
        assert len(result.feature_points) > 0

    def test_parse_file(self, parser, tmp_path):
        """测试文件解析"""
        test_file = tmp_path / "test.html"
        test_file.write_text(
            """<html><head><title>Test File</title></head>
<body><h1>Title</h1></body></html>""",
            encoding='utf-8'
        )

        result = parser.parse_file(str(test_file))
        assert result.title == "Test File"

    def test_parse_file_with_allowed_dir(self, parser, tmp_path):
        """测试带allowed_dir的文件解析"""
        test_dir = tmp_path / "docs"
        test_dir.mkdir()
        test_file = test_dir / "test.html"
        test_file.write_text("<html><head><title>Test</title></head></html>", encoding='utf-8')

        result = parser.parse_file(str(test_file), allowed_dir=str(tmp_path))
        assert result.title == "Test"

    def test_path_traversal_protection(self, parser, tmp_path):
        """测试路径遍历保护"""
        with pytest.raises(ValueError, match="escapes allowed directory"):
            parser.parse_file("/etc/passwd", allowed_dir=str(tmp_path))

    def test_content_size_limit(self, parser):
        """测试内容大小限制"""
        large_html = "<html><body>" + "x" * (11 * 1024 * 1024) + "</body></html>"
        with pytest.raises(ValueError, match="exceeds maximum"):
            parser.parse(large_html)

    def test_metadata(self, parser, sample_html):
        """测试元数据"""
        result = parser.parse(sample_html)
        assert "parser_version" in result.metadata
        assert result.metadata["parser_version"] == "1.0"
        assert "source_type" in result.metadata
        assert result.metadata["source_type"] == "html"

    def test_input_with_priority_attribute(self, parser):
        """测试带优先级属性的输入框"""
        html = """<html>
<body>
<input type="text" id="username" data-feature="用户名输入" required>
<input type="email" id="email" data-feature="邮箱输入">
</body>
</html>"""
        result = parser.parse(html)
        # 有required的属性应该是MUST优先级
        assert len(result.feature_points) > 0


class TestHTMLParserConvenienceFunctions:
    """便捷函数测试"""

    def test_parse_html(self):
        """测试parse_html便捷函数"""
        from src.peas.understanding.html_parser import parse_html

        result = parse_html("<html><head><title>Test</title></head></html>")
        assert result.title == "Test"

    def test_parse_html_file(self, tmp_path):
        """测试parse_html_file便捷函数"""
        from src.peas.understanding.html_parser import parse_html_file

        test_file = tmp_path / "test.html"
        test_file.write_text("<html><head><title>File Test</title></head></html>", encoding='utf-8')

        result = parse_html_file(str(test_file))
        assert result.title == "File Test"
