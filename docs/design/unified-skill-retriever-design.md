# Unified Skill Retrieval Layer 设计

> 版本: 1.0.0
> 更新日期: 2026-03-02
> 目标: 协调 Package Manager 与 SkillBank 的技能检索

---

## 1. 设计目标

| 目标 | 说明 |
|------|------|
| **统一入口** | 单一的 Skill 检索 API |
| **双轨检索** | Package Manager 精确匹配 + SkillBank 语义检索 |
| **智能合并** | 多来源结果智能排序与去重 |
| **无冲突** | 清晰的优先级和来源标注 |
| **可扩展** | 支持新增 Skill 来源 |

---

## 2. 核心类设计

### 2.1 UnifiedSkillRetriever

```python
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from enum import Enum
import numpy as np

class SkillSource(Enum):
    """Skill 来源枚举"""
    PACKAGE = "package"           # Package Manager 安装
    EVOLVED = "evolved"          # Evolver 进化生成
    LOCAL = "local"              # 本地定义
    HYBRID = "hybrid"            # 混合来源

@dataclass
class SkillMetadata:
    """统一的 Skill 元数据"""
    skill_id: str
    name: str
    description: str

    # 来源信息
    source: SkillSource
    sources: Set[SkillSource] = field(default_factory=set)  # 多来源

    # 版本信息
    version: Optional[str] = None
    versions: Dict[SkillSource, str] = field(default_factory=dict)

    # 检索相关
    embedding: Optional[List[float]] = None  # 语义向量
    tags: List[str] = field(default_factory=list)

    # 优先级
    priority: int = 100  # 越小越高

    # 原始引用
    package_ref: Optional[str] = None  # Package Manager 引用
    capsule_ref: Optional[str] = None   # Capsule 引用

@dataclass
class RetrievalResult:
    """检索结果"""
    skill: SkillMetadata
    score: float
    match_type: str  # "exact" | "semantic" | "tag" | "hybrid"
    source: SkillSource

@dataclass
class RetrievalConfig:
    """检索配置"""
    # 检索模式
    mode: str = "hybrid"  # "package_only" | "evolved_only" | "hybrid"

    # 语义检索配置
    semantic_enabled: bool = True
    semantic_top_k: int = 5
    semantic_threshold: float = 0.7

    # 精确匹配配置
    exact_enabled: bool = True
    exact_weight: float = 1.0

    # 标签匹配配置
    tag_enabled: bool = True
    tag_weight: float = 0.5

    # 合并配置
    merge_strategy: str = "score_weighted"  # "score_weighted" | "priority_first" | "source_priority"
    final_top_k: int = 10

    # 来源优先级 (越小越高)
    source_priority: Dict[SkillSource, int] = field(default_factory=lambda: {
        SkillSource.EVOLVED: 1,
        SkillSource.LOCAL: 2,
        SkillSource.HYBRID: 3,
        SkillSource.PACKAGE: 4,
    })

class UnifiedSkillRetriever:
    """统一 Skill 检索器"""

    def __init__(self, config: RetrievalConfig):
        self.config = config
        self.package_retriever = None  # Package Manager 检索器
        self.skillbank_retriever = None  # SkillBank 检索器
        self.unified_index: Dict[str, SkillMetadata] = {}
        self._initialized = False

    async def initialize(
        self,
        package_skills: List[SkillMetadata],
        evolved_skills: List[SkillMetadata]
    ) -> None:
        """初始化统一索引"""
        # 1. 构建统一索引
        for skill in package_skills + evolved_skills:
            if skill.skill_id in self.unified_index:
                # 已存在，合并来源
                existing = self.unified_index[skill.skill_id]
                existing.sources.add(skill.source)
                existing.versions[skill.source] = skill.version

                # 取最新的版本
                if skill.version and (not existing.version or
                    self._compare_version(skill.version, existing.version) > 0):
                    existing.version = skill.version
            else:
                self.unified_index[skill.skill_id] = skill

        # 2. 预计算 (如果启用语义检索)
        if self.config.semantic_enabled:
            await self._build_semantic_index()

        self._initialized = True

    async def retrieve(self, query: str) -> List[RetrievalResult]:
        """统一检索入口"""
        if not self._initialized:
            raise RuntimeError("UnifiedSkillRetriever not initialized")

        results: List[RetrievalResult] = []

        # 1. 精确匹配 (Package Manager)
        if self.config.exact_enabled:
            exact_results = await self._exact_search(query)
            results.extend(exact_results)

        # 2. 语义检索 (SkillBank)
        if self.config.semantic_enabled:
            semantic_results = await self._semantic_search(query)
            results.extend(semantic_results)

        # 3. 标签匹配
        if self.config.tag_enabled:
            tag_results = await self._tag_search(query)
            results.extend(tag_results)

        # 4. 合并与排序
        merged = self._merge_results(results)

        return merged[:self.config.final_top_k]

    async def _exact_search(self, query: str) -> List[RetrievalResult]:
        """精确匹配搜索"""
        results = []
        query_lower = query.lower()

        for skill_id, skill in self.unified_index.items():
            # 名称精确匹配
            if query_lower in skill.name.lower():
                results.append(RetrievalResult(
                    skill=skill,
                    score=1.0 * self.config.exact_weight,
                    match_type="exact",
                    source=skill.source
                ))
            # 描述包含
            elif query_lower in skill.description.lower():
                results.append(RetrievalResult(
                    skill=skill,
                    score=0.8 * self.config.exact_weight,
                    match_type="exact",
                    source=skill.source
                ))

        return results

    async def _semantic_search(self, query: str) -> List[RetrievalResult]:
        """语义检索 (使用 Embedding API)"""
        # 1. 获取查询的 embedding
        query_embedding = await self._get_embedding(query)

        # 2. 计算相似度
        results = []
        for skill_id, skill in self.unified_index.items():
            if skill.embedding is None:
                continue

            score = self._cosine_similarity(query_embedding, skill.embedding)

            if score >= self.config.semantic_threshold:
                results.append(RetrievalResult(
                    skill=skill,
                    score=score,
                    match_type="semantic",
                    source=skill.source
                ))

        # 3. 返回 top-k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:self.config.semantic_top_k]

    async def _tag_search(self, query: str) -> List[RetrievalResult]:
        """标签搜索"""
        results = []
        query_tags = set(query.lower().split())

        for skill_id, skill in self.unified_index.items():
            overlap = query_tags.intersection(set(t.lower() for t in skill.tags))
            if overlap:
                score = len(overlap) / max(len(query_tags), len(skill.tags))
                results.append(RetrievalResult(
                    skill=skill,
                    score=score * self.config.tag_weight,
                    match_type="tag",
                    source=skill.source
                ))

        return results

    def _merge_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """合并检索结果"""
        # 1. 按 skill_id 分组
        grouped: Dict[str, List[RetrievalResult]] = {}
        for r in results:
            if r.skill.skill_id not in grouped:
                grouped[r.skill.skill_id] = []
            grouped[r.skill.skill_id].append(r)

        # 2. 合并每个 skill 的多结果
        merged: List[RetrievalResult] = []
        for skill_id, skill_results in grouped.items():
            # 合并分数 (取最高分)
            best_result = max(skill_results, key=lambda x: x.score)

            # 更新 match_type
            match_types = set(r.match_type for r in skill_results)
            best_result.match_type = "+".join(sorted(match_types))

            # 合并来源
            sources = set(r.source for r in skill_results)
            best_result.skill.sources = sources

            merged.append(best_result)

        # 3. 排序
        if self.config.merge_strategy == "score_weighted":
            merged.sort(key=lambda x: x.score, reverse=True)
        elif self.config.merge_strategy == "priority_first":
            merged.sort(key=lambda x: (
                self.config.source_priority.get(x.source, 999),
                -x.score
            ))
        else:
            merged.sort(key=lambda x: x.score, reverse=True)

        return merged

    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本 embedding (调用线上 API)"""
        # 实现: 调用 OpenAI/Cohere Embedding API
        pass

    async def _build_semantic_index(self):
        """构建语义索引"""
        for skill in self.unified_index.values():
            if skill.embedding is None and skill.description:
                skill.embedding = await self._get_embedding(skill.description)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    @staticmethod
    def _compare_version(v1: str, v2: str) -> int:
        """比较版本号"""
        # 简单实现: 假设格式为 x.y.z
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        for p1, p2 in zip(parts1, parts2):
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        return 0
```

