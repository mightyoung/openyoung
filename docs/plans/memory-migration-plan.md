# 记忆系统迁移计划

## 现状分析

### 旧模块 (`src/memory/`)
| 模块 | 功能 | 使用情况 |
|------|------|----------|
| `checkpoint.py` | 文件版本管理 (SQLite) | 被 young_agent.py, datacenter.py 使用 |
| `vector_store.py` | 向量存储 | 被多个模块使用 |
| `auto_memory.py` | 三层记忆 | **未被使用** |

### 新模块 (`src/core/memory/`)
| 模块 | 功能 | 使用情况 |
|------|------|----------|
| `working.py` | L0 任务上下文 | 0 引用 |
| `semantic.py` | L2 知识检索 | 0 引用 |
| `checkpoint_integration.py` | Agent 状态快照 (PostgreSQL) | 0 引用 |
| `facade.py` | 统一 API | 0 引用 |
| `handlers.py` | EventBus 集成 | 0 引用 |

---

## 关键发现

### 两个 Checkpoint 是完全不同的概念！

| | 旧 CheckpointManager | 新 checkpoint_integration |
|---|---|---|
| **用途** | 文件版本控制 | Agent 运行时状态恢复 |
| **存储** | SQLite | PostgreSQL |
| **目标** | 恢复误删/误改的文件 | 恢复 Agent 执行状态 |
| **使用者** | young_agent (sandbox) | (无人使用) |

---

## 迁移策略

### 方案: 保留旧模块 + 集成新模块到 Agent

**不是简单的替换，而是功能增强：**

1. **保留** `src/memory/checkpoint.py` - 文件版本控制是有效功能
2. **保留** `src/memory/vector_store.py` - 向量检索被多个模块依赖
3. **废弃** `src/memory/auto_memory.py` - 完全未被使用
4. **集成** 新模块到 `young_agent.py` - 增强 Agent 记忆能力

---

## 执行计划

### Phase M1: 创建 Bridge 适配层 ✅

- [x] 创建 `src/core/memory/bridge.py`
- [x] 导出 MemoryBackend 枚举
- [x] 导出 create_memory_system, store_knowledge, retrieve_knowledge
- [x] 更新 `src/core/memory/__init__.py` 导出
- [x] 标记 `src/memory/auto_memory.py` 废弃

### Phase M2: 集成到 YoungAgent ✅

- [x] 添加 `memory_facade` 参数到 `__init__` 方法
- [x] 添加 `_memory_facade_injected` 标志
- [x] 添加 `_init_memory_facade()` 方法
- [x] 添加 `get_memory_facade()` 获取方法
- [x] 添加 `store_knowledge()` 存储方法
- [x] 添加 `retrieve_knowledge()` 检索方法
- [x] 验证导入成功

```python
# 使用示例
agent = YoungAgent(config)
memory = agent.get_memory_facade()
await agent.store_knowledge("重要信息", layer="semantic")
results = await agent.retrieve_knowledge("查询内容")
```

### Phase M3: 清理旧模块 ✅

- [x] 更新 `src/memory/__init__.py` 移除废弃导出
- [x] 添加废弃说明文档
- [x] 保留 CheckpointManager 向后兼容

---

## 依赖文件迁移清单

| 文件 | 当前引用 | 迁移动作 |
|------|----------|----------|
| young_agent.py | checkpoint | 保留 + 可选集成新checkpoint |
| datacenter.py | checkpoint | 保留 |
| knowledge.py | vector_store | 保留 |
| agent_retriever.py | vector_store | 保留 |
| registry.py | vector_store | 保留 |
| cli/main.py | vector_store | 保留 |

---

## 验收标准

- [x] Bridge 模块创建完成
- [x] 新模块 MemoryFacade 可导入使用
- [x] 旧模块功能正常（向后兼容）
- [x] auto_memory.py 标记废弃
- [x] 测试通过 (50 passed)
- [x] 新模块 MemoryFacade 被 young_agent 引用 (M2)

---

**最后更新**: 2026-03-17

---

## M2 执行总结

### 修改文件

1. **`src/agents/young_agent.py`**
   - 添加 `memory_facade` 参数到 `__init__`
   - 添加 `_memory_facade_injected` 标志
   - 添加 `_init_memory_facade()` 方法（使用Bridge层）
   - 添加 `get_memory_facade()` 获取方法
   - 添加 `store_knowledge()` 异步存储方法
   - 添加 `retrieve_knowledge()` 异步检索方法

### 集成方式

```python
# 依赖注入（测试友好）
agent = YoungAgent(config, memory_facade=my_facade)

# 或自动初始化（生产环境）
agent = YoungAgent(config)
facade = agent.get_memory_facade()

# 使用分层记忆
await agent.store_knowledge("学习到的知识", layer="semantic")
results = await agent.retrieve_knowledge("相关查询")
```

### 向后兼容

- 旧模块 `src/memory/checkpoint.py` 保持正常工作
- 新 MemoryFacade 使用 Bridge 层自动降级
- 不影响现有功能
