"""
Skill Registry - Skill 注册表
"""

import json
from pathlib import Path

from .loader import SkillLoader
from .metadata import SkillMetadata


class SkillRegistry:
    """Skill 注册表 - 管理 Skill 索引"""

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or Path.home() / ".mightyoung" / "skill_registry.json"
        self._index: dict[str, SkillMetadata] = {}

    def load(self) -> dict[str, SkillMetadata]:
        """从文件加载注册表"""
        if not self.registry_path.exists():
            return {}

        try:
            data = json.loads(self.registry_path.read_text())
            self._index = {}

            for name, item in data.items():
                self._index[name] = SkillMetadata(
                    name=item["name"],
                    description=item["description"],
                    file_path=Path(item["file_path"]),
                    source=item.get("source", "local"),
                    version=item.get("version"),
                    tags=item.get("tags", []),
                )
            return self._index
        except Exception:
            return {}

    def save(self):
        """保存注册表到文件"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for name, metadata in self._index.items():
            data[name] = {
                "name": metadata.name,
                "description": metadata.description,
                "file_path": str(metadata.file_path),
                "source": metadata.source,
                "version": metadata.version,
                "tags": metadata.tags,
            }

        self.registry_path.write_text(json.dumps(data, indent=2))

    def register(self, metadata: SkillMetadata):
        """注册 Skill"""
        self._index[metadata.name] = metadata

    def unregister(self, name: str) -> bool:
        """注销 Skill"""
        if name in self._index:
            del self._index[name]
            return True
        return False

    def get(self, name: str) -> SkillMetadata | None:
        """获取 Skill 元数据"""
        return self._index.get(name)

    def list_all(self) -> list[SkillMetadata]:
        """列出所有 Skills"""
        return list(self._index.values())

    def search_by_tag(self, tag: str) -> list[SkillMetadata]:
        """按标签搜索"""
        tag_lower = tag.lower()
        return [m for m in self._index.values() if any(tag_lower in t.lower() for t in m.tags)]

    def search_by_source(self, source: str) -> list[SkillMetadata]:
        """按来源搜索"""
        return [m for m in self._index.values() if m.source == source]

    def build_from_loader(self, loader: SkillLoader):
        """从 SkillLoader 构建注册表"""
        self._index = loader._metadata_index.copy()
