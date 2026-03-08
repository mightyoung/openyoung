"""
Prompt Template Tests - Phase 4
"""

import pytest

from src.prompts.templates import (
    PromptRegistry,
    PromptTemplate,
    TemplateType,
    get_registry,
    render_template,
)


class TestPromptTemplate:
    """Test PromptTemplate - Task 4.1"""

    def test_template_creation(self):
        template = PromptTemplate(
            name="test",
            template_type=TemplateType.MINIMAL,
            content="Hello {{name}}",
            description="Test template",
        )
        assert template.name == "test"
        assert template.template_type == TemplateType.MINIMAL

    def test_render_variables(self):
        template = PromptTemplate(
            name="test",
            template_type=TemplateType.MINIMAL,
            content="Hello {{name}}!",
            variables={"name": "World"},
        )
        result = template.render()
        assert result == "Hello World!"

    def test_render_override(self):
        template = PromptTemplate(
            name="test",
            template_type=TemplateType.MINIMAL,
            content="Hello {{name}}!",
            variables={"name": "Default"},
        )
        result = template.render(name="Override")
        assert result == "Hello Override!"


class TestPromptRegistry:
    """Test PromptRegistry"""

    @pytest.fixture
    def registry(self):
        return PromptRegistry()

    def test_default_templates(self, registry):
        """测试默认模板注册"""
        templates = registry.list_templates()
        assert "minimal" in templates
        assert "manus" in templates
        assert "devin" in templates
        assert "windsurf" in templates

    def test_get_template(self, registry):
        template = registry.get("minimal")
        assert template is not None
        assert template.template_type == TemplateType.MINIMAL

    def test_get_by_type(self, registry):
        template = registry.get_by_type(TemplateType.MANUS)
        assert template is not None
        assert template.name == "manus"

    def test_render(self, registry):
        result = registry.render(
            "minimal", agent_name="TestAgent", task_description="Do something"
        )
        assert "TestAgent" in result
        assert "Do something" in result

    def test_render_missing_template(self, registry):
        with pytest.raises(ValueError, match="not found"):
            registry.render("nonexistent", task="test")


class TestGlobalRegistry:
    """Test global registry"""

    def test_get_registry(self):
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_render_template(self):
        result = render_template(
            "minimal", agent_name="Agent", task_description="Test task"
        )
        assert "Agent" in result
        assert "Test task" in result
