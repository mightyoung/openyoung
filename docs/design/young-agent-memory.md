#VB|# YoungAgent 记忆系统设计
#KM|
#MR|> 版本: 1.1.0
#BP|> 更新日期: 2026-03-02
#BT|
#SM|> 关联: [datacenter-design.md](./datacenter-design.md) - Checkpoint Layer 架构定义

> 版本: 1.1.0
> 更新日期: 2026-03-02

---

## 1. Checkpoint 系统 (来自 Claude Code)

### 1.1 设计理念

Claude Code 的 Checkpoint 系统允许用户在文件编辑前创建快照，支持回滚。YoungAgent 借鉴这一设计：

- **编辑前快照**：每次编辑前自动创建文件快照
- **可回滚**：支持回滚到任意历史版本
- **自动清理**：自动清理过期快照

### 1.2 实现

```python
import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class CheckpointManager:
    """Checkpoint 管理器"""

    def __init__(self, checkpoint_dir: str = ".young/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = 10

    async def create_checkpoint(
        self,
        file_path: str,
        reason: str = "edit"
    ) -> str:
        """创建检查点"""

        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # 生成唯一 ID
        checkpoint_id = f"{file_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 存储路径
        checkpoint_path = self.checkpoint_dir / checkpoint_id
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # 复制文件
        shutil.copy2(file_path, checkpoint_path / file_path.name)

        # 保存元数据
        metadata = {
            "checkpoint_id": checkpoint_id,
            "original_path": str(file_path),
            "reason": reason,
            "created_at": datetime.now().isoformat(),
            "file_size": file_path.stat().st_size
        }

        with open(checkpoint_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # 清理旧检查点
        await self._cleanup_old_checkpoints(file_path.name)

        return checkpoint_id

    async def restore_checkpoint(
        self,
        checkpoint_id: str,
        target_path: str = None
    ) -> bool:
        """恢复检查点"""

        checkpoint_path = self.checkpoint_dir / checkpoint_id

        if not checkpoint_path.exists():
            return False

        # 读取元数据
        with open(checkpoint_path / "metadata.json") as f:
            metadata = json.load(f)

        original_path = target_path or metadata["original_path"]

        # 恢复文件
        source_file = checkpoint_path / Path(original_path).name
        shutil.copy2(source_file, original_path)

        return True

    async def list_checkpoints(self, file_path: str = None) -> list:
        """列出检查点"""

        checkpoints = []

        for checkpoint_dir in self.checkpoint_dir.iterdir():
            if not checkpoint_dir.is_dir():
                continue

            metadata_path = checkpoint_dir / "metadata.json"
            if not metadata_path.exists():
                continue

            with open(metadata_path) as f:
                metadata = json.load(f)

            if file_path is None or metadata["original_path"] == file_path:
                checkpoints.append(metadata)

        return sorted(checkpoints, key=lambda x: x["created_at"], reverse=True)

    async def _cleanup_old_checkpoints(self, file_name: str):
        """清理旧检查点"""

        # 找到相关检查点
        related = [
            d for d in self.checkpoint_dir.iterdir()
            if d.is_dir() and d.name.startswith(file_name)
        ]

        # 只保留最新的
        if len(related) > self.max_checkpoints:
            old = sorted(related, key=lambda x: x.stat().st_mtime)[:-self.max_checkpoints]
            for old_dir in old:
                shutil.rmtree(old_dir)
```

---

## 2. Auto Memory 系统 (来自 Claude Code)

### 2.1 设计理念

Claude Code 的 Auto Memory 系统自动管理对话中的关键信息：

- **重要性判断**：判断信息是否值得记忆
- **自动提取**：从对话中提取关键信息
- **按需加载**：需要时加载相关记忆
- **遗忘机制**：自动清理过期记忆

### 2.2 实现

