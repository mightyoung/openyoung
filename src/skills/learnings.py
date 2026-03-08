"""
Learnings - 结构化的"记忆"

实现 OpenClaw 风格的经验日志系统，自动记录错误和学习，形成可复用的长期记忆。
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """学习记录类型"""

    LEARNING = "learning"  # 学习到的最佳实践
    ERROR = "error"  # 失败的操作
    CORRECTION = "correction"  # 用户的纠正
    FEATURE_REQUEST = "feature_request"  # 功能请求
    IMPROVEMENT = "improvement"  # 改进建议


class Priority(Enum):
    """优先级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LearningEntry:
    """学习条目"""

    id: str
    type: LearningType
    title: str
    description: str
    timestamp: str
    priority: Priority = Priority.MEDIUM
    tags: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    solution: str | None = None
    resolved: bool = False


class LearningsManager:
    """经验日志管理器

    管理 .learnings/ 目录，分类存储各类经验：
    - LEARNINGS.md: 最佳实践和知识更新
    - ERRORS.md: 失败操作和解决方案
    - FEATURE_REQUESTS.md: 功能请求
    """

    LEARNINGS_DIR = ".learnings"
    LEARNINGS_FILE = "LEARNINGS.md"
    ERRORS_FILE = "ERRORS.md"
    FEATURE_REQUESTS_FILE = "FEATURE_REQUESTS.md"

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()
        self.learnings_dir = self.workspace / self.LEARNINGS_DIR
        self._ensure_directory()

    def _ensure_directory(self):
        """确保学习目录存在"""
        if not self.learnings_dir.exists():
            self.learnings_dir.mkdir(parents=True, exist_ok=True)
            self._init_files()

    def _init_files(self):
        """初始化学习文件"""
        files = {
            self.LEARNINGS_FILE: "# Learnings\n\n记录学习到的最佳实践和知识更新\n",
            self.ERRORS_FILE: "# Errors\n\n记录失败的操作、API异常及解决方案\n",
            self.FEATURE_REQUESTS_FILE: "# Feature Requests\n\n记录用户提出的功能请求\n",
        }

        for filename, content in files.items():
            filepath = self.learnings_dir / filename
            if not filepath.exists():
                filepath.write_text(content)

    # ============ 记录方法 ============

    async def log_learning(
        self,
        title: str,
        description: str,
        tags: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> LearningEntry:
        """记录学习 - 最佳实践和知识更新

        Args:
            title: 学习标题
            description: 详细描述
            tags: 标签列表
            context: 上下文信息

        Returns:
            创建的学习条目
        """
        entry = LearningEntry(
            id=self._generate_id(LearningType.LEARNING),
            type=LearningType.LEARNING,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            tags=tags or [],
            context=context or {},
        )

        await self._append_to_file(self.LEARNINGS_FILE, entry)
        logger.info(f"Logged learning: {entry.id} - {title}")

        return entry

    async def log_error(
        self,
        error: Exception,
        context: dict[str, Any],
        solution: str | None = None,
        priority: Priority = Priority.MEDIUM,
    ) -> LearningEntry:
        """记录错误 - 失败的操作和异常

        Args:
            error: 异常对象
            context: 错误上下文
            solution: 解决方案
            priority: 优先级

        Returns:
            创建的错误条目
        """
        entry = LearningEntry(
            id=self._generate_id(LearningType.ERROR),
            type=LearningType.ERROR,
            title=f"{type(error).__name__}: {str(error)[:50]}",
            description=str(error),
            timestamp=datetime.now().isoformat(),
            priority=priority,
            context=context,
            solution=solution,
        )

        await self._append_to_file(self.ERRORS_FILE, entry)
        logger.info(f"Logged error: {entry.id} - {type(error).__name__}")

        return entry

    async def log_correction(
        self,
        correction: str,
        original_action: str,
        context: dict[str, Any] | None = None,
    ) -> LearningEntry:
        """记录纠正 - 用户对智能体的纠正

        Args:
            correction: 纠正内容
            original_action: 原始操作
            context: 上下文信息

        Returns:
            创建的纠正条目
        """
        entry = LearningEntry(
            id=self._generate_id(LearningType.CORRECTION),
            type=LearningType.CORRECTION,
            title=f"Correction: {original_action[:50]}",
            description=correction,
            timestamp=datetime.now().isoformat(),
            priority=Priority.HIGH,
            context=context or {"original_action": original_action},
        )

        await self._append_to_file(self.LEARNINGS_FILE, entry)
        logger.info(f"Logged correction: {entry.id}")

        return entry

    async def log_feature_request(
        self,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> LearningEntry:
        """记录功能请求

        Args:
            title: 功能标题
            description: 功能描述
            context: 上下文信息

        Returns:
            创建的功能请求条目
        """
        entry = LearningEntry(
            id=self._generate_id(LearningType.FEATURE_REQUEST),
            type=LearningType.FEATURE_REQUEST,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            context=context or {},
        )

        await self._append_to_file(self.FEATURE_REQUESTS_FILE, entry)
        logger.info(f"Logged feature request: {entry.id} - {title}")

        return entry

    async def log_improvement(
        self,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
    ) -> LearningEntry:
        """记录改进建议

        Args:
            title: 改进标题
            description: 改进描述
            context: 上下文信息

        Returns:
            创建的改进条目
        """
        entry = LearningEntry(
            id=self._generate_id(LearningType.IMPROVEMENT),
            type=LearningType.IMPROVEMENT,
            title=title,
            description=description,
            timestamp=datetime.now().isoformat(),
            context=context or {},
        )

        await self._append_to_file(self.LEARNINGS_FILE, entry)
        logger.info(f"Logged improvement: {entry.id} - {title}")

        return entry

    # ============ 查询方法 ============

    async def get_recent_errors(self, limit: int = 10) -> list[LearningEntry]:
        """获取最近的错误记录"""
        return await self._read_entries(self.ERRORS_FILE, limit)

    async def get_recent_learnings(self, limit: int = 10) -> list[LearningEntry]:
        """获取最近的学习记录"""
        return await self._read_entries(self.LEARNINGS_FILE, limit)

    async def get_unresolved_errors(self) -> list[LearningEntry]:
        """获取未解决的错误"""
        entries = await self._read_entries(self.ERRORS_FILE, 100)
        return [e for e in entries if not e.resolved]

    async def search(self, query: str, file_type: LearningType | None = None) -> list[LearningEntry]:
        """搜索学习记录

        Args:
            query: 搜索关键词
            file_type: 限定文件类型

        Returns:
            匹配的学习条目列表
        """
        results = []
        files = [self.LEARNINGS_FILE, self.ERRORS_FILE, self.FEATURE_REQUESTS_FILE]

        if file_type == LearningType.LEARNING:
            files = [self.LEARNINGS_FILE]
        elif file_type == LearningType.ERROR:
            files = [self.ERRORS_FILE]
        elif file_type == LearningType.FEATURE_REQUEST:
            files = [self.FEATURE_REQUESTS_FILE]

        for filename in files:
            entries = await self._read_entries(filename, 100)
            for entry in entries:
                if query.lower() in entry.title.lower() or query.lower() in entry.description.lower():
                    results.append(entry)

        return results

    # ============ 辅助方法 ============

    def _generate_id(self, learning_type: LearningType) -> str:
        """生成唯一ID"""
        date_str = datetime.now().strftime("%Y%m%d")
        import random

        random_suffix = f"{random.randint(0, 999):03d}"
        prefix = {
            LearningType.LEARNING: "LRN",
            LearningType.ERROR: "ERR",
            LearningType.CORRECTION: "COR",
            LearningType.FEATURE_REQUEST: "FR",
            LearningType.IMPROVEMENT: "IMP",
        }.get(learning_type, "UNK")

        return f"{prefix}-{date_str}-{random_suffix}"

    async def _append_to_file(self, filename: str, entry: LearningEntry):
        """追加条目到文件"""
        filepath = self.learnings_dir / filename
        if not filepath.exists():
            self._ensure_directory()

        content = self._format_entry(entry)
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(content)

    def _format_entry(self, entry: LearningEntry) -> str:
        """格式化条目为 Markdown"""
        priority_emoji = {
            Priority.LOW: "🟢",
            Priority.MEDIUM: "🟡",
            Priority.HIGH: "🟠",
            Priority.CRITICAL: "🔴",
        }

        tags_str = ", ".join(f"`{tag}`" for tag in entry.tags) if entry.tags else "无"

        lines = [
            f"\n## {entry.id} {priority_emoji.get(entry.priority, '')}",
            f"\n**时间**: {entry.timestamp}",
            f"\n**标题**: {entry.title}",
            f"\n**类型**: {entry.type.value}",
            f"\n**标签**: {tags_str}",
            f"\n**描述**:",
            f"\n{entry.description}",
        ]

        if entry.context:
            lines.append(f"\n**上下文**:")
            for key, value in entry.context.items():
                lines.append(f"- {key}: `{value}`")

        if entry.solution:
            lines.append(f"\n**解决方案**:")
            lines.append(f"\n{entry.solution}")

        if entry.resolved:
            lines.append(f"\n**状态**: ✅ 已解决")

        lines.append("\n---\n")

        return "\n".join(lines)

    async def _read_entries(self, filename: str, limit: int = 10) -> list[LearningEntry]:
        """读取条目"""
        filepath = self.learnings_dir / filename
        if not filepath.exists():
            return []

        entries = []
        current_entry: dict | None = None

        for line in filepath.read_text(encoding="utf-8").split("\n"):
            if line.startswith("## "):
                if current_entry:
                    entry = self._parse_entry(current_entry)
                    if entry:
                        entries.append(entry)
                current_entry = {"id": line[3:].split(" ")[0], "raw": [line]}
            elif current_entry:
                current_entry["raw"].append(line)

        if current_entry:
            entry = self._parse_entry(current_entry)
            if entry:
                entries.append(entry)

        # 按时间倒序返回
        entries.sort(key=lambda x: x.timestamp, reverse=True)
        return entries[:limit]

    def _parse_entry(self, data: dict) -> LearningEntry | None:
        """解析条目"""
        raw_lines = data.get("raw", [])
        if not raw_lines:
            return None

        try:
            entry_type = LearningType.LEARNING
            title = ""
            description = ""
            timestamp = ""
            priority = Priority.MEDIUM
            tags: list[str] = []
            context = {}
            solution = None
            resolved = False

            for line in raw_lines:
                line = line.strip()
                if line.startswith("**时间**:"):
                    timestamp = line.split(":", 1)[1].strip()
                elif line.startswith("**标题**:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("**类型**:"):
                    try:
                        entry_type = LearningType(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("**标签**:"):
                    tag_str = line.split(":", 1)[1].strip()
                    if tag_str != "无":
                        tags = [t.strip("`") for t in tag_str.split(", ")]
                elif line.startswith("**描述**:"):
                    description = ""
                elif line.startswith("**上下文**:"):
                    context = {}
                elif line.startswith("- ") and ":" in line and "上下文" not in line:
                    # 解析上下文键值对
                    pass
                elif line.startswith("**解决方案**:"):
                    solution = ""
                elif line.startswith("**状态**:"):
                    resolved = "已解决" in line
                elif description and line and not line.startswith("#") and not line.startswith("**"):
                    description += line + "\n"

            return LearningEntry(
                id=data.get("id", ""),
                type=entry_type,
                title=title,
                description=description.strip(),
                timestamp=timestamp,
                priority=priority,
                tags=tags,
                context=context,
                solution=solution,
                resolved=resolved,
            )
        except Exception as e:
            logger.warning(f"Failed to parse entry: {e}")
            return None


# 全局实例
_default_learnings_manager: LearningsManager | None = None


def get_learnings_manager() -> LearningsManager:
    """获取全局经验日志管理器"""
    global _default_learnings_manager
    if _default_learnings_manager is None:
        _default_learnings_manager = LearningsManager()
    return _default_learnings_manager


def set_learnings_manager(manager: LearningsManager):
    """设置全局经验日志管理器"""
    global _default_learnings_manager
    _default_learnings_manager = manager
