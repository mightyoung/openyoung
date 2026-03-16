# OpenYoung Skill Marketplace 设计方案

> 基于 Vercel Skills 和 Claude Code Market 最佳实践
> 创建时间: 2026-03-13

---

## 一、现有架构分析

### 1.1 已有的Skill系统

| 模块 | 功能 | 状态 |
|------|------|------|
| `src/skills/registry.py` | SkillRegistry - 本地注册表 | ✅ |
| `src/skills/loader.py` | SkillLoader - 动态加载器 | ✅ |
| `src/skills/creator.py` | SkillCreator - 模板创建器 | ✅ |
| `src/skills/versioning.py` | SkillVersionManager - 版本管理 | ✅ |
| `src/skills/metadata.py` | SkillMetadata - 元数据 | ✅ |
| `src/skills/retriever.py` | UnifiedSkillRetriever - 检索 | ✅ |

### 1.2 已有30+预置Skills

```
.claude/skills/
├── agentdb-advanced/
├── agentdb-learning/
├── github-code-review/
├── v3-core-implementation/
├── v3-performance-optimization/
├── ... (30+ skills)
```

---

## 二、顶级专家视角分析

### 2.1 Vercel Skills 架构洞见

**核心设计原则**:
- **声明式配置** - skill.yaml 定义技能行为
- **触发器驱动** - 关键词/模式/事件触发
- **可组合性** - 技能可嵌套调用
- **沙箱执行** - 安全隔离运行

**关键特性**:
```yaml
# skill.yaml 示例
name: code-review
trigger:
  type: keyword
  pattern: "/review"
actions:
  - name: analyze
    handler: review.py
  - name: report
    handler: report.py
```

### 2.2 Claude Code Market 模式

** marketplace 核心要素**:
1. **发现系统** - 分类、搜索、推荐
2. **安装系统** - 一键安装、自动更新
3. **评分系统** - 星级、评论、下载量
4. **发布系统** - 打包、发布、版本管理

### 2.3 Andrej Karpathy Agent架构

**Skill在Agent中的角色**:
```
Agent = LLM + Memory + Tools + Skills
                ↑
           Skill是预置的工具链
```

---

## 三、Skill Marketplace 架构设计

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   Skill Marketplace                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Discovery   │  │   Publish    │  │  Install    │  │
│  │   Service   │  │   Service   │  │   Service   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│         ↓                ↓                ↓            │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Skill Registry (SQLite)              │  │
│  │  - skills: id, name, author, version, rating     │  │
│  │  - reviews: skill_id, user, rating, comment     │  │
│  │  - downloads: skill_id, count, date             │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心数据模型

```python
# skill_marketplace/models.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class SkillStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"

@dataclass
class MarketplaceSkill:
    """市场技能"""
    id: str
    name: str
    display_name: str
    description: str
    author: str
    version: str

    # 分类
    category: str
    tags: list[str]

    # 指标
    rating: float = 0.0
    review_count: int = 0
    download_count: int = 0

    # 状态
    status: SkillStatus = SkillStatus.DRAFT
    created_at: datetime = None
    updated_at: datetime = None

    # 仓库
    repo_url: str = ""
    homepage: str = ""

@dataclass
class SkillReview:
    """技能评价"""
    id: str
    skill_id: str
    user_id: str
    rating: int  # 1-5
    comment: str
    created_at: datetime
```

### 3.3 服务组件

```python
# skill_marketplace/services.py

class DiscoveryService:
    """发现服务"""
    async def search(query: str, filters: SearchFilters) -> list[MarketplaceSkill]
    async def get_featured() -> list[MarketplaceSkill]
    async def get_by_category(category: str) -> list[MarketplaceSkill]
    async def get_trending() -> list[MarketplaceSkill]

class PublishService:
    """发布服务"""
    async def publish(skill: MarketplaceSkill, package: SkillPackage) -> str
    async def update(skill_id: str, version: str) -> bool
    async def deprecate(skill_id: str) -> bool

class InstallService:
    """安装服务"""
    async def install(skill_id: str, target_path: Path) -> bool
    async def uninstall(skill_id: str) -> bool
    async def check_updates() -> list[SkillUpdate]

class ReviewService:
    """评价服务"""
    async def submit_review(review: SkillReview) -> bool
    async def get_reviews(skill_id: str) -> list[SkillReview]
    async def update_rating(skill_id: str) -> float
```

