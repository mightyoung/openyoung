# Phase 0 剩余任务详细执行计划

> 生成时间: 2026-03-08
> 目标: LangGraph 集成、插件式 EvalService、Skill Creator 架构

---

## 当前状态

### 已完成

| 任务 | 状态 |
|------|------|
| R2-1: package_manager 重构 | ✅ hub模块已建立 |
| 数据类型统一 | ✅ 完成 |
| 测试覆盖提升 | ✅ 61测试用例 |
| ExecutionRecord 集成 | ✅ unified_store已集成 |
| 数据导出能力 | ✅ DataExporter已实现 |

### 已完成 (2026-03-08)

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 采用 Skill Creator 架构 | P0 | ✅ 已完成 |
| 集成 LangGraph 工作流 | P0 | ✅ 已完成 |
| 插件式 EvalService | P0 | ✅ 已完成 |
| OpenTelemetry 集成 | P1 | ✅ 已完成 |

### 待执行 (后续阶段)

| 任务 | 优先级 | 状态 |
|------|--------|------|
| LangGraph 深度集成 | P1 | ✅ 已完成 (AgentGraphBuilder) |
| 插件系统扩展 | P2 | ✅ 已完成 (7+ 插件) |

---

## 1. 集成 LangGraph 工作流

### 1.1 现状分析

项目已有 `src/flow` 模块：
- `base.py` - 基础抽象
- `pipeline.py` - 对标 LangGraph StateGraph
- `sequential.py` - 顺序执行
- `parallel.py` - 并行执行
- `loop.py` - 循环执行
- `conditional.py` - 条件执行
- `development.py` - 开发工作流
- `composite.py` - 组合模式

### 1.2 集成方案

**方案**: 渐进式集成 - 保留现有 flow，扩展支持 LangGraph

```python
# 新增 src/flow/langgraph_adapter.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

class LangGraphAdapter:
    """LangGraph 适配器"""

    def __init__(self):
        self.graph = None

    def create_agent_graph(self, nodes: list, edges: list) -> StateGraph:
        """从现有节点创建 LangGraph"""
        ...

    def create_react_agent(self, tools: list) -> create_react_agent:
        """创建 ReAct Agent"""
        ...
```

### 1.3 执行计划

| 步骤 | 任务 | 预计行数 |
|------|------|----------|
| 1 | 创建 langgraph_adapter.py | ~150 |
| 2 | 实现 StateGraph 转换器 | ~100 |
| 3 | 实现 ReAct Agent 工厂 | ~80 |
| 4 | 集成到 YoungAgent | ~50 |
| 5 | 测试验证 | - |

---

## 2. 插件式 EvalService

### 2.1 现状分析

现有评估模块：
- `src/evaluation/hub.py` - EvaluationHub
- `src/evaluation/task_eval.py` - 任务评估
- `src/evaluation/code_eval.py` - 代码评估

### 2.2 插件方案

```python
# 新增 src/evaluation/plugins.py
from abc import ABC, abstractmethod
from typing import Any

class EvalPlugin(ABC):
    """评估插件基类"""

    @abstractmethod
    def evaluate(self, task: Task, result: Any) -> EvalResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

# 内置插件
class CodeQualityPlugin(EvalPlugin):
    """代码质量评估"""

class SecurityPlugin(EvalPlugin):
    """安全评估"""

class PerformancePlugin(EvalPlugin):
    """性能评估"""

class PluginRegistry:
    """插件注册中心"""

    def register(self, plugin: EvalPlugin):
        ...

    def get(self, name: str) -> EvalPlugin:
        ...
```

### 2.3 执行计划

| 步骤 | 任务 | 预计行数 |
|------|------|----------|
| 1 | 创建 plugins.py 定义插件接口 | ~100 |
| 2 | 实现 PluginRegistry | ~50 |
| 3 | 实现 CodeQuality/Security/Performance 插件 | ~200 |
| 4 | 集成到 EvaluationHub | ~80 |
| 5 | 测试验证 | - |

---

## 3. Skill Creator 架构

### 3.1 现状分析

现有 Skills 模块：
- `src/skills/loader.py` - 技能加载器
- `src/skills/registry.py` - 技能注册表
- `src/skills/metadata.py` - 元数据
- `src/skills/retriever.py` - 检索

### 3.2 架构方案

参考 ClawHub Skill Creator：

```python
# 新增 src/skills/creator.py
from dataclasses import dataclass
from typing import Callable

@dataclass
class SkillTemplate:
    """技能模板"""
    name: str
    description: str
    trigger: str
    actions: list[Callable]
    validation: Callable

class SkillCreator:
    """技能创建器"""

    def create_from_template(self, template: SkillTemplate) -> Skill:
        """从模板创建技能"""

    def validate_skill(self, skill: Skill) -> bool:
        """验证技能有效性"""
```

