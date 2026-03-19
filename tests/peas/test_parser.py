"""
Tests for MarkdownParser
"""
import pytest
from src.peas.understanding import MarkdownParser
from src.peas.types import Priority, FeaturePoint


class TestMarkdownParser:
    """MarkdownParser测试"""

    @pytest.fixture
    def parser(self):
        return MarkdownParser()

    @pytest.fixture
    def sample_markdown(self):
        return """# 用户管理系统 PRD

## 1. 功能需求

### 1.1 用户注册
- Feature: 邮箱验证注册
- 用户输入邮箱和密码进行注册
- 必须发送验证邮件

### 1.2 用户登录
- Feature: 密码强度检查
- 密码长度至少8位
- 必须包含大小写字母和数字

### 1.3 账户安全
- Feature: 登录失败锁定
- 连续3次失败后锁定账户15分钟
- Should: 显示剩余尝试次数

## 2. 非功能需求

### 2.1 性能要求
- Could: 支持1000并发用户
- 响应时间<200ms

## 3. 验收标准

Given 用户已注册
When 用户输入正确密码
Then 允许登录并跳转到首页

Given 用户连续登录失败3次
When 用户再次尝试登录
Then 锁定账户15分钟并提示
"""

    def test_extract_title(self, parser, sample_markdown):
        """测试标题提取"""
        result = parser.parse(sample_markdown)
        assert result.title == "用户管理系统 PRD"

    def test_extract_sections(self, parser, sample_markdown):
        """测试章节提取"""
        result = parser.parse(sample_markdown)
        assert any("功能需求" in s for s in result.sections)
        assert any("用户注册" in s for s in result.sections)
        assert any("非功能需求" in s for s in result.sections)

    def test_extract_feature_points(self, parser, sample_markdown):
        """测试功能点提取"""
        result = parser.parse(sample_markdown)
        assert len(result.feature_points) >= 3

    def test_feature_priority_detection(self, parser, sample_markdown):
        """测试优先级检测"""
        result = parser.parse(sample_markdown)

        # 找到邮箱验证功能点
        email_fp = None
        for fp in result.feature_points:
            if "邮箱验证" in fp.title or "邮箱" in fp.title:
                email_fp = fp
                break

        assert email_fp is not None
        assert email_fp.priority == Priority.MUST

    def test_gwt_criteria_extraction(self, parser, sample_markdown):
        """测试Given-When-Then验收标准提取"""
        result = parser.parse(sample_markdown)

        # 找到登录相关功能点
        login_fp = None
        for fp in result.feature_points:
            if "登录" in fp.title:
                login_fp = fp
                break

        assert login_fp is not None
        assert len(login_fp.acceptance_criteria) > 0

    def test_empty_document(self, parser):
        """测试空文档"""
        result = parser.parse("")
        assert result.title == "Untitled Document"
        assert result.feature_points == []

    def test_minimal_document(self, parser):
        """测试最小文档"""
        result = parser.parse("# Test\n- Feature: A simple feature")
        assert result.title == "Test"
        assert len(result.feature_points) == 1

    def test_chinese_priority_must(self, parser):
        """测试中文必须优先级"""
        result = parser.parse("# Test\n- Feature: 必须完成的功能")
        assert len(result.feature_points) == 1
        assert result.feature_points[0].priority == Priority.MUST

    def test_chinese_priority_should(self, parser):
        """测试中文应该优先级"""
        result = parser.parse("# Test\n- Feature: 应该实现的功能")
        assert len(result.feature_points) == 1
        assert result.feature_points[0].priority == Priority.SHOULD

    def test_feature_counter(self, parser):
        """测试功能点ID递增"""
        content = """
# Test
- Feature: Feature 1
- Feature: Feature 2
- Feature: Feature 3
"""
        result = parser.parse(content)
        assert len(result.feature_points) == 3
        assert result.feature_points[0].id == "FP-001"
        assert result.feature_points[1].id == "FP-002"
        assert result.feature_points[2].id == "FP-003"

    def test_parse_file(self, parser, tmp_path):
        """测试文件解析"""
        test_file = tmp_path / "test.md"
        test_file.write_text("# Test File\n- Feature: Test feature", encoding='utf-8')

        result = parser.parse_file(str(test_file))
        assert result.title == "Test File"
        assert len(result.feature_points) == 1

    def test_metadata(self, parser, sample_markdown):
        """测试元数据"""
        result = parser.parse(sample_markdown)
        assert "parser_version" in result.metadata
        assert "line_count" in result.metadata
        assert result.metadata["line_count"] > 0


class TestFeaturePoint:
    """FeaturePoint测试"""

    def test_feature_point_creation(self):
        """测试功能点创建"""
        fp = FeaturePoint(
            id="FP-001",
            title="Test Feature",
            description="A test feature",
            priority=Priority.MUST
        )
        assert fp.id == "FP-001"
        assert fp.title == "Test Feature"
        assert fp.priority == Priority.MUST

    def test_feature_point_string(self):
        """测试功能点字符串表示"""
        fp = FeaturePoint(
            id="FP-001",
            title="Test Feature",
            description="A test feature",
            priority=Priority.MUST
        )
        assert "FP-001" in str(fp)
        assert "Test Feature" in str(fp)
