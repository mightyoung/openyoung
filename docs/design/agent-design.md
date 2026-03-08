# Mightyoung 智能体设计

> 版本: 1.0.0
> 更新日期: 2026-03-01

> 关联: [young-agent-core.md](./young-agent-core.md) - YoungAgent 核心架构定义

---

## 4. Agent 支柱详解

### 4.1 定位

Agent 支柱为 LLM 提供**可装备、可成长、可评估**的智能体范式。设计原则：**继承体系清晰、依赖注入解耦、Skill 灵活组合、自进化内置**。

### 4.2 三层映射

| 层级 | 内容 | 本次范围 |
|------|------|---------|
| **合作层**: 通用 Skill/MCP | Skill 库、MCP Server 库、Tool 库 | ✅ 定义标准 |
| **通用层**: Agent 范式 | AdvancedAgent + SubAgent | ✅ 实现 |
| **价值提升层**: 行业 Agent | 行业 Skill、Evolver 包、Flow Skill | ❌ Package |

### 4.3 OpenCode 对齐架构

参考 OpenCode 的设计，采用 **AdvancedAgent + SubAgent** 架构：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OpenCode 对齐架构                                  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                   AdvancedAgent (通用模板 Agent)                      │  │
│  │                                                                   │  │
│  │  类似于 OpenCode 的 "Build" Agent                                 │  │
│  │  • 完整工具权限 (read/write/edit/bash)                           │  │
│  │  • 可调用 SubAgent                                                │  │
│  │  • 通用模板 - 无功能定位区分                                       │  │
│  │                                                                   │  │
│  │  配置化权限控制 (完全对齐 OpenCode)：                              │  │
│  │  • permission: { "*": "allow", "bash": "ask", "edit": "deny" } │  │
│  │  • 支持通配符模式匹配                                              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│                              ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                      Task Tool (任务调度)                          │  │
│  │  description + prompt + subagent_type + task_id                    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                              │                                        │
│         ┌──────────────────┼──────────────────┐                      │
│         ▼                  ▼                  ▼                      │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐              │
│  │  SubAgent  │    │  SubAgent  │    │  SubAgent  │              │
│  │  (explore) │    │  (general) │    │  (search)  │              │
│  └────────────┘    └────────────┘    └────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Agent 类型定义

#### 4.4.1 Agent Mode (代理模式)

```python
from enum import Enum

class AgentMode(Enum):
    """Agent 模式 - 参考 OpenCode"""
    PRIMARY = "primary"     # 主 Agent，直接与用户交互
    SUBAGENT = "subagent"  # 子 Agent，被主 Agent 调用
    ALL = "all"           # 两者皆可
```

#### 4.4.2 Permission 权限控制 (完全对齐 OpenCode)

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from enum import Enum

class PermissionAction(Enum):
    """权限动作 - 完全对齐 OpenCode"""
    ALLOW = "allow"  # 无需批准直接执行
    ASK = "ask"      # 提示用户确认
    DENY = "deny"    # 阻止执行

@dataclass
class PermissionRule:
    """权限规则 - 参考 OpenCode PermissionNext.Rule"""
    permission: str           # 权限类型 (edit, bash, task 等)
    pattern: str = "*"      # 匹配模式 (支持通配符)
    action: PermissionAction = PermissionAction.ALLOW