### 3.3 执行计划

| 步骤 | 任务 | 预计行数 |
|------|------|----------|
| 1 | 创建 creator.py 定义模板 | ~80 |
| 2 | 实现 SkillCreator 类 | ~120 |
| 3 | 添加内置模板 (Code, Review, Test) | ~150 |
| 4 | 集成到 skills 模块 | ~50 |
| 5 | CLI 命令支持 | ~30 |

---

## 4. OpenTelemetry 集成

### 4.1 现状分析

现有 tracing 模块：
- `src/datacenter/tracing.py`
- `src/tools/tracing.py`

### 4.2 集成方案

```python
# 新增 src/telemetry/otel.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

class OpenTelemetryConfig:
    """OpenTelemetry 配置"""

    def __init__(self, service_name: str):
        self.provider = TracerProvider()
        trace.set_tracer_provider(self.provider)
```

### 4.3 执行计划

| 步骤 | 任务 | 预计行数 |
|------|------|----------|
| 1 | 创建 telemetry/otel.py | ~100 |
| 2 | 实现自动 instrumentation | ~80 |
| 3 | 集成到 LLM 客户端 | ~50 |
| 4 | 集成到 Agent 执行 | ~50 |
| 5 | 配置和导出器 | ~60 |

---

## 执行顺序建议

1. **LangGraph 集成** - 优先级最高（战略目标）
2. **插件式 EvalService** - 评估能力核心
3. **Skill Creator** - 技能系统增强
4. **OpenTelemetry** - 可观测性基础

---

## 风险与依赖

| 任务 | 风险 | 依赖 |
|------|------|------|
| LangGraph 集成 | API 变更 | Python 3.10+ |
| 插件式 EvalService | 性能开销 | 无 |
| Skill Creator | 复杂度 | 现有 skills 模块 |
| OpenTelemetry | 配置复杂 | opentelemetry SDK |

---

## 建议执行周期

每个任务 1-2 周：
- Week 1-2: LangGraph 集成
- Week 3-4: 插件式 EvalService
- Week 5-6: Skill Creator
- Week 7-8: OpenTelemetry

总周期: ~2 个月

---

## 实现结果 (2026-03-08)

### 1. LangGraph 集成 ✅

**文件**: `src/flow/langgraph_adapter.py` (270行)

实现内容:
- `LangGraphAdapter` - 主适配器类
- `StateGraphConverter` - 将现有 Flow 节点转换为 LangGraph
- `ReActAgentFactory` - ReAct Agent 工厂
- `FlowNode`, `FlowEdge` - 数据模型
- `create_simple_agent()` - 便捷函数
- 优雅降级：未安装 langgraph 时可用

### 2. 插件式 EvalService ✅

**文件**: `src/evaluation/plugins.py` (395行)

实现内容:
- `EvalPlugin` - 抽象基类
- `EvalResult`, `EvalContext` - 数据模型
- `PluginRegistry` - 插件注册中心
- 内置插件:
  - `CodeQualityPlugin` - 代码质量评估
  - `SecurityPlugin` - 安全评估
  - `PerformancePlugin` - 性能评估
  - `CorrectnessPlugin` - 正确性评估
- `evaluate()` - 便捷函数
- 导出到 `src/evaluation/__init__.py`

### 3. Skill Creator 架构 ✅

**文件**: `src/skills/creator.py` (310行)

实现内容:
- `SkillTemplate` - 技能模板定义
- `SkillCreator` - 技能创建器
- `TemplateRegistry` - 模板注册中心
- 内置模板:
  - `code` - 代码生成模板
  - `review` - 代码审查模板
  - `test` - 测试生成模板
- `create_skill()`, `list_templates()` - 便捷函数
- 导出到 `src/skills/__init__.py`

### 4. OpenTelemetry 集成 ✅

**文件**: `src/telemetry/otel.py` (280行)

实现内容:
- `TelemetryConfig` - 遥测配置
- `OpenTelemetryConfig` - 配置管理器
- `LLMTelemetry` - LLM 调用追踪
- `AgentTelemetry` - Agent 执行追踪
- `FlowTelemetry` - 工作流追踪
- `trace_span()` - 上下文管理器
- `traced()` - 装饰器
- 优雅降级：未安装 opentelemetry 时可用

### 测试结果

```
505 passed, 8 skipped, 7 warnings
```

### 依赖安装 (可选)

```bash
# LangGraph 支持
pip install langgraph

# OpenTelemetry 支持
pip install opentelemetry-api opentelemetry-sdk
```