```python
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid

@dataclass
class Memory:
    """记忆条目"""
    id: str
    content: str
    importance: float  # 0-1
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    tags: List[str] = field(default_factory=list)

class AutoMemory:
    """自动记忆系统"""

    def __init__(
        self,
        max_memories: int = 100,
        importance_threshold: float = 0.5
    ):
        self.max_memories = max_memories
        self.importance_threshold = importance_threshold
        self.memories: List[Memory] = []
        self.llm = None  # 用于判断重要性

    async def add_memory(
        self,
        content: str,
        context: dict = None
    ) -> Memory:
        """添加记忆"""

        # 评估重要性
        importance = await self._evaluate_importance(content, context)

        # 只保留重要记忆
        if importance < self.importance_threshold:
            return None

        memory = Memory(
            id=str(uuid.uuid4()),
            content=content,
            importance=importance,
            created_at=datetime.now(),
            last_accessed=datetime.now()
        )

        self.memories.append(memory)

        # 清理低访问记忆
        await self._cleanup()

        return memory

    async def get_relevant_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Memory]:
        """获取相关记忆"""

        # 简单实现：按重要性排序
        relevant = sorted(
            self.memories,
            key=lambda m: (m.importance, m.access_count),
            reverse=True
        )[:limit]

        # 更新访问信息
        for memory in relevant:
            memory.last_accessed = datetime.now()
            memory.access_count += 1

        return relevant

    async def _evaluate_importance(
        self,
        content: str,
        context: dict
    ) -> float:
        """评估重要性"""

        # 简化实现：基于关键词
        important_keywords = [
            "important", "记住", "don't forget",
            "preference", "配置", "setting"
        ]

        for keyword in important_keywords:
            if keyword.lower() in content.lower():
                return 0.8

        return 0.3

    async def _cleanup(self):
        """清理低价值记忆"""

        if len(self.memories) > self.max_memories:
            # 按访问频率和重要性排序
            self.memories = sorted(
                self.memories,
                key=lambda m: (m.importance, m.access_count),
                reverse=True
            )[:self.max_memories]
```

---

## 3. Skills Progressive Disclosure (来自 Codex) + 统一检索

### 3.1 设计理念

Codex 的 Skills 采用渐进式披露：

1. **索引时**: 只加载元数据 (name + description)
2. **运行时**: 按需加载完整指令
3. **完成后**: 卸载 Skill 释放上下文

**增强**: 新增统一检索层，支持语义搜索

### 3.2 Skill 元数据格式

```yaml
# skill.yaml - Skill 元数据
name: code-reviewer
description: "Reviews code for best practices.
               Use when: PR review, code quality check."
disable_model_invocation: false
trigger_patterns:
  - "review"
  - "PR"
tags:
  - code-review
  - quality
```

### 3.3 SkillLoader 实现 (增强版)

```python
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import yaml

@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str
    description: str
    file_path: Path
    source: str = "local"  # package | evolved | local
    version: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

@dataclass
class LoadedSkill:
    """已加载的 Skill"""
    metadata: SkillMetadata
    content: str
    loaded_at: datetime

@dataclass
class RetrievalConfig:
    """检索配置"""
    mode: str = "hybrid"  # package_only | evolved_only | hybrid
    semantic_enabled: bool = True
    semantic_top_k: int = 5
    semantic_threshold: float = 0.7
    final_top_k: int = 10

class SkillLoader:
    """Skill 加载器 - 渐进式披露 + 统一检索"""

    def __init__(self, skills_dir: Path, config: RetrievalConfig):
        self.skills_dir = skills_dir
        self.config = config
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
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_yaml = skill_dir / "skill.yaml"
            if not skill_yaml.exists():
                continue

            metadata = self._parse_metadata(skill_yaml)
            metadata.source = "local"
            self._metadata_index[metadata.name] = metadata

        # 2. 从 Package Manager 加载 (TODO)
        await self._load_from_package_manager()

        # 3. 从 SkillBank (Evolver) 加载 (TODO)
        await self._load_from_skillbank()

    async def _load_from_package_manager(self):
        """从 Package Manager 加载 Skills"""
        # TODO: 集成 Package Manager
        pass

    async def _load_from_skillbank(self):
        """从 SkillBank (Evolver) 加载进化的 Skills"""
        # TODO: 集成 SkillBank
        pass

    async def _init_retriever(self):
        """初始化统一检索器"""
        try:
            from unified_skill_retriever import UnifiedSkillRetriever
        except ImportError:
            # 回退到简单搜索
            return

        skills = list(self._metadata_index.values())
        self._retriever = UnifiedSkillRetriever(self.config)
        await self._retriever.initialize(skills)

    async def find_skills_for_task(self, task_description: str) -> List[LoadedSkill]:
        """根据任务描述找到相关 Skills - 统一检索入口"""

        if self._retriever and self.config.semantic_enabled:
            # 使用统一检索器 (语义检索)
            results = await self._retriever.retrieve(task_description)

            loaded = []
            for result in results[:self.config.final_top_k]:
                skill = await self.load_skill(result.skill.name)
                if skill:
                    loaded.append(skill)
            return loaded
        else:
            # 回退到简单标签匹配
            return await self._simple_search(task_description)

    async def _simple_search(self, query: str) -> List[LoadedSkill]:
        """简单搜索 (无 Embedding 时回退)"""
        query_lower = query.lower()
        results = []

        for name, metadata in self._metadata_index.items():
            if query_lower in metadata.description.lower():
                skill = await self.load_skill(name)
                if skill:
                    results.append(skill)

        return results[:self.config.final_top_k]

    async def load_skill(self, skill_name: str) -> LoadedSkill:
        """阶段 2: 按需加载完整指令"""

        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        metadata = self._metadata_index.get(skill_name)
        if not metadata:
            return None

        # 加载完整内容
        content = await self._load_skill_content(metadata.file_path)

        loaded = LoadedSkill(
            metadata=metadata,
            content=content,
            loaded_at=datetime.now()
        )

        self._loaded_skills[skill_name] = loaded
        return loaded

    async def unload_skill(self, skill_name: str):
        """阶段 3: 卸载 Skill"""

        if skill_name in self._loaded_skills:
            del self._loaded_skills[skill_name]

    def _parse_metadata(self, skill_yaml: Path) -> SkillMetadata:
        """解析 Skill 元数据"""
        data = yaml.safe_load(skill_yaml.read_text())
        return SkillMetadata(
            name=data.get("name", ""),
            description=data.get("description", ""),
            file_path=skill_yaml.parent,
            tags=data.get("tags", [])
        )

    async def _load_skill_content(self, skill_dir: Path) -> str:
        """加载 Skill 完整内容"""
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text()
        return ""
```

