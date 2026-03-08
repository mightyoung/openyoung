# R2-1: Package Manager 重构执行计划

> 版本: 1.0
> 更新日期: 2026-03-07

---

## 目标

将 `src/package_manager` 重构为 `src/hub`，按功能领域组织模块，保持包级别兼容。

---

## 方案 B: 仅包级别兼容

- 创建新 `hub` 模块
- 修改导入路径
- 保持 `from src.package_manager import XXX` 可用（通过兼容层）

---

## 新模块结构

```
src/
├── hub/                    # 新模块名
│   ├── __init__.py        # 兼容导出
│   ├── discover/          # 发现
│   │   ├── __init__.py
│   │   └── retriever.py   # agent_retriever.py
│   ├── evaluate/          # 评估 (核心)
│   │   ├── __init__.py
│   │   └── evaluator.py   # agent_evaluator.py
│   ├── badge/            # Badge (核心)
│   │   ├── __init__.py
│   │   └── system.py     # badge_system.py
│   ├── intent/           # Intent (核心)
│   │   ├── __init__.py
│   │   └── analyzer.py   # intent_analyzer.py
│   ├── registry/          # 注册
│   │   ├── __init__.py
│   │   ├── agent.py      # registry.py
│   │   └── base.py       # base_registry.py
│   ├── mcp/              # MCP 集成
│   │   ├── __init__.py
│   │   ├── manager.py    # mcp_manager.py
│   │   └── loader.py     # mcp_loader.py
│   ├── hooks/            # Hooks
│   │   ├── __init__.py
│   │   └── loader.py     # hooks_loader.py
│   ├── import/           # 导入
│   │   ├── __init__.py
│   │   ├── manager.py    # import_manager.py
│   │   ├── git.py        # git_importer.py
│   │   └── github.py     # github_importer.py
│   ├── version/          # 版本
│   │   ├── __init__.py
│   │   └── manager.py    # version_manager.py
│   ├── storage/          # 存储
│   │   ├── __init__.py
│   │   └── store.py      # storage.py
│   ├── io/               # 导入导出
│   │   ├── __init__.py
│   │   └── agent.py      # agent_io.py
│   ├── compare/          # 比较
│   │   ├── __init__.py
│   │   └── comparer.py   # agent_compare.py
│   └── subagent/         # 子 Agent
│       ├── __init__.py
│       └── registry.py    # subagent_registry.py
│
└── package_manager/       # 兼容层 (仅重导出)
    └── __init__.py       # 从 hub 导入并导出
```

---

## 执行阶段

### Phase 1: 创建目录结构

| 步骤 | 任务 | 状态 |
|------|------|------|
| 1.1 | 创建 src/hub/ 目录 | 🔲 |
| 1.2 | 创建各子模块目录 | 🔲 |
| 1.3 | 创建 __init__.py | 🔲 |

### Phase 2: 迁移核心业务模块

| 步骤 | 模块 | 文件 | 状态 |
|------|------|------|------|
| 2.1 | evaluate | agent_evaluator.py | 🔲 |
| 2.2 | badge | badge_system.py | 🔲 |
| 2.3 | intent | intent_analyzer.py | 🔲 |

### Phase 3: 迁移基础设施模块

| 步骤 | 模块 | 文件 | 状态 |
|------|------|------|------|
| 3.1 | registry | registry.py, base_registry.py | 🔲 |
| 3.2 | mcp | mcp_manager.py, mcp_loader.py | 🔲 |
| 3.3 | hooks | hooks_loader.py | 🔲 |
| 3.4 | storage | storage.py | 🔲 |

### Phase 4: 迁移其他模块

| 步骤 | 模块 | 文件 | 状态 |
|------|------|------|------|
| 4.1 | import | import_manager.py, git_importer.py, github_importer.py, enhanced_importer.py | 🔲 |
| 4.2 | version | version_manager.py | 🔲 |
| 4.3 | discover | agent_retriever.py | 🔲 |
| 4.4 | io | agent_io.py | 🔲 |
| 4.5 | compare | agent_compare.py | 🔲 |
| 4.6 | subagent | subagent_registry.py | 🔲 |
| 4.7 | template | template_registry.py | 🔲 |
| 4.8 | dependency | dependency_resolver.py, dependency_installer.py | 🔲 |
| 4.9 | provider | provider.py | 🔲 |
| 4.10 | manager | manager.py | 🔲 |

### Phase 5: 创建兼容层

| 步骤 | 任务 | 状态 |
|------|------|------|
| 5.1 | 更新 package_manager/__init__.py 从 hub 导入 | 🔲 |
| 5.2 | 验证所有导入路径兼容 | 🔲 |

### Phase 6: 测试验证

| 步骤 | 任务 | 状态 |
|------|------|------|
| 6.1 | 运行单元测试 | 🔲 |
| 6.2 | 运行全流程测试 | 🔲 |
| 6.3 | CLI 功能验证 | 🔲 |

---

## 文件映射表

| 原路径 | 新路径 |
|--------|--------|
| `package_manager/agent_evaluator.py` | `hub/evaluate/evaluator.py` |
| `package_manager/badge_system.py` | `hub/badge/system.py` |
| `package_manager/intent_analyzer.py` | `hub/intent/analyzer.py` |
| `package_manager/registry.py` | `hub/registry/agent.py` |
| `package_manager/base_registry.py` | `hub/registry/base.py` |
| `package_manager/mcp_manager.py` | `hub/mcp/manager.py` |
| `package_manager/mcp_loader.py` | `hub/mcp/loader.py` |
| `package_manager/hooks_loader.py` | `hub/hooks/loader.py` |
| `package_manager/storage.py` | `hub/storage/store.py` |
| `package_manager/import_manager.py` | `hub/import/manager.py` |
| `package_manager/git_importer.py` | `hub/import/git.py` |
| `package_manager/github_importer.py` | `hub/import/github.py` |
| `package_manager/enhanced_importer.py` | `hub/import/enhanced.py` |
| `package_manager/version_manager.py` | `hub/version/manager.py` |
| `package_manager/agent_retriever.py` | `hub/discover/retriever.py` |
| `package_manager/agent_io.py` | `hub/io/agent.py` |
| `package_manager/agent_compare.py` | `hub/compare/comparer.py` |
| `package_manager/subagent_registry.py` | `hub/subagent/registry.py` |
| `package_manager/template_registry.py` | `hub/template/registry.py` |
| `package_manager/dependency_resolver.py` | `hub/dependency/resolver.py` |
| `package_manager/dependency_installer.py` | `hub/dependency/installer.py` |
| `package_manager/provider.py` | `hub/provider/manager.py` |
| `package_manager/manager.py` | `hub/manager.py` |

---

## 注意事项

1. **保持类名不变**: 避免大规模修改
2. **更新 import 语句**: 每个文件内的 import 需要更新
3. **测试驱动**: 每迁移一个模块，运行测试验证
4. **向后兼容**: 最终通过 package_manager/__init__.py 导出

---

## 风险缓解

| 风险 | 缓解措施 |
|------|----------|
| 破坏现有功能 | 每步测试验证 |
| 导入路径错误 | 兼容层兜底 |
| 遗漏文件 | 使用文件映射表检查 |