@dataclass
class AgentPermission:
    """权限配置 - 完全对齐 OpenCode"""
    # 简单配置：全局设置
    _global: str = "allow"  # 默认动作

    # 粒度配置：按工具 + 模式
    rules: List[PermissionRule] = field(default_factory=list)

    @staticmethod
    def from_dict(perm: Dict[str, Union[str, dict]]) -> "AgentPermission":
        """从字典创建 - 参考 OpenCode fromConfig"""
        rules = []
        for key, value in perm.items():
            if key == "*":
                continue
            if isinstance(value, str):
                rules.append(PermissionRule(permission=key, action=PermissionAction(value)))
            elif isinstance(value, dict):
                for pattern, action in value.items():
                    rules.append(PermissionRule(permission=key, pattern=pattern, action=PermissionAction(action)))
        return AgentPermission(rules=rules)

    def evaluate(self, permission: str, pattern: str = "*") -> PermissionAction:
        """评估权限 - 参考 OpenCode PermissionNext.evaluate"""
        # 查找匹配规则 (最后匹配的规则优先)
        for rule in reversed(self.rules):
            if self._match(permission, rule.permission) and self._match(pattern, rule.pattern):
                return rule.action
        return PermissionAction(self._global)

    @staticmethod
    def _match(text: str, pattern: str) -> bool:
        """通配符匹配 - 参考 OpenCode Wildcard.match"""
        import fnmatch
        return fnmatch.fnmatch(text, pattern)
```

#### 4.4.3 可用权限类型

| 权限 | 说明 | 匹配内容 |
|------|------|---------|
| `read` | 读取文件 | 文件路径 |
| `edit` | 文件修改 (包含 write, patch) | 文件路径 |
| `bash` | 执行 Shell 命令 | 命令字符串 |
| `grep` | 内容搜索 | 正则表达式 |
| `glob` | 文件匹配 | Glob 模式 |
| `list` | 目录列表 | 目录路径 |
| `task` | 启动 SubAgent | SubAgent 名称 |
| `skill` | 加载 Skill | Skill 名称 |
| `webfetch` | 获取网页 | URL |
| `websearch` | 网页搜索 | 搜索查询 |
| `*` | 通配符 | 匹配所有 |

#### 4.4.4 Agent 配置

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class AgentConfig:
    """Agent 配置 - 参考 OpenCode"""
    name: str
    description: str                              # 必须：描述 Agent 用途
    mode: AgentMode = AgentMode.PRIMARY         # 模式
    model: str = "default"                       # 模型
    temperature: float = 0.7                     # 温度
    max_steps: Optional[int] = None               # 最大迭代次数
    hidden: bool = False                         # 是否隐藏（不在 @ 提示中显示）

    # 权限配置 - 完全对齐 OpenCode
    permission: AgentPermission = field(default_factory=AgentPermission)

    # 提示词
    prompt: Optional[str] = None                 # 内联提示词
    prompt_file: Optional[str] = None           # 提示词文件路径
```

### 4.5 SubAgent 定义

#### 4.5.1 SubAgent 类型

```python
from enum import Enum

class SubAgentType(Enum):
    """预定义 SubAgent 类型 - 参考 OpenCode"""
    EXPLORE = "explore"      # 探索代码库（只读）
    GENERAL = "general"       # 通用任务
    SEARCH = "search"        # 搜索
    BUILDER = "builder"     # 构建/执行
    REVIEWER = "reviewer"    # 代码审查
```

#### 4.5.2 SubAgent 接口

```python
from typing import Protocol, Any, Optional, List
from dataclasses import dataclass

@dataclass
class SubAgentConfig:
    """SubAgent 轻量配置"""
    name: str
    type: SubAgentType
    description: str                    # 必须：描述 SubAgent 用途
    model: str = "default"
    max_tokens: int = 4096
    temperature: float = 0.7
    instructions: Optional[str] = None
    hidden: bool = False
    permission: AgentPermission = field(default_factory=AgentPermission)

class SubAgent(Protocol):
    """SubAgent 协议 - 轻量级任务执行者"""

    @property
    def name(self) -> str:
        """SubAgent 名称"""
        ...

    @property
    def description(self) -> str:
        """SubAgent 描述"""
        ...

    @property
    def agent_type(self) -> SubAgentType:
        """SubAgent 类型"""
        ...

    async def run(self, prompt: str, context: dict) -> dict:
        """执行任务，返回结果"""
        ...

    def get_capabilities(self) -> List[str]:
        """返回能力列表"""
        ...
```

