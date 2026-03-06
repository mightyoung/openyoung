# OpenYoung 数据系统改进方案 v3.0

## 基于行业最佳实践的全面改进

基于 LangGraph、Anthropic、Microsoft AutoGen 的最佳实践，结合 OpenYoung 项目定位（智能 Agent 发现与部署平台）制定。

---

## 一、行业最佳实践对照

| 框架 | 核心特性 | 借鉴点 |
|------|----------|--------|
| **LangGraph** | SqliteSaver、Thread 隔离、跨线程共享 | 标准 Checkpoint 接口 |
| **Anthropic** | Initializer/Coder 角色、增量执行 | Agent 角色系统 |
| **AutoGen** | 独立工作区、共享黑板、消息传递 | Agent 间通信 |

---

## 二、当前设计问题

### 问题 1: 缺乏标准 Checkpoint 接口

**现状**: 自定义实现，与行业不兼容

**应该**: 像 LangGraph 那样提供标准接口

### 问题 2: 无 Agent 角色定义

**现状**: 只有 agent_id，无角色分工

**应该**: 像 Anthropic 那样区分 Initializer/Coder/Reviewer

### 问题 3: 缺乏 Agent 间通信

**现状**: 隔离存储，无消息机制

**应该**: 像 AutoGen 那样实现消息总线

---

## 三、改进方案

### Phase 1: 标准 Checkpoint 接口

#### 1.1 定义 CheckpointSaver 协议

```python
# src/datacenter/checkpoint.py
from typing import Protocol, Dict, Any, List, Optional
from datetime import datetime

class CheckpointSaver(Protocol):
    """标准 Checkpoint 接口 - LangGraph 风格"""

    def get(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取检查点"""

    def put(self, thread_id: str, state: Dict[str, Any]) -> str:
        """保存检查点，返回 checkpoint_id"""

    def list(self, thread_id: str = None, limit: int = 10) -> List[Dict]:
        """列出检查点"""

    def delete(self, thread_id: str) -> bool:
        """删除检查点"""
```

#### 1.2 实现 SqliteCheckpointSaver

```python
class SqliteCheckpointSaver:
    """SQLite 检查点存储"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def get(self, thread_id: str) -> Optional[Dict]:
        """获取最新检查点"""

    def put(self, thread_id: str, state: Dict) -> str:
        """保存检查点"""

    def list(self, thread_id: str = None, limit: int = 10) -> List[Dict]:
        """列出检查点"""

    def delete(self, thread_id: str) -> bool:
        """删除检查点"""
```

---

### Phase 2: Agent 角色系统

#### 2.1 Agent 角色枚举

```python
class AgentRole(str, Enum):
    """Agent 角色 - 借鉴 Anthropic"""
    INITIALIZER = "initializer"     # 环境初始化
    CODER = "coder"               # 代码生成
    REVIEWER = "reviewer"         # 代码审查
    EXECUTOR = "executor"         # 任务执行
    ORCHESTRATOR = "orchestrator" # 编排协调
    RESEARCHER = "researcher"     # 调研分析
```

#### 2.2 角色配置

```python
@dataclass
class AgentConfig:
    """Agent 配置"""
    agent_id: str
    name: str
    role: AgentRole

    # 能力
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)

    # 工作区
    workspace: str = ""  # 独立工作区路径
    shared_state: str = ""  # 共享状态文件
```

---

### Phase 3: Agent 消息总线

#### 3.1 消息类型

```python
class MessageType(str, Enum):
    """消息类型"""
    REQUEST = "request"     # 请求
    RESPONSE = "response"   # 响应
    NOTIFICATION = "notify" # 通知
    BROADCAST = "broadcast" # 广播


@dataclass
class AgentMessage:
    """Agent 消息"""
    message_id: str
    sender_id: str
    receiver_id: str  # 空表示广播
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
```

#### 3.2 消息总线实现

