# OpenYoung 全链路测试计划

> 版本: 1.0
> 创建日期: 2026-03-08
> 状态: 实施中

---

## 1. 测试架构概述

### 1.1 金字塔型测试模型

```
         ┌─────────────────────────────────────┐
         │       E2E 全链路测试 (5-10%)        │  ← 真实复杂任务场景
         ├─────────────────────────────────────┤
         │     集成测试 (20-30%)              │  ← 跨模块协同
         ├─────────────────────────────────────┤
         │      单元测试 (60-70%)             │  ← 模块独立功能
         └─────────────────────────────────────┘
```

### 1.2 测试矩阵

| 维度 | 测试内容 | 占比 |
|------|----------|------|
| 功能测试 | 任务执行、评估、工具调用 | 50% |
| 性能测试 | 响应时间、并发、Token消耗 | 20% |
| 稳定性测试 | 错误恢复、边界条件、超时 | 20% |
| 安全测试 | 权限、隔离、沙箱 | 10% |

---

## 2. 单元测试层 (60-70%)

### 2.1 模块划分

| 模块 | 现有测试数 | 目标测试数 | 优先级 |
|------|-----------|-----------|--------|
| agents/ | 25+ | 40+ | P0 |
| flow/ | 15+ | 30+ | P0 |
| evaluation/ | 20+ | 35+ | P0 |
| datacenter/ | 30+ | 45+ | P1 |
| skills/ | 29 | 40+ | P1 |
| package_manager/ | 10+ | 25+ | P2 |
| llm/ | 15+ | 25+ | P1 |
| memory/ | 10+ | 20+ | P2 |

### 2.2 单元测试标准

```python
# 测试模板
class TestModuleName:
    """模块名测试套件"""

    def test_success_case(self):
        """正常流程测试"""
        pass

    def test_edge_case(self):
        """边界条件测试"""
        pass

    def test_error_handling(self):
        """错误处理测试"""
        pass

    def test_concurrent_access(self):
        """并发访问测试"""
        pass
```

### 2.3 Agent 模块测试重点

| 测试类 | 测试内容 | 测试数目标 |
|--------|----------|-----------|
| TestYoungAgent | 任务执行、评估集成 | 15 |
| TestDispatcher | 任务分发、路由 | 10 |
| TestPermission | 权限检查、规则评估 | 10 |
| TestEvaluationCoordinator | 评估协调、评分 | 10 |

### 2.4 Flow 模块测试重点

| 测试类 | 测试内容 | 测试数目标 |
|--------|----------|-----------|
| TestSequentialFlow | 顺序执行 | 8 |
| TestParallelFlow | 并行执行 | 8 |
| TestConditionalFlow | 条件分支 | 7 |
| TestLoopFlow | 循环执行 | 7 |

---

## 3. 集成测试层 (20-30%)

### 3.1 跨模块集成测试矩阵

| 集成场景 | 测试内容 | 优先级 |
|----------|----------|--------|
| Agent + Flow | 任务流转、执行控制 | P0 |
| Agent + Evaluation | 评估闭环、数据沉淀 | P0 |
| Agent + DataCenter | 执行记录、状态追踪 | P0 |
| Flow + Skills | 技能调用、结果处理 | P1 |
| Evaluation + DataCenter | 评估数据持久化 | P1 |
| Agent + Tools | 工具执行、结果返回 | P0 |

### 3.2 集成测试用例设计

```python
# 集成测试模板
class TestAgentFlowIntegration:
    """Agent + Flow 集成测试"""

    @pytest.mark.asyncio
    async def test_task_execution_flow(self):
        """测试任务执行全流程"""
        # 1. 创建任务
        # 2. 分发到 Flow
        # 3. 执行技能链
        # 4. 验证结果
        pass

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """测试错误恢复流程"""
        pass

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """测试并发任务执行"""
        pass
```

### 3.3 具体集成测试用例

#### T001: Agent → Flow 任务流转
- 输入: 带 Flow 技能的任务
- 验证: 任务正确分发到 Flow 执行
- 断言: Flow 输出正确传递给 Agent

