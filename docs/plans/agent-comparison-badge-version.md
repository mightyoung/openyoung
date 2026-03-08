# Agent 对比功能、质量徽章系统、版本管理 实现计划

## 目标
增加 Agent 对比功能、质量徽章系统和版本管理，提升 Agent 发现和选择体验

---

## Phase 1: Agent 对比功能

### 1.1 设计方案

```python
# 对比结果结构
@dataclass
class AgentComparison:
    agent_a: str          # Agent A 名称
    agent_b: str          # Agent B 名称
    dimensions: Dict[str, ComparisonResult]  # 各维度对比
    winner: Optional[str]  # 胜出者
    summary: str          # 总结

@dataclass
class ComparisonResult:
    agent_a_score: float  # Agent A 分数
    agent_b_score: float  # Agent B 分数
    winner: str           # 胜出者
    reasoning: str        # 理由
```

### 1.2 对比维度

| 维度 | 数据来源 | 权重 |
|------|----------|------|
| 质量评分 | AgentEvaluator | 0.3 |
| 使用次数 | usage_stats | 0.2 |
| 文档完整性 | documentation 评估 | 0.15 |
| 功能完整性 | completeness 评估 | 0.15 |
| 安全性 | security 评估 | 0.1 |
| 依赖数量 | dependencies 评估 | 0.1 |

### 1.3 CLI 命令

```bash
# 对比两个 Agent
openyoung agent compare agent-coder agent-reviewer

# 输出：
# === Agent Comparison: agent-coder vs agent-reviewer ===
#
# Quality Score:    agent-coder (0.61) vs agent-reviewer (0.55) → agent-coder ✓
# Usage Count:      agent-coder (5) vs agent-reviewer (2) → agent-coder ✓
# Documentation:   agent-coder (0.0) vs agent-reviewer (0.3) → agent-reviewer ✓
# ...
#
# Winner: agent-coder
```

---

## Phase 2: 质量徽章系统

### 2.1 徽章类型

| 徽章 | 条件 | 颜色 |
|------|------|------|
| **Verified** | 官方验证 | 🟢 绿色 |
| **Top Rated** | 评分 >= 4.5 | 🟡 金色 |
| **Trending** | 最近 7 天增长最快 | 🔥 红色 |
| **New** | 最近 30 天内添加 | 🆕 蓝色 |
| **Popular** | 使用次数 >= 100 | ⭐ 黄色 |
| **Well-Documented** | 文档评分 >= 0.8 | 📚 青色 |

### 2.2 数据结构

```python
@dataclass
class AgentBadge:
    badge_type: str        # 徽章类型
    earned_at: str         # 获得时间
    expires_at: Optional[str]  # 过期时间

@dataclass
class AgentMetadata:
    name: str
    badges: List[AgentBadge]  # 徽章列表
    rating: float           # 评分 (0-5)
    download_count: int     # 下载次数
    trending_score: float   # 趋势分数
```

### 2.3 趋势算法

```python
def calculate_trending_score(
    recent_downloads: int,   # 7天内下载
    total_downloads: int,     # 总下载
    rating: float,           # 评分
    days_since_release: int  # 发布天数
) -> float:
    velocity_score = recent_downloads / max(total_downloads, 1) * 10
    rating_score = rating * 2
    freshness_score = max(0, 1 - days_since_release / 30)

    return velocity_score * 0.5 + rating_score * 0.3 + freshness_score * 0.2
```

---

## Phase 3: 版本管理

### 3.1 版本规范

遵循 Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH` (例如: 1.2.3)
- MAJOR: 不兼容的 API 变更
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的 bug 修复

### 3.2 数据结构

```python
@dataclass
class AgentVersion:
    version: str            # 版本号
    changelog: str          # 变更日志
    released_at: str        # 发布时间
    compatible_with: str    # 兼容版本
    breaking_changes: List[str]  # 重大变更

@dataclass
class VersionHistory:
    agent_name: str
    current_version: str
    versions: List[AgentVersion]
    latest_major: str
    latest_minor: str
    latest_patch: str
```

### 3.3 CLI 命令

```bash
# 查看版本历史
openyoung agent versions agent-coder

# 输出：
# === agent-coder Versions ===
#
# Current: 1.2.0 (2026-03-06)
#
# v1.2.0 (latest) - 2026-03-06
#   + 新增代码审查功能
#   + 优化性能
#
# v1.1.0 - 2026-02-01
#   + 添加测试支持
#
# v1.0.0 - 2026-01-01
#   Initial release
```

---

## 实现步骤

### Step 1: 创建 Agent Comparer 模块
- [ ] 创建 `src/package_manager/agent_compare.py`
- [ ] 实现 `compare_agents()` 函数
- [ ] 实现各维度对比计算

### Step 2: 创建徽章系统模块
- [ ] 创建 `src/package_manager/badge_system.py`
- [ ] 实现徽章类型枚举
- [ ] 实现趋势分数计算
- [ ] 实现徽章授予逻辑

### Step 3: 创建版本管理模块
- [ ] 创建 `src/package_manager/version_manager.py`
- [ ] 实现版本解析 (SemVer)
- [ ] 实现版本历史存储
- [ ] 实现版本比较

### Step 4: CLI 集成
- [ ] 添加 `agent compare` 命令
- [ ] 添加徽章显示到 `agent list`
- [ ] 添加 `agent versions` 命令

### Step 5: 测试
- [ ] 测试对比功能
- [ ] 测试徽章计算
- [ ] 测试版本解析

---

## 关键文件

| 功能 | 文件 |
|------|------|
| 对比 | `src/package_manager/agent_compare.py` |
| 徽章 | `src/package_manager/badge_system.py` |
| 版本 | `src/package_manager/version_manager.py` |

---

## 预期效果

### Agent 对比
```
$ openyoung agent compare agent-coder agent-reviewer

========================================
         Agent Comparison
========================================

┌─────────────────┬──────────────┬──────────────┐
│ Dimension       │ agent-coder  │ agent-reviewer│
├─────────────────┼──────────────┼──────────────┤
│ Quality         │    0.61 ✓   │     0.55     │
│ Downloads       │     150      │      89      │
│ Rating         │    4.2 ✓     │     4.5      │
│ Badges         │  Popular ✓   │    Verified  │
│ Version        │   v1.2.0 ✓  │    v1.1.0    │
└─────────────────┴──────────────┴──────────────┘

🏆 Winner: agent-coder (3/5 dimensions)
```

### 徽章显示
```
$ openyoung agent list

🟢 • agent-coder (Popular, Trending)
   Version: 1.2.0 | Quality: 0.61 | Downloads: 150

🟡 • agent-reviewer (Verified, Top Rated)
   Version: 1.1.0 | Quality: 0.55 | Downloads: 89

📚 • agent-researcher (Well-Documented)
   Version: 2.0.0 | Quality: 0.72 | Downloads: 200
```

---

## 估算工作量

| 功能 | 工作量 |
|------|--------|
| Agent 对比 | 2-3 小时 |
| 质量徽章 | 3-4 小时 |
| 版本管理 | 2-3 小时 |
| **总计** | **7-10 小时** |
