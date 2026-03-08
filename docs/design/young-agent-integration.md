# YoungAgent 外部系统集成设计

> 版本: 1.0.0
> 更新日期: 2026-03-01

---

## 1. 外部系统集成概述

YoungAgent 与外部系统的集成架构：

- **Package Manager**: 包管理
- **DataCenter**: 数据中心
- **EvaluationHub**: 评估中心
- **Evolver**: 进化器
- **Harness**: 测试/评估框架

---

VZ|## 2. 与 Package Manager 集成

### 2.1 集成架构

```
YoungAgent
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              PackageManagerIntegration                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  1. 安装/加载 Package                           │    │
│  │  2. 解析 package.yaml                           │    │
│  │  3. 提取 Skill/MCP/Tools                      │    │
│  │  4. 注册到 Agent 上下文                         │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              Package Manager                                │
│  - .mightyoung/packages/ (已安装包)                     │
│  - .mightyoung/evolved/ (进化包)                       │
│  - lock.yaml (版本锁定)                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 加载流程

```python
class YoungAgent:
    def __init__(self, config: AgentConfig):
        self.package_manager = PackageManager()
        self.packages: Dict[str, Package] = {}
        self.skills: Dict[str, Skill] = {}
        self.tools: Dict[str, BaseTool] = {}

    async def initialize(self):
        """初始化时加载配置的包"""
        # 1. 读取 Agent 配置中的依赖
        for pkg_name in self.config.dependencies:
            # 2. 从 Package Manager 获取包
            package = await self.package_manager.get(pkg_name)
            self.packages[pkg_name] = package

            # 3. 提取并注册 Skill
            if package.has_skill():
                skill = package.get_skill()
                self.skills[skill.name] = skill

            # 4. 提取并注册 Tools
            if package.has_tools():
                tools = package.get_tools()
                for tool in tools:
                    self.tools[tool.name] = tool

    async def load_skill(self, skill_name: str) -> Skill:
        """按需加载 Skill"""
        if skill_name in self.skills:
            return self.skills[skill_name]

        # 动态加载
        package = await self.package_manager.get(f"@{skill_name}")
        skill = package.get_skill()
        self.skills[skill_name] = skill
        return skill
```

### 2.3 配置示例

```yaml
# young.yaml
agent:
  name: "my-agent"
  dependencies:
    - "@skills/coding"        # Skill 包
    - "@mcp/github"          # MCP 包
    - "@tools/linter"        # Tools 包
    - "@eval/correctness"   # Evaluation 包

packages:
    install_on_startup: true
    source_priority:
      - evolved    # 进化版本优先
      - local
      - package
```

### 2.4 Skill 加载优先级

```
加载优先级 (高 → 低):
1. agents/my-agent/evolved/   ← Agent 进化的 Skill
2. .mightyoung/evolved/       ← 全局进化的 Skill
3. .mightyoung/packages/      ← Package Manager 安装的 Skill

同一 Skill 多来源时:
- 使用进化版本 (evolved > package)
- 记录来源便于追溯
```

BH|---


XN|## 3. 与 DataCenter 集成

### 3.1 集成架构

```
YoungAgent
    │
    ├─────────────────────────────┬──────────────────────┐
    │                             │                      │
    ▼                             ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  TraceCollector │   │  Memory Layer   │   │ QualityChecker │
│  执行轨迹收集    │   │  三层记忆       │   │ 质量检查       │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      DataCenter        │
                    │  - PostgreSQL          │
                    │  - Redis (可选)       │
                    │  - S3 (可选)          │
                    └─────────────────────────┘
```

### 3.2 DataCenter 配置加载


```python
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

class StorageType(Enum):
    MEMORY = "memory"
    POSTGRES = "postgres"
    REDIS = "redis"

@dataclass
class DataCenterConfig:
    """DataCenter 配置"""
    # 存储类型
    storage: StorageType = StorageType.MEMORY

    # PostgreSQL 配置
    postgres:
        host: str = "localhost"
        port: int = 5432
        database: str = "young"
        user: str = "postgres"
        password: str = ""

    # Redis 配置 (可选)
    redis:
        host: str = "localhost"
        port: int = 6379
        password: str = ""
        db: int = 0

    # 数据保留策略
    retention:
        trace_days: int = 30        # 轨迹保留天数
        memory_days: int = 90       # 记忆保留天数
        checkpoint_days: int = 7     # 检查点保留天数

    # Harness 配置
    harness:
        enabled: bool = True
        trace_tools: bool = True      # 跟踪工具调用
        trace_llm: bool = True        # 跟踪 LLM 调用
        sample_rate: float = 1.0      # 采样率