---

## 3. 协调机制

### 3.1 Skill 来源检测与标注

```python
class SkillSourceDetector:
    """Skill 来源检测器"""

    @staticmethod
    def detect(skill_path: str) -> SkillSource:
        """检测 Skill 来源"""
        path = Path(skill_path)

        # 检查路径模式
        if "/evolved/" in str(path):
            # 检查是 Agent 级还是全局
            if "/agents/" in str(path):
                return SkillSource.LOCAL  # Agent 级进化
            else:
                return SkillSource.EVOLVED  # 全局进化
        elif "/packages/" in str(path):
            return SkillSource.PACKAGE
        else:
            return SkillSource.LOCAL
```

### 3.2 冲突解决

```python
class ConflictResolver:
    """冲突解决器"""

    @dataclass
    class Conflict:
        skill_id: str
        versions: Dict[SkillSource, str]
        resolution: str
        resolved_version: str

    def resolve(
        self,
        skill_id: str,
        versions: Dict[SkillSource, str]
    ) -> Conflict:
        """解决版本冲突"""

        if len(versions) == 1:
            # 只有一个来源，无冲突
            source = list(versions.keys())[0]
            return Conflict(
                skill_id=skill_id,
                versions=versions,
                resolution="single_source",
                resolved_version=versions[source]
            )

        # 多来源: 使用优先级
        # 优先级: EVOLVED > LOCAL > HYBRID > PACKAGE
        priority_order = [
            SkillSource.EVOLVED,
            SkillSource.LOCAL,
            SkillSource.HYBRID,
            SkillSource.PACKAGE
        ]

        for source in priority_order:
            if source in versions:
                return Conflict(
                    skill_id=skill_id,
                    versions=versions,
                    resolution=f"priority_{source.value}",
                    resolved_version=versions[source]
                )

        # 不应到达这里
        raise ValueError(f"Unexpected conflict state for {skill_id}")
```