#### T002: Agent → Evaluation 评估闭环
- 输入: 执行完成的任务
- 验证: 自动触发评估流程
- 断言: 评估结果正确记录

#### T003: Agent → DataCenter 数据沉淀
- 输入: 任意任务执行
- 验证: TraceRecord 正确保存
- 断言: 数据可查询、可追溯

#### T004: Flow → Skills 技能调用
- 输入: 需要技能的 Flow
- 验证: 技能正确加载和执行
- 断言: 技能结果正确返回

---

## 4. E2E 测试层 (5-10%)

### 4.1 真实复杂任务场景

#### 场景 1: 数据采集 → 分析 → 报告生成

```
用户输入: "爬取小红书热榜前10帖子，提取评论情感，分析趋势"
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 1: 技能检索                                      │
│  - 匹配: web_scraper, sentiment_analysis, reporter   │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 2: Flow 编排                                     │
│  - Sequential: 爬取 → 分析 → 报告                      │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 3: 工具执行                                      │
│  - HTTP 请求 → 数据解析 → LLM 分析 → 报告生成         │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 4: 评估执行                                      │
│  - TaskCompletionEval: 验证输出完整性                  │
│  - LLMJudge: 评估报告质量                             │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Step 5: 数据沉淀                                      │
│  - 保存 TraceRecord                                    │
│  - 保存评估结果                                        │
└─────────────────────────────────────────────────────────┘
```

**测试用例**:
- E2E-001: 完整流程执行成功
- E2E-002: 部分失败时的错误恢复
- E2E-003: 评估结果准确性验证

#### 场景 2: 代码审查 → 问题修复 → 测试验证

```
用户输入: "审查 src/agents/ 目录代码，修复发现的问题，运行测试"
```

**测试用例**:
- E2E-004: 代码审查完整性
- E2E-005: 问题修复正确性
- E2E-006: 测试通过验证

#### 场景 3: 多 Agent 协作

```
用户输入: "分析市场数据并生成投资建议"
                    │
                    ▼
        ┌───────────────────┐
        │  主 Agent: 协调   │
        └────────┬──────────┘
                 │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐ ┌───────┐ ┌───────┐
│Research│ │Analysis│ │Report │
│ Agent │ │ Agent │ │ Agent │
└───┬───┘ └───┬───┘ └───┬───┘
    │         │         │
    └─────────┼─────────┘
              ▼
        ┌───────────────────┐
        │  主 Agent: 汇总   │
        └───────────────────┘
```

**测试用例**:
- E2E-007: 多 Agent 任务分发
- E2E-008: Agent 间消息传递
- E2E-009: 结果聚合正确性

### 4.2 E2E 测试标准

```python
# E2E 测试模板
class TestE2EScenarios:
    """E2E 场景测试"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_data_pipeline_scenario(self):
        """场景1: 数据采集→分析→报告"""
        # 准备测试数据
        # 执行完整流程
        # 验证各阶段输出
        # 验证评估结果
        # 验证数据沉淀
        pass
```

---

## 5. 测试矩阵补充

### 5.1 性能测试

| 测试项 | 目标指标 | 测试方法 |
|--------|---------|----------|
| 任务响应时间 | P95 < 5s | 压力测试 |
| 并发任务数 | 10+ 并发 | 并发测试 |
| Token 消耗 | 符合预期 | 消耗统计 |
| 内存占用 | < 500MB | 资源监控 |

### 5.2 稳定性测试

| 测试项 | 测试方法 |
|--------|----------|
| 网络超时 | 模拟超时场景 |
| API 错误 | Mock 错误响应 |
| 资源耗尽 | 限制内存/CPU |
| 并发冲突 | 多线程并发写 |

### 5.3 安全测试

| 测试项 | 测试方法 |
|--------|----------|
| 权限绕过 | 尝试越权操作 |
| 注入攻击 | 恶意输入测试 |
| 数据泄露 | 敏感数据检查 |
| 沙箱隔离 | 跨边界访问测试 |

