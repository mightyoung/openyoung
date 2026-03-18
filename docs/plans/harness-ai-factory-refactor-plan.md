# Harness驱动的AI软件工厂 - 架构改进计划

> 以Harness为核心，建立真正的AI软件工厂架构

## 愿景声明

**核心目标**: 将Harness从"评估工具"提升为"AI软件工厂的核心调度引擎"

```
用户需求 → Harness编排 → 多Agent协作 → 标准化输出
                    ↑
              SemanticMemory (知识沉淀)
              WorkingMemory (执行上下文)
              Checkpoint (状态恢复)
```

---

## P0: 核心架构重构

### P0.1: 拆分 young_agent.py (1665行 → 5+模块)

**问题**: God Object反模式，7个包的所有逻辑混在一个文件

**目标**: 以Harness为中心重构

```
src/agents/
├── young_agent.py          # 主入口，轻量协调者 (→300行)
├── harness/
│   ├── __init__.py
│   ├── harness_runner.py   # Harness执行引擎
│   ├── task_compiler.py    # Task → Harness Graph
│   └── resource_manager.py # 资源分配
├── memory/
│   ├── working_memory.py   # 短期上下文
│   ├── semantic_memory.py  # 知识检索
│   └── checkpoint.py       # 状态持久化
├── execution/
│   ├── agent_executor.py   # Agent生命周期
│   ├── tool_executor.py   # 工具调用
│   └── event_bus.py       # 事件驱动
└── evaluation/
    ├── harness_eval.py    # 评估接口
    └── metrics.py         # 指标收集
```

**关键原则**:
- YoungAgent只做: 初始化 → 委托Harness → 监控结果
- 所有业务逻辑下沉到子模块
- Harness是唯一调度者

---

### P0.2: 拆分 cli/main.py (2167行 → 5+模块)

**问题**: CLI混入了所有业务逻辑

**目标**: 清晰的命令行入口与业务解耦

```
src/cli/
├── main.py                 # 入口 (→200行)
├── commands/
│   ├── run.py             # openyoung run
│   ├── chat.py            # openyoung chat
│   ├── eval.py            # openyoung eval
│   └── config.py          # openyoung config
└── formatters/            # 输出格式化
```

---

### P0.3: 删除废弃代码

**待删除**:
- [ ] `src/agents/heartbeat/event_bus.py` (已标记DEPRECATED)
- [ ] `src/cli/test/__init__.py` (已标记DEPRECATED)
- [ ] `src/cli/config.py` (已标记DEPRECATED)
- [ ] `src/distillation/` (空目录)
- [ ] `src/evaluation/` (旧评估系统)

**验证**: 删除前确认无import引用

---

## P1: Harness为中心的系统对接

### P1.1: 让Harness真正驱动Agent执行

**当前问题**: young_agent.py的main_loop是`while True + match case`，Harness只在eval时用

**改进**:

```python
# young_agent.py 主循环应该委托给 Harness
async def run(self, task: Task) -> Result:
    harness_graph = self.task_compiler.compile(task)
    async for partial_result in harness_graph.run():
        yield partial_result  # 流式输出
        await self.event_bus.emit(TaskProgress(partial_result))
```

### P1.2: 统一评估系统

**当前问题**: `hub/evaluate/` (新) + `evaluation/` (旧) 并存

**决策**: 保留 `hub/evaluate/harness.py` 作为唯一评估入口
- 将旧evaluation代码逐步迁移到harness接口
- 删除 `src/evaluation/` 目录

### P1.3: 合并错误处理系统

**当前问题**: `error_handler.py` + `exception_handler.py` 两个系统

**决策**: 保留 `exception_handler.py` (更完整)
- 迁移 error_handler 的特有功能
- 删除 error_handler.py

---

## P2: 基础设施完善

### P2.1: 修复硬编码路径

```python
# young_agent.py line 89
# 当前: "/Users/muyi/Downloads/dev/openyoung/output/"
# 改为: self.config.get("output_dir", "./output/")
```

### P2.2: SemanticMemory作为Harness的知识背书

- Harness执行时查询SemanticMemory获取相关经验
- 执行结果沉淀到SemanticMemory
- 实现"学习"闭环

### P2.3: Checkpoint支持Harness中断恢复

- Harness图执行可中断
- Checkpoint保存执行状态
- 恢复时从断点继续

---

## P3: 质量提升

### P3.1: 为Harness核心编写测试

```python
tests/
├── harness/
│   ├── test_task_compiler.py
│   ├── test_harness_runner.py
│   └── test_resource_manager.py
└── agents/
    └── test_young_agent_integration.py
```

### P3.2: CLI模块测试

### P3.3: 性能基准测试

---

## 执行顺序

```
阶段1: 准备 (1天)
├── 备份当前代码
├── 建立git branch: feature/harness-central-refactor
└── 编写P0迁移测试

阶段2: P0核心重构 (3-5天)
├── 拆分young_agent.py
├── 拆分cli/main.py
└── 删除废弃代码

阶段3: P1 Harness中心化 (2-3天)
├── Harness驱动Agent执行
├── 统一评估系统
└── 合并错误处理

阶段4: P2基础设施 (1-2天)
├── 修复硬编码
├── Memory-Harness集成
└── Checkpoint支持

阶段5: P3质量 (持续)
├── 单元测试
└── 集成测试
```

---

## 成功指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| young_agent.py行数 | 1665 | ≤400 |
| cli/main.py行数 | 2167 | ≤500 |
| Harness覆盖率 | 30% | 95% |
| 单元测试覆盖率 | ~20% | 80% |
| 硬编码路径数 | 1 | 0 |

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 重构破坏现有功能 | 高 | 每步有测试验证 |
| 多分支并行开发冲突 | 中 | 使用feature flag |
| 性能回退 | 中 | 基准测试对比 |

---

## 下一步行动

1. 确认上述计划是否符合战略方向
2. 确定优先级是否正确
3. 开始阶段1准备工作
