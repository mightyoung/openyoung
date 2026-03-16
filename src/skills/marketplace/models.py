"""
Skill Marketplace Models - 技能市场数据模型

基于 npm registry 和 Vercel Skills 设计
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SkillStatus(str, Enum):
    """技能状态"""

    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ReleaseType(str, Enum):
    """发布类型"""

    MAJOR = "major"  # 破坏性更新
    MINOR = "minor"  # 新功能
    PATCH = "patch"  # 修复


class SkillCategory(str, Enum):
    """技能分类"""

    CODE = "code"  # 代码生成
    REVIEW = "review"  # 代码审查
    TEST = "test"  # 测试
    DATA = "data"  # 数据处理
    DEVOPS = "devops"  # DevOps
    RESEARCH = "research"  # 研究
    SECURITY = "security"  # 安全
    UTILITY = "utility"  # 工具
    CUSTOM = "custom"  # 自定义


@dataclass
class SkillManifest:
    """技能清单 - 描述技能包内容"""

    # 基础信息
    name: str = ""
    version: str = "1.0.0"
    description: str = ""

    # 分类
    category: SkillCategory = SkillCategory.CUSTOM
    tags: list[str] = field(default_factory=list)

    # 作者
    author: str = ""
    author_url: str = ""

    # 仓库
    repository_url: str = ""
    homepage: str = ""
    license: str = "MIT"

    # 依赖
    dependencies: dict[str, str] = field(default_factory=dict)  # name -> version
    peer_dependencies: dict[str, str] = field(default_factory=dict)

    # 触发器
    trigger_keywords: list[str] = field(default_factory=list)
    trigger_patterns: list[str] = field(default_factory=list)

    # 入口
    entry_point: str = "skill.py"
    readme: str = ""

    # 元数据
    keywords: list[str] = field(default_factory=list)
    engines: dict[str, str] = field(default_factory=dict)  # {"openyoung": ">=1.0.0"}

    # 评分相关
    rating: float = 0.0
    rating_count: int = 0

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category.value,
            "tags": self.tags,
            "author": self.author,
            "repository": self.repository_url,
            "homepage": self.homepage,
            "license": self.license,
            "dependencies": self.dependencies,
            "keywords": self.keywords,
            "rating": self.rating,
            "rating_count": self.rating_count,
        }


@dataclass
class MarketplaceSkill:
    """市场技能 - 完整的技能条目"""

    # ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # 基础信息
    name: str = ""
    display_name: str = ""
    description: str = ""

    # 版本
    version: str = "1.0.0"
    latest_version: str = "1.0.0"
    versions: list[str] = field(default_factory=list)

    # 分类
    category: SkillCategory = SkillCategory.CUSTOM
    tags: list[str] = field(default_factory=list)

    # 作者
    author: str = ""
    author_email: str = ""
    author_url: str = ""

    # 仓库
    repository_url: str = ""
    homepage: str = ""
    license: str = "MIT"

    # 包信息
    tarball_url: str = ""  # 下载地址
    file_size: int = 0

    # 统计
    download_count: int = 0
    rating: float = 0.0
    rating_count: int = 0

    # 状态
    status: SkillStatus = SkillStatus.DRAFT

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: datetime = field(default_factory=datetime.now)

    # 清单
    manifest: Optional[SkillManifest] = None

    # 兼容性
    engines: dict[str, str] = field(default_factory=dict)

    def to_registry_format(self) -> dict:
        """转换为registry格式"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category.value,
            "author": {
                "name": self.author,
                "email": self.author_email,
                "url": self.author_url,
            },
            "repository": {
                "type": "git",
                "url": self.repository_url,
            },
            "homepage": self.homepage,
            "license": self.license,
            "downloads": self.download_count,
            "rating": {
                "average": self.rating,
                "count": self.rating_count,
            },
            "versions": {
                self.version: {
                    "tarball": self.tarball_url,
                    "size": self.file_size,
                    "engines": self.engines,
                }
            },
        }


@dataclass
class SkillReview:
    """技能评价"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_id: str = ""
    skill_version: str = ""

    # 用户
    user_id: str = ""
    user_name: str = ""

    # 评价
    rating: int = 5  # 1-5
    title: str = ""
    comment: str = ""

    # 反馈
    helpful_count: int = 0
    not_helpful_count: int = 0

    # 状态
    is_verified: bool = False  # 是否已验证安装

    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SkillDownload:
    """技能下载记录"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    skill_id: str = ""
    version: str = ""

    # 客户端信息
    client_id: str = ""
    client_version: str = ""
    platform: str = ""

    # 时间
    downloaded_at: datetime = field(default_factory=datetime.now)


@dataclass
class SkillUpdate:
    """技能更新信息"""

    skill_id: str = ""
    current_version: str = ""
    latest_version: str = ""
    update_type: ReleaseType = ReleaseType.PATCH
    changelog: str = ""
    release_notes: str = ""


@dataclass
class SearchFilters:
    """搜索过滤器"""

    query: str = ""
    category: Optional[SkillCategory] = None
    tags: list[str] = field(default_factory=list)

    # 排序
    sort_by: str = "relevance"  # relevance | downloads | rating | newest
    sort_order: str = "desc"  # asc | desc

    # 分页
    page: int = 1
    page_size: int = 20

    # 过滤
    is_featured: Optional[bool] = None
    is_deprecated: bool = False
    min_rating: float = 0.0


@dataclass
class SearchResult:
    """搜索结果"""

    skills: list[MarketplaceSkill]
    total_count: int
    page: int
    page_size: int
    total_pages: int

    # 聚合
    categories: dict[str, int] = field(default_factory=dict)  # category -> count
    tags: dict[str, int] = field(default_factory=dict)  # tag -> count


@dataclass
class InstallOptions:
    """安装选项"""

    skill_name: str = ""
    version: str = ""  # 空表示最新版本

    # 目标路径
    target_dir: str = ".claude/skills"

    # 行为
    force: bool = False
    save_exact: bool = True  # 精确版本

    # 依赖
    include_deps: bool = True
    optional_deps: bool = False


@dataclass
class PublishOptions:
    """发布选项"""

    # 来源
    skill_path: str = ""

    # 访问
    is_public: bool = True
    access_token: str = ""

    # 发布
    skip_validation: bool = False
    skip_tests: bool = False


# 类型别名
SkillList = list[MarketplaceSkill]
ReviewList = list[SkillReview]
