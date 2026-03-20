# PEAS 框架集成可行性分析

> PEAS (Principle, Environment, Actuator, Sensor) 作为"评估对齐层"与主流AI Agent框架的集成方案

## 1. 框架集成分析

### 1.1 Claude Code

| 维度 | 详情 |
|------|------|
| **扩展机制** | Hooks + Plugins + MCP Servers |
| **集成点** | `settings.json` hooks配置, `skills/` 目录, MCP服务器 |
| **Hook类型** | `PreToolUse`, `PostToolUse`, `Stop`, `Notification`, `Message` |
| **PEAS可行性** | ✅ **高度可行** |
| **集成方式** | 在 `PostToolUse` hook 中插入PEAS评估逻辑 |
| **技术挑战** | 1. Hook是同步的，需评估延迟影响<br>2. 无内置状态持久化，需外部存储<br>3. 只能访问tool输入输出，无法修改执行流程 |

**推荐集成架构**:
```
Claude Code Session
    │
    ├─ PreToolUse (可选: 注入约束)
    │
    ├─ Tool Execution
    │
    └─ PostToolUse ──> PEAS Evaluator ──> 评估结果 ──> Memory/Reporter
```

---

### 1.2 LangGraph

| 维度 | 详情 |
|------|------|
| **扩展机制** | Custom Nodes + Middleware + ToolNode |
| **集成点** | StateGraph, before_model/after_model middleware |
| **PEAS可行性** | ✅ **最佳适配** |
| **集成方式** | 1. Custom Node: `PEASReviewNode`<br>2. Middleware: 全局拦截<br>3. Conditional Edge: 评估后路由 |

**LangGraph原生支持**:
- `ToolNode`: 标准化工具调用封装
- `Middleware`: before_model/after_model 拦截
- `StateGraph`: 可注入自定义节点到任意位置

**推荐集成架构**:
```python
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("peas_evaluator", PEASReviewNode())  # <-- 插入评估层
graph.add_edge("agent", "peas_evaluator")
graph.add_conditional_edges(
    "peas_evaluator",
    should_continue,
    {"continue": "agent", "stop": "__end__"}
)
```

---

### 1.3 CrewAI

| 维度 | 详情 |
|------|------|
| **扩展机制** | Custom Tools + Agent Adapters |
| **集成点** | `BaseToolAdapter`, `Tools` 类 |
| **PEAS可行性** | ⚠️ **部分可行** |
| **集成方式** | 1. Custom Tool: 封装评估逻辑<br>2. Agent Adapter: 包装agent行为<br>3. Process hooks (limited) |

**技术挑战**:
1. CrewAI的tool是agent主动调用的，无法强制评估
2. Agent Adapter可以包装行为，但侵入性强
3. 缺乏原生middleware概念

---

### 1.4 AutoGPT

| 维度 | 详情 |
|------|------|
| **扩展机制** | Plugins (plugins_config.yaml) |
| **集成点** | Plugin lifecycle hooks |
| **PEAS可行性** | ⚠️ **可行但过气** |
| **集成方式** | 1. 创建评估Plugin<br>2. 监听tool执行事件 |

**技术挑战**:
1. AutoGPT项目活跃度下降
2. 插件系统较老旧，缺乏现代middleware
3. 文档较少

---

## 2. 集成方案矩阵

| 框架 | 集成方式 | 集成点 | 难度 | 价值 | 推荐度 |
|------|----------|--------|------|------|--------|
| **LangGraph** | Custom Node + Middleware | StateGraph, before/after_model | ⭐⭐ | ⭐⭐⭐⭐⭐ | 🥇 **首选** |
| **Claude Code** | Hook + MCP | PostToolUse, settings.json | ⭐⭐ | ⭐⭐⭐⭐ | 🥈 **次选** |
| **CrewAI** | Custom Tool + Adapter | BaseToolAdapter, Tools | ⭐⭐⭐ | ⭐⭐⭐ | 🥉 |
| **AutoGPT** | Plugin | plugins_config.yaml | ⭐⭐⭐ | ⭐⭐ | ❌ 不推荐 |

---

## 3. 关键结论

### PEAS作为"评估对齐层"的定位

PEAS的核心价值:
1. **原则注入 (P)**: 通过Middleware/Hook注入行为约束
2. **环境感知 (E)**: 通过Sensor收集执行上下文
3. **执行监控 (A)**: 通过Tool wrapper监控Actuator行为
4. **结果评估 (S)**: 通过评估节点输出对齐结果

### 技术挑战总结

| 挑战 | 描述 | 解决方案 |
|------|------|----------|
| **执行时延** | Hook/Middleware增加调用延迟 | 异步评估 + 缓存 |
| **状态管理** | 评估结果需跨工具持久化 | 外部DB/Redis |
| **流程控制** | 评估失败如何阻止执行 | Conditional Edge |
| **标准化接口** | 跨框架通用 | 抽象PEAS Interface |

### 最佳方案: LangGraph

理由:
1. **原生支持**: Middleware + Custom Node设计天然适合评估层
2. **灵活性**: 可插入到任意执行节点前后
3. **状态流**: 内置StateGraph管理评估上下文
4. **社区活跃**: 持续更新，文档完善

---

## 4. 后续步骤

1. **原型验证**: 用LangGraph实现最小PEAS评估节点
2. **接口抽象**: 定义PEAS评估标准接口
3. **适配器开发**: 为Claude Code开发MCP评估服务
4. **性能测试**: 评估集成对执行延迟的影响