class YoungAgent:
    def __init__(self, config: AgentConfig):
        # DataCenter 配置
        self.datacenter_config = config.datacenter
        self.datacenter: Optional[DataCenter] = None
        self.harness: Optional[Harness] = None

    async def initialize(self):
        """初始化 DataCenter"""
        # 1. 创建 DataCenter 实例
        self.datacenter = DataCenter(self.datacenter_config)

        # 2. 初始化存储
        await self.datacenter.initialize()

        # 3. 初始化 Harness
        if self.datacenter_config.harness.enabled:
            self.harness = Harness(
                collector=self.datacenter.trace_collector,
                config=self.datacenter_config.harness
            )
            await self.harness.initialize()

    async def _record_trace(self, tool_call: ToolCall, result: str):
        """记录执行轨迹到 DataCenter"""
        if self.harness:
            await self.harness.trace.record(
                session_id=self._session_id,
                tool_name=tool_call.function.name,
                result=result
            )
```

### 3.3 高质量数据获取

DataCenter 为 YoungAgent 提供高质量数据的获取能力：


#### 3.3.1 数据类型

| 数据类型 | 来源 | 用途 |
|---------|------|------|
| **执行轨迹** | TraceCollector | 分析错误模式、优化决策 |
| **成功案例** | TraceCollector | 学习有效策略 |
| **失败模式** | PatternDetector | 识别常见错误 |
| **质量评分** | QualityChecker | 评估执行质量 |
| **记忆数据** | Memory Layer | 上下文理解 |


#### 3.3.2 数据获取 API

```python
class DataAccessor:
    """高质量数据访问接口"""

    async def get_similar_tasks(
        self,
        task_description: str,
        limit: int = 5
    ) -> List[TraceRecord]:
        """获取相似任务的执行轨迹"""
        # 使用语义检索找到相似任务
        return await self.datacenter.search_similar(
            query=task_description,
            limit=limit
        )

    async def get_failure_patterns(
        self,
        tool_name: str = None
    ) -> List[FailurePattern]:
        """获取失败模式"""
        return await self.datacenter.patterns.get_failures(
            tool_name=tool_name
        )

    async def get_success_strategies(
        self,
        task_type: str
    ) -> List[Strategy]:
        """获取成功策略"""
        return await self.datacenter.learn.from_success(
            task_type=task_type
        )

    async def get_quality_metrics(
        self,
        session_id: str = None
    ) -> QualityMetrics:
        """获取质量指标"""
        return await self.datacenter.quality.get_metrics(
            session_id=session_id
        )

class YoungAgent:
    """YoungAgent 集成 DataAccessor"""

    async def _get_relevant_data(self, task: Task) -> dict:
        """获取任务相关的高质量数据"""
        data_accessor = DataAccessor(self.datacenter)

        # 并行获取多种数据
        results = await asyncio.gather(
            data_accessor.get_similar_tasks(task.description),
            data_accessor.get_failure_patterns(),
            return_exceptions=True
        )

        return {
            "similar_tasks": results[0] if not isinstance(results[0], Exception) else [],
            "failure_patterns": results[1] if not isinstance(results[1], Exception) else [],
        }
```

### 3.4 配置示例

```yaml
# young.yaml
datacenter:
  storage: postgres  # memory | postgres | redis

  postgres:
    host: ${PG_HOST}
    port: 5432
    database: young

  redis:
    host: ${REDIS_HOST}
    port: 6379

  retention:
    trace_days: 30
    memory_days: 90

  harness:
    enabled: true
    trace_tools: true
    trace_llm: true
    sample_rate: 1.0
```

RJ|

```python
class YoungAgent:
    def __init__(self, ...):
        # Package Manager 加载 Skills
        self.skills: List[Skill] = []
        self.packages: Dict[str, Package] = {}

    async def load_skill(self, skill_name: str) -> Skill:
        """从 Package Manager 加载 Skill"""
        package = await PackageManager.get_package(f"@{skill_name}")
        return package.get_skill()

    async def load_tools(self) -> List[BaseTool]:
        """从 Package Manager 加载 Tools"""
        tools = []
        for pkg in self.packages.values():
            tools.extend(pkg.get_tools())
        return tools
