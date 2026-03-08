# OpenYoung 战略规划 (完整版)

> 版本: 2.0
> 更新日期: 2026-03-07
> 状态: 已确认

---

## 1. 战略定位

### 愿景
**AI Docker** - 智能 Agent 容器化平台

### 核心价值

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenYoung 核心理念                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🎯 愿景: AI Docker - 智能 Agent 容器化平台                       │
│                                                                  │
│  📦 核心价值:                                                    │
│     ├── Agent 容器化: 标准化打包、隔离运行                          │
│     ├── 智能编排: young-agent 守护执行                            │
│     ├── 数据资产: 本地采集 → 价值沉淀 → 市场交易                   │
│     └── 生态分发: 技能市场 + 增值服务                             │
│                                                                  │
│  🏆 差异化:                                                      │
│     └── 评估驱动 - 让每个 Agent 执行都有质量保障                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 行业对标

| 领域 | 对标产品 | 差异化策略 |
|------|----------|-------------|
| Agent 编排 | LangGraph | 集成而非自研 |
| 评估 | LangSmith | 开放生态 |
| 技能市场 | ClawHub | 本地化 + 数据资产 |
| 工具集成 | MCP | 行业标准 |

---

## 2. 技术决策 (已确认)

| 决策项 | 选择 | 理由 |
|--------|------|------|
| FlowGraph 引擎 | 集成 LangGraph | 行业标杆，社区成熟 |
| 评估服务架构 | 插件式服务 | 保持灵活性 |
| 数据市场模式 | 开源 + 订阅混合 | 社区优先，稳定收入 |
| 工具集成 | MCP | 行业标准，生态丰富 |
| 包管理 | 简化 + 复用主流 | 聚焦核心业务 |

---

## 3. 行业最佳实践研究

### 3.1 评估平台

| 特性 | LangSmith | PromptFoo | OpenYoung 现状 | 策略 |
|------|-----------|-----------|----------------|------|
| Tracing | ✅ Native | ✅ 基础 | ✅ 基础 | 升级到 OpenTelemetry |
| Eval Dataset | ✅ 完整 | ✅ 完整 | ⚠️ 21用例 | 扩充至 50+ |
| Comparison View | ✅ 仪表板 | ✅ CLI | ❌ 缺失 | 自研仪表板 |
| CI/CD 集成 | ✅ | ✅ 强 | ❌ 缺失 | 插件支持 |

### 3.2 Agent 编排

| 框架 | 特点 | 适用场景 | 决策 |
|------|------|----------|------|
| LangGraph | 图工作流 | 复杂流程 | ✅ 集成 |
| AutoGen | 对话驱动 | 协商场景 | ⚠️ 未来考虑 |
| CrewAI | 角色扮演 | 企业 | ❌ 不采用 |

### 3.3 MCP 生态

- **MCP 已成为 AI 工具集成的事实标准**
- 10,000+ MCP 服务器
- Linux Foundation 托管
- **策略**: 以 MCP 为核心工具集成层

---

## 4. ClawHub 集成策略

### 4.1 集成优先级

| 项目 | 定位 | 核心价值 | 优先级 |
|------|------|----------|--------|
| **Skill Creator** | 技能创建指南 | 最佳实践模式 | P0 |
| **MCPorter** | MCP 工具调用 | CLI 生成/类型化 | P1 |
| **Auto-Updater** | 自动更新 | 业务逻辑参考 | P2 |
| **API Gateway** | OAuth 认证 | 100+ API | ❌ 不采用 |

### 4.2 Skill Creator 设计模式

采用 ClawHub 的 Skill 架构：

```
agent-name/
├── SKILL.md              # 必需: 元数据 + 指令
├── scripts/              # 可选: 可执行代码
├── references/           # 可选: 参考文档
├── assets/              # 可选: 资源文件
└── evaluation/           # 评估规则
```

**渐进式加载**:
1. **元数据** (name + description) - 始终加载 (~100 tokens)
2. **SKILL.md body** - 触发时加载 (<5k tokens)
3. **Bundled resources** - 按需加载 (无限)

### 4.3 MCPorter 集成价值

```
当前: 手动加载 MCP 配置
改进: 使用 MCPorter 的自动发现

功能:
- 零配置发现 MCP 服务器
- 一键生成 CLI
- 类型化工具客户端
- OAuth + stdio 支持
- 临时连接
```

---

## 5. 执行路线图

### Phase 0: 基础巩固 (Q1-Q2 2026)

**目标**: 架构稳固 + 核心能力就绪

