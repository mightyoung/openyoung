"""
Skill Creator 模块

提供技能创建的标准化模板和工具:
- SkillTemplate: 技能模板定义
- SkillCreator: 技能创建器
- 内置模板: Code, Review, Test

参考 ClawHub Skill Creator 架构
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """技能分类"""

    CODE = "code"
    REVIEW = "review"
    TEST = "test"
    DATA = "data"
    DEVOPS = "devops"
    RESEARCH = "research"
    CUSTOM = "custom"


class TriggerType(Enum):
    """触发类型"""

    KEYWORD = "keyword"
    PATTERN = "pattern"
    SCHEDULE = "schedule"
    EVENT = "event"
    MANUAL = "manual"


@dataclass
class SkillAction:
    """技能动作定义"""

    name: str
    description: str
    handler: Optional[Callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillTemplate:
    """技能模板"""

    name: str
    description: str
    category: SkillCategory
    trigger: TriggerType
    trigger_value: str  # 关键词、正则表达式等
    actions: List[SkillAction] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CreatedSkill:
    """创建的技能"""

    name: str
    path: Path
    template: SkillTemplate
    files: Dict[str, str] = field(default_factory=dict)  # 文件名 -> 内容


class TemplateRegistry:
    """内置模板注册中心"""

    TEMPLATES: Dict[str, SkillTemplate] = {}

    @classmethod
    def register(cls, name: str, template: SkillTemplate):
        cls.TEMPLATES[name] = template

    @classmethod
    def get(cls, name: str) -> Optional[SkillTemplate]:
        return cls.TEMPLATES.get(name)

    @classmethod
    def list_templates(cls) -> List[str]:
        return list(cls.TEMPLATES.keys())


def _create_code_template() -> SkillTemplate:
    """创建代码生成模板"""
    return SkillTemplate(
        name="code_generator",
        description="根据需求生成代码",
        category=SkillCategory.CODE,
        trigger=TriggerType.KEYWORD,
        trigger_value="写代码",
        actions=[
            SkillAction(
                name="analyze_requirement", description="分析需求", parameters={"required": True}
            ),
            SkillAction(
                name="generate_code", description="生成代码", parameters={"language": "python"}
            ),
            SkillAction(name="add_tests", description="添加测试", parameters={"required": False}),
        ],
        validation_rules={
            "min_score": 0.7,
            "check_syntax": True,
            "check_types": True,
        },
    )


def _create_review_template() -> SkillTemplate:
    """创建代码审查模板"""
    return SkillTemplate(
        name="code_reviewer",
        description="审查代码质量",
        category=SkillCategory.REVIEW,
        trigger=TriggerType.KEYWORD,
        trigger_value="审查代码",
        actions=[
            SkillAction(
                name="check_style", description="检查代码风格", parameters={"standard": "pep8"}
            ),
            SkillAction(name="find_bugs", description="查找潜在bug", parameters={"level": "basic"}),
            SkillAction(
                name="suggest_improvements",
                description="建议改进",
                parameters={"max_suggestions": 5},
            ),
        ],
        validation_rules={
            "check_security": True,
            "check_performance": True,
        },
    )


def _create_test_template() -> SkillTemplate:
    """创建测试生成模板"""
    return SkillTemplate(
        name="test_generator",
        description="生成测试用例",
        category=SkillCategory.TEST,
        trigger=TriggerType.KEYWORD,
        trigger_value="生成测试",
        actions=[
            SkillAction(
                name="analyze_code", description="分析待测代码", parameters={"required": True}
            ),
            SkillAction(
                name="generate_unit_tests",
                description="生成单元测试",
                parameters={"framework": "pytest"},
            ),
            SkillAction(
                name="generate_integration_tests",
                description="生成集成测试",
                parameters={"required": False},
            ),
        ],
        validation_rules={
            "min_coverage": 80,
            "check_edge_cases": True,
        },
    )


def _create_data_analysis_template() -> SkillTemplate:
    """创建数据分析模板"""
    return SkillTemplate(
        name="data_analysis",
        description="数据分析与可视化",
        category=SkillCategory.DATA,
        trigger=TriggerType.KEYWORD,
        trigger_value="分析数据",
        actions=[
            SkillAction(
                name="load_data",
                description="加载数据",
                parameters={"formats": ["csv", "json", "excel"]},
            ),
            SkillAction(
                name="explore_data", description="探索数据", parameters={"statistics": True}
            ),
            SkillAction(
                name="visualize",
                description="生成可视化",
                parameters={"charts": ["bar", "line", "scatter"]},
            ),
        ],
        validation_rules={
            "check_nulls": True,
            "check_duplicates": True,
        },
    )


def _create_research_template() -> SkillTemplate:
    """创建研究调查模板"""
    return SkillTemplate(
        name="research",
        description="信息收集与研究",
        category=SkillCategory.RESEARCH,
        trigger=TriggerType.KEYWORD,
        trigger_value="研究",
        actions=[
            SkillAction(
                name="search", description="搜索信息", parameters={"sources": ["web", "docs"]}
            ),
            SkillAction(name="summarize", description="总结要点", parameters={"max_points": 5}),
            SkillAction(name="cite", description="引用来源", parameters={"format": "apa"}),
        ],
        validation_rules={
            "verify_sources": True,
            "min_sources": 3,
        },
    )


# 注册内置模板
TemplateRegistry.register("code", _create_code_template())
TemplateRegistry.register("review", _create_review_template())
TemplateRegistry.register("test", _create_test_template())
TemplateRegistry.register("data_analysis", _create_data_analysis_template())
TemplateRegistry.register("research", _create_research_template())


class SkillCreator:
    """技能创建器

    提供标准化的技能创建流程:
    1. 选择模板
    2. 自定义配置
    3. 生成技能文件
    4. 验证有效性
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("skills")
        self._templates = TemplateRegistry.TEMPLATES.copy()

    def register_template(self, name: str, template: SkillTemplate):
        """注册自定义模板

        Args:
            name: 模板名称
            template: 模板实例
        """
        self._templates[name] = template

    def create_from_template(
        self, template_name: str, skill_name: str, customizations: Optional[Dict[str, Any]] = None
    ) -> CreatedSkill:
        """从模板创建技能

        Args:
            template_name: 模板名称
            skill_name: 技能名称
            customizations: 自定义配置

        Returns:
            创建的技能

        Raises:
            ValueError: 模板不存在
        """
        template = self._templates.get(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")

        customizations = customizations or {}

        # 应用自定义配置
        skill_path = self.output_dir / skill_name

        # 生成文件
        files = self._generate_files(template, skill_name, customizations)

        return CreatedSkill(
            name=skill_name,
            path=skill_path,
            template=template,
            files=files,
        )

    def _generate_files(
        self, template: SkillTemplate, skill_name: str, customizations: Dict[str, Any]
    ) -> Dict[str, str]:
        """生成技能文件"""
        files = {}

        # SKILL.md
        files["SKILL.md"] = self._generate_skill_md(template, skill_name, customizations)

        # __init__.py
        files["__init__.py"] = f'"""Skill: {skill_name}"""\n'

        # main.py (可选)
        if template.category == SkillCategory.CODE:
            files["main.py"] = self._generate_main_py(template, customizations)

        return files

    def _generate_skill_md(
        self, template: SkillTemplate, skill_name: str, customizations: Dict[str, Any]
    ) -> str:
        """生成 SKILL.md"""
        lines = [
            f"# {skill_name}",
            "",
            f"> {template.description}",
            "",
            "## Metadata",
            "",
            f"- **Category**: {template.category.value}",
            f"- **Trigger**: {template.trigger.value}: `{template.trigger_value}`",
            "- **Version**: 1.0.0",
            "",
            "## Actions",
            "",
        ]

        for action in template.actions:
            lines.append(f"### {action.name}")
            lines.append("")
            lines.append(f"_{action.description}_")
            lines.append("")

        lines.extend(
            [
                "## Usage",
                "",
                f"Trigger with: `{template.trigger_value}`",
                "",
                "## Validation",
                "",
            ]
        )

        for key, value in template.validation_rules.items():
            lines.append(f"- **{key}**: {value}")

        return "\n".join(lines)

    def _generate_main_py(self, template: SkillTemplate, customizations: Dict[str, Any]) -> str:
        """生成 main.py"""
        return f'''"""Main entry point for {template.name}"""

from typing import Any, Dict

async def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the skill"""
    # TODO(wontfix): Implement skill logic
    return {{
        "status": "success",
        "data": input_data
    }}

if __name__ == "__main__":
    import asyncio
    result = asyncio.run(execute({{"test": "data"}}))
    print(result)
'''

    def save_skill(self, skill: CreatedSkill) -> Path:
        """保存技能到磁盘

        Args:
            skill: 创建的技能

        Returns:
            技能目录路径
        """
        skill.path.mkdir(parents=True, exist_ok=True)

        for filename, content in skill.files.items():
            file_path = skill.path / filename
            file_path.write_text(content, encoding="utf-8")

        logger.info(f"Saved skill to: {skill.path}")
        return skill.path

    def validate_skill(self, skill: CreatedSkill) -> bool:
        """验证技能有效性

        Args:
            skill: 创建的技能

        Returns:
            是否有效
        """
        # 基本检查
        if not skill.name:
            return False

        if not skill.template:
            return False

        # 检查必需的文件
        if "SKILL.md" not in skill.files:
            return False

        return True


# 便捷函数
def create_skill(
    name: str, template: str = "code", output_dir: Optional[Path] = None, save: bool = True
) -> CreatedSkill:
    """创建技能

    Args:
        name: 技能名称
        template: 模板名称
        output_dir: 输出目录
        save: 是否保存到磁盘

    Returns:
        创建的技能
    """
    creator = SkillCreator(output_dir)
    skill = creator.create_from_template(template, name)

    if save:
        creator.save_skill(skill)

    return skill


def list_templates() -> List[str]:
    """列出可用模板"""
    return TemplateRegistry.list_templates()


__all__ = [
    "SkillCategory",
    "TriggerType",
    "SkillAction",
    "SkillTemplate",
    "CreatedSkill",
    "TemplateRegistry",
    "SkillCreator",
    "create_skill",
    "list_templates",
]
