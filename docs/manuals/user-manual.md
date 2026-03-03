# OpenYoung 用户手册

> **版本**: 1.0.0  
> **更新日期**: 2026-03-02

---

## 1. 产品概述

### 1.1 什么是 OpenYoung

OpenYoung 是一个自主 AI Agent 系统，参考 OpenCode 架构设计，支持多 Agent 协作、流程控制、记忆系统和自进化能力。

### 1.2 核心特性

| 特性 | 说明 |
|------|------|
| **多 Agent 架构** | 支持 Primary Agent 和 SubAgent 模式 |
| **流程控制** | 顺序、并行、条件、循环流程 |
| **记忆系统** | 三层记忆架构 (Working/Session/Persistent) |
| **自进化** | 基因、胶囊、人格演化系统 |
| **评估机制** | 多维度评估指标体系 |
| **技能管理** | 动态技能加载与发现 |
| **MCP 协议** | Model Context Protocol 支持 |

---

## 2. 快速开始

### 2.1 安装

```bash
# 克隆项目
git clone https://github.com/your-org/openyoung.git
cd openyoung

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "from src.agents.young_agent import YoungAgent; print('OK')"
```

### 2.2 第一个 Agent

```python
from src.agents.young_agent import YoungAgent
from src.core.types import AgentConfig, AgentMode, PermissionConfig, PermissionAction

# 创建配置
config = AgentConfig(
    name="my_agent",
    model="gpt-4",
    mode=AgentMode.PRIMARY,
    permission=PermissionConfig(_global=PermissionAction.ALLOW)
)

# 创建 Agent
agent = YoungAgent(config)

# 运行任务
result = await agent.run("你好，请介绍一下自己")
print(result)
```

### 2.3 使用内置 SubAgent

```python
# 使用 @mention 调用 SubAgent
result = await agent.run("@explore 查找项目中的 Python 文件")

# 可用的 SubAgent:
# - @explore: 快速探索代码库
# - @general: 通用任务处理
# - @search: 复杂搜索
# - @builder: 构建和执行
# - @reviewer: 代码审查
# - @eval: 评估任务
```

---

## 3. Agent 系统

### 3.1 Agent 模式

#### Primary 模式
- 直接与用户交互
- 拥有完整工具权限
- 负责任务规划和委派

```python
config = AgentConfig(
    name="main",
    model="gpt-4",
    mode=AgentMode.PRIMARY,
    permission=PermissionConfig(_global=PermissionAction.ALLOW)
)
```

#### SubAgent 模式
- 被主 Agent 调用
- 执行特定子任务
- 受限的权限控制

```python
from src.core.types import SubAgentType

config = SubAgentConfig(
    name="coder",
    type=SubAgentType.BUILDER,
    description="执行代码编写任务",
    permission=PermissionConfig(_global=PermissionAction.ALLOW)
)
```

### 3.2 权限管理

```python
from src.core.types import PermissionConfig, PermissionAction, PermissionRule

# 配置权限
config = AgentConfig(
    name="secure_agent",
    permission=PermissionConfig(
        _global=PermissionAction.ASK,  # 默认询问用户
        rules=[
            # 只读操作允许
            PermissionRule(
                tool_pattern="read|glob|grep",
                action=PermissionAction.ALLOW
            ),
            # 写操作需要确认
            PermissionRule(
                tool_pattern="write|edit|bash",
                action=PermissionAction.ASK
            ),
            # 危险操作拒绝
            PermissionRule(
                tool_pattern="rm -rf|system.*admin",
                action=PermissionAction.DENY
            )
        ]
    )
)
```

---

## 4. 流程控制

### 4.1 顺序流 (Sequential)

按顺序执行任务步骤。

```python
from src.flow.sequential import SequentialFlow

flow = SequentialFlow()
flow.configure(
    steps=[
        {"action": "analyze", "description": "分析需求"},
        {"action": "design", "description": "设计架构"},
        {"action": "implement", "description": "实现代码"},
        {"action": "test", "description": "测试验证"}
    ]
)

result = await flow.execute(task)
```

### 4.2 并行流 (Parallel)

同时执行多个任务。