---

## 6. 测试数据管理

### 6.1 测试数据集

| 数据集 | 用途 | 数量 |
|--------|------|------|
| eval_dataset.json | 评估测试 | 21+ |
| mock_responses.json | Mock 数据 | 50+ |
| test_tasks.json | 任务输入 | 30+ |

### 6.2 测试夹具 (Fixtures)

```python
# conftest.py 示例
@pytest.fixture
async def mock_llm_response():
    """Mock LLM 响应"""
    return {"choices": [{"message": {"content": "test response"}}]}

@pytest.fixture
def sample_task():
    """示例任务"""
    return Task(
        id="test-001",
        description="测试任务",
        expected_result={"key": "value"}
    )
```

---

## 7. CI/CD 集成

### 7.1 GitHub Actions 配置

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run unit tests
        run: pytest tests/ -m "not e2e" --cov

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run integration tests
        run: pytest tests/ -m "integration"

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run E2E tests
        run: pytest tests/ -m "e2e"
```

### 7.2 测试标记

| 标记 | 用途 |
|------|------|
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.e2e` | E2E 测试 |
| `@pytest.mark.slow` | 慢速测试 |
| `@pytest.mark.performance` | 性能测试 |

---

## 8. 实施计划

### Phase 1: 单元测试完善 (Week 1-2)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T1.1 | 完善 Agent 模块单元测试 | P0 |
| T1.2 | 完善 Flow 模块单元测试 | P0 |
| T1.3 | 完善 Evaluation 模块单元测试 | P0 |
| T1.4 | 添加 DataCenter 模块单元测试 | P1 |

### Phase 2: 集成测试 (Week 3-4)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T2.1 | Agent + Flow 集成测试 | P0 |
| T2.2 | Agent + Evaluation 集成测试 | P0 |
| T2.3 | Agent + DataCenter 集成测试 | P0 |
| T2.4 | Flow + Skills 集成测试 | P1 |

### Phase 3: E2E 测试 (Week 5-6)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T3.1 | 实现场景1: 数据采集→分析→报告 | P0 |
| T3.2 | 实现场景2: 代码审查→修复→验证 | P0 |
| T3.3 | 实现场景3: 多 Agent 协作 | P1 |

### Phase 4: 性能与安全测试 (Week 7-8)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T4.1 | 性能基准测试 | P1 |
| T4.2 | 并发压力测试 | P1 |
| T4.3 | 安全渗透测试 | P2 |

### Phase 5: CI/CD 集成 (Week 9)

| 任务 | 描述 | 优先级 |
|------|------|--------|
| T5.1 | GitHub Actions 配置 | P0 |
| T5.2 | 测试报告集成 | P1 |
| T5.3 | 覆盖率监控 | P1 |

---

## 9. 验收标准

### 9.1 测试覆盖率目标

| 指标 | 当前 | 目标 |
|------|------|------|
| 单元测试覆盖率 | ~60% | 80% |
| 集成测试覆盖模块 | 60% | 100% |
| E2E 场景覆盖 | 0% | 100% |

### 9.2 测试执行标准

| 标准 | 目标 |
|------|------|
| 单元测试执行时间 | < 5 min |
| 集成测试执行时间 | < 10 min |
| E2E 测试执行时间 | < 30 min |
| 测试通过率 | > 95% |

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试数据不足 | 高 | 扩充测试数据集 |
| 外部依赖不稳定 | 中 | Mock 关键依赖 |
| 测试执行时间长 | 中 | 优化测试并行度 |
| 测试维护成本 | 中 | 建立测试规范 |

---

## 11. 关联文档

- [task_plan.md](../task_plan.md) - 任务追踪
- [progress.md](../progress.md) - 进度记录
- [2026-03-07-strategic-roadmap-v2.md](./2026-03-07-strategic-roadmap-v2.md) - 战略规划
- [evaluation-improvement-v2.md](./evaluation-improvement-v2.md) - 评估系统改进
