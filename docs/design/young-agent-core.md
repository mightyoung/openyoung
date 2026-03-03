# YoungAgent 核心架构设计

> 版本: 1.0.0
> 更新日期: 2026-03-01

---

## 1. 架构概述

YoungAgent 是 OpenYoung 的核心 Agent 引擎，基于 OpenCode 架构改造，提供：

- **Primary Agent**: 对标 OpenCode build 模式，全工具权限
- **SubAgent System**: 支持 @mention 调用子任务
- **Permission System**: ask/allow/deny 三级权限控制
- **Flow Control**: 通过 Flow Skill 编排工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                      Young-Agent 架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Primary Agent                          │
│  │   (对标 OpenCode build，全工具权限)                    │
│  │   - 完整工具集 (read/write/edit/bash)                │
│  │   - 权限控制 (ask/allow/deny)                       │
│  │   - 可调用 SubAgent                                  │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                  │
│         ┌──────────────────┼──────────────────┐              │
│         ▼                  ▼                  ▼              │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐       │
│  │  SubAgent │    │  SubAgent │    │  SubAgent │       │
│  │ (explore) │    │ (general) │    │ (search)  │       │
│  └────────────┘    └────────────┘    └────────────┘       │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Task Dispatcher                           │
│  │   - @mention 触发                                     │
│  │   - Session 层级管理                                  │
│  │   - 结果聚合                                          │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Permission Evaluator                      │
│  │   - ask/allow/deny 三级                               │
│  │   - 通配符匹配                                         │
│  │   - 用户确认流程                                       │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心类型定义

### 2.1 Agent Mode

```python
from enum import Enum

class AgentMode(Enum):
    """Agent 模式 - 对标 OpenCode"""
    PRIMARY = "primary"     # 主 Agent，直接与用户交互
    SUBAGENT = "subagent"  # 子 Agent，被主 Agent 调用
    ALL = "all"           # 两者皆可
```

### 2.2 Permission Action

```python
class PermissionAction(Enum):
    """权限动作 - 对标 OpenCode"""
    ALLOW = "allow"  # 无需批准直接执行
    ASK = "ask"      # 提示用户确认
    DENY = "deny"   # 阻止执行
```

### 2.3 Agent Config

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    mode: AgentMode = AgentMode.PRIMARY
    
    # 模型配置
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    # 工具配置
    tools: List[str] = field(default_factory=list)
    
    # 权限配置
    permission: "PermissionConfig" = field(default_factory=lambda: PermissionConfig())
    
    # Flow Skill
    flow_skill: Optional["FlowSkill"] = None
