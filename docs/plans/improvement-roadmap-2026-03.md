# OpenYoung 改进路线图 2026-03

**生成时间**: 2026-03-21
**基于**: 多维度Agent分析 + PEAS评估 + 最佳实践研究

---

## 一、项目现状评估

### 1.1 综合评分

| 维度 | 分数 | 主要问题 |
|------|------|----------|
| **架构设计** | 5.5/10 | YoungAgent God Object、Singleton滥用 |
| **类型安全** | 5/10 | Any类型滥用、47 F821错误 |
| **安全性** | 3.5/10 | XOR加密、无沙箱隔离、Shell注入 |
| **性能** | 4.5/10 | 异步阻塞、连接泄漏、无连接池 |
| **代码质量** | 4.5/10 | 416 bare except、print替代logger |

### 1.2 已完成改进 (2026-03-21)

| 任务 | 状态 | 说明 |
|------|------|------|
| PII扫描器 | ✅ | 58测试，支持身份证/银行卡/电话/SSN等 |
| 安全文档 | ✅ | 修正沙箱声明，创建威胁模型文档 |
| 网络隔离 | ✅ | 17测试，ToolExecutor + SandboxManager |
| MCP Server | ✅ | STDIO + JSON-RPC 2.0 |
| Agent Adapter | ✅ | 13测试，SubAgent → EvalRunner格式转换 |
| Checkpoint系统 | ✅ | 统一实现 |

### 1.3 核心问题优先级

```
CRITICAL (立即修复):
├── 🔴 vault.py XOR加密 → Fernet
├── 🔴 ProcessSandbox 无实际隔离 → Docker/E2B
└── 🔴 Shell注入漏洞 → create_subprocess_exec

HIGH (本周修复):
├── 🟠 YoungAgent God Object (30+组件初始化)
├── 🟠 全局Singleton绕过DI
├── 🟠 阻塞文件I/O (asyncio事件循环)
└── 🟠 use-after-release连接泄漏

MEDIUM (持续改进):
├── 🟡 Any类型清理
├── 🟡 HTTP连接池
└── 🟡 类型注解覆盖率
```

---

## 二、架构改进

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenYoung 架构                           │
├─────────────────────────────────────────────────────────────┤
│  工作流层 (LangGraph/Temporal)                               │
│  ├── 有状态工作流 (LangGraph)                               │
│  └── 长期任务持久化 (Temporal)                              │
├─────────────────────────────────────────────────────────────┤
│  Agent执行层 (HarnessEngine)                               │
│  ├── EvaluatorSelector                                      │
│  ├── FeedbackCollector                                      │
│  └── AgentAdapter (已实现 ✅)                              │
├─────────────────────────────────────────────────────────────┤
│  内存层                                                     │
│  ├── WorkingMemory (短期)                                  │
│  ├── SemanticMemory (长期，含HNSW索引)                     │
│  └── CheckpointMemory (状态快照)                           │
├─────────────────────────────────────────────────────────────┤
│  安全层                                                     │
│  ├── SandboxManager (E2B > Docker > Process)               │
│  ├── Firewall (网络隔离 ✅ 已完成)                          │
│  ├── SecretScanner + PII扫描 ✅ 已完成                      │
│  └── PermissionEvaluator                                    │
├─────────────────────────────────────────────────────────────┤
│  MCP层 (STDIO Server ✅ 已完成)                            │
│  ├── JSON-RPC 2.0 Protocol                                │
│  └── ToolRegistry                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 架构改进任务

| 优先级 | 任务 | 工时 | 依赖 |
|--------|------|------|------|
| P0 | YoungAgent.__init__ 拆分 | 8h | - |
| P1 | Singleton移除/DI集成 | 6h | YoungAgent拆分 |
| P1 | LangGraphWorkflow集成 | 4h | - |
| P2 | EventType枚举开放化 | 4h | - |
| P2 | init_* 注册表模式 | 6h | - |

---

## 三、安全改进

### 3.1 安全问题修复

| 优先级 | 问题 | 修复方案 | 工时 |
|--------|------|----------|------|
| **P0** | vault.py XOR加密 | Fernet AES加密 | 2h |
| **P0** | ProcessSandbox无隔离 | 强制Docker/E2B，禁用Process | 4h |
| **P0** | Shell注入 | create_subprocess_exec() | 1h |
| P1 | 硬编码路径 | 环境变量/配置 | 1h |
| P1 | DNS rebinding | 默认拒绝 | 0.5h |
| P1 | 环境变量泄露 | subprocess env=参数 | 2h |

### 3.2 已完成安全改进 ✅

| 组件 | 状态 | 测试 |
|------|------|------|
| PII扫描器 | ✅ | 58测试 |
| 网络隔离 | ✅ | 17测试 |
| 安全文档 | ✅ | 威胁模型 |

---

## 四、性能改进

### 4.1 性能问题修复

| 优先级 | 问题 | 修复方案 | 工时 |
|--------|------|----------|------|
| **P0** | 阻塞文件I/O | aiofiles / asyncio.to_thread | 2h |
| **P0** | use-after-release | 连接在async with内使用 | 1h |
| **P0** | 无HTTP连接池 | httpx.AsyncClient复用 | 4h |
| P1 | ConnectionPool竞态 | asyncio.Condition | 3h |
| P1 | RateLimiter崩溃 | time.monotonic() | 1h |
| P2 | LRUCache O(n) | OrderedDict双向链表 | 2h |
| P2 | Semantic ILIKE | pg_trgm索引 | 2h |

### 4.2 异步最佳实践