#### 4.5.3 内置 SubAgent

| SubAgent | 描述 | 默认权限 |
|-----------|------|---------|
| **explore** | 快速探索代码库，只读 | edit: deny, bash: deny |
| **general** | 通用任务处理 | 全部允许 |
| **search** | 复杂搜索任务 | edit: deny, bash: deny |
| **builder** | 构建和执行任务 | 全部允许 |
| **reviewer** | 代码审查 | edit: deny, bash: deny |

### 4.6 AdvancedAgent 定义

#### 4.6.1 核心接口

```python
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field
import uuid

@dataclass
class Task:
    """任务定义"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""           # 简短描述 (3-5 词)
    prompt: str = ""               # 详细任务提示
    sub_agent_type: str = ""        # 子智能体类型

class AdvancedAgent:
    """高级智能体 - 参考 OpenCode Primary Agent

    通用模板 Agent：
    - 完整工具权限 (可配置)
    - 可调用 SubAgent
    - 无功能定位区分 (Plan/Build)
    """

    def __init__(
        self,
        name: str,
        llm_client: Any,
        config: AgentConfig,
        skills: List["Skill"] = field(default_factory=list),
        tools: List["BaseTool"] = field(default_factory=list),
        sub_agents: List[SubAgent] = field(default_factory=list),
    ):
        self.name = name
        self.llm_client = llm_client
        self.config = config
        self.skills = skills
        self.tools = tools
        self.sub_agents = {sa.name: sa for sa in sub_agents}

        # 会话上下文
        self._context: Dict[str, Any] = {}
        self._session_id: str = str(uuid.uuid4())

    async def run(self, user_input: str) -> str:
        """主入口：接收用户输入，返回结果"""
        # 1. 检查权限
        self._check_permissions()

        # 2. 上下文准备
        context = await self._prepare_context(user_input)

        # 3. 决定是否调用 SubAgent
        if needs_subagent := await self._should_delegate(context):
            return await self._delegate_to_subagent(context)

        # 4. 直接执行
        return await self._execute_direct(context)

    def _check_permissions(self):
        """检查权限配置"""
        # 权限在执行工具时动态检查
        pass

    # === 内部方法 ===

    async def _prepare_context(self, user_input: str) -> dict:
        """准备执行上下文"""
        ...

    async def _should_delegate(self, context: dict) -> bool:
        """判断是否需要委托给 SubAgent"""
        ...

    async def _delegate_to_subagent(self, context: dict) -> str:
        """委托任务给 SubAgent"""
        ...

    async def _execute_direct(self, context: dict) -> str:
        """直接执行任务"""
        ...
```

### 4.7 Task Dispatch (任务调度) - 完全对齐 OpenCode

#### 4.7.1 Task Tool 参数

参考 OpenCode Task Tool：

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskDispatchParams:
    """Task Tool 参数 - 完全对齐 OpenCode"""
    description: str           # 简短描述 (3-5 词) [必须]
    prompt: str               # 详细任务提示 [必须]
    sub_agent_type: str       # 子智能体类型 [必须]
    task_id: Optional[str] = None   # 可选：继续之前的任务
    command: Optional[str] = None    # 可选：触发命令
