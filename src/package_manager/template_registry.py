"""
Template Registry - Agent 模板注册表
"""

import builtins
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .base_registry import BaseRegistry


@dataclass
class Template:
    """模板"""
    name: str
    source: str  # GitHub URL 或 local:路径
    description: str = ""
    rating: float = 0.0
    installs: int = 0
    tags: list[str] = field(default_factory=list)
    author: str = ""
    version: str = "1.0.0"
    source_host: str = "github.com"  # github.com, local
    added_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.added_at


class TemplateRegistry(BaseRegistry):
    """模板注册表"""

    def __init__(self, registry_path: str = "templates/registry.yaml"):
        # 模板注册表使用文件而非目录
        self.registry_path = Path(registry_path)
        self.templates: dict[str, Template] = {}
        # 调用基类但不使用 base_dir（模板使用文件存储）
        # 使用一个虚拟目录
        super().__init__("templates")
        self._load()

    def _load(self):
        """加载注册表"""
        if not self.registry_path.exists():
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            self._save()
            return

        try:
            with open(self.registry_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "templates" in data:
                    for t in data["templates"]:
                        template = Template(**t)
                        self.templates[template.name] = template
        except Exception as e:
            print(f"[Warning] Failed to load registry: {e}")

    def _save(self):
        """保存注册表"""
        data = {
            "templates": [asdict(t) for t in self.templates.values()],
            "updated_at": datetime.now().isoformat(),
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def add(self, template: Template):
        """添加模板"""
        self.templates[template.name] = template
        self._save()

    def remove(self, name: str) -> bool:
        """移除模板"""
        if name in self.templates:
            del self.templates[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> Template | None:
        """获取模板"""
        return self.templates.get(name)

    def list(self, tags: list[str] | None = None, sort_by: str = "rating") -> list[Template]:
        """列出模板"""
        templates = list(self.templates.values())

        # 过滤标签
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]

        # 排序
        if sort_by == "rating":
            templates.sort(key=lambda t: t.rating, reverse=True)
        elif sort_by == "installs":
            templates.sort(key=lambda t: t.installs, reverse=True)
        elif sort_by == "name":
            templates.sort(key=lambda t: t.name)

        return templates

    def search(self, query: str) -> builtins.list[Template]:
        """搜索模板"""
        query = query.lower()
        results = []

        for template in self.templates.values():
            if (query in template.name.lower() or
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)

        return sorted(results, key=lambda t: t.rating, reverse=True)

    def update_stats(self, name: str, rating: float | None = None, installs: int | None = None):
        """更新统计"""
        if name in self.templates:
            template = self.templates[name]
            if rating is not None:
                # 简单平均
                if template.rating > 0:
                    template.rating = (template.rating + rating) / 2
                else:
                    template.rating = rating
            if installs is not None:
                template.installs += installs
            template.updated_at = datetime.now().isoformat()
            self._save()

    def export_json(self) -> str:
        """导出为 JSON"""
        return json.dumps(
            [asdict(t) for t in self.templates.values()],
            indent=2,
            ensure_ascii=False
        )


# ========== 便捷函数 ==========

def get_registry(registry_path: str = "templates/registry.yaml") -> TemplateRegistry:
    """获取注册表实例"""
    return TemplateRegistry(registry_path)


def add_template(
    name: str,
    source: str,
    description: str = "",
    tags: list[str] | None = None,
    author: str = "",
    registry_path: str = "templates/registry.yaml"
) -> Template:
    """添加模板的便捷函数"""
    # 确定 source_host
    source_host = "local"
    if "github.com" in source:
        source_host = "github.com"

    template = Template(
        name=name,
        source=source,
        description=description,
        tags=tags or [],
        author=author,
        source_host=source_host,
    )

    registry = get_registry(registry_path)
    registry.add(template)
    return template