---

## 4. 配置示例

### 4.1 检索配置

```yaml
# unified_retriever.yaml
retriever:
  # 检索模式
  mode: hybrid  # package_only | evolved_only | hybrid

  # 语义检索
  semantic:
    enabled: true
    provider: openai  # openai | cohere | local
    model: text-embedding-3-small
    api_key: ${OPENAI_API_KEY}
    top_k: 5
    threshold: 0.7

  # 精确匹配
  exact:
    enabled: true
    weight: 1.0

  # 标签匹配
  tag:
    enabled: true
    weight: 0.5

  # 合并策略
  merge:
    strategy: score_weighted  # score_weighted | priority_first
    final_top_k: 10

  # 来源优先级 (可选)
  source_priority:
    evolved: 1    # 进化技能最高优先级
    local: 2      # 本地次之
    hybrid: 3     # 混合第三
    package: 4    # Package Manager 最后
```

### 4.2 Skill 定义扩展

```yaml
# 扩展 Skill 元数据支持多来源
skill:
  id: "@org/coding-skill"
  name: "Coding Skill"
  description: "Advanced coding capabilities"

  # 多来源标注 (自动生成)
  sources:
    - package
    - evolved

  # 版本信息
  versions:
    package: "1.0.0"
    evolved: "1.0.1-evolved"

  # 当前活跃版本
  active_version: "1.0.1-evolved"

  # 语义向量 (可选, 按需生成)
  embedding_cache: "./cache/embeddings/coding-skill.npy"

  # 标签
  tags:
    - coding
    - programming
    - development
```

---

