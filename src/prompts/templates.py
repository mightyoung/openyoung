"""
Prompt Template System - 提示词模板系统
"""

import re
from typing import Optional, Dict, Any
from enum import Enum


class TemplateType(str, Enum):
    """模板类型"""

    DEVIN = "devin"  # 专业开发模式
    WINDSURF = "windsurf"  # 协作编程模式
    MANUS = "manus"  # 通用任务模式
    MINIMAL = "minimal"  # 精简模式


class PromptTemplate:
    """提示词模板

    支持变量替换和模板继承
    """

    def __init__(
        self,
        name: str,
        template_type: TemplateType,
        content: str,
        description: str = "",
        variables: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.template_type = template_type
        self.content = content
        self.description = description
        self.variables = variables or {}

    def render(self, **kwargs) -> str:
        """渲染模板，支持变量替换"""
        result = self.content
        for key, value in {**self.variables, **kwargs}.items():
            pattern = r"\{\{" + re.escape(key) + r"\}\}"
            result = re.sub(pattern, str(value), result)
        return result

    def __str__(self) -> str:
        return f"PromptTemplate({self.name}, type={self.template_type.value})"


class PromptRegistry:
    """提示词模板注册表"""

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_defaults()

    def _register_defaults(self):
        """注册默认模板"""
        # Minimal template
        self.register(
            PromptTemplate(
                name="minimal",
                template_type=TemplateType.MINIMAL,
                description="精简模式 - 简洁快速",
                content="""你是 {{agent_name}}。
{{task_description}}
{{#if tools}}
可用工具: {{tools}}
{{/if}}
{{#if context}}
上下文: {{context}}
{{/if}}
""",
            )
        )

        # Manus template (full)
        self.register(
            PromptTemplate(
                name="manus",
                template_type=TemplateType.MANUS,
                description="通用任务模式 - Manus方法论",
                content="""# 身份定义
你是 {{agent_name}}，一个先进的自主 AI 代理。

# 核心能力
你能够：
- 理解任务、接收指令
- 以接近人类思维的方式解决问题
- 自主执行复杂的、多步骤的任务

# 工作方法论
1. 理解任务：分析用户需求，明确目标
2. 规划步骤：将复杂任务分解为可执行的步骤
3. 执行计划：按步骤执行，必要时调整
4. 验证结果：确保结果符合预期

# 工具规则
{{tools_rules}}

# 安全限制
{{safety_rules}}

# 当前任务
{{task_description}}

{{#if context}}
# 上下文
{{context}}
{{/if}}
""",
            )
        )

        # Devin template
        self.register(
            PromptTemplate(
                name="devin",
                template_type=TemplateType.DEVIN,
                description="专业开发模式 - 规划模式、测试优先",
                content="""# 角色
你是 {{agent_name}}，专业软件工程师。

# 核心原则
- 测试优先 (Test-Driven Development)
- 规划后再行动
- 严谨的代码质量

# 开发流程
1. 分析需求，编写测试
2. 实现功能，使测试通过
3. 重构优化
4. 验证完整

# 工具使用
{{tools_rules}}

# 安全规则
{{safety_rules}}

# 任务
{{task_description}}

{{#if context}}
# 上下文
{{context}}
{{/if}}
""",
            )
        )

        # Windsurf template
        self.register(
            PromptTemplate(
                name="windsurf",
                template_type=TemplateType.WINDSURF,
                description="协作编程模式 - 效率优先",
                content="""# 角色
你是 {{agent_name}}，协作编程助手。

# 核心原则
- 高效执行
- 工具规则优先
- 快速响应

# 工作方式
- 理解意图，快速行动
- 最小化交互
- 最大化产出

# 工具规则
{{tools_rules}}

# 安全规则
{{safety_rules}}

# 任务
{{task_description}}

{{#if context}}
# 上下文
{{context}}
{{/if}}
""",
            )
        )

    def register(self, template: PromptTemplate):
        """注册模板"""
        self._templates[template.name] = template

    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self._templates.get(name)

    def get_by_type(self, template_type: TemplateType) -> Optional[PromptTemplate]:
        """根据类型获取模板"""
        for template in self._templates.values():
            if template.template_type == template_type:
                return template
        return None

    def list_templates(self) -> list[str]:
        """列出所有模板"""
        return list(self._templates.keys())

    def render(self, template_name: str, **kwargs) -> str:
        """渲染指定模板"""
        template = self.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        return template.render(**kwargs)


# 全局注册表
_global_registry: Optional[PromptRegistry] = None


def get_registry() -> PromptRegistry:
    """获取全局注册表"""
    global _global_registry
    if _global_registry is None:
        _global_registry = PromptRegistry()
    return _global_registry


def render_template(template_name: str, **kwargs) -> str:
    """便捷的模板渲染函数"""
    return get_registry().render(template_name, **kwargs)
