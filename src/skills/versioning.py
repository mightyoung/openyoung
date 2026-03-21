"""
Skill Versioning - 技能版本化管理

实现规范的技能发布格式，支持语义版本控制和版本升级检查。
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ReleaseType(Enum):
    """发布类型"""

    PATCH = "patch"  # 补丁版本 (bug修复)
    MINOR = "minor"  # 小版本 (新功能)
    MAJOR = "major"  # 主版本 (破坏性变更)


@dataclass
class SkillVersion:
    """语义版本"""

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

    def __repr__(self) -> str:
        return f"SkillVersion({self.major}, {self.minor}, {self.patch})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SkillVersion):
            return False
        return (self.major, self.minor, self.patch) == (
            other.major,
            other.minor,
            other.patch,
        )

    def __lt__(self, other: "SkillVersion") -> bool:
        return (self.major, self.minor, self.patch) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __le__(self, other: "SkillVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SkillVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "SkillVersion") -> bool:
        return not self < other

    @classmethod
    def parse(cls, version_str: str) -> "SkillVersion | None":
        """解析版本字符串"""
        # 移除 'v' 前缀
        version_str = version_str.strip().lstrip("v")

        match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str)
        if not match:
            return None

        try:
            return cls(
                major=int(match.group(1)),
                minor=int(match.group(2)),
                patch=int(match.group(3)),
            )
        except ValueError:
            return None

    def bump(self, release_type: ReleaseType) -> "SkillVersion":
        """根据发布类型升级版本"""
        if release_type == ReleaseType.MAJOR:
            return SkillVersion(self.major + 1, 0, 0)
        elif release_type == ReleaseType.MINOR:
            return SkillVersion(self.major, self.minor + 1, 0)
        else:  # PATCH
            return SkillVersion(self.major, self.minor, self.patch + 1)


@dataclass
class SkillRelease:
    """技能发布信息"""

    version: SkillVersion
    changelog: str
    release_date: str
    download_url: str | None = None
    breaking_changes: list[str] = field(default_factory=list)
    new_features: list[str] = field(default_factory=list)
    bug_fixes: list[str] = field(default_factory=list)
    dependencies: dict[str, str] = field(default_factory=dict)


class SkillVersionManager:
    """技能版本管理器

    管理技能的版本控制、检查更新和安装。
    """

    def __init__(self, skills_dir: Path | None = None):
        self.skills_dir = skills_dir or Path(__file__).parent.parent / "skills"
        self._version_cache: dict[str, SkillVersion] = {}

    def get_installed_version(self, skill_name: str) -> SkillVersion | None:
        """获取已安装的技能版本

        Args:
            skill_name: 技能名称

        Returns:
            当前安装的版本，如果未安装返回 None
        """
        # 优先从缓存获取
        if skill_name in self._version_cache:
            return self._version_cache[skill_name]

        # 从 SKILL.md 的 frontmatter 读取
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            return None

        try:
            content = skill_md.read_text(encoding="utf-8")
            version = self._extract_version_from_content(content)

            if version:
                self._version_cache[skill_name] = version

            return version
        except Exception as e:
            logger.warning(f"Failed to read version for {skill_name}: {e}")
            return None

    def _extract_version_from_content(self, content: str) -> SkillVersion | None:
        """从内容中提取版本号"""
        if not content.startswith("---"):
            return None

        # 提取 frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter = parts[1].strip()

        # 查找 version 字段
        for line in frontmatter.split("\n"):
            if line.startswith("version:"):
                version_str = line.split(":", 1)[1].strip()
                return SkillVersion.parse(version_str)

        return None

    def list_installed_skills(self) -> dict[str, SkillVersion]:
        """列出所有已安装的技能及版本"""
        skills = {}

        if not self.skills_dir.exists():
            return skills

        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            version = self.get_installed_version(skill_dir.name)
            if version:
                skills[skill_dir.name] = version

        return skills

    async def check_updates(self, skill_name: str) -> list[SkillVersion]:
        """检查技能更新

        Args:
            skill_name: 技能名称

        Returns:
            可用的版本列表（从旧到新）
        """
        current = self.get_installed_version(skill_name)

        # TODO(wontfix): 实现从远程仓库检查更新
        # 1. 从 GitHub 检查 releases
        # 2. 从包管理器检查最新版本
        # 3. 从 Skill Bank 检查进化版本

        logger.info(f"Checking updates for {skill_name}, current: {current}")

        return []

    async def install_version(
        self,
        skill_name: str,
        version: SkillVersion,
        source: str = "local",
    ) -> bool:
        """安装指定版本的技能

        Args:
            skill_name: 技能名称
            version: 版本号
            source: 来源 (local, github, package)

        Returns:
            是否安装成功
        """
        logger.info(f"Installing {skill_name} {version} from {source}")

        # TODO(wontfix): 实现安装逻辑
        # 1. 下载技能包
        # 2. 验证签名
        # 3. 解压到 skills 目录
        # 4. 更新版本缓存

        return False

    async def upgrade_latest(self, skill_name: str) -> bool:
        """升级到最新版本

        Args:
            skill_name: 技能名称

        Returns:
            是否升级成功
        """
        updates = await self.check_updates(skill_name)

        if not updates:
            logger.info(f"No updates available for {skill_name}")
            return False

        latest = updates[-1]
        current = self.get_installed_version(skill_name)

        if current and latest <= current:
            logger.info(f"{skill_name} is already at latest version {current}")
            return False

        return await self.install_version(skill_name, latest)

    def create_release(
        self,
        skill_name: str,
        release_type: ReleaseType,
        changelog: str,
        changes: dict[str, list[str]] | None = None,
    ) -> SkillRelease | None:
        """创建新发布

        Args:
            skill_name: 技能名称
            release_type: 发布类型
            changelog: 更新日志
            changes: 变更详情 {new_features: [], bug_fixes: [], breaking_changes: []}

        Returns:
            发布信息
        """
        current = self.get_installed_version(skill_name)
        if not current:
            logger.error(f"Skill {skill_name} not found")
            return None

        new_version = current.bump(release_type)

        changes = changes or {}
        release = SkillRelease(
            version=new_version,
            changelog=changelog,
            release_date=datetime.now().isoformat(),
            new_features=changes.get("new_features", []),
            bug_fixes=changes.get("bug_fixes", []),
            breaking_changes=changes.get("breaking_changes", []),
        )

        # 更新 SKILL.md 的版本
        self._update_version_in_skill(skill_name, new_version)

        # 添加到 CHANGELOG
        self._add_to_changelog(skill_name, release)

        logger.info(f"Created release {new_version} for {skill_name}")
        return release

    def _update_version_in_skill(self, skill_name: str, version: SkillVersion):
        """更新技能文件中的版本号"""
        skill_dir = self.skills_dir / skill_name
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.exists():
            logger.warning(f"SKILL.md not found for {skill_name}")
            return

        try:
            content = skill_md.read_text(encoding="utf-8")

            if not content.startswith("---"):
                logger.warning(f"SKILL.md for {skill_name} has no frontmatter")
                return

            parts = content.split("---", 2)
            frontmatter = parts[1]
            body = parts[2] if len(parts) > 2 else ""

            # 更新版本行
            lines = frontmatter.split("\n")
            new_lines = []
            for line in lines:
                if line.strip().startswith("version:"):
                    new_lines.append(f"version: {version}")
                else:
                    new_lines.append(line)

            new_frontmatter = "\n".join(new_lines)
            new_content = f"---\n{new_frontmatter}\n---\n{body}"

            skill_md.write_text(new_content, encoding="utf-8")

            # 更新缓存
            self._version_cache[skill_name] = version

        except Exception as e:
            logger.error(f"Failed to update version: {e}")

    def _add_to_changelog(self, skill_name: str, release: SkillRelease):
        """添加发布到 CHANGELOG"""
        changelog_path = self.skills_dir / skill_name / "CHANGELOG.md"

        if release.breaking_changes:
            changes = ["\n### 🚨 Breaking Changes"]
            for change in release.breaking_changes:
                changes.append(f"- {change}")

        if release.new_features:
            changes = ["\n### ✨ New Features"]
            for feature in release.new_features:
                changes.append(f"- {feature}")

        if release.bug_fixes:
            changes = ["\n### 🐛 Bug Fixes"]
            for fix in release.bug_fixes:
                changes.append(f"- {fix}")

        changelog_content = f"""# Changelog

## {release.version} - {release.release_date}

{release.changelog}

{"".join(changes) if release.new_features or release.bug_fixes or release.breaking_changes else ""}
"""

        # 追加到现有 CHANGELOG
        if changelog_path.exists():
            existing = changelog_path.read_text(encoding="utf-8")
            changelog_content = existing + "\n" + changelog_content

        changelog_path.write_text(changelog_content, encoding="utf-8")

    def compare_versions(self, v1: SkillVersion, v2: SkillVersion) -> ReleaseType:
        """比较两个版本，确定发布类型

        Returns:
            需要发布的版本类型
        """
        if v2.major > v1.major:
            return ReleaseType.MAJOR
        elif v2.minor > v1.minor:
            return ReleaseType.MINOR
        else:
            return ReleaseType.PATCH


# 全局实例
_default_version_manager: SkillVersionManager | None = None


def get_version_manager() -> SkillVersionManager:
    """获取全局版本管理器"""
    global _default_version_manager
    if _default_version_manager is None:
        _default_version_manager = SkillVersionManager()
    return _default_version_manager


def set_version_manager(manager: SkillVersionManager):
    """设置全局版本管理器"""
    global _default_version_manager
    _default_version_manager = manager