```python
# ❌ 错误 - 阻塞事件循环
async with asyncio.Lock():
    with open(path, "w") as f:  # 同步阻塞!
        f.write(data)

# ✅ 正确 - 使用aiofiles
import aiofiles
async with aiofiles.open(path, "w") as f:
    await f.write(data)
```

---

## 五、代码质量改进

### 5.1 代码质量问题

| 优先级 | 问题 | 修复方案 | 工时 |
|--------|------|----------|------|
| **P0** | 启用E722 (bare except) | 移除ruff ignore | 1h |
| **P0** | print→logger | young_agent.py等 | 3h |
| **P0** | 修复47 F821错误 | torch导入检查 | 2h |
| P1 | 清理238 F401 | 删除未使用导入 | 4h |
| P1 | 拆分大文件 | >500行文件 | 8h |
| P2 | 类型注解覆盖 | 渐进式添加 | 持续 |

### 5.2 ruff配置修复

```toml
# pyproject.toml
[tool.ruff]
# 移除这些忽略规则
ignore = [
    # E722 - bare except (应启用)
    # F401 - unused imports (应清理)
    # F811 - redefinition (应修复)
]
```

---

## 六、实施计划

### Phase 1: 紧急修复 (P0) - 第1周

```
┌────────────────────────────────────────────────────────────┐
│ 安全修复周                                                  │
├────────────────────────────────────────────────────────────┤
│ Day 1-2:                                                   │
│   ├── vault.py XOR → Fernet (2h)                         │
│   └── Shell注入修复 (1h)                                  │
│ Day 3-4:                                                   │
│   ├── ProcessSandbox → 强制Docker/E2B (4h)               │
│   └── 硬编码路径移除 (1h)                                 │
│ Day 5:                                                     │
│   └── 验证所有P0安全修复                                   │
└────────────────────────────────────────────────────────────┘
```

### Phase 2: 架构修复 (P1) - 第2-3周

```
┌────────────────────────────────────────────────────────────┐
│ 架构重构周                                                  │
├────────────────────────────────────────────────────────────┤
│ Week 2:                                                     │
│   ├── YoungAgent.__init__拆分 (8h)                        │
│   ├── Singleton → DI容器 (6h)                              │
│   └── 阻塞文件I/O修复 (2h)                                │
│ Week 3:                                                     │
│   ├── HTTP连接池 (4h)                                     │
│   ├── use-after-release修复 (1h)                          │
│   └── 类型注解清理 (6h)                                   │
└────────────────────────────────────────────────────────────┘
```

### Phase 3: 持续改进 (P2) - 第4周及以后

| 任务 | 工时 |
|------|------|
| ConnectionPool竞态修复 | 3h |
| RateLimiter修复 | 1h |
| 大文件拆分 (5+文件) | 8h |
| LangGraph集成 | 4h |
| EventType开放化 | 4h |
| pg_trgm索引 | 2h |

---

## 七、测试策略

### 7.1 测试覆盖目标

| 阶段 | 覆盖目标 | 当前状态 |
|------|----------|----------|
| 单元测试 | 80%+ | 需提升 |
| 集成测试 | 60%+ | 需提升 |
| E2E测试 | 关键路径 | 需新增 |

### 7.2 已完成测试

| 组件 | 测试数 | 状态 |
|------|--------|------|
| PII扫描器 | 58 | ✅ |
| 网络隔离 | 17 | ✅ |
| Agent Adapter | 13 | ✅ |
| 运行时安全 | 42 | ✅ |
| **总计** | **130+** | ✅ |

---

## 八、文件清单

### 8.1 待修改文件

| 文件 | 问题 | 优先级 |
|------|------|--------|
| `src/runtime/security/vault.py` | XOR加密 | P0 |
| `src/runtime/sandbox/manager.py` | ProcessSandbox | P0 |
| `src/tools/executor.py` | Shell注入 | P0 |
| `src/agents/young_agent.py` | God Object | P0 |
| `src/core/events.py` | Singleton | P1 |
| `src/core/memory/working.py` | 阻塞I/O | P0 |
| `src/core/memory/semantic.py` | 连接泄漏 | P0 |
| `src/llm/providers.py` | 无连接池 | P0 |

### 8.2 新增文件

| 文件 | 说明 |
|------|------|
| `docs/security/threat_model.md` | 威胁模型 ✅ |
| `tests/sandbox/test_network_isolation.py` | 网络隔离测试 ✅ |
| `tests/core/security/test_pii_scanner.py` | PII扫描测试 ✅ |
| `tests/runtime/security/test_network_isolation.py` | 运行时安全测试 ✅ |

---

## 九、验收标准

### 9.1 完成标准

- [ ] 所有CRITICAL安全问题修复
- [ ] YoungAgent拆分完成，<400行
- [ ] ruff启用完整检查 (无E722/F401/F811忽略)
- [ ] 类型注解覆盖率 >70%
- [ ] 测试覆盖 >80%

### 9.2 质量门禁

```bash
# 必须全部通过
pytest tests/ -v --tb=short
ruff check src/ --fix
mypy src/ --strict
```

---

## 十、总结

### 10.1 改进优先级

1. **立即**: 安全P0修复 (加密、沙箱、注入)
2. **本周**: 性能P0修复 (I/O、连接池)
3. **下周**: 架构重构 (YoungAgent、DI)
4. **持续**: 代码质量提升

### 10.2 资源估算

| Phase | 工时 | 关键依赖 |
|-------|------|----------|
| Phase 1 (P0安全) | 10h | - |
| Phase 2 (P1架构) | 27h | Phase 1 |
| Phase 3 (P2改进) | 24h | Phase 2 |
| **总计** | **61h** | ~3周 |

---

*本方案基于多维度Agent分析 + Tavily最佳实践研究生成*