---

## 4. 记忆系统目录结构

```
src/young/
├── agent/               # Agent 主类
├── subagent/           # SubAgent 系统
├── flow/                # FlowSkill
├── session/            # Session 管理
├── loader/             # 配置加载
├── checkpoint/         # Checkpoint
│   ├── __init__.py
│   └── manager.py
├── memory/            # Auto Memory
│   ├── __init__.py
│   └── auto_memory.py
└── skills/            # Skills
    ├── __init__.py
    ├── loader.py      # SkillLoader (含统一检索)
    └── registry.py
```

---

## 5. 与 OpenCode 功能对照

| OpenCode/Codex | Young-Agent | 说明 |
|----------------|-------------|------|
| Checkpoint | CheckpointManager | 文件编辑快照 |
| CLAUDE.md | young.md | 显式记忆 |
| Auto Memory | AutoMemory | 按需加载 |
| Skills Progressive | SkillLoader | 渐进式披露 + 统一检索 |

---

## 6. 设计原则

1. **零外部依赖** - 核心仅使用 Python 标准库
2. **配置驱动** - YAML/Markdown 定义 Agent
3. **权限优先** - 每次工具调用前检查权限
4. **可扩展** - Flow Skill 编排工作流
5. **可成长** - Evolver 自进化能力
6. **可回滚** - Checkpoint 支持文件编辑回滚
7. **记忆分层** - 显式 + 自动分层记忆
8. **渐进加载** - Skills 按需加载避免上下文膨胀
9. **智能检索** - 语义检索 + 多来源统一

---

## 7. 统一检索集成说明

### 7.1 集成位置

SkillLoader 是统一检索层的集成点，负责：

1. **加载多来源 Skills**: 本地 + Package Manager + SkillBank (Evolver)
2. **初始化检索索引**: 构建统一的元数据索引
3. **提供检索入口**: `find_skills_for_task()` 方法

### 7.2 数据流

```
Agent 任务
    │
    ▼
SkillLoader.find_skills_for_task(task)
    │
    ▼
UnifiedSkillRetriever.retrieve(query)
    ├── 精确匹配 (Package Manager)
    ├── 语义检索 (Embedding API)
    └── 标签匹配
    │
    ▼
返回 Top-K Skills
    │
    ▼
SkillLoader.load_skill() → 注入上下文
```

### 7.3 相关文档

- [统一检索层设计](./unified-skill-retriever-design.md)
- [Evolver 设计](./evolver-design.md)
- [Package Manager 设计](./package-manager-design.md)

---

*本文档定义 YoungAgent 记忆系统设计*
