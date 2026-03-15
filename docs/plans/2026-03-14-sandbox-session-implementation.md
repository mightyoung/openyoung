# OpenYoung 安全沙箱 + 持久化Agent 实施计划

> 基于 E2B、LangGraph、Temporal 等业界最佳实践
> 日期: 2026-03-14

---

## 背景与目标

### 用户需求
1. **强制沙箱执行** - 确保任务执行安全性
2. **长时间运行Agent** - 持久会话，支持Web界面/API交互

### 业界参考
- **沙箱**: E2B (150ms冷启动), Daytona (Docker/K8s), gVisor
- **持久化**: LangGraph Checkpoint, Temporal Durable Execution, Mem0

---

## 阶段一：强制沙箱执行

### 任务 1.1: 安全策略引擎

**文件**: `src/runtime/sandbox/security_policy.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**实现内容**:
```python
class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SandboxPolicy:
    force_sandbox: bool = True
    working_directory: str = "/tmp/sandbox"  # 工作目录限制
    restrict_to_working_dir: bool = True
    allow_network: bool = False
    allowed_domains: list = []
    blocked_patterns: list = [r"rm\s+-rf", ...]
```

### 任务 1.2: E2B 沙箱适配器

**文件**: `src/runtime/sandbox/e2b_adapter.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**依赖**: `e2b-code-interpreter`

### 任务 1.3: 沙箱管理器工厂

**文件**: `src/runtime/sandbox/manager.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**功能**:
- SandboxFactory: 创建不同类型沙箱
- 自动选择后端 (E2B > Docker > Process)

### 任务 1.4: 集成到 TaskExecutor

**文件**: `src/agents/task_executor.py` (修改)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**修改**:
- 添加安全策略检查
- 自动强制沙箱执行

---

## 阶段二：持久化Agent会话

### 任务 2.1: 扩展 Session 数据结构

**文件**: `src/agents/session.py` (修改)

| 字段 | 值 |
|------|-----|
| 优先级 | P1 |
| 状态 | ✅ 已完成 |

**添加**:
```python
@dataclass
class Session:
    # ... 现有字段 ...
    status: SessionStatus = "idle"  # 新增: idle, running, suspended
    messages: list = field(default_factory=list)  # 新增: 对话历史
    artifacts: dict = field(default_factory=dict)  # 新增: 生成的文件
    checkpoint_id: str = ""  # 新增: 状态快照ID
```

### 任务 2.2: 检查点存储

**文件**: `src/datacenter/checkpoint_store.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P1 |
| 状态 | ✅ 已完成 |

**功能**:
- 保存/恢复Agent状态
- 类似 LangGraph Checkpointer

### 任务 2.3: API 服务器

**文件**: `src/api/session_api.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P1 |
| 状态 | ✅ 已完成 |

**端点**:
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/sessions | 创建会话 |
| POST | /api/sessions/{id}/messages | 发送消息 |
| GET | /api/sessions/{id}/history | 获取历史 |
| POST | /api/sessions/{id}/suspend | 暂停 |
| POST | /api/sessions/{id}/resume | 恢复 |
| WS | /api/ws/{id} | WebSocket |

### 任务 2.4: CLI 命令扩展

**文件**: `src/cli/session_cli.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P1 |
| 状态 | ✅ 已完成 |

**命令**:
```bash
openyoung session create <agent>
openyoung session send <id> "message"
openyoung session list
openyoung session suspend <id>
openyoung session resume <id>
```

---

## 阶段三：MCP安全适配器 (2025安全最佳实践)

### 任务 3.1: MCP服务器安全适配器

**文件**: `src/runtime/sandbox/mcp_security.py` (新建)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**功能**:
- 网络隔离 (域名白名单/黑名单)
- 路径访问控制
- 命令验证 (阻止危险命令)
- 环境变量清理 (遮蔽敏感信息)
- 审计日志

### 任务 3.2: 工作目录限制

**文件**: `src/runtime/sandbox/security_policy.py` (增强)

| 字段 | 值 |
|------|-----|
| 优先级 | P0 |
| 状态 | ✅ 已完成 |

**功能**:
- 工作目录限制 (`working_directory`)
- 路径穿越检测 (`..`, `%2e%2e`)
- 危险路径阻止 (`/proc`, `/sys`, `/dev`)
- 自动创建工作目录

---

## 实施顺序

```
Phase 1 (优先级 P0)
├── 1.1 安全策略引擎 ✅
├── 1.2 E2B 适配器 ✅
├── 1.3 沙箱管理器 ✅
└── 1.4 TaskExecutor 集成 ✅

Phase 2 (优先级 P1)
├── 2.1 扩展 Session ✅
├── 2.2 检查点存储 ✅
├── 2.3 API 服务器 ✅
└── 2.4 CLI 命令 ✅

Phase 3 (2025安全实践)
├── 3.1 MCP安全适配器 ✅
└── 3.2 工作目录限制 ✅
```
```

---

## 依赖关系

| 任务 | 前置任务 |
|------|----------|
| 1.2 E2B适配器 | 1.1 安全策略 |
| 1.3 沙箱管理器 | 1.2 E2B适配器 |
| 1.4 TaskExecutor集成 | 1.3 沙箱管理器 |
| 2.2 检查点存储 | 2.1 扩展Session |
| 2.3 API服务器 | 2.2 检查点存储 |
| 2.4 CLI命令 | 2.3 API服务器 |

---

## 验收标准

### 强制沙箱
- [ ] 所有代码执行默认在沙箱中运行
- [ ] 危险命令被阻止
- [ ] 可配置风险级别阈值

### 持久会话
- [ ] 创建长期Agent会话
- [ ] 通过API发送消息
- [ ] 支持暂停/恢复
- [ ] WebSocket实时交互
- [ ] 状态持久化到磁盘

---

## 里程碑

| 阶段 | 里程碑 | 预计时间 |
|------|--------|----------|
| Phase 1 | 强制沙箱可用 | 2小时 |
| Phase 2 | 持久会话API | 3小时 |
| 合计 | 完整功能 | 5小时 |

---

*计划创建: 2026-03-14*
*方法论: E2B + LangGraph + Temporal 最佳实践*