```python
from src.flow.parallel import ParallelFlow

flow = ParallelFlow()
flow.configure(
    tasks=[
        {"id": "task1", "description": "下载数据"},
        {"id": "task2", "description": "处理图片"},
        {"id": "task3", "description": "发送通知"}
    ]
)

results = await flow.execute(task)
```

### 4.3 条件流 (Conditional)

根据条件分支执行。

```python
from src.flow.conditional import ConditionalFlow

flow = ConditionalFlow()
flow.configure(
    conditions=[
        {"pattern": r".*bug.*", "branch": "fix_bug"},
        {"pattern": r".*feature.*", "branch": "add_feature"},
        {"pattern": r".*docs.*", "branch": "update_docs"}
    ],
    default_branch="general"
)
```

### 4.4 循环流 (Loop)

循环执行直到满足条件。

```python
from src.flow.loop import LoopFlow

flow = LoopFlow()
flow.configure(
    max_iterations=5,
    condition={"type": "until_success"},
    body={"action": "retry_task"}
)
```

---

## 5. 记忆系统

### 5.1 三层记忆架构

| 层级 | 说明 | 持久化 |
|------|------|---------|
| **Working Memory** | 当前任务相关 | 否 |
| **Session Memory** | 当前会话 | 短期 |
| **Persistent Memory** | 长期记忆 | 是 |

### 5.2 使用记忆

```python
from src.memory.auto_memory import AutoMemory

memory = AutoMemory()

# 添加工作记忆
await memory.add_memory(
    content="用户想要一个登录功能",
    layer="working"
)

# 添加会话记忆
await memory.add_memory(
    content="用户偏好暗色主题",
    layer="session"
)

# 添加持久记忆
await memory.add_memory(
    content="项目使用 Django 框架",
    layer="persistent"
)

# 检索相关记忆
relevant = await memory.get_relevant_memories("登录功能")
```

### 5.3 检查点管理

```python
from src.memory.checkpoint import CheckpointManager

manager = CheckpointManager()

# 创建检查点
checkpoint_id = manager.create_checkpoint(
    "session_001",
    {"memory": memory.get_all_memory()}
)

# 恢复检查点
state = manager.restore_checkpoint(checkpoint_id)
memory.restore(state)

# 列出检查点
checkpoints = manager.list_checkpoints("session_001")
```

---

## 6. 提示词系统

### 6.1 模板使用

```python
from src.prompts.templates import PromptTemplate, PromptRegistry, TemplateType

# 创建模板
template = PromptTemplate(
    name="custom",
    template_type=TemplateType.DEVIN,
    content="""",
# 角色
你是 {{agent_name}}，专业软件工程师。

# 任务
{{task_description}}

# 要求
{{requirements}}
"""
)

# 渲染模板
result = template.render(
    agent_name="Devin",
    task_description="实现用户登录",
    requirements="使用 JWT 认证"
)
```

### 6.2 注册表

```python
registry = PromptRegistry()

# 注册模板
registry.register(template)

# 获取模板
tpl = registry.get("devin")

# 按类型获取
tpl = registry.get_by_type(TemplateType.DEVIN)

# 渲染
result = registry.render("devin", agent_name="Devin")
```

---

## 7. 评估系统

### 7.1 评估中心

```python
from src.evaluation.hub import EvaluationHub

hub = EvaluationHub()

# 注册评估指标
async def accuracy_metric(input_data):
    # 实现评估逻辑
    return 0.95

hub.register_metric("accuracy", accuracy_metric)

# 执行评估
result = await hub.evaluate("accuracy", response)
print(result.score)  # 0.95
```

### 7.2 多维度评估

```python
# 综合评估
results = await hub.evaluate_comprehensive(
    response="...",
    criteria_list=[
        "accuracy",
        "coherence", 
        "safety",
        "helpfulness"
    ]
)

for r in results:
    print(f"{r.metric}: {r.score}")
```

---

## 8. 技能管理

### 8.1 注册技能

```python
from src.skills import SkillManager, Skill

manager = SkillManager()

# 定义技能
skill = Skill(
    name="code_analyzer",
    handler=analyze_code,
    description="分析代码质量"
)

# 注册技能
manager.register(skill)

# 加载技能
manager.load("code_analyzer")

# 执行技能
result = manager.execute_skill("code_analyzer", code)
```

### 8.2 技能发现