## 5. 数据流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        统一检索数据流                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   请求: "帮我写一个 Python 函数"                                              │
│        │                                                                    │
│        ▼                                                                    │
│   ┌─────────────────────────────────────────────────────────────────┐        │
│   │              UnifiedSkillRetriever.retrieve()                    │        │
│   └─────────────────────────────────────────────────────────────────┘        │
│        │                                                                    │
│        ├──────────────────────┬───────────────────────────────────┐        │
│        ▼                      ▼                                   ▼        │
│   ┌────────────┐      ┌────────────┐                    ┌────────────┐   │
│   │ 精确匹配    │      │ 语义检索   │                    │ 标签匹配   │   │
│   │ (名称/描述) │      │(Embedding) │                    │ (Tags)     │   │
│   └──────┬─────┘      └──────┬─────┘                    └─────┬──────┘   │
│        │                      │                                │           │
│        └──────────────────────┼────────────────────────────────┘           │
│                               ▼                                              │
│                    ┌─────────────────────┐                                 │
│                    │   _merge_results()  │                                 │
│                    │   - 按 skill_id 分组│                                 │
│                    │   - 合并分数        │                                 │
│                    │   - 去重            │                                 │
│                    └──────────┬──────────┘                                 │
│                               │                                            │
│                               ▼                                            │
│                    ┌─────────────────────┐                                 │
│                    │   排序返回 Top-K    │                                 │
│                    └──────────┬──────────┘                                 │
│                               │                                            │
│                               ▼                                            │
│   返回:                                                                      │
│   [{skill: "@org/coding-skill", score: 0.95, source: "evolved",         │
│     match_type: "semantic+exact"}, ...]                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. API 设计

### 6.1 核心 API

```python
class UnifiedSkillAPI:
    """统一 Skill API"""

    def __init__(self, config: RetrievalConfig):
        self.retriever = UnifiedSkillRetriever(config)

    async def search(self, query: str) -> List[RetrievalResult]:
        """搜索 Skill"""
        return await self.retriever.retrieve(query)

    async def get(self, skill_id: str) -> Optional[SkillMetadata]:
        """获取指定 Skill"""
        return self.retriever.unified_index.get(skill_id)

    async def list_by_source(
        self,
        source: SkillSource
    ) -> List[SkillMetadata]:
        """按来源列出 Skill"""
        return [
            s for s in self.retriever.unified_index.values()
            if source in s.sources
        ]

    async def rebuild_index(
        self,
        package_skills: List[SkillMetadata],
        evolved_skills: List[SkillMetadata]
    ) -> None:
        """重建索引"""
        await self.retriever.initialize(package_skills, evolved_skills)
```

---

## 7. 与现有系统集成

### 7.1 Package Manager 集成

```python
class PackageManagerIntegration:
    """Package Manager 集成"""

    def __init__(self, package_manager):
        self.pm = package_manager

    async def get_package_skills(self) -> List[SkillMetadata]:
        """获取 Package Manager 中的所有 Skill"""
        skills = []

        for package in await self.pm.list_packages():
            if package.type == "skill":
                skill = SkillMetadata(
                    skill_id=package.name,
                    name=package.skill.name,
                    description=package.skill.description,
                    source=SkillSource.PACKAGE,
                    version=package.version,
                    tags=package.skill.tags,
                    package_ref=package.name
                )
                skills.append(skill)

        return skills
```

### 7.2 SkillBank 集成

```python
class SkillBankIntegration:
    """SkillBank 集成"""

    def __init__(self, skill_bank_path: str):
        self.path = Path(skill_bank_path)

    async def get_evolved_skills(self) -> List[SkillMetadata]:
        """获取所有进化的 Skill"""
        skills = []

        # 读取 evolved 目录
        evolved_dir = self.path / "evolved"
        if evolved_dir.exists():
            for skill_file in evolved_dir.rglob("*.yaml"):
                skill_data = yaml.safe_load(skill_file.read_text())

                skill = SkillMetadata(
                    skill_id=skill_data["id"],
                    name=skill_data.get("name", ""),
                    description=skill_data.get("summary", ""),
                    source=SkillSource.EVOLVED,
                    version=skill_data.get("version"),
                    tags=skill_data.get("tags", [])
                )
                skills.append(skill)

        return skills
```

---

## 8. 总结

| 组件 | 职责 |
|------|------|
| **UnifiedSkillRetriever** | 统一检索入口，双轨检索，智能合并 |
| **SkillSourceDetector** | 检测 Skill 来源 |
| **ConflictResolver** | 处理版本冲突 |
| **PackageManagerIntegration** | 从 Package Manager 加载 Skill |
| **SkillBankIntegration** | 从 SkillBank 加载进化的 Skill |

### 关键特性

1. **无冲突**: 通过优先级和来源标注解决
2. **可扩展**: 轻松添加新的 Skill 来源
3. **高性能**: 支持 Embedding 缓存和批量处理
4. **可配置**: 多种检索模式和合并策略

是否需要我继续完善某个具体模块的实现？