---

## 四、与现有系统集成

### 4.1 复用现有Skill系统

```
现有系统                     Marketplace扩展
─────────────────────────────────────────────
SkillRegistry    →    MarketplaceRegistry (继承)
SkillLoader      →    MarketplaceLoader (扩展)
SkillCreator     →    MarketplacePublisher (新)
SkillVersion     →    支持Marketplace版本
```

### 4.2 集成点

```python
# src/skills/marketplace/__init__.py
from .client import SkillMarketplaceClient
from .registry import MarketplaceRegistry

# 扩展现有注册表
class ExtendedSkillRegistry(SkillRegistry):
    """扩展的技能注册表，支持市场"""

    def __init__(self):
        super().__init__()
        self.marketplace = SkillMarketplaceClient()

    async def discover_from_marketplace(self, query: str):
        """从市场发现技能"""
        skills = await self.marketplace.search(query)
        return skills
```

---

## 五、实施计划

### Phase 1: 基础架构 (Week 1-2)

| 任务 | 交付物 | 预估工时 |
|------|--------|----------|
| P1-1 数据模型 | models.py | 1天 |
| P1-2 SQLite注册表 | marketplace.db | 1天 |
| P1-3 核心服务 | services.py | 2天 |
| P1-4 CLI命令 | market CLI | 1天 |

### Phase 2: 发现与发布 (Week 3-4)

| 任务 | 交付物 | 预估工时 |
|------|--------|----------|
| P2-1 搜索服务 | 全文搜索+过滤 | 2天 |
| P2-2 发布工作流 | publish流程 | 2天 |
| P2-3 安装服务 | install/uninstall | 1天 |
| P2-4 版本管理 | 依赖解析 | 1天 |

### Phase 3: 社区功能 (Week 5-6)

| 任务 | 交付物 | 预估工时 |
|------|--------|----------|
| P3-1 评价系统 | rating + review | 2天 |
| P3-2 下载统计 | 计数器 | 1天 |
| P3-3 推荐系统 | trending | 1天 |
| P3-4 通知系统 | 更新提醒 | 2天 |

### Phase 4: 高级功能 (Week 7-8)

| 任务 | 交付物 | 预估工时 |
|------|--------|----------|
| P4-1 技能验证 | 自动测试 | 2天 |
| P4-2 依赖解析 | 版本约束 | 2天 |
| P4-3 离线模式 | 本地缓存 | 1天 |
| P4-4 Web UI | Dashboard | 3天 |

---

## 六、CLI 命令设计

```bash
# 发现技能
young skill search "code review"
young skill featured
young skill trending

# 安装/卸载
young skill install github-review
young skill uninstall github-review

# 发布
young skill publish ./my-skill
young skill update github-review --version 1.1.0

# 评价
young skill rate github-review 5 "Great skill!"
young skill reviews github-review

# 管理
young skill list --installed
young skill updates check
```

---

## 七、关键文件

### 新增文件

| 文件 | 描述 |
|------|------|
| `src/skills/marketplace/__init__.py` | 模块入口 |
| `src/skills/marketplace/models.py` | 数据模型 |
| `src/skills/marketplace/services.py` | 业务服务 |
| `src/skills/marketplace/client.py` | API客户端 |
| `src/skills/marketplace/registry.py` | 市场注册表 |
| `src/skills/marketplace/cli.py` | CLI命令 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/skills/__init__.py` | 导出Marketplace模块 |
| `task_plan.md` | 添加Marketplace任务 |

---

## 八、里程碑

| 周 | 里程碑 | 交付物 |
|----|--------|---------|
| W2 | **Alpha** | 基础架构+CLI |
| W4 | **Beta** | 发布+安装流程 |
| W6 | **RC1** | 社区功能完成 |
| W8 | **GA** | Web UI + 完整功能 |

---

*设计时间: 2026-03-13*
*参考: Vercel Skills, Claude Code Market, npm registry*
