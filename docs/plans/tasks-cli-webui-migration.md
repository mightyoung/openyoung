# CLI到WebUI迁移 - 任务清单

## 快速开始

**目标**: 用WebUI替换CLI，聚焦3个核心能力

**执行命令**: `openyoung plan exec 2026-03-17`

---

## 任务清单

### Phase 1: 补全WebUI功能

| ID | 任务 | 状态 | 方案 | 子任务 |
|----|------|------|------|--------|
| T1 | 完善Chat页面流式输出 | ✅ completed | B - SSE真实流式 | T1.1-T1.4 (全部完成, 9 tests passed) |
| T2 | 创建Skills管理页面 | ✅ completed | B - 独立页面+全部功能 | 6_Skills.py已创建 |
| T3 | 添加评估运行功能 | ✅ completed | B - 独立页面 | 4_Dashboard Run tab已添加 |
| T4 | Settings完整CRUD | ✅ completed | A - 本地YAML | 5_Settings已扩展 |
| T2 | 创建Skills管理页面 | ⚪ pending | B - 独立页面+全部功能 | - |
| T3 | 添加评估运行功能 | ⚪ pending | B - 独立页面 | - |
| T4 | 完善Settings完整CRUD | ⚪ pending | A - 本地YAML | - |

### Phase 2: 统一架构

| ID | 任务 | 状态 | 方案 | 依赖 |
|----|------|------|------|------|
| T5 | 统一API服务层 | ✅ completed | 创建routes目录 | T1,T2,T3 |
| T6 | 消除loader重复 | ✅ completed | 迁移到src/agents/ | - |
| T7 | 消除session_cli重复 | ✅ completed | 标记弃用 | - |

### Phase 3: 精简代码

| ID | 任务 | 状态 | 方案 | 依赖 |
|----|------|------|------|------|
| T8 | 删除config.py重复 | ✅ completed | 标记弃用 | T5 |
| T9 | 删除config_manager.py | ✅ completed | 标记弃用 | T5 |
| T10 | 保留run轻量入口 | ✅ completed | run+repl | T5,T7 |

---

## 当前任务

**T1: Chat流式输出** (🔵 in_progress)

---

## 任务执行顺序

```
Phase 1 (T1-T4) - 补全WebUI功能
    │
    ├── T1: Chat流式输出 ──────────┐
    ├── T2: Skills管理页面 ───────┤
    ├── T3: 评估运行功能 ──────────┤
    └── T4: Settings完整CRUD ──────┘
                                      │
Phase 2 (T5-T7) - 统一架构 ◀───────┘
    │
    ├── T5: 统一API服务层 ──────────┐
    ├── T6: 消除loader重复 ────────┤
    └── T7: 消除session_cli重复 ────┘
                                      │
Phase 3 (T8-T10) - 精简代码 ◀──────┘
    │
    ├── T8: 删除config.py ──────────┐
    ├── T9: 删除config_manager.py ──┤
    └── T10: 保留run轻量入口 ───────┘
```

---

## 详细文档

完整计划: [2026-03-17-cli-to-webui-migration-plan.md](./2026-03-17-cli-to-webui-migration-plan.md)
