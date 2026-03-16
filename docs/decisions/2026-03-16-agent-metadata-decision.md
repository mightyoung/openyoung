# 决策文档: Agent 元数据提取系统

> 日期: 2026-03-16
> 问题: Agent 元数据提取（特性、skills、subagent、README）
> 决策: A - 导入时提取

---

## 1. 问题背景

OpenYoung 需要在导入 Agent 时自动提取元数据，包括：
- Capabilities（能力列表）
- Skills（技能定义）
- Subagents（子Agent配置）
- README 摘要
- 兼容性信息

实现渐进式披露，按需加载不同层级的元数据。

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| arXiv | 模块化技能提取框架，从GitHub仓库提取程序化知识 |
| SkillsGate | 索引45,000+ GitHub Agent技能，可发现和安装 |
| Anthropic Skills | Claude技能系统，结构化技能定义 |
| JAMEX | 多Agent管道，结构化元数据提取 |

### 2.2 核心技术方案

```
┌─────────────────────────────────────────────────────────────────┐
│                    渐进式披露模型                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: Basic (name, description, badges)                    │
│  ┌─────────────────────────────────────────────┐               │
│  │ agent_id, name, description, version, tier │               │
│  └─────────────────────────────────────────────┘               │
│                        │                                         │
│                        ▼                                         │
│  Level 2: Capabilities + Skills                                 │
│  ┌─────────────────────────────────────────────┐               │
│  │ capabilities, skills[], compatibility        │               │
│  └─────────────────────────────────────────────┘               │
│                        │                                         │
│                        ▼                                         │
│  Level 3: Orchestration                                         │
│  ┌─────────────────────────────────────────────┐               │
│  │ subagents[], dependencies, max_context      │               │
│  └─────────────────────────────────────────────┘               │
│                        │                                         │
│                        ▼                                         │
│  Level 4: Performance                                          │
│  ┌─────────────────────────────────────────────┐               │
│  │ performance, evaluation_scores, last_eval   │               │
│  └─────────────────────────────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Import Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Repository   │  │   Code       │  │   README     │       │
│  │ Analysis     │  │   Extraction  │  │   Summary    │       │
│  │              │  │              │  │              │       │
│  │ - Owner     │  │ - Skills    │  │ - Capabilities│       │
│  │ - Stars     │  │ - Subagents │  │ - Use Cases  │       │
│  │ - Language  │  │ - APIs      │  │ - Limitations│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│           │                  │                  │              │
│           └──────────────────┼──────────────────┘              │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              LLM Metadata Enrichment                      │   │
│  │                                                          │   │
│  │  Input: Raw extracted data                               │   │
│  │  Output: Structured AgentProfile with capabilities,      │   │
│  │          skills, subagents, compatibility,              │   │
│  │          performance estimates                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Progressive Disclosure Loader                 │   │
│  │                                                          │   │
│  │  Level 1 → Level 2 → Level 3 → Level 4               │   │
│  │  (按需加载)                                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 元数据模式

```python
class AgentMetadata:
    """完整Agent元数据"""

    # Level 1 - Basic (Always loaded)
    agent_id: str
    name: str
    description: str
    version: str
    source_repo: str
    tier: AgentTier  # foundation, specialized, orchestrator

    # Level 2 - Capabilities (On selection)
    capabilities: list[AgentCapability]
    skills: list[SkillDefinition]
    compatibility: CompatibilityInfo

    # Level 3 - Orchestration (On assignment)
    subagents: list[SubAgentConfig]
    dependencies: list[str]
    max_context_length: int

    # Level 4 - Performance (On evaluation)
    performance: PerformanceMetrics
    evaluation_scores: dict
    last_evaluated: datetime
```

### 3.3 提取管道

```python
class MetadataExtractor:
    """元数据提取器"""

    async def extract_from_github(
        self,
        repo_url: str,
        access_token: Optional[str] = None,
    ) -> AgentMetadata:
        """从GitHub仓库提取元数据"""

        # 1. 获取仓库信息
        repo = self._get_github_repo(repo_url, access_token)

        # 2. 分析代码结构
        code_structure = await self._analyze_code_structure(repo)

        # 3. 提取技能定义
        skills = await self._extract_skills(repo, code_structure)

        # 4. 提取子Agent配置
        subagents = await self._extract_subagents(repo, code_structure)

        # 5. LLM丰富
        enriched = await self._enrich_with_llm(
            basic_info, code_structure, skills, subagents
        )

        return enriched
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 元数据 Schema | `src/agents/metadata/schema.py` |
| Phase 1 | LLM Enrichment | `src/agents/metadata/enricher.py` |
| Phase 2 | 提取管道 | `src/agents/metadata/extractor.py` |
| Phase 2 | 渐进加载器 | `src/agents/metadata/loader.py` |
| Phase 3 | Import 集成 | `src/package_manager/importer.py` |
| Phase 3 | 任务匹配集成 | `src/agents/matching/task_matcher.py` |
| Phase 4 | 缓存层 | `src/agents/metadata/cache.py` |
| Phase 4 | 测试 | `tests/test_metadata.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 提取慢 | 导入时间长 | 异步提取 + 缓存 |
| LLM 调用失败 | 元数据不完整 | 回退到规则提取 |
| 提取不准确 | 匹配错误 | 允许用户手动编辑 |

---

## 6. 参考实现

- arXiv Framework: https://arxiv.org/html/2603.11808v1
- SkillsGate: https://www.reddit.com/r/ClaudeAI/comments/1rr8ts4/
- Anthropic Skills: https://github.com/anthropics/skills

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准
