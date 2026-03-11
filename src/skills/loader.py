"""
Skill Loader - 渐进式披露 + 统一检索
"""

from datetime import datetime
from pathlib import Path

import yaml

from .metadata import LoadedSkill, RetrievalConfig, SkillMetadata, SkillRequires


class SkillLoader:
    """Skill 加载器 - 渐进式披露 + 统一检索"""

    def __init__(
        self,
        skills_dir: Path | None = None,
        config: RetrievalConfig | None = None,
    ):
        self.skills_dir = skills_dir or Path(__file__).parent.parent / "skills"
        self.config = config or RetrievalConfig()
        self._metadata_index: dict[str, SkillMetadata] = {}
        self._loaded_skills: dict[str, LoadedSkill] = {}

        # 统一检索器
        self._retriever = None

    async def initialize(self):
        """初始化 - 加载所有 Skill 元数据"""
        # 构建元数据索引
        await self._build_metadata_index()

        # 初始化统一检索器
        if self.config.semantic_enabled:
            await self._init_retriever()

    async def _build_metadata_index(self):
        """构建元数据索引"""
        # 1. 从本地 skills 目录加载
        if not self.skills_dir.exists():
            return

        for skill_dir in self.skills_dir.iterdir():
            # 处理子目录 (skills_dir/skill_name/skill.yaml)
            if skill_dir.is_dir():
                skill_yaml = skill_dir / "skill.yaml"
                if not skill_yaml.exists():
                    continue

                metadata = self._parse_metadata(skill_yaml)
                metadata.source = "local"
                self._metadata_index[metadata.name] = metadata
            # 处理根目录的 skill.yaml 文件 (skills_dir/skill.yaml)
            elif skill_dir.suffix in (".yaml", ".yml"):
                if skill_dir.name == "skill.yaml":
                    metadata = self._parse_metadata(skill_dir)
                    metadata.source = "local"
                    self._metadata_index[metadata.name] = metadata

        # 2. 从 Package Manager 加载
        await self._load_from_package_manager()

        # 3. 从 SkillBank (Evolver) 加载
        await self._load_from_skillbank()

    async def _load_from_package_manager(self):
        """从 Package Manager 加载 Skills"""
        try:
            from src.package_manager.manager import PackageManager

            pm = PackageManager()

            # 获取已安装的 skill 包
            packages = pm.list_packages()
            for pkg_name in packages:
                # 查找 skill.yaml
                pkg_dir = pm.storage.get_package_dir(pkg_name)
                if not pkg_dir:
                    continue

                skill_yaml = pkg_dir / "skill.yaml"
                if not skill_yaml.exists():
                    continue

                metadata = self._parse_metadata(skill_yaml)
                metadata.source = "package"
                self._metadata_index[metadata.name] = metadata
        except Exception:
            # Package Manager 可能未初始化，静默失败
            pass

    async def _load_from_skillbank(self):
        """从 SkillBank (Evolver) 加载进化的 Skills"""
        # TODO(future): 集成 Evolver - 需要 evolver 模块完成开发
        pass

    async def _init_retriever(self):
        """初始化统一检索器"""
        try:
            from src.skills.retriever import UnifiedSkillRetriever
        except ImportError:
            # 回退到简单搜索
            return

        skills = list(self._metadata_index.values())
        self._retriever = UnifiedSkillRetriever(self.config)
        await self._retriever.initialize(skills)

    async def find_skills_for_task(self, task_description: str) -> list[LoadedSkill]:
        """根据任务描述找到相关 Skills - 统一检索入口"""
        # 优先尝试语义检索
        if self._retriever and self.config.semantic_enabled:
            results = await self._retriever.retrieve(task_description)

            if results:
                loaded = []
                for result in results[: self.config.final_top_k]:
                    skill = await self.load_skill(result.skill.name)
                    if skill:
                        loaded.append(skill)
                return loaded

        # 回退到简单搜索
        return await self._simple_search(task_description)

    def _tokenize(self, text: str) -> list[str]:
        """分词处理 - 支持中英文"""
        text_lower = text.lower()

        # 尝试使用 jieba 分词
        try:
            import jieba

            words = list(jieba.cut(text_lower))
            return [w for w in words if w.strip()]
        except ImportError:
            pass

        # 回退: 英文按空格, 中文按字符 (2-4gram)
        words = text_lower.split()
        if len(words) == 1 and any("\u4e00" <= c <= "\u9fff" for c in text):
            # 中文: 生成 2-4 字词组
            chinese_text = "".join(c for c in text_lower if "\u4e00" <= c <= "\u9fff")
            ngrams = []
            for n in range(2, 5):
                ngrams.extend([chinese_text[i : i + n] for i in range(len(chinese_text) - n + 1)])
            words = ngrams

        return words

    async def _simple_search(self, query: str) -> list[LoadedSkill]:
        """简单搜索 (无 Embedding 时回退)"""
        query_words = self._tokenize(query)
        results = []

        for name, metadata in self._metadata_index.items():
            # 检查触发模式匹配
            for pattern in metadata.trigger_patterns:
                pattern_lower = pattern.lower()
                if any(pattern_lower in word or word in pattern_lower for word in query_words):
                    skill = await self.load_skill(name)
                    if skill:
                        results.append(skill)
                    break
            else:
                # 检查描述匹配 (任意词匹配)
                desc_lower = metadata.description.lower()
                if any(word in desc_lower for word in query_words):
                    skill = await self.load_skill(name)
                    if skill:
                        results.append(skill)
                # 检查标签匹配
                elif any(any(word in tag.lower() for word in query_words) for tag in metadata.tags):
                    skill = await self.load_skill(name)
                    if skill:
                        results.append(skill)

        return results[: self.config.final_top_k]

    async def load_skill(self, skill_name: str) -> LoadedSkill | None:
        """阶段 2: 按需加载完整指令"""
        # 如果已加载，直接返回
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        metadata = self._metadata_index.get(skill_name)
        if not metadata:
            return None

        # 加载完整内容
        content = await self._load_skill_content(metadata.file_path)

        loaded = LoadedSkill(
            metadata=metadata, content=content, loaded_at=datetime.now().isoformat()
        )

        self._loaded_skills[skill_name] = loaded
        return loaded

    async def unload_skill(self, skill_name: str):
        """阶段 3: 卸载 Skill"""
        if skill_name in self._loaded_skills:
            del self._loaded_skills[skill_name]

    def get_metadata(self, skill_name: str) -> SkillMetadata | None:
        """获取 Skill 元数据（不加载内容）"""
        return self._metadata_index.get(skill_name)

    def list_all_metadata(self) -> list[SkillMetadata]:
        """列出所有 Skill 元数据"""
        return list(self._metadata_index.values())

    def _parse_metadata(self, skill_yaml: Path) -> SkillMetadata:
        """解析 Skill 元数据

        支持两种格式:
        1. skill.yaml - YAML 格式
        2. SKILL.md - YAML frontmatter 格式
        """
        # 优先尝试 SKILL.md (YAML frontmatter)
        skill_md = skill_yaml.parent / "SKILL.md"
        if skill_md.exists():
            metadata = self._parse_frontmatter(skill_md)
            if metadata:
                return metadata

        # 回退到 skill.yaml
        try:
            data = yaml.safe_load(skill_yaml.read_text()) or {}
        except Exception:
            data = {}

        # 解析 requires 字段
        requires_data = data.get("requires", {})
        requires = SkillRequires(
            bins=requires_data.get("bins", []),
            env=requires_data.get("env", []),
        )

        return SkillMetadata(
            name=data.get("name", skill_yaml.parent.name),
            description=data.get("description", ""),
            file_path=skill_yaml.parent,
            tags=data.get("tags", []),
            disable_model_invocation=data.get("disable_model_invocation", False),
            trigger_patterns=data.get("trigger_patterns", []),
            version=data.get("version"),
            always=data.get("always", False),
            requires=requires,
            tools=data.get("tools", []),
        )

    def _parse_frontmatter(self, skill_md: Path) -> SkillMetadata:
        """解析 SKILL.md 的 YAML frontmatter

        格式:
        ---
        name: github
        description: GitHub 操作技能
        version: 1.0.0
        always: false
        requires:
          bins: [gh, git]
          env: [GH_TOKEN]
        tools:
          - create_issue
          - create_pr
        ---

        # Skill 内容...
        """
        try:
            content = skill_md.read_text()
            if not content.startswith("---"):
                return None

            # 提取 frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter = parts[1].strip()
            data = yaml.safe_load(frontmatter) or {}

            # 解析 requires
            requires_data = data.get("requires", {})
            requires = SkillRequires(
                bins=requires_data.get("bins", []),
                env=requires_data.get("env", []),
            )

            return SkillMetadata(
                name=data.get("name", skill_md.parent.name),
                description=data.get("description", ""),
                file_path=skill_md.parent,
                tags=data.get("tags", []),
                version=data.get("version"),
                always=data.get("always", False),
                requires=requires,
                tools=data.get("tools", []),
                trigger_patterns=data.get("trigger_patterns", []),
            )
        except Exception:
            return None

    def check_requirements(self, metadata: SkillMetadata) -> tuple[bool, list[str]]:
        """检查 Skill 依赖是否满足

        Returns:
            (是否满足, 缺失的依赖列表)
        """
        import os
        import shutil

        missing = []

        # 检查 CLI 工具
        for bin in metadata.requires.bins:
            if not shutil.which(bin):
                missing.append(f"bin: {bin}")

        # 检查环境变量
        for env in metadata.requires.env:
            if not os.getenv(env):
                missing.append(f"env: {env}")

        return len(missing) == 0, missing

    def get_always_skills(self) -> list[SkillMetadata]:
        """获取总是加载的 Skills"""
        return [meta for meta in self._metadata_index.values() if meta.always]

    async def _load_skill_content(self, skill_dir: Path) -> str:
        """加载 Skill 完整内容"""
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text()

        # 回退到 README.md
        readme_md = skill_dir / "README.md"
        if readme_md.exists():
            return readme_md.read_text()

        return ""

    def get_loaded_skills(self) -> dict[str, LoadedSkill]:
        """获取所有已加载的 Skills"""
        return self._loaded_skills.copy()

    async def unload_all(self):
        """卸载所有 Skills"""
        self._loaded_skills.clear()