| 任务 | 子任务 | 优先级 | 状态 |
|------|--------|--------|------|
| **技术债务** | | | |
| | R2-1: package_manager 重构 | P1 | ✅ | hub 模块已建立 |
| | 数据类型统一 | P2 | ✅ |
| | 测试覆盖提升 | P1 | ✅ | 61测试用例 |
| **核心引擎** | | | |
| | 采用 Skill Creator 架构 | P0 | 🔲 | 见 phase0-remaining-tasks.md |
| | 集成 LangGraph 工作流 | P0 | 🔲 | 见 phase0-remaining-tasks.md |
| | 插件式 EvalService | P0 | 🔲 | 见 phase0-remaining-tasks.md |
| | OpenTelemetry 集成 | P1 | 🔲 | 见 phase0-remaining-tasks.md |
| **数据资产** | | | |
| | ExecutionRecord 集成 | P1 | ✅ | unified_store 已集成 |
| | 数据导出能力 | P1 | ✅ | DataExporter 已实现 |

**里程碑**:
- 清晰的模块架构 (< 500行/模块)
- LangGraph 驱动的动态工作流
- 插件式评估服务
- 标准化数据采集

### Phase 1: 差异化构建 (Q3-Q4 2026)

**目标**: 评估能力领先 + 数据资产成型

| 任务 | 优先级 |
|------|--------|
| EvalHub 独立评估服务 | P0 |
| 评估仪表板 | P1 |
| MCPorter MCP 增强 | P1 |
| 数据质量评分系统 | P1 |
| 数据服务 API | P1 |
| Auto-Updater 逻辑参考 | P2 |

**里程碑**:
- 独立的评估服务 API
- 可视化评估面板
- MCP 能力增强
- 数据资产基础框架

### Phase 2: 生态基础 (Q1-Q2 2027)

**目标**: 平台化能力 + 安全运行

| 任务 | 优先级 |
|------|--------|
| 技能市场基础 | P1 |
| 包自动化构建 | P1 |
| 质量审核机制 | P1 |
| Agent 沙箱 (WASM) | P1 |
| 安全策略引擎 | P2 |

**里程碑**:
- 完整的技能分发平台
- 可运行不受信任的 Agent

### Phase 3: 商业化 (Q3-Q4 2027)

**目标**: 收入模式 + 生态活跃

| 任务 | 优先级 |
|------|--------|
| 开源社区建设 | P0 |
| 订阅服务 | P1 |
| 数据市场 | P2 |
| 技能市场 | P2 |

---

## 6. 模块架构 (改进后)

```
src/
├── agent/                 # Agent 核心
│   ├── engine.py       # LangGraph 集成
│   ├── runtime.py      # 运行时
│   └── registry.py      # Agent 注册
│
├── hub/                 # Agent Hub (原包管理重构)
│   ├── discover.py      # 发现 (Skill Creator 模式)
│   ├── evaluate.py     # 评估 (EvalService)
│   ├── badge.py        # Badge
│   └── intent.py       # Intent 分析
│
├── mcp/                 # MCP 集成 (增强 MCPorter)
│   ├── loader.py       # MCP 加载
│   ├── servers.py      # 服务器管理
│   └── porter.py       # MCPorter 集成
│
├── flow/                # 工作流
│   ├── graph.py        # LangGraph 集成
│   └── skills.py       # FlowSkill
│
├── data/                # 数据层
│   ├── storage.py     # 存储抽象
│   ├── telemetry.py    # OpenTelemetry
│   └── marketplace.py # 数据市场基础
│
└── skills/             # 技能系统
    ├── loader.py       # 技能加载
    ├── creator.py      # Skill Creator 模式
    └── updater.py      # Auto-Updater 逻辑
```

---

## 7. 关键指标

| 阶段 | 指标 | 目标 |
|------|------|------|
| Phase 0 | 模块行数 | < 500 行/模块 |
| Phase 0 | 测试覆盖率 | > 70% |
| Phase 1 | 评估用例 | > 50 个 |
| Phase 1 | MCP 服务器 | > 20 个 |
| Phase 2 | 技能市场 | 上线 |
| Phase 2 | 沙箱隔离 | WASM 运行时 |
| Phase 3 | 订阅用户 | 1000+ |
| Phase 3 | 社区贡献 | 50+ PR |

---

## 8. 风险与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| Scope Creep | 🔴 高 | 严格控制 Phase 范围 |
| 资源不足 | 🔴 高 | 社区协作 |
| 技术选型 | 🟡 中 | 先小范围试点 |
| 竞争压力 | 🟡 中 | 差异化评估 |

---

## 9. 下一步行动

1. ✅ 确认技术决策
2. ✅ 确认 ClawHub 集成策略
3. 🔲 详细设计 Phase 0 任务
4. 🔲 开始执行 R2-1 package_manager 重构

---

## 附录: 参考资料

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [ClawHub Skills](https://github.com/anthropics/claude-code)
- [Skill Creator Best Practices](https://clawhub.ai/chindden/skill-creator)
- [MCPorter](https://github.com/steipete/mcporter)
- [LangSmith](https://www.langchain.com/langsmith)