```python
# 自动发现技能
skills = manager.discover_skills("src/skills/")

# 列出所有技能
print(manager.list_skills())
```

---

## 9. MCP 协议

### 9.1 连接 MCP Server

```python
from src.mcp import MCPClient, MCPServer

# 创建 Server
server = MCPServer("http://localhost:8080")

# 创建 Client
client = MCPClient(server)

# 连接
client.connect()

# 使用工具
tools = client.list_tools()
result = client.call_tool("web_search", {"query": "python"})
```

### 9.2 工具映射

```python
from src.mcp import MCPToolMapper

mapper = MCPToolMapper(client)

# 映射工具名称
mapper.map_tool("local_search", "remote_web_search")

# 使用本地名称调用
result = mapper.call_local_tool("local_search", {"query": "..."})
```

---

## 10. 自进化系统

### 10.1 基因系统

```python
from src.evolver.models import Gene, Capsule, Personality

# 创建基因
gene = Gene(
    name="creativity",
    value=0.8,
    version=1
)

# 创建胶囊
capsule = Capsule(
    id="creative_agent_001",
    name="Creative Agent",
    description="具有创造力的 Agent",
    genes=[gene]
)

# 创建人格
personality = Personality(name="innovator")
personality.update_trait("creativity", 0.9)
personality.update_trait("patience", 0.7)
```

### 10.2 基因加载

```python
from src.evolver.models import GeneLoader

data = {
    "genes": {
        "intelligence": 0.8,
        "creativity": 0.6,
        "speed": 0.7
    }
}

genes = GeneLoader.load_genes(data)
```

---

## 11. 数据中心

### 11.1 追踪收集

```python
from src.datacenter.datacenter import TraceCollector, Trace

collector = TraceCollector()

# 添加追踪
trace = Trace(
    id="trace_001",
    agent_id="agent_001",
    action="execute",
    input="用户请求",
    output="处理结果"
)
collector.add_trace(trace)

# 查询追踪
traces = collector.get_traces(agent_id="agent_001")
```

### 11.2 预算控制

```python
from src.datacenter.datacenter import BudgetController

controller = BudgetController(max_tokens=10000)

# 检查预算
if controller.check_budget(1000):
    controller.use_tokens(1000)
    # 执行任务
else:
    print("预算不足")
```

### 11.3 模式检测

```python
from src.datacenter.datacenter import PatternDetector

detector = PatternDetector()

# 记录模式
detector.record_pattern("file_read")
detector.record_pattern("code_analyze")
detector.record_pattern("file_read")

# 获取 top 模式
top = detector.get_top_patterns(limit=5)
# [("file_read", 2), ("code_analyze", 1)]
```

---

## 12. 配置管理

### 12.1 加载配置

```python
from src.config.loader import ConfigLoader

loader = ConfigLoader()

# 加载 YAML
config = loader.load_yaml("config/agent.yaml")

# 加载 JSON
config = loader.load_json("config/settings.json")

# 加载环境变量
env_config = loader.load_env(prefix="YOUNG_")

# 合并配置
full_config = loader.merge_configs(yaml_config, json_config, env_config)
```

### 12.2 使用配置

```python
# 设置值
loader.set("agent.name", "my_agent")
loader.set("agent.model", "gpt-4")

# 获取值
name = loader.get("agent.name", "default")

# 加载所有配置
config = loader.load_all()
```

---

## 13. 常见问题

### 13.1 如何设置 Agent 权限?

使用 `PermissionConfig` 配置权限规则，详见 3.2 节。

### 13.2 如何添加自定义评估指标?

使用 `hub.register_metric()` 注册评估函数，详见 7.1 节。

### 13.3 如何实现技能?

定义技能处理器函数并注册到 SkillManager，详见 8.1 节。

### 13.4 如何持久化记忆?

使用 `layer="persistent"` 添加持久记忆，或使用 CheckpointManager。

---

## 14. 附录

### 14.1 API 快速参考

| 类 | 说明 |
|---|------|
| `YoungAgent` | 主 Agent 类 |
| `AgentConfig` | Agent 配置 |
| `SequentialFlow` | 顺序流程 |
| `ParallelFlow` | 并行流程 |
| `AutoMemory` | 自动记忆 |
| `EvaluationHub` | 评估中心 |
| `SkillManager` | 技能管理 |
| `MCPClient` | MCP 客户端 |
| `ConfigLoader` | 配置加载 |

