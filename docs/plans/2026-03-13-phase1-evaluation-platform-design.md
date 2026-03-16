# OpenYoung Phase 1 评估平台实施计划

> 版本: 1.0
> 状态: 设计完成，待批准
> 基于: 用户批准方案 + 行业最佳实践

---

## 一、行业最佳实践研究

### 1.1 LangSmith 架构分析

| 特性 | LangSmith 实现 | 本项目参考 |
|------|---------------|------------|
| 数据模型 | traces + datasets + evaluations | 复用现有 TraceRecord + 新增 EvaluationRecord |
| API层 | REST + GraphQL | FastAPI (REST) + SSE (实时) |
| 可视化 | React Dashboard | Streamlit (快速迭代) |
| 查询 | 灵活过滤 + 分页 | SQLite 索引优化 |

**关键洞察**: LangSmith 的核心是 **数据模型统一** + **API灵活性**

### 1.2 Streamlit 数据应用最佳实践

| 场景 | 推荐模式 | 本项目应用 |
|------|----------|------------|
| 指标展示 | st.metric + st.columns | 4列指标卡片 |
| 趋势图 | st.line_chart / Altair | 评估分数趋势 |
| 数据表格 | st.dataframe + 分页 | 执行记录查询 |
| 实时更新 | st.rerun / auto-refresh | SSE 推送 |

### 1.3 FastAPI + SSE 实时推送模式

```python
# 行业标准模式
from fastapi import APIRouter, SSE
import asyncio

router = APIRouter()

@router.get("/stream/{task_id}")
async def stream_task(task_id: str):
    """Server-Sent Events 实时推送"""
    async def event_generator():
        while True:
            # 获取最新状态
            status = await get_task_status(task_id)
            yield {"event": "status", "data": status}
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())
```

---

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1 评估平台                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Streamlit UI 层                         │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐        │   │
│  │  │Dashboard   │ │Query       │ │Export      │        │   │
│  │  │(指标展示)  │ │(执行查询)  │ │(数据导出)  │        │   │
│  │  └────────────┘ └────────────┘ └────────────┘        │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │          Live Monitor (实时监控)                 │ │   │
│  │  └──────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   FastAPI 后端层                         │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐        │   │
│  │  │/executions │ │/exports    │ │/stream     │        │   │
│  │  │  (查询)    │ │  (导出)    │ │  (SSE)    │        │   │
│  │  └────────────┘ └────────────┘ └────────────┘        │   │
│  │  ┌──────────────────────────────────────────────────┐ │   │
│  │  │      中间件: 认证 / 限流 / 日志                  │ │   │
│  │  └──────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   DataCenter 数据层                       │   │
│  │  ┌────────────────┐ ┌────────────────┐                  │   │
│  │  │ traces.db     │ │ evaluations.db │                  │   │
│  │  │ (执行记录)     │ │ (评估记录)     │                  │   │
│  │  └────────────────┘ └────────────────┘                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型设计

#### ExecutionRecord (执行记录)

```python
@dataclass
class ExecutionRecord:
    """执行记录 - 扩展现有 TraceRecord"""

    # 基础字段 (复用)
    run_id: str
    session_id: str
    agent_name: str
    task_description: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: int
    model: str

    # Token 统计
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

    # 状态
    status: ExecutionStatus  # running, success, failed, timeout
    error: Optional[str]

    # 评估关联
    evaluation_id: Optional[str]
    score: Optional[float]

    # 元数据
    metadata: dict
    tags: list[str]
```

#### EvaluationRecord (评估记录)

```python
@dataclass
class EvaluationRecord:
    """评估记录"""

    id: str
    execution_id: str

    # 评估维度
    dimensions: list[EvaluationDimension]
    overall_score: float
    passed: bool

    # 评估详情
    evaluator_type: str  # code, task, llm_judge, safety
    feedback: str

    # 时间
    evaluated_at: datetime
    iteration: int

    # 元数据
    metadata: dict
```

#### EvaluationDimension (评估维度)

```python
@dataclass
class EvaluationDimension:
    """评估维度"""

    name: str  # correctness, safety, efficiency, robustness
    score: float
    threshold: float
    passed: bool
    reasoning: str
    evidence: list[str]
```

### 2.3 API 设计

#### 执行记录查询 API

```
GET /api/v1/executions

Query Parameters:
- session_id: str (可选)
- agent_name: str (可选)
- status: str (可选: running/success/failed/timeout)
- start_date: datetime (可选)
- end_date: datetime (可选)
- limit: int (默认 50, 最大 100)
- offset: int (默认 0)

Response:
{
  "items": [ExecutionRecord],
  "total": int,
  "limit": int,
  "offset": int
}
```

