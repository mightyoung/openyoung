"""
Tests for StyleProfiler
"""

import pytest

from src.peas.understanding.style_profiler import (
    StyleProfiler,
    StyleProfile,
    ToneStyle,
    DocumentationType,
    profile_document,
)


class TestStyleProfiler:
    """StyleProfiler测试"""

    @pytest.fixture
    def profiler(self):
        return StyleProfiler()

    def test_analyze_empty_content(self, profiler):
        """测试空内容"""
        profile = profiler.analyze("")
        assert profile.doc_type == DocumentationType.UNKNOWN
        assert profile.consistency_score == 1.0

    def test_detect_zh_document(self, profiler):
        """测试中文文档检测"""
        content = """
# 用户认证系统

## 功能需求

- 实现JWT登录
- 实现Token验证
- 实现登出功能
"""
        profile = profiler.analyze(content)
        assert profile.language == "zh"

    def test_detect_en_document(self, profiler):
        """测试英文文档检测"""
        content = """
# User Authentication System

## Features

- Implement JWT login
- Validate tokens
"""
        profile = profiler.analyze(content)
        assert profile.language == "en"

    def test_detect_spec_document(self, profiler):
        """测试规格说明书类型检测"""
        content = """
# 功能需求规格

## 功能需求

- Feature: 用户认证
- Must: 实现JWT登录
"""
        profile = profiler.analyze(content)
        assert profile.doc_type == DocumentationType.SPEC

    def test_detect_api_document(self, profiler):
        """测试API文档类型检测"""
        content = """
# API Documentation

## Endpoints

GET /api/users - Get users
POST /api/users - Create user
"""
        profile = profiler.analyze(content)
        assert profile.doc_type == DocumentationType.API

    def test_detect_tone_technical(self, profiler):
        """测试技术性语调检测"""
        content = """
# System Design

API endpoint with async middleware
Authentication via JWT tokens
Database query optimization
"""
        profile = profiler.analyze(content)
        assert profile.tone == ToneStyle.TECHNICAL

    def test_has_numbered_sections(self, profiler):
        """测试编号章节检测"""
        content = """
1.1 第一步
1.2 第二步
2.1 第三步
"""
        profile = profiler.analyze(content)
        assert profile.has_numbered_sections is True

    def test_uses_bullet_points(self, profiler):
        """测试列表使用检测"""
        content = """
- Item 1
- Item 2
- Item 3
"""
        profile = profiler.analyze(content)
        assert profile.uses_bullet_points is True

    def test_code_examples_count(self, profiler):
        """测试代码示例统计"""
        content = """
# Guide

```python
def hello():
    print("world")
```

Some text

```
console.log("test")
```
"""
        profile = profiler.analyze(content)
        assert profile.code_examples_count == 2

    def test_section_depth(self, profiler):
        """测试章节深度计算"""
        content = "# Title\n## Section 1\n### Section 1.1\n"
        profile = profiler.analyze(content)
        # 最小标题级别是3 (###)
        assert profile.section_depth == 3

    def test_technical_density(self, profiler):
        """测试技术术语密度"""
        content = """
API endpoint with authentication
Using JWT tokens for security
Database optimization
"""
        profile = profiler.analyze(content)
        assert profile.technical_terms_density > 0

    def test_consistency_calculation(self, profiler):
        """测试风格一致性计算"""
        content = """
## Section A
## Section B
## Section C
"""
        profile = profiler.analyze(content)
        assert profile.consistency_score > 0.8

    def test_compare_profiles(self, profiler):
        """测试风格相似度比较"""
        p1 = StyleProfile(
            tone=ToneStyle.TECHNICAL,
            doc_type=DocumentationType.API,
            language="en",
        )
        p2 = StyleProfile(
            tone=ToneStyle.TECHNICAL,
            doc_type=DocumentationType.API,
            language="en",
        )
        similarity = profiler.compare(p1, p2)
        assert similarity == 1.0

    def test_compare_different_profiles(self, profiler):
        """测试不同风格比较"""
        p1 = StyleProfile(
            tone=ToneStyle.TECHNICAL,
            doc_type=DocumentationType.API,
            language="en",
        )
        p2 = StyleProfile(
            tone=ToneStyle.CASUAL,
            doc_type=DocumentationType.GUIDE,
            language="zh",
        )
        similarity = profiler.compare(p1, p2)
        assert similarity < 0.5

    def test_profile_document_function(self):
        """测试便捷函数"""
        content = "# Test Document\n\nSome content"
        profile = profile_document(content)
        assert isinstance(profile, StyleProfile)
        assert profile.doc_type == DocumentationType.UNKNOWN


class TestStyleProfile:
    """StyleProfile数据类测试"""

    def test_profile_str(self):
        """测试字符串表示"""
        profile = StyleProfile(
            tone=ToneStyle.TECHNICAL,
            doc_type=DocumentationType.SPEC,
            language="zh",
            consistency_score=0.9,
        )
        s = str(profile)
        assert "spec" in s
        assert "technical" in s
        assert "zh" in s

    def test_profile_defaults(self):
        """测试默认值"""
        profile = StyleProfile()
        assert profile.tone == ToneStyle.TECHNICAL
        assert profile.doc_type == DocumentationType.UNKNOWN
        assert profile.language == "zh"
        assert profile.avg_sentence_length == 20.0
