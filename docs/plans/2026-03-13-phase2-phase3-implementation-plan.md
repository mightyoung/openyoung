# Phase 2 生态基础 + Phase 3 实施计划

> 基于顶级AI科学家视角，结合OpenYoung项目现状设计
> 创建时间: 2026-03-13

---

## 一、项目现状分析

### 已完成里程碑

| Phase | 内容 | 状态 |
|--------|------|------|
| Phase 1.1 | 数据基础设施 (EvalHub + SQLite) | ✅ |
| Phase 1.2 | 评估仪表板 (Streamlit Dashboard) | ✅ |
| Phase 1.3 | 数据导出与实时流 (SSE) | ✅ |
| Phase 2.1 | Agent工作流增强 (TaskPlanner, Reflection, ToolSelector) | ✅ |
| Phase 2.2 | 多Agent协作 (Crew, Orchestrator, TeamMemory) | ✅ |
| Phase 2.3 | 性能优化 (Cache, Async, ResourceManager) | ✅ |

### Phase 2 剩余任务

| 任务ID | 任务 | 优先级 | 依赖 |
|--------|------|--------|------|
| P2-4-1 | 技能市场基础 (Skill Marketplace) | P1 | P2.3 |
| P2-4-2 | Agent沙箱 (WASM Sandbox) | P1 | P2.3 |
| P2-4-3 | 安全策略引擎 (Security Policy Engine) | P2 | P2.1 |

---

## 二、顶级专家视角分析

### 2.1 John Ousterhout 设计哲学

> "Design for tomorrow, but implement for today."

**核心原则**:
- 渐进式交付，小步迭代
- 模块化设计支持渐进替换
- 每个阶段交付可工作代码

### 2.2 Andrej Karpathy AI Agent架构洞见

**Agent系统核心组件**:
1. **Memory** - 短期/长期记忆
2. **Planning** - 任务分解与反思 (已完成)
3. **Tools** - 外部工具调用 (已完成)
4. **Safety** - 沙箱与安全 (Phase 2.4)
5. **Observability** - 可观测性 (Phase 3)

### 2.3 行业最佳实践

| 项目 | 关键特性 | 借鉴 |
|------|---------|------|
| LangChain | LCEL表达式链式调用 | 技能市场设计 |
| CrewAI | Agent团队协作 | MultiAgentCrew扩展 |
| AutoGPT | 自主Agent循环 | Lifecycle管理 |
| GPT-Engineer | 生成式代码生成 | 技能模板化 |
| LangSmith | 可观测性标杆 |  tracing集成 |

---

## 三、Phase 2.4: 安全与沙箱 (W7-W8)

### 3.1 WASM Agent沙箱

**目标**: 安全执行不受信任的Agent代码

**技术方案**:
```
Python Agent → WASM Sandbox → 安全执行 → 结果返回
```

**核心模块**:
- `src/runtime/sandbox/wasm_runtime.py` - WASM运行时
- `src/runtime/sandbox/isolated_fs.py` - 隔离文件系统
- `src/runtime/sandbox/resource_limits.py` - 资源限制

**实现要点**:
- 基于Pyodide或WebAssembly执行Python
- 内存限制: 512MB
- CPU时间限制: 30秒
- 网络白名单

### 3.2 安全策略引擎

**目标**: 统一的安全策略管理

**核心功能**:
- 提示注入检测 (Prompt Injection)
- 敏感信息扫描 (Secret Scanning)
- 网络防火墙 (Domain Whitelist)
- 审计日志 (Audit Logging)

**模块设计**:
```python
# src/runtime/security/__init__.py
class SecurityPolicy:
    prompt_detection: bool = True
    secret_scanning: bool = True
    firewall: bool = True
    audit: bool = True

class SecurityEngine:
    def __init__(self, policy: SecurityPolicy)
    async def check(self, content: str) -> SecurityResult
    async def scan_secrets(self, content: str) -> SecretResult
```

---

## 四、Phase 3: 可观测性与生命周期 (W9-W12)

### 3.1 Memory System - 记忆系统

**目标**: 持久化记忆 + Checkpoint恢复

**技术架构**:
```
Agent Memory
├── Working Memory (当前上下文)
├── Episodic Memory (会话历史)
└── Semantic Memory (知识图谱)
```

**核心模块**:
- `src/memory/checkpoint.py` - 状态检查点
- `src/memory/auto_memory.py` - 三层记忆
- `src/memory/vector_store.py` - 向量存储

**实现方案**:
```python
class CheckpointManager:
    """Agent状态检查点管理"""
    async def save(self, agent_id: str, state: AgentState) -> str
    async def restore(self, checkpoint_id: str) -> AgentState
    async def list_checkpoints(self, agent_id: str) -> list[Checkpoint]
```