#### 数据导出 API

```
GET /api/v1/exports

Query Parameters:
- execution_ids: list[str] (可选)
- start_date: datetime (可选)
- end_date: datetime (可选)
- format: str (json/csv/parquet)

Response: File download
```

#### 实时流 API

```
GET /api/v1/stream/{task_id}

Event Types:
- status: 执行状态更新
- evaluation: 评估结果
- error: 错误信息
```

---

## 三、实施计划

### 3.1 第一阶段：数据基础设施 (第1-3周)

| 周 | 任务 | 交付物 | 依赖 |
|----|------|--------|------|
| W1 | 扩展DataCenter数据模型 | ExecutionRecord, EvaluationRecord, EvaluationDimension 类 | 现有 TraceRecord |
| W1 | 创建评估数据库表 | evaluations.sqlite | W1任务 |
| W2 | FastAPI项目初始化 | 项目结构 + 基础路由 | W1完成 |
| W2 | 中间件基础 | 认证 / 日志中间件 | W2任务 |
| W3 | 执行记录查询API | `/api/v1/executions` 端点 | W2完成 |

**验收标准**:
- [ ] ExecutionRecord 模型可用
- [ ] API 能返回执行记录列表
- [ ] 支持分页和过滤

### 3.2 第二阶段：评估仪表板 (第4-6周)

| 周 | 任务 | 交付物 | 依赖 |
|----|------|--------|------|
| W4 | Streamlit项目初始化 | 项目结构 + 基础路由 | W3完成 |
| W4 | Dashboard组件-指标卡片 | 4列指标卡片 | W4任务 |
| W5 | Dashboard组件-趋势图 | 评估分数趋势图 | W4完成 |
| W5 | Dashboard组件-对比表 | 并排对比视图 | W5任务 |
| W6 | 查询与过滤功能 | 高级搜索 + 筛选器 | W5完成 |

**验收标准**:
- [ ] Streamlit 仪表板可运行
- [ ] 指标卡片显示正确
- [ ] 趋势图可交互

### 3.3 第三阶段：数据导出与实时流 (第7-8周)

| 周 | 任务 | 交付物 | 依赖 |
|----|------|--------|------|
| W7 | 数据导出API | `/api/v1/exports` 端点 | W3完成 |
| W7 | 导出UI组件 | 导出按钮 + 格式选择 | W7任务 |
| W8 | SSE实时流 | `/api/v1/stream/{task_id}` | W3完成 |
| W8 | 实时监控面板 | Live Monitor组件 | W8任务 |

**验收标准**:
- [ ] 支持 JSON/CSV 导出
- [ ] 实时流延迟 < 1秒
- [ ] 完整集成测试通过

---

## 四、技术决策

### 4.1 架构选择

| 决策点 | 选择 | 理由 |
|--------|------|------|
| **后端框架** | FastAPI | 高性能、自动API文档、内置SSE |
| **前端框架** | Streamlit | 快速迭代、无需前端技能 |
| **实时推送** | Server-Sent Events | 简单可靠、比WebSocket轻量 |
| **数据格式** | JSON + CSV | 通用性强、便于分析 |

### 4.2 性能优化

| 优化点 | 方案 | 预期收益 |
|--------|------|----------|
| **查询性能** | SQLite 索引 | 查询提升 10x |
| **分页** | cursor-based pagination | 大数据量稳定 |
| **实时流** | 异步生成器 | 低内存占用 |

### 4.3 安全性

| 安全措施 | 实现 |
|----------|------|
| **认证** | API Key 认证 |
| **限流** | 100 req/min |
| **审计** | 请求日志 |

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Streamlit定制化限制 | 某些复杂交互难实现 | 使用自定义组件 |
| 数据量增长 | 查询性能下降 | 添加索引、分页 |
| 实时连接数 | 并发限制 | 连接池管理 |
| SSE断连 | 实时更新丢失 | 客户端重连机制 |

---

## 六、里程碑

| 周 | 里程碑 | 交付物 |
|----|--------|--------|
| W3 | **Alpha** | 数据模型 + 查询API可用 |
| W6 | **Beta** | 完整仪表板 |
| W8 | **GA** | 完整功能 + 测试通过 |

---

## 七、总结

本计划基于以下最佳实践：

1. **LangSmith 架构**: 统一数据模型 + 灵活API
2. **Streamlit 模式**: 快速迭代 + 数据驱动
3. **FastAPI + SSE**: 高性能 + 实时性

**核心理念**: 渐进式交付，小步迭代

---

*文档版本: 1.0*
*设计日期: 2026-03-13*
*方法论: Kent Beck TDD + John Ousterhout 增量设计*
