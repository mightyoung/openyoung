"""
Skill Publish Service - 技能发布服务

处理技能包的创建、验证和发布
"""

import json
import logging
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from .models import (
    MarketplaceSkill,
    PublishOptions,
    SkillCategory,
    SkillManifest,
    SkillStatus,
)
from .registry import MarketplaceRegistry


class PublishService:
    """技能发布服务

    处理技能包的创建、验证和发布
    """

    def __init__(self, registry: MarketplaceRegistry):
        """初始化发布服务

        Args:
            registry: MarketplaceRegistry实例
        """
        self._registry = registry

    def publish(
        self,
        skill_path: str,
        options: Optional[PublishOptions] = None,
    ) -> MarketplaceSkill:
        """发布技能

        Args:
            skill_path: 技能目录路径
            options: 发布选项

        Returns:
            MarketplaceSkill: 已发布的技能

        Raises:
            ValueError: 验证失败
            FileNotFoundError: 技能目录不存在
        """
        options = options or PublishOptions(skill_path=skill_path)

        # 验证技能
        manifest = self._validate_skill(skill_path, options)

        # 创建技能包
        skill = self._create_skill(manifest, skill_path, options)

        # 注册技能
        self._registry.register_skill(skill)

        return skill

    def _validate_skill(
        self,
        skill_path: str,
        options: PublishOptions,
    ) -> SkillManifest:
        """验证技能

        Args:
            skill_path: 技能目录路径
            options: 发布选项

        Returns:
            SkillManifest: 验证后的技能清单

        Raises:
            ValueError: 验证失败
        """
        path = Path(skill_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill path not found: {skill_path}")

        if not path.is_dir():
            raise ValueError(f"Skill path is not a directory: {skill_path}")

        # 读取 manifest.json
        manifest_path = path / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"manifest.json not found in {skill_path}")

        with open(manifest_path) as f:
            manifest_data = json.load(f)

        # 验证必需字段
        required_fields = ["name", "version", "description"]
        for field in required_fields:
            if field not in manifest_data:
                raise ValueError(f"Missing required field: {field}")

        # 验证版本格式
        version = manifest_data["version"]
        if not self._is_valid_version(version):
            raise ValueError(f"Invalid version format: {version}")

        # 创建 SkillManifest
        category_str = manifest_data.get("category", "custom")
        try:
            category = SkillCategory(category_str)
        except ValueError:
            category = SkillCategory.CUSTOM

        manifest = SkillManifest(
            name=manifest_data["name"],
            version=manifest_data["version"],
            description=manifest_data.get("description", ""),
            category=category,
            tags=manifest_data.get("tags", []),
            author=manifest_data.get("author", ""),
            author_url=manifest_data.get("author_url", ""),
            repository_url=manifest_data.get("repository_url", ""),
            homepage=manifest_data.get("homepage", ""),
            license=manifest_data.get("license", "MIT"),
            dependencies=manifest_data.get("dependencies", {}),
            entry_point=manifest_data.get("entry_point", "skill.py"),
        )

        return manifest

    def _is_valid_version(self, version: str) -> bool:
        """验证版本号格式

        Args:
            version: 版本号

        Returns:
            bool: 是否有效
        """
        parts = version.split(".")
        if len(parts) not in (2, 3):
            return False

        for part in parts:
            if not part.isdigit():
                return False

        return True

    def _create_skill(
        self,
        manifest: SkillManifest,
        skill_path: str,
        options: PublishOptions,
    ) -> MarketplaceSkill:
        """创建技能对象

        Args:
            manifest: 技能清单
            skill_path: 技能路径
            options: 发布选项

        Returns:
            MarketplaceSkill: 技能对象
        """
        path = Path(skill_path)

        # 计算文件大小
        file_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        # 创建 tarball
        tarball_path = self._create_tarball(path, manifest.name, manifest.version)

        skill = MarketplaceSkill(
            name=manifest.name,
            display_name=manifest.name.replace("-", " ").title(),
            description=manifest.description,
            version=manifest.version,
            latest_version=manifest.version,
            category=manifest.category,
            tags=manifest.tags,
            author=manifest.author,
            author_url=manifest.author_url,
            repository_url=manifest.repository_url,
            homepage=manifest.homepage,
            license=manifest.license,
            tarball_url=str(tarball_path) if tarball_path else "",
            file_size=file_size,
            status=SkillStatus.PUBLISHED if options.is_public else SkillStatus.DRAFT,
            manifest=manifest,
            engines=manifest.engines,
        )

        return skill

    def _create_tarball(
        self,
        skill_path: Path,
        name: str,
        version: str,
    ) -> Optional[Path]:
        """创建技能压缩包

        Args:
            skill_path: 技能目录
            name: 技能名称
            version: 版本

        Returns:
            Optional[Path]: 压缩包路径
        """
        try:
            tarball_name = f"{name}-{version}.tar.gz"
            tarball_path = Path(tempfile.gettempdir()) / tarball_name

            with tarfile.open(tarball_path, "w:gz") as tar:
                tar.add(skill_path, arcname=name)

            return tarball_path
        except Exception as e:
            logger.warning(f"Failed to create tarball: {e}")
            return None

    def unpublish(self, skill_id: str) -> bool:
        """取消发布技能

        Args:
            skill_id: 技能ID

        Returns:
            bool: 是否成功
        """
        skill = self._registry.get_skill(skill_id)
        if not skill:
            return False

        skill.status = SkillStatus.DRAFT
        return self._registry.register_skill(skill)

    def deprecate(self, skill_id: str) -> bool:
        """废弃技能

        Args:
            skill_id: 技能ID

        Returns:
            bool: 是否成功
        """
        skill = self._registry.get_skill(skill_id)
        if not skill:
            return False

        skill.status = SkillStatus.DEPRECATED
        return self._registry.register_skill(skill)