### 3.2 Observability - 可观测性

**目标**: 全链路 tracing + 指标采集

**技术选型**:
- **Tracing**: OpenTelemetry
- **Metrics**: Prometheus
- **Logging**: 结构化日志

**集成点**:
```python
# src/agents/hooks/telemetry.py
from opentelemetry import trace
from opentelemetry.exporter.otlp import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider

class TelemetryHook:
    def on_agent_start(self, agent_id: str, input: str)
    def on_tool_call(self, tool: str, input: dict)
    def on_agent_end(self, agent_id: str, output: str, duration_ms: int)
```

**Span类型**:
| Span Name | 类型 | 关键属性 |
|-----------|------|----------|
| agent.run | agent | agent_id, input_tokens |
| tool.call | tool | tool_name, duration |
| llm.request | external | model, prompt_tokens |
| eval.run | internal | task_id, score |

### 3.3 Lifecycle Management - 生命周期

**目标**: Agent完整生命周期管理

**状态机**:
```
PENDING → RUNNING → WAITING → COMPLETED
              ↓                    ↓
            ERROR ←────────────── FAILED
              ↓
           SUSPENDED
```

**核心功能**:
- Agent启动/暂停/恢复
- 超时管理
- 资源清理
- 异常恢复

---

## 五、详细实施计划

### Phase 2.4: 安全与沙箱 (W7-W8)

| 任务ID | 任务 | 交付物 | 预估工时 |
|--------|------|--------|----------|
| P2-4-1 | WASM沙箱基础 | wasm_runtime.py | 3天 |
| P2-4-2 | 隔离文件系统 | isolated_fs.py | 2天 |
| P2-4-3 | 资源限制器 | resource_limits.py | 1天 |
| P2-4-4 | 安全策略引擎 | security_policy.py | 2天 |
| P2-4-5 | 提示注入检测 | prompt_detector.py | 2天 |
| P2-4-6 | 敏感信息扫描 | secret_scanner.py | 1天 |
| P2-4-7 | 集成测试 | E2E测试 | 1天 |

### Phase 3: 可观测性与生命周期 (W9-W12)

| 任务ID | 任务 | 交付物 | 预估工时 |
|--------|------|--------|----------|
| P3-1-1 | Checkpoint管理 | checkpoint.py | 2天 |
| P3-1-2 | 三层记忆系统 | auto_memory.py | 3天 |
| P3-1-3 | OpenTelemetry集成 | telemetry.py | 2天 |
| P3-1-4 | Tracing Hooks | tracing_hooks.py | 2天 |
| P3-1-5 | 生命周期状态机 | lifecycle.py | 2天 |
| P3-1-6 | 异常恢复机制 | recovery.py | 2天 |
| P3-1-7 | 集成测试 | E2E测试 | 1天 |

---

## 六、里程碑

| 周 | 里程碑 | 交付物 |
|----|--------|--------|
| W7 | **RC1** | WASM沙箱可用 |
| W8 | **Beta** | 安全策略引擎完成 |
| W10 | **Alpha** | Checkpoint + Memory可用 |
| W12 | **GA** | 完整可观测性 + Lifecycle |

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| WASM性能 | 执行慢 | 预加载+缓存 |
| 检测误报 | 阻断正常功能 | 白名单+阈值可调 |
| 内存泄漏 | 系统不稳定 | 定期GC+监控 |
| 存储膨胀 | 磁盘满 | 自动清理+TTL |

---

## 八、关键文件清单

### 新增文件

| 文件 | 描述 |
|------|------|
| `src/runtime/sandbox/__init__.py` | 沙箱模块入口 |
| `src/runtime/sandbox/wasm_runtime.py` | WASM运行时 |
| `src/runtime/sandbox/isolated_fs.py` | 隔离文件系统 |
| `src/runtime/security/__init__.py` | 安全模块入口 |
| `src/runtime/security/policy.py` | 策略引擎 |
| `src/runtime/security/prompt_detector.py` | 注入检测 |
| `src/runtime/security/secret_scanner.py` | 敏感信息扫描 |
| `src/memory/checkpoint.py` | 检查点管理 |
| `src/memory/auto_memory.py` | 三层记忆 |
| `src/telemetry/__init__.py` | 可观测性模块 |
| `src/telemetry/hooks.py` | Telemetry Hooks |
| `src/agents/lifecycle.py` | 生命周期管理 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/agents/young_agent.py` | 集成Checkpoint/Lifecycle |
| `task_plan.md` | 更新Phase 2.4/3状态 |

---

*计划生成时间: 2026-03-13*
*方法论: John Ousterhout 增量设计 + Andrej Karpathy Agent架构*
