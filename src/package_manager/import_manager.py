"""
Import Manager - 统一导入入口 + 增量更新
"""

import datetime
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .agent_evaluator import AgentEvaluator, AgentQualityReport
from .agent_retriever import AgentRetriever
from .enhanced_importer import EnhancedGitHubImporter
from .registry import AgentRegistry


class ImportStrategy(Enum):
    """导入策略"""

    CLONE_FULL = "clone_full"  # 完整克隆
    CLONE_LAZY = "clone_lazy"  # 延迟克隆
    API_ONLY = "api_only"  # 仅 API 获取


@dataclass
class ImportRequest:
    """导入请求"""

    url: str
    agent_name: str | None = None
    strategy: ImportStrategy = ImportStrategy.CLONE_FULL
    force: bool = False  # 强制覆盖
    evaluate: bool = True  # 导入后评估


@dataclass
class ImportResult:
    """导入结果"""

    success: bool
    agent_name: str
    version: str
    source_url: str
    quality_report: dict | None = None
    message: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class UpdateResult:
    """更新结果"""

    agent_name: str
    updated: bool
    old_version: str
    new_version: str
    changes: list[str]


class ImportManager:
    """
    统一导入管理器

    功能：
    1. 统一导入入口
    2. 增量更新
    3. 质量评估集成
    4. 版本管理
    """

    def __init__(
        self, packages_dir: str = "packages", registry_path: str = ".young/agent_registry.json"
    ):
        self.packages_dir = Path(packages_dir)
        self.registry_path = Path(registry_path)

        # 依赖模块
        self._registry = AgentRegistry(packages_dir)
        self._retriever = AgentRetriever(packages_dir)
        self._evaluator = AgentEvaluator()
        self._importer = EnhancedGitHubImporter(packages_dir)

        # 注册表缓存
        self._registry_cache: dict[str, dict] = {}
        self._load_registry()

    # ========== 核心 API ==========

    async def import_agent(self, request: ImportRequest) -> ImportResult:
        """
        导入 Agent

        Args:
            request: 导入请求

        Returns:
            ImportResult: 导入结果
        """
        # 1. 解析名称
        agent_name = request.agent_name or self._parse_name(request.url)

        # 2. 检查是否已存在
        existing = self._get_registry_entry(agent_name)
        if existing and not request.force:
            return ImportResult(
                success=False,
                agent_name=agent_name,
                version=existing.get("version", "unknown"),
                source_url=request.url,
                message=f"Agent '{agent_name}' already exists. Use --force to overwrite.",
            )

        # 3. 执行导入
        try:
            use_git_clone = request.strategy == ImportStrategy.CLONE_FULL
            import_result = self._importer.import_from_url(
                url=request.url, agent_name=agent_name, use_git_clone=use_git_clone
            )

            if "error" in import_result:
                return ImportResult(
                    success=False,
                    agent_name=agent_name,
                    version="",
                    source_url=request.url,
                    message=import_result.get("error", "Unknown error"),
                )

            # 4. 获取版本
            version = await self._get_agent_version(agent_name)

            # 5. 质量评估
            quality_report = None
            if request.evaluate:
                report = await self._evaluator.evaluate(self.packages_dir / agent_name)
                quality_report = {
                    "overall_score": report.overall_score,
                    "passed": report.passed,
                    "warnings": report.warnings,
                    "dimensions": [
                        {"dimension": d.dimension.value, "score": d.score, "passed": d.passed}
                        for d in report.dimensions
                    ],
                }

            # 6. 更新注册表
            self._update_registry(
                agent_name,
                {
                    "version": version,
                    "source_url": request.url,
                    "last_updated": datetime.datetime.now().isoformat(),
                    "import_strategy": request.strategy.value,
                    "quality_score": quality_report.get("overall_score")
                    if quality_report
                    else None,
                },
            )

            return ImportResult(
                success=True,
                agent_name=agent_name,
                version=version,
                source_url=request.url,
                quality_report=quality_report,
                message="Import successful",
                warnings=quality_report.get("warnings", []) if quality_report else [],
            )

        except Exception as e:
            return ImportResult(
                success=False,
                agent_name=agent_name,
                version="",
                source_url=request.url,
                message=f"Import failed: {str(e)}",
            )

    async def update_agent(self, agent_name: str) -> UpdateResult:
        """
        更新已安装的 Agent

        Args:
            agent_name: Agent 名称

        Returns:
            UpdateResult: 更新结果
        """
        # 1. 检查是否存在
        entry = self._get_registry_entry(agent_name)
        if not entry:
            return UpdateResult(
                agent_name=agent_name, updated=False, old_version="", new_version="", changes=[]
            )

        old_version = entry.get("version", "unknown")
        source_url = entry.get("source_url")

        # 2. 重新导入（强制覆盖）
        request = ImportRequest(
            url=source_url,
            agent_name=agent_name,
            force=True,
            evaluate=False,  # 更新时跳过评估
        )

        result = await self.import_agent(request)

        if result.success:
            new_version = await self._get_agent_version(agent_name)
            changes = ["version_changed"]
            if old_version != new_version:
                changes.append(f"{old_version} -> {new_version}")

            return UpdateResult(
                agent_name=agent_name,
                updated=True,
                old_version=old_version,
                new_version=new_version,
                changes=changes,
            )

        return UpdateResult(
            agent_name=agent_name,
            updated=False,
            old_version=old_version,
            new_version=old_version,
            changes=[],
        )

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        搜索已安装的 Agent

        Args:
            query: 搜索关键词
            limit: 返回数量

        Returns:
            List[Dict]: 搜索结果
        """
        result = await self._retriever.search(query, limit=limit)

        # 获取注册表中的额外信息
        results = []
        for a in result.agents:
            item = {
                "name": a.name,
                "description": getattr(a, "description", ""),
                "version": a.version,
                "quality_score": getattr(a, "quality_score", None),
            }
            # 添加注册表信息
            registry_info = self._get_registry_entry(a.name) or {}
            item.update(registry_info)
            results.append(item)
        return results

    async def list_agents(self) -> list[dict]:
        """
        列出所有已安装的 Agent

        Returns:
            List[Dict]: Agent 列表
        """
        agents = await self._retriever.list_all()
        results = []
        for a in agents:
            item = {
                "name": a.name,
                "version": a.version,
                "description": getattr(a, "description", ""),
            }
            registry_info = self._get_registry_entry(a.name) or {}
            item.update(registry_info)
            results.append(item)
        return results

    async def evaluate_agent(self, agent_name: str) -> AgentQualityReport | None:
        """
        评估 Agent 质量

        Args:
            agent_name: Agent 名称

        Returns:
            AgentQualityReport: 质量报告
        """
        agent_path = self.packages_dir / agent_name
        if not agent_path.exists():
            return None

        return await self._evaluator.evaluate(agent_path)

    # ========== 辅助方法 ==========

    def _load_registry(self):
        """加载注册表"""
        if self.registry_path.exists():
            try:
                self._registry_cache = json.loads(self.registry_path.read_text(encoding="utf-8"))
            except:
                self._registry_cache = {}
        else:
            self._registry_cache = {}

    def _save_registry(self):
        """保存注册表"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(self._registry_cache, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def _get_registry_entry(self, name: str) -> dict | None:
        """获取注册表条目"""
        return self._registry_cache.get(name)

    def _update_registry(self, name: str, data: dict):
        """更新注册表"""
        if name not in self._registry_cache:
            self._registry_cache[name] = {}
        self._registry_cache[name].update(data)
        self._save_registry()

    def _parse_name(self, url: str) -> str:
        """从 URL 解析名称"""
        # https://github.com/owner/repo -> repo
        parts = url.split("/")
        return parts[-1].replace(".git", "")

    async def _get_agent_version(self, agent_name: str) -> str:
        """获取 Agent 版本"""
        agent_yaml = self.packages_dir / agent_name / "agent.yaml"
        if agent_yaml.exists():
            try:
                import yaml

                config = yaml.safe_load(agent_yaml.read_text(encoding="utf-8"))
                return config.get("version", "1.0.0") if config else "1.0.0"
            except:
                return "1.0.0"
        return "unknown"


# ========== 便捷函数 ==========


def create_import_manager(
    packages_dir: str = "packages", registry_path: str = ".young/agent_registry.json"
) -> ImportManager:
    """创建 ImportManager 实例"""
    return ImportManager(packages_dir, registry_path)
