"""
Skill Install Service - 技能安装服务

处理技能包的下载、安装和卸载
"""

import json
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .models import (
    MarketplaceSkill,
)
from .registry import MarketplaceRegistry


class InstallService:
    """技能安装服务

    处理技能包的下载、安装和卸载
    """

    def __init__(self, registry: MarketplaceRegistry):
        """初始化安装服务

        Args:
            registry: MarketplaceRegistry实例
        """
        self._registry = registry

    def install(
        self,
        skill_name: str,
        version: Optional[str] = None,
        target_dir: str = ".claude/skills",
        force: bool = False,
    ) -> MarketplaceSkill:
        """安装技能

        Args:
            skill_name: 技能名称
            version: 版本 (默认最新)
            target_dir: 目标目录
            force: 强制覆盖

        Returns:
            MarketplaceSkill: 已安装的技能

        Raises:
            ValueError: 技能不存在
        """
        # 获取技能
        skill = self._registry.get_skill_by_name(skill_name, version)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        # 创建目标目录
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)

        # 检查是否已安装
        skill_path = target_path / skill.name
        if skill_path.exists() and not force:
            raise ValueError(f"Skill already installed: {skill_name}. Use force=True to overwrite.")

        # 下载并解压技能包
        if skill.tarball_url:
            self._download_and_extract(skill.tarball_url, skill_path)
        else:
            # 如果没有 tarball，创建空目录
            skill_path.mkdir(parents=True, exist_ok=True)

        # 记录下载
        self._registry.record_download(skill.id, skill.version)

        return skill

    def uninstall(
        self,
        skill_name: str,
        target_dir: str = ".claude/skills",
    ) -> bool:
        """卸载技能

        Args:
            skill_name: 技能名称
            target_dir: 目标目录

        Returns:
            bool: 是否成功
        """
        skill_path = Path(target_dir) / skill_name

        if not skill_path.exists():
            return False

        # 删除目录
        shutil.rmtree(skill_path)
        return True

    def update(
        self,
        skill_name: str,
        target_dir: str = ".claude/skills",
    ) -> MarketplaceSkill:
        """更新技能

        Args:
            skill_name: 技能名称
            target_dir: 目标目录

        Returns:
            MarketplaceSkill: 更新后的技能

        Raises:
            ValueError: 技能未安装或不存在更新
        """
        # 获取技能信息
        skill = self._registry.get_skill_by_name(skill_name)
        if not skill:
            raise ValueError(f"Skill not found: {skill_name}")

        # 检查是否已安装
        skill_path = Path(target_dir) / skill_name
        if not skill_path.exists():
            raise ValueError(f"Skill not installed: {skill_name}")

        # 卸载旧版本
        shutil.rmtree(skill_path)

        # 安装新版本
        return self.install(skill_name, target_dir=target_dir, force=True)

    def list_installed(
        self,
        target_dir: str = ".claude/skills",
    ) -> list[str]:
        """列出已安装的技能

        Args:
            target_dir: 目标目录

        Returns:
            list[str]: 已安装的技能名称列表
        """
        target_path = Path(target_dir)

        if not target_path.exists():
            return []

        installed = []
        for item in target_path.iterdir():
            if item.is_dir():
                # 检查是否是有效的技能目录
                if (item / "manifest.json").exists():
                    installed.append(item.name)

        return installed

    def is_installed(
        self,
        skill_name: str,
        target_dir: str = ".claude/skills",
    ) -> bool:
        """检查技能是否已安装

        Args:
            skill_name: 技能名称
            target_dir: 目标目录

        Returns:
            bool: 是否已安装
        """
        skill_path = Path(target_dir) / skill_name
        return skill_path.exists() and (skill_path / "manifest.json").exists()

    def get_installed_skill_info(
        self,
        skill_name: str,
        target_dir: str = ".claude/skills",
    ) -> Optional[dict]:
        """获取已安装技能的信息

        Args:
            skill_name: 技能名称
            target_dir: 目标目录

        Returns:
            Optional[dict]: 技能信息
        """
        skill_path = Path(target_dir) / skill_name
        manifest_path = skill_path / "manifest.json"

        if not manifest_path.exists():
            return None

        with open(manifest_path) as f:
            return json.load(f)

    def _download_and_extract(
        self,
        url: str,
        target_path: Path,
    ):
        """下载并解压技能包

        Args:
            url: 下载 URL
            target_path: 目标路径
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # 下载
            urllib.request.urlretrieve(url, tmp_path)

            # 解压
            target_path.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tmp_path, "r:gz") as tar:
                tar.extractall(target_path)

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def verify_installation(
        self,
        skill_name: str,
        target_dir: str = ".claude/skills",
    ) -> bool:
        """验证技能安装

        Args:
            skill_name: 技能名称
            target_dir: 目标目录

        Returns:
            bool: 安装是否有效
        """
        skill_path = Path(target_dir) / skill_name

        if not skill_path.exists():
            return False

        # 检查必需文件
        manifest_path = skill_path / "manifest.json"
        if not manifest_path.exists():
            return False

        # 验证 manifest.json 格式
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
                return "name" in manifest and "version" in manifest
        except (OSError, json.JSONDecodeError):
            return False