```

---

## 3. 核心 Agent 类

### 3.1 YoungAgent 主类

```python
class YoungAgent:
    """YoungAgent 主类 - 对标 OpenCode"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.mode = config.mode
        self._session_id = None
        self._history: List[Message] = []
        self._sub_agents: Dict[str, SubAgent] = {}
        self._permission = PermissionEvaluator(config.permission)
        self._dispatcher = TaskDispatcher(self._sub_agents)
    
    async def run(self, user_input: str) -> str:
        """主运行循环"""
        
        # 1. 权限检查
        if not await self._permission.can_run(user_input):
            return "Permission denied"
        
        # 2. 解析输入（检测 @mention）
        task = await self._parse_input(user_input)
        
        # 3. 判断是否需要委托给 SubAgent
        if await self._should_delegate(task):
            return await self._delegate_to_subagent(task)
        
        # 4. 执行任务
        result = await self._execute(task)
        
        # 5. 后处理
        return await self._post_process(result)
    
    async def _parse_input(self, user_input: str) -> Task:
        """解析用户输入"""
        # 检测 @mention
        # 提取任务描述
        pass
    
    async def _should_delegate(self, task: Task) -> bool:
        """判断是否需要委托"""
        # 根据任务类型和 SubAgent 配置决定
        pass
    
    async def _delegate_to_subagent(self, task: Task) -> str:
        """委托给 SubAgent"""
        result = await self._dispatcher.dispatch(
            params=TaskDispatchParams(...),
            parent_context=self._get_context()
        )
        return result["output"]
```

---

## 4. SubAgent 系统

### 4.1 SubAgent 类型

```python
class SubAgentType(Enum):
    """预定义 SubAgent 类型 - 对标 OpenCode"""
    EXPLORE = "explore"      # 快速探索代码库（只读）
    GENERAL = "general"      # 通用任务处理
    SEARCH = "search"       # 复杂搜索任务
    BUILDER = "builder"     # 构建和执行
    REVIEWER = "reviewer"   # 代码审查
    EVAL = "eval"           # 评估任务
```

### 4.2 SubAgent 配置

```python
@dataclass
class SubAgentConfig:
    """SubAgent 轻量配置"""
    name: str
    type: SubAgentType
    description: str                    # 必须：描述 SubAgent 用途
    model: str = "default"
    temperature: float = 0.7
    instructions: Optional[str] = None
    hidden: bool = False
    permission: PermissionConfig = field(default_factory=lambda: PermissionConfig(
        _global="allow" if SubAgentType in [SubAgentType.GENERAL, SubAgentType.BUILDER] else "deny"
    ))
```

### 4.3 内置 SubAgent

| SubAgent | 描述 | 默认权限 |
|----------|------|---------|
| **explore** | 快速探索代码库，只读 | edit: deny, bash: deny |
| **general** | 通用任务处理 | 全部允许 |
| **search** | 复杂搜索任务 | edit: deny, bash: deny |
| **builder** | 构建和执行任务 | 全部允许 |
| **reviewer** | 代码审查 | edit: deny, bash: deny |
| **eval** | 执行评估任务 | edit: deny, bash: deny |

### 4.4 SubAgent 调用逻辑 (融合设计)

#### 4.4.1 调用触发方式

| 触发方式 | 描述 | 示例 |
|----------|------|------|
| **@mention** | 用户显式调用 | `@eval 评估这段代码` |
| **工具调用** | 显式 Agent 工具 | `Agent(tool="eval", action="evaluate")` |
| **消息触发** | 自动识别评估需求 | Primary Agent 识别到需要评估时 |

#### 4.4.2 Session 模型 (Claude Code 方式)

```
Primary Agent Context
    │
    │ 调用 @mention 或 Agent()
    ▼
┌─────────────────────────────────────────┐
│  EvalSubAgent Context (独立)           │
│  - 全新 context window                 │
│  - 执行评估                            │
│  - 返回 Summary                        │
└─────────────────────────────────────────┘
    │
    │ Summary 返回
    │
    ▼
Primary Agent Context (保持清洁)
```

**核心设计：**
- SubAgent 运行在**独立上下文**中
- 执行完成后返回 **Summary**，而非完整输出
- 主上下文保持清洁，不被中间过程污染

#### 4.4.3 结果返回机制

```python
class SubAgentResult:
    """SubAgent 执行结果"""
    
    summary: str              # 执行摘要（返回给主上下文）
    detailed_output: str      # 详细输出（保留在子上下文）
    status: str             # success | failed | partial
    metrics: dict           # 执行指标
    session_id: str        # 子会话 ID（用于恢复）
```

#### 4.4.4 Harness 记录

```python
class SubAgentRecorder:
    """SubAgent 执行记录器"""
    
    async def record_invocation(
        self,
        subagent_type: str,
        params: dict,
        parent_session_id: str
    ):
        """记录调用"""
        record = {
            "record_type": "subagent_invocation",
            "timestamp": datetime.now().isoformat(),
            "parent_session": parent_session_id,
            "subagent_type": subagent_type,
            "params": params,
        }
        await self.harness.record(record)
    
    async def record_result(
        self,
        session_id: str,
        result: SubAgentResult
    ):
        """记录结果"""
        record = {
            "record_type": "subagent_result",
            "session_id": session_id,
            "summary": result.summary,
            "status": result.status,
            "metrics": result.metrics,
            "duration_ms": result.metrics.get("duration_ms", 0),
        }
        await self.harness.record(record)
```

#### 4.4.5 分层设计：工具 + Flow Skill

```
┌─────────────────────────────────────────────────────────┐
│  基础层：工具调用 (高灵活性)                            │
├─────────────────────────────────────────────────────────┤
│  eval_search()           - 搜索评估包                  │
│  eval_exact_match()     - 精确匹配                    │
│  eval_syntax_check()    - 语法检查                    │
│  eval_llm_judge()       - LLM 评判                    │
│  eval_aggregate()       - 聚合结果                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  流程层：Flow Skill (复杂流程封装)                    │
├─────────────────────────────────────────────────────────┤
│  code-eval-flow       - 代码评估流程 (含自修正)       │
│  pr-review-flow        - PR 审查流程                   │
│  test-validate-flow    - 测试验证流程                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  触发层：消息自动 (根据上下文识别)                     │
├─────────────────────────────────────────────────────────┤
│  "代码编辑完成"   → 自动触发代码评估                 │
│  "安全问题"       → 自动触发安全检查                  │
│  "性能问题"       → 自动触发效率评估                  │
└─────────────────────────────────────────────────────────┘
```

#### 4.4.6 EvalSubAgent 配置

```yaml
# 内置 SubAgent 配置
subagents:
  - name: eval
    type: EVAL
    description: "执行评估任务，包括规则评估和 LLM 评判"
    model: gpt-4o-mini
    tools:
      - eval_search
      - eval_load_package
      - eval_exact_match
      - eval_syntax_check
      - eval_llm_judge
      - eval_aggregate
      - eval_log
    
    # 触发模式
    trigger:
      @mention: true      # 支持 @eval 调用
      auto: true          # 支持自动触发
      tools:
        - Agent          # 支持 Agent() 工具调用
    
    # 上下文配置
    context:
      isolation: true    # 独立上下文
      summary_mode: true  # Summary 返回模式
      max_turns: 50
```

---

## 5. Task Dispatch 系统

### 5.1 Task Tool

```python
@dataclass
class TaskDispatchParams:
    """Task Tool 参数 - 对标 OpenCode"""
    description: str           # 简短描述 (3-5 词) [必须]
    prompt: str               # 详细任务提示 [必须]
    sub_agent_type: str      # 子智能体类型 [必须]
    task_id: Optional[str] = None   # 可选：继续之前的任务
    command: Optional[str] = None    # 可选：触发命令
```

### 5.2 Task Dispatcher

```python
class TaskDispatcher:
    """任务调度器 - 对标 OpenCode task.ts"""
    
    def __init__(self, sub_agents: Dict[str, SubAgent]):
        self.sub_agents = sub_agents
    
    async def dispatch(
        self,
        params: TaskDispatchParams,
        parent_context: dict,
        existing_task_id: Optional[str] = None
    ) -> dict:
        """调度任务到 SubAgent"""
        
        # 1. 获取或恢复会话
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
        
        # 5. 返回结果
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
        """获取或创建会话"""
        if task_id:
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
```

---

## 6. 权限系统

### 6.1 Permission Evaluator

```python
class PermissionEvaluator:
    """权限评估器 - 对标 OpenCode PermissionNext"""
    
    def __init__(self, permission: PermissionConfig):
        self.permission = permission
    
    async def check(self, tool_name: str, params: dict) -> PermissionAction:
        """检查权限"""
        
        # 1. 检查通配符规则
        for rule in self.permission.rules:
            if self._match_rule(tool_name, params, rule):
                return rule.action
        
        # 2. 返回全局默认
        return self.permission._global
    
    def _match_rule(self, tool_name: str, params: dict, rule: PermissionRule) -> bool:
        """匹配规则"""
        # 通配符匹配
        pass
```

### 6.2 Permission Config

```python
@dataclass
class PermissionRule:
    """权限规则"""
    tool_pattern: str         # 工具名模式（支持通配符）
    params_pattern: dict = None  # 参数模式
    action: PermissionAction = PermissionAction.ASK

@dataclass
class PermissionConfig:
    """权限配置"""
    _global: PermissionAction = PermissionAction.ASK
    rules: List[PermissionRule] = field(default_factory=list)
    confirm_message: str = "确认执行此操作?"
```

### 6.3 权限配置示例

```yaml
# young.yaml
permission:
  _global: ask
  
  rules:
    # 文件操作需要确认
    - tool: "write"
      action: ask
    - tool: "edit"
      action: ask
    
    # 危险操作需要确认
    - tool: "bash"
      params:
        command: "rm -rf"
      action: deny
    
    # 安全操作直接允许
    - tool: "read"
      action: allow
    - tool: "glob"
      action: allow
    - tool: "grep"
      action: allow
```

---

## 7. 配置格式

### 7.1 young.yaml

```yaml
# young.yaml - YoungAgent 配置文件

# Agent 基本配置
agent:
  name: "young-agent"
  mode: primary
  model: "gpt-4o"
  temperature: 0.7
  
  # 工具配置
  tools:
    read: allow
    write: ask
    edit: ask
    bash: ask
    grep: allow
    glob: allow
  
  # SubAgent 配置
  sub_agents:
    explore:
      enabled: true
      model: "gpt-4o-mini"
    eval:
      enabled: true
      model: "gpt-4o-mini"

# 权限配置
permission:
  _global: ask
  rules:
    - tool: "bash"
      action: ask
    - tool: "write"
      action: ask

# Flow Skill 配置
flow_skills:
  enabled: true
  skills:
    - name: "code-review"
      description: "代码审查流程"
    - name: "test-generator"
      description: "测试生成流程"

# Prompt 模板配置
prompt:
  template: "manus"  # devin | windsurf | manus | minimal
  custom_sections:
    - name: "custom-rule"
      content: |
        你的自定义规则...
```

---

## 8. 设计原则

1. **零外部依赖** - 核心仅使用 Python 标准库
2. **配置驱动** - 通过 YAML/Markdown 定义 Agent
3. **权限优先** - 每次工具调用前检查权限
4. **可扩展** - Flow Skill 编排工作流
5. **可成长** - Evolver 自进化能力
6. **可回滚** - Checkpoint 支持文件编辑回滚
7. **记忆分层** - 显式 + 自动分层记忆
8. **渐进加载** - Skills 按需加载避免上下文膨胀

---

*本文档定义 YoungAgent 核心架构*