```python
class MessageBus:
    """Agent 消息总线 - AutoGen 黑板模式"""

    def __init__(self, db_path: str = ".young/message_bus.db"):
        self.db_path = db_path
        self._init_db()

    def publish(self, message: AgentMessage):
        """发布消息"""

    def subscribe(self, agent_id: str, handler: Callable):
        """订阅消息"""

    def get_messages(self, agent_id: str, unread_only: bool = True) -> List[AgentMessage]:
        """获取消息"""

    def mark_read(self, message_id: str):
        """标记已读"""
```

---

## 四、实施计划

### Sprint 1: Checkpoint 接口 (1周)

| 任务 | 估计 | 验收 |
|------|------|------|
| 定义 CheckpointSaver Protocol | 1h | 接口定义完成 |
| 实现 SqliteCheckpointSaver | 2h | 通过测试 |
| 实现 RedisCheckpointSaver | 2h | 可选 |
| 迁移现有 CheckpointManager | 2h | 兼容旧 API |

### Sprint 2: Agent 角色系统 (1周)

| 任务 | 估计 | 验收 |
|------|------|------|
| 定义 AgentRole 枚举 | 30min | 6+ 角色 |
| 创建 AgentConfig 数据模型 | 1h | 完整配置 |
| 集成到 AgentRegistry | 2h | 角色生效 |
| 更新文档 | 30min | 文档完整 |

### Sprint 3: 消息总线 (1周)

| 任务 | 估计 | 验收 |
|------|------|------|
| 实现 MessageBus | 2h | 消息收发正常 |
| 实现订阅机制 | 1h | 异步通知 |
| 集成到 Workspace | 1h | 共享状态 |
| 集成测试 | 1h | 端到端 |

---

## 五、使用示例

### 示例 1: Checkpoint 使用

```python
from src.datacenter.checkpoint import SqliteCheckpointSaver

# 创建检查点存储
saver = SqliteCheckpointSaver(".young/checkpoints.db")

# 保存状态
checkpoint_id = saver.put("thread-001", {
    "messages": [...],
    "current_step": 5
})

# 加载状态
state = saver.get("thread-001")
```

### 示例 2: Agent 角色

```python
from src.datacenter.agent import AgentConfig, AgentRole

# 创建不同角色的 Agent
init_agent = AgentConfig(
    agent_id="init-001",
    name="Initializer",
    role=AgentRole.INITIALIZER,
    capabilities=["setup_env", "install_deps"]
)

coder_agent = AgentConfig(
    agent_id="coder-001",
    name="Coder",
    role=AgentRole.CODER,
    capabilities=["write_code", "refactor"]
)
```

### 示例 3: Agent 通信

```python
from src.datacenter.message import MessageBus, AgentMessage, MessageType

bus = MessageBus()

# Agent A 发送消息给 Agent B
bus.publish(AgentMessage(
    message_id="msg-001",
    sender_id="coder-001",
    receiver_id="reviewer-001",
    message_type=MessageType.REQUEST,
    content={"action": "review", "pr_url": "..."}
))

# Agent B 接收消息
messages = bus.get_messages("reviewer-001")
```

---

## 六、依赖

```bash
# 已有依赖
pip install sqlalchemy blinker cachetools

# 新增依赖 (可选)
pip install redis  # Redis 检查点
pip install aioredis  # 异步 Redis
```

---

## 七、风险控制

| 风险 | 缓解 |
|------|------|
| 破坏兼容性 | 保留旧接口，内部调用新实现 |
| 性能下降 | 缓存 + 异步 |
| 复杂度增加 | 渐进式实现 |

---

## 八、验收标准

- [ ] CheckpointSaver 接口兼容 LangGraph
- [ ] 支持 6+ Agent 角色
- [ ] 消息总线支持发布/订阅
- [ ] 完整单元测试
- [ ] 向后兼容

---

*版本: 3.0*
*创建日期: 2026-03-06*