```

---

## 3. 与 DataCenter 集成

```python
class YoungAgent:
    def __init__(self, ...):
        # DataCenter 集成
        self.datacenter: Optional[DataCenter] = None
        self.harness: Optional[Harness] = None

    async def _record_trace(self, tool_call: ToolCall, result: str):
        """记录执行轨迹到 DataCenter"""
        if self.harness:
            await self.harness.trace.record(
                session_id=self._session_id,
                tool_name=tool_call.function.name,
                result=result
            )
```

---

## 4. 与 EvaluationHub/EvalSubAgent 集成

### 4.1 集成架构

```
Primary Agent
    │
    │ @eval evaluate
    ▼
EvalSubAgent (执行评估)
    │
    │ 1. search(feature_codes) → EvaluationHub
    │ 2. load_evaluators() → EvaluationHub
    │ 3. 执行评估 (按维度分批)
    │ 4. 聚合结果
    │ 5. 记录到 Harness → DataCenter
    │
    ▼
{passed, score, feedback}
```

### 4.2 EvaluationHub

EvaluationHub 是评估包仓库，仅提供包注册与加载，不执行评估任务。

#### 4.2.1 定位

- **仅提供包仓库**：不执行评估任务，仅管理评估包元数据与加载
- **被调用方**：Eval SubAgent 负责执行，Hub 提供包
- **包版本管控**：由 Package Manager 管理版本与依赖

#### 4.2.2 核心组件

```python
@dataclass
class EvalPackage:
    """评估包定义"""
    name: str
    version: str
    description: str
    dimension: EvalDimension
    level: EvalLevel
    feature_codes: list[str]
    evaluator_classes: list[type[EvaluatorDefinition]]


class PackageRegistry:
    """包注册表"""

    def __init__(self):
        self._packages: dict[str, EvalPackage] = {}

    def register(self, package: EvalPackage) -> None:
        """注册评估包"""
        self._packages[package.package_id] = package

    def get(self, name: str, version: str = None) -> EvalPackage:
        """获取包"""
        ...

    def search(
        self,
        feature_codes: list[str] = None,
        dimension: EvalDimension = None,
        level: EvalLevel = None
    ) -> list[EvalPackage]:
        """多维搜索"""
        ...


class EvaluationHub:
    """评估中心 - 仅包仓库，不执行评估"""

    def __init__(self, package_manager: PackageManager):
        self.package_manager = package_manager
        self.registry = PackageRegistry()
        self.loader = PackageLoader(self.registry)
        self.index_builder = IndexBuilder(self.registry)
```

### 4.3 EvalSubAgent

#### 4.3.1 EvalSubAgent 架构

```python
class EvalSubAgent:
    """评估子代理 - 负责执行评估"""

    def __init__(
        self,
        evaluation_hub: EvaluationHub,
        llm_client,
        harness: "Harness"
    ):
        self.hub = evaluation_hub
        self.llm_client = llm_client
        self.harness = harness
        self._loaded_packages: dict[str, list] = {}

    async def evaluate(
        self,
        feature_codes: list[str],
        input_data: dict,
        context: dict = None,
        config: dict = None
    ) -> EvaluationReport:
        """执行评估 - 主流程"""

        # 1. 从 Hub 搜索包
        packages = self.hub.search(feature_codes=feature_codes)

        # 2. 加载评估器
        evaluators = []
        for pkg in packages:
            if pkg.package_id not in self._loaded_packages:
                self._loaded_packages[pkg.package_id] = \
                    self.hub.load_evaluators(pkg)
            evaluators.extend(self._loaded_packages[pkg.package_id])

        # 3. 按维度分批执行
        results = await self._execute_by_dimension(
            evaluators, input_data, context
        )

        # 4. 聚合结果
        report = self._aggregate(results)

        # 5. 记录到 Harness (→ DataCenter)
        await self._log_to_harness(report, context)

        return report