```

#### 4.7.2 任务调度器

参考 OpenCode task.ts 实现：

```python
class TaskDispatcher:
    """任务调度器 - 完全对齐 OpenCode"""

    def __init__(self, sub_agents: Dict[str, SubAgent]):
        self.sub_agents = sub_agents

    async def dispatch(
        self,
        params: TaskDispatchParams,
        parent_context: dict,
        existing_task_id: Optional[str] = None
    ) -> dict:
        """调度任务到 SubAgent"""

        # 1. 获取或恢复会话 (参考 OpenCode Session.create)
        session_id = await self._get_or_create_session(
            params.task_id or existing_task_id,
            parent_context.get("session_id"),
            params.description
        )

        # 2. 构建隔离上下文
        context = self._build_isolated_context(params, parent_context)

        # 3. 获取 SubAgent
        sub_agent = self.sub_agents.get(params.sub_agent_type)
        if not sub_agent:
            raise ValueError(f"Unknown sub_agent_type: {params.sub_agent_type}")

        # 4. 执行任务
        result = await sub_agent.run(params.prompt, context)

        # 5. 返回结果 (对齐 OpenCode 输出格式)
        return {
            "task_id": session_id,
            "result": result,
            "output": self._format_output(result),
            "status": "success"
        }

    async def _get_or_create_session(
        self,
        task_id: Optional[str],
        parent_session_id: str,
        description: str
    ) -> str:
        """获取或创建会话 - 参考 OpenCode Session.create"""
        if task_id:
            # 恢复之前的任务
            existing = await self._get_session(task_id)
            if existing:
                return existing

        # 创建新的子会话
        new_session_id = str(uuid.uuid4())
        await self._create_session(
            parent_id=parent_session_id,
            session_id=new_session_id,
            title=f"{description} (@{self.sub_agent_type})"
        )
        return new_session_id

    def _build_isolated_context(
        self,
        params: TaskDispatchParams,
        parent_context: dict
    ) -> dict:
        """构建隔离的上下文"""
        return {
            "task_description": params.description,
            "parent_summary": parent_context.get("summary", ""),
            "relevant_files": parent_context.get("relevant_files", []),
            "session_id": parent_context.get("session_id")
        }

    def _format_output(self, result: dict) -> str:
        """格式化输出 - 参考 OpenCode task.ts"""
        return f"""<task_result>
{result.get('text', '')}
</task_result>"""
```

#### 4.7.3 执行模式 (完全对齐 OpenCode)

```python
class TaskExecutor:
    """任务执行器 - 完全对齐 OpenCode"""

    async def execute_tasks(
        self,
        tasks: List[TaskDispatchParams],
        parent_context: dict,
        mode: str = "sequential"
    ) -> List[dict]:
        """执行任务 - 参考 OpenCode 实现

        Sequential: 默认模式，串行执行
        Parallel: 通过多次 task 调用实现并行
        """

        if mode == "parallel":
            # 并行执行 - 多个 task 调用创建独立子会话
            results = await asyncio.gather(
                *[self._dispatch_one(task, parent_context) for task in tasks]
            )
            return list(results)
        else:
            # 串行执行 - 默认模式
            results = []
            for task in tasks:
                result = await self._dispatch_one(task, parent_context)
                results.append(result)
            return results

    async def _dispatch_one(
        self,
        params: TaskDispatchParams,
        parent_context: dict
    ) -> dict:
        """执行单个任务"""
        dispatcher = TaskDispatcher(self.sub_agents)
        return await dispatcher.dispatch(params, parent_context)
```

#### 4.7.4 权限检查 (完全对齐 OpenCode)

```python
class PermissionChecker:
    """权限检查器 - 完全对齐 OpenCode PermissionNext"""

    def __init__(self, permission: AgentPermission):
        self.permission = permission

    async def check(
        self,
        tool_name: str,
        pattern: str = "*",
        user_override: Optional[str] = None
    ) -> bool:
        """检查权限 - 参考 OpenCode PermissionNext.evaluate

        Returns True if allowed, False if denied.
        Raises PermissionAskError if user confirmation needed.
        """
        # 1. 检查用户覆盖 (once/always/reject)
        if user_override:
            return user_override in ("once", "always")

        # 2. 评估权限规则
        action = self.permission.evaluate(tool_name, pattern)

        if action == PermissionAction.ALLOW:
            return True
        elif action == PermissionAction.DENY:
            return False
        else:  # ASK
            raise PermissionAskError(tool_name, pattern)

    async def check_subagent(self, subagent_type: str) -> bool:
        """检查 SubAgent 调用权限"""
        return await self.check("task", subagent_type)

