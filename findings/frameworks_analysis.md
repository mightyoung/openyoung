# Agent框架 Plan-Execution 能力对比分析

## 研究背景

分析主流Agent编程框架在规划(Plan)与执行(Execution)方面的能力差异，特别关注：
1. 如何处理"规划与执行不一致"
2. 验证或对齐机制
3. 用户如何检测执行偏离

---

## 框架对比表

| 框架 | Plan能力 | Execution | 验证机制 | 用户记忆 |
|------|----------|-----------|----------|----------|
| **Claude Code** | Task系统 + 子Agent编排 | 自主执行、测试、修复 | 内置验证Agent模式 | Task上下文 + 持久化memory |
| **OpenAI Codex** | 基于GitHub Issues/PR自动分解 | 云端容器自主执行 | PR工作流集成 + 安全审计 | GitHub上下文 |
| **LangGraph** | 显式图结构定义DAG | 节点执行 + 条件边跳转 | Checkpoint + 状态回滚 | State Schema定义 |
| **AutoGPT** | 目标分解为TODO列表 | 自主循环执行 | 人工监督(防无限循环) | 有限上下文窗口 |

---

## 详细分析

### 1. Claude Code

**Plan能力:**
- Task系统支持任务分解和子Agent编排
- 支持创建专门的builder/validator Agent配对
- 可通过Agent tool调用多个专业Agent协同工作

**Execution:**
- 自主执行：写代码→运行→测试→修复
- 内循环验证能力

**验证机制:**
- 内置"验证Agent"模式：创建专门验证工作的子Agent
- 可配置Plan Mode进行结构化规划

**用户记忆:**
- Task上下文信息
- MCP server提供持久化memory

---

### 2. OpenAI Codex / GitHub Copilot

**Plan能力:**
- 基于GitHub Issues自动理解任务
- 在PR工作流中执行

**Execution:**
- 云端容器中完全自主执行
- 有独立终端环境

**验证机制:**
- 与GitHub Actions集成
- 安全和透明度优先设计
- PR工作流提供审查点

**用户记忆:**
- 完全依赖GitHub仓库上下文
- 无独立memory系统

---

### 3. LangGraph

**Plan能力:**
- 显式图结构定义执行流程
- 支持条件分支和循环控制

**Execution:**
- 确定性执行模型
- 支持checkpoint和状态恢复
- 并行执行多个节点

**验证机制:**
- State Schema强制类型检查
- Checkpoint持久化支持审计回溯
- 可在任意节点插入验证逻辑

**用户记忆:**
- State可完全自定义
- 支持多Agent共享状态

---

### 4. AutoGPT

**Plan能力:**
- 将目标分解为具体TODO步骤
- 任务优先级排序

**Execution:**
- 自主循环执行直到达成目标
- 支持工具调用和API集成

**验证机制:**
- 需要人工监督防止无限循环
- 错误管理和成本控制依赖人类

**用户记忆:**
- 有限的上下文窗口
- 无持久化memory设计

---

## 关键问题回答

### Q1: 如何处理"规划与执行不一致"？

| 框架 | 处理方式 |
|------|----------|
| Claude Code | 验证Agent模式 + Plan Mode |
| Codex | PR工作流提供审查点 |
| LangGraph | 条件边动态跳转 + Replan能力 |
| AutoGPT | 依赖人工干预 |

### Q2: 是否有验证或对齐机制？

- **LangGraph**: 最完善 - Checkpoint + State Schema + 条件边
- **Claude Code**: 验证Agent + 子Agent配对
- **Codex**: GitHub PR工作流
- **AutoGPT**: 人工监督为主

### Q3: 用户如何检测执行偏离？

| 框架 | 检测方式 |
|------|----------|
| Claude Code | Task状态跟踪 + Agent报告 |
| Codex | PR变更审查 |
| LangGraph | Checkpoint审计 + State检查点 |
| AutoGPT | 人工监控 + 成本/循环限制 |

---

## 学术研究进展

**Plan-Execute-Verify-Replan模式** (VMAO - Verified Multi-Agent Orchestration):
- 将复杂查询分解为DAG
- 并行执行领域特定Agent
- 通过LLM验证结果完整性
- 自适应重规划填补空白

**VERIMAP** (Verification-Aware Planning):
- 将验证内建于规划阶段
- 提前预防错误而非事后检查

**Agent GPA框架** (Goal-Plan-Action):
- 评估Agent在目标、计划、行动三层面的表现
- 开源(TruLens库)
- 暴露内部错误如幻觉、工具使用错误、计划遗漏

---

## 结论

| 框架 | 成熟度 | 适用场景 |
|------|--------|----------|
| **LangGraph** | 高 | 需要确定性控制和审计的复杂工作流 |
| **Claude Code** | 高 | IDE环境 + 代码开发任务 |
| **Codex** | 高 | 全自动代码开发(云端) |
| **AutoGPT** | 中 | 实验性自动化任务 |

**推荐**: 对于需要强验证和执行追踪的场景，LangGraph的显式图结构 + Checkpoint机制是目前最完善的解决方案。

---

*生成时间: 2026-03-20*