```

#### 4.3.2 按维度分批执行

```python
async def _execute_by_dimension(
    self,
    evaluators: list,
    input_data: dict,
    context: dict
) -> list[EvalResult]:
    """按维度分批执行 - 安全 → 正确性 → 效率 → UX"""

    # 分组
    groups = {}
    for e in evaluators:
        if e.dimension not in groups:
            groups[e.dimension] = []
        groups[e.dimension].append(e)

    # 执行顺序
    order = [SAFETY, CORRECTNESS, EFFICIENCY, UX]

    all_results = []
    for dim in order:
        if dim not in groups:
            continue

        # 并行执行该批次
        batch = groups[dim]
        results = await self._execute_batch(batch, input_data, context)
        all_results.extend(results)

    return all_results

async def _execute_batch(
    self,
    evaluators: list,
    input_data: dict,
    context: dict
) -> list[EvalResult]:
    """执行一批评估器"""
    semaphore = asyncio.Semaphore(3)

    async def run(e):
        async with semaphore:
            return await e.evaluate(input_data, context)

    return await asyncio.gather(*[run(e) for e in evaluators])
```

#### 4.3.3 评估工具

| 工具 | 描述 | 类型 |
|------|------|------|
| `eval_search` | 搜索评估包 | Hub |
| `eval_load_package` | 加载评估包 | Hub |
| `eval_exact_match` | 精确匹配 | 规则 |
| `eval_syntax_check` | 语法检查 | 规则 |
| `eval_run_linter` | 运行 linter | 规则 |
| `eval_run_tests` | 运行测试 | 规则 |
| `eval_llm_judge` | LLM 评判 | LLM |
| `eval_safety_check` | 安全检查 | 规则+LLM |
| `eval_aggregate` | 聚合结果 | 执行 |

#### 4.3.4 自修正策略

```python
class SelfCorrectionStrategy:
    """分层自修正 - 基于主流实践"""

    MAX_ATTEMPTS = 3

    @staticmethod
    async def correct(task, output, eval_result, agent) -> str:
        """分层自修正"""

        for attempt in range(SelfCorrectionStrategy.MAX_ATTEMPTS):

            # 1. Tool-Based: 确定性错误直接修复
            if await SelfCorrectionStrategy._tool_fix(task, output, eval_result):
                if (await agent.eval_subagent.evaluate(...)).passed:
                    return output

            # 2. Prompt-Refine: 语义错误提示词修正
            corrected = await SelfCorrectionStrategy._prompt_refine(
                task, output, eval_result
            )
            if corrected and (await agent.eval_subagent.evaluate(...)).passed:
                return corrected

            # 3. SubTask-Split: 拆分子任务 (最后尝试)
            if attempt == SelfCorrectionStrategy.MAX_ATTEMPTS - 1:
                subtasks = await SelfCorrectionStrategy._split(task)
                output = await agent._execute_subtasks(subtasks)

        return output
```

### 4.4 评估指标

| 维度 | 指标 | 测量方式 | 阈值 |
|------|------|----------|------|
| **正确性** | exact_match | 规则 | 1.0 |
| | syntax_valid | 规则 | 1.0 |
| | semantic_correct | LLM | 4.0/5.0 |
| **效率** | token_usage | 规则 | 0.8 |
| | latency | 规则 | 0.8 |
| **安全性** | pII_leak | 规则 | 1.0 |
| | injection_attempt | 规则 | 1.0 |
| **UX** | response_clarity | LLM | 3.5/5.0 |
| | helpfulness | LLM | 3.5/5.0 |

---

## 5. 与 Evolver 集成

```python
class YoungAgent:
    async def on_session_end(self):
        """会话结束时触发 Evolver"""
        if self.evolver and self.harness:
            # 提取知识
            distillate = await self.evolver.distill(
                self.harness.get_trace()
            )

            # 生成 Gene
            if distillate.should_evolve():
                gene = await self.evolver.compile(distillate)
                await self.evolver.verify(gene)
                await self.evolver.apply(gene)
```

---

## 6. 目录结构

```
src/young/
├── agent/               # Agent 主类
├── subagent/           # SubAgent 系统
├── flow/                # FlowSkill
├── session/            # Session 管理
├── loader/             # 配置加载
├── checkpoint/         # Checkpoint
├── memory/            # Auto Memory
├── skills/            # Skills
├── evaluation/        # EvaluationHub/EvalSubAgent
│   ├── hub.py
│   ├── subagent.py
│   ├── evaluator.py
│   └── packages/
│       ├── correctness/
│       ├── efficiency/
│       ├── safety/
│       └── ux/
└── ...
```

---

*本文档定义 YoungAgent 外部系统集成设计*