class PermissionAskError(Exception):
    """需要用户确认的权限请求"""
    def __init__(self, tool: str, pattern: str):
        self.tool = tool
        self.pattern = pattern
        super().__init__(f"Permission required: {tool} {pattern}")
```

### 4.8 结果聚合

```python
class ResultAggregator:
    """结果聚合器 - 参考 OpenCode task.ts 输出格式"""

    @staticmethod
    async def aggregate(results: List[dict]) -> str:
        """聚合多个子任务的结果

        输出格式对齐 OpenCode:
        task_id: xxx
        <task_result>
        ...
        </task_result>
        """
        outputs = []
        for r in results:
            task_id = r.get("task_id", "unknown")
            result_text = r.get("output", r.get("result", ""))
            outputs.append(f"task_id: {task_id}\n\n{result_text}")

        return "\n\n---\n\n".join(outputs)
```

### 4.9 执行流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                   AdvancedAgent.run()                         │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 1. _check_permissions()                           │  │
│  │ 2. _prepare_context()                             │  │
│  │ 3. _should_delegate()                            │  │
│  │    │                                              │  │
│  │    ├── True → TaskDispatcher.dispatch()            │  │
│  │    │    ├── _get_or_create_session()              │  │
│  │    │    ├── _build_isolated_context()             │  │
│  │    │    └── sub_agent.run()                       │  │
│  │    │                                              │  │
│  │    └── False → _execute_direct()                  │  │
│  │         └── Tool execution + permission check       │  │
│  └─────────────────────────────────────────────────────┘  │
│    │                                                      │
│    ▼                                                      │
│ ResultAggregator.aggregate()                              │
│    │                                                      │
│    ▼                                                      │
│ 最终输出                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 4.10 依赖注入设计

Agent 通过构造函数接受 `llm_client` 参数，实现与 LLM 提供商的解耦：

```python
# 方式 1: 默认内置客户端
agent = AdvancedAgent(name="assistant", ...)  # 使用默认 LLM 客户端

# 方式 2: 注入自定义客户端
custom_client = MyLLMClient(api_key="...")
agent = AdvancedAgent(name="assistant", llm_client=custom_client, ...)

# 方式 3: 通过工厂创建（推荐）
from src.core.agent_factory import AgentFactory

agent = AgentFactory.create(
    agent_type="advanced",
    name="assistant",
    config=AgentConfig(...),
    llm_provider="openai",  # 配置化
)
```

### 4.11 核心引擎入口设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Layer                            │
│                      /api/v1/agents/{id}/run                    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AgentFactory.create()                        │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ 1. 加载 mightyoung.yaml 配置                              │   │
│  │ 2. 解析 Agent 定义 (mode, permission)                   │   │
│  │ 3. 初始化 LLM 客户端                                    │   │
│  │ 4. 加载 Skills/Tools/SubAgents                         │   │
│  │ 5. 实例化 AdvancedAgent                                 │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AdvancedAgent.run()                            │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ 1. _check_permissions() → 权限检查                      │   │
│  │ 2. _prepare_context() → 准备上下文                      │   │
│  │ 3. _should_delegate() → 判断是否委托                   │   │
│  │ 4. TaskDispatcher.dispatch() → 调用 SubAgent 或工具      │   │
│  │ 5. ResultAggregator.aggregate() → 聚合结果            │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 4.12 配置文件格式 (mightyoung.yaml)

```yaml
# Agent 定义 - 完全对齐 OpenCode 配置格式
agents:
  # 主 Agent 配置
  primary:
    name: "assistant"
    description: "通用助手，处理各种任务"
    mode: "primary"
    model: "qwen-plus"
    temperature: 0.7
    max_steps: 100

    # 权限配置 - 完全对齐 OpenCode
    permission:
      # 全局默认
      "*": "allow"
      # 粒度配置
      edit:
        "*": "deny"
        "packages/**": "allow"
      bash:
        "*": "ask"
        "git *": "allow"
        "npm *": "allow"
        "rm *": "deny"
      task:
        "*": "allow"
        "builder": "deny"

    prompt: "{file:./prompts/assistant.txt}"

  # SubAgent 配置
  sub_agents:
    - name: "explore"
      type: "explore"
      description: "快速探索代码库"
      hidden: false
      permission:
        edit: "deny"
        bash: "deny"
        read: "allow"
        grep: "allow"
        glob: "allow"

    - name: "general"
      type: "general"
      description: "通用任务处理"
      hidden: false
      permission:
        "*": "allow"

    - name: "reviewer"
      type: "reviewer"
      description: "代码审查"
      hidden: false
      permission:
        edit: "deny"
        bash: "deny"
        webfetch: "allow"