### 14.2 示例代码

完整示例请参考 `examples/` 目录。

### 14.3 获取帮助

- 文档: https://docs.openyoung.example.com
- Issue: https://github.com/your-org/openyoung/issues


---

## 15. CLI 命令行工具

### 15.1 基本用法

```bash
# 查看帮助
openyoung --help

# 运行 Agent
openyoung run <agent_name> <task>

# 交互式模式
openyoung run <agent_name> -i
```

### 15.2 Agent 管理

```bash
# 列出所有 Agent
openyoung agent list

# 查看 Agent 详情
openyoung agent info <agent_name>

# 设置默认 Agent
openyoung agent use <agent_name>
```

### 15.3 LLM Provider 管理

```bash
# 列出 LLM Provider
openyoung llm list
openyoung llm list --enabled

# 添加 Provider
openyoung llm add <provider_name> --api-key <key> --base-url <url> --models <model1,model2> --default

# 查看 Provider 信息
openyoung llm info <provider_name>

# 设置默认 Provider
openyoung llm use <provider_name>

# 移除 Provider
openyoung llm remove <provider_name>
```

支持的 Provider: DeepSeek, Moonshot, Qwen, GLM

### 15.4 包管理

```bash
# 列出已安装包
openyoung package list

# 安装包
openyoung install <package_name>
```

### 15.5 配置管理

```bash
# 列出配置
openyoung config list

# 获取配置值
openyoung config get <key>

# 设置配置值
openyoung config set <key> <value>
```

### 15.6 源码管理

```bash
# 列出源码源
openyoung source list

# 添加源码源
openyoung source add <source_name> --url <url>
```

### 15.7 Agent 配置验证

```python
from src.cli.main import AgentLoader

loader = AgentLoader()

# 验证配置
is_valid, error = loader.validate_config(config)
if not is_valid:
    print(f"Invalid: {error}")

# 验证 Agent 文件
is_valid, error = loader.validate_agent_file(Path("agents/my_agent.yaml"))
```

---

## 16. 外部系统集成

### 16.1 PackageManager 集成

YoungAgent 与 PackageManager 深度集成，支持动态加载技能和包：

```python
from src.agents.young_agent import YoungAgent

agent = YoungAgent(config)

# 加载包
await agent.load_package("my_package")

# 加载技能
await agent.load_skill("code_analyzer")
```

### 16.2 DataCenter 集成

支持追踪记录和质量检查：

```python
from src.agents.young_agent import YoungAgent

agent = YoungAgent(config)

# 记录执行追踪
await agent._record_trace(
    action="execute",
    input_data={"task": "my task"},
    output_data={"result": "..."}
)

# 质量检查
is_quality_ok = await agent._check_quality(result)
```

### 16.3 Evolver 集成

支持 Agent 自进化能力：

```python
from src.agents.young_agent import YoungAgent

agent = YoungAgent(config)

# 触发进化
await agent._trigger_evolution(
    gene_name="creativity",
    new_value=0.9
)
```

### 16.4 EvaluationHub 集成

支持自动纠错和评估：

```python
from src.agents.young_agent import YoungAgent

agent = YoungAgent(config)

# 自纠正
corrected = await agent._self_correct(
    task="original task",
    response="original response",
    feedback="needs more detail"
)
```

---

## 17. E2E 测试

### 17.1 运行测试

```bash
# 运行所有 E2E 测试
pytest tests/e2e/ -v

# 运行特定测试文件
pytest tests/e2e/test_cli_e2e.py -v

# 运行特定测试
pytest tests/e2e/test_cli_e2e.py::test_llm_api_deepseek -v
```

### 17.2 测试覆盖

E2E 测试覆盖以下功能：

- CLI 命令（llm, agent, config, package, source）
- LLM API 调用（DeepSeek, Moonshot, Qwen, GLM）
- Agent 执行
- 模块导入
- Evolver 系统（Gene, Capsule, EvolutionEvent, Personality）
- FlowSkills（Sequential, Parallel, Conditional, Loop）
- Harness 控制（start, pause, resume, stop, stats）
