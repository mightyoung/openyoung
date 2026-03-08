"""
Hub Template Module
模板注册器
"""

from .registry import (
    Template,
    TemplateRegistry,
    add_template,
    get_registry,
)

__all__ = [
    "Template",
    "TemplateRegistry",
    "get_registry",
    "add_template",
]