## 4.13 Harness 集成

### 4.13.1 设计原则

- **零外部依赖**: 核心代码仅使用 Python 标准库
- **内存优先**: 默认使用内存存储，可扩展到数据库
- **可插拔架构**: 核心与可选扩展分离

### 4.13.2 核心组件

| 组件 | 功能 |
|------|------|
| **TraceCollector** | 执行轨迹收集与统计 |
| **BudgetController** | 动态预算分配与复杂度估算 |
| **PatternDetector** | 失败模式检测与建议 |
| **QualityChecker** | 输出质量检查 |
| **MiddlewareChain** | 中间件链式处理 |

### 4.13.3 EnhancedAdvancedAgent

```python
class EnhancedAdvancedAgent(AdvancedAgent):
    """增强型 Agent - 集成 Harness"""

    def __init__(
        self,
        *args,
        harness_config: HarnessConfig = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        # 初始化 Harness 组件
        self._trace_collector = TraceCollector()
        self._budget_controller = BudgetController()
        self._pattern_detector = PatternDetector()
        self._quality_checker = QualityChecker()

        # 构建中间件链
        self._middleware_chain = self._build_middleware_chain()
```

### 4.13.4 执行流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. 预算分配 (BudgetController)              │
│    • 复杂度估算                            │
│    • 动态预算分配                          │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 2. 执行前中间件 (Pre-Execute)              │
│    • TraceMiddleware                      │
│    • BudgetMiddleware                    │
│    • LoopDetectionMiddleware             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 3. Agent 执行                             │
│    • TaskDispatcher / Tool execution     │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. 执行后中间件 (Post-Execute)            │
│    • TraceMiddleware                     │
│    • QualityMiddleware                   │
└─────────────────────────────────────────────┘
    │
    ├─ 成功 → 返回结果
    │
    └─ 失败 → PatternDetector.detect() → 自动修复
```

### 4.13.5 配置

```yaml
harness:
  enabled: true
  mode: "auto"  # auto | manual | disabled

  storage:
    backend: "memory"  # memory | postgres

  trace:
    enabled: true

  budget:
    enabled: true
    dynamic: true

  pattern_detection:
    enabled: true
    auto_apply: true

  quality_check:
    enabled: true
```

---



---

## 附录：与 OpenCode 功能对照

| OpenCode 概念 | Mightyoung 实现 | 说明 |
|---------------|----------------|------|
| Primary Agent | AdvancedAgent | 主 Agent |
| SubAgent | SubAgent | 子 Agent |
| Build Agent | AdvancedAgent | 通用模板，无功能区分 |
| Task Tool | TaskDispatcher | 任务调度 |
| permission: ask/allow/deny | PermissionAction | 权限控制 |
| Wildcard 模式 | fnmatch | 通配符匹配 |
| last rule wins | reversed(self.rules) | 规则匹配顺序 |
| @mention | sub_agent_type | 调用子 Agent |
| task_id | task_id | 继续之前任务 |
| Session parentID | parent_session_id | 会话层级 |

---

*本文档基于 ARCHITECTURE.md v1.2，完全对齐 OpenCode 设计*
