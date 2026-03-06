---
name: gitnexus
description: "代码知识图谱分析与 AI 增强导航。使用场景：理解代码架构、追踪依赖关系、分析修改影响范围、代码重构规划、调试追踪。前提：需先安装 gitnexus (npm install -g gitnexus) 并在代码库运行 npx gitnexus analyze 建立索引。"
trigger_patterns:
  - "代码结构"
  - "架构分析"
  - "依赖关系"
  - "影响分析"
  - "blast radius"
  - "what depends"
  - "代码追踪"
  - "调用链"
  - "explore"
  - "understand code"
  - "impact analysis"
  - "refactor"
tags:
  - code-analysis
  - knowledge-graph
  - dependencies
  - refactoring
  - debugging
requires:
  bins:
    - node
    - npm
    - npx
---

# GitNexus - 代码知识图谱分析

## 首要步骤：环境检查 + 索引健康检查 ⚠️

**在执行任何代码分析之前，必须首先完成此检查！**

### 步骤 1: 安装检查 (仅首次或缺失时)

```
# 检查 gitnexus 是否已安装
which gitnexus || npx -y gitnexus@latest --version

# 如果不存在，执行安装
npm install -g gitnexus

# 验证安装
gitnexus --version
```

### 步骤 2: 索引健康检查

```
# 步骤 A: 检查当前 git 状态
git status --porcelain

# 步骤 B: 检查是否有未提交的更改
# 如果有修改 → 需要重新索引

# 步骤 C: 运行 gitnexus analyze (任选一种)
# 方式 A: 标准索引
npx gitnexus analyze
# 方式 B: 跳过 embedding (更快)
npx gitnexus analyze --skip-embeddings

# 步骤 D: 验证索引状态
npx gitnexus status
```

### 自动检测逻辑

```
# 伪代码: 每次 Skill 触发时执行

IF gitnexus 未安装:
    → npm install -g gitnexus
    → 继续下一步

ELSE IF 索引不存在:
    → 执行 npx gitnexus analyze
    → 继续下一步

ELSE IF git 有新 commit (commitsBehind > 0):
    → 执行 npx gitnexus analyze --skip-embeddings
    → 继续下一步

ELSE:
    → 直接继续下一步
```

### 验证索引状态

每次工具调用后，检查返回内容是否包含 `staleness` 警告：

```
IF 工具返回包含 "Index is stale" 或 "stale":
    → 停止当前操作
    → 执行 npx gitnexus analyze
    → 重新执行原操作
```

## 先决条件检查

### 安装 (仅首次)

```bash
# 1. 安装 gitnexus CLI
npm install -g gitnexus

# 2. (可选) 配置 MCP 自动启动
npx gitnexus setup
```

### ⚠️ 每次使用前的强制检查清单

```
- [ ] 运行 git status --porcelain 检查是否有未提交更改
- [ ] 运行 npx gitnexus status 检查索引状态
- [ ] 如果有更改或索引不存在: npx gitnexus analyze
- [ ] 如果索引 stale: npx gitnexus analyze --skip-embeddings
```

> **关键原则**: 永远不要在未确认索引是最新的情况下进行代码分析！

## 核心工作流

### 0. 【必须】健康检查 (每次)

```
1. git status --porcelain                  → 检查是否有未提交更改
2. npx gitnexus status                    → 检查索引状态
3. 如需要 → npx gitnexus analyze          → 更新索引
4. READ gitnexus://repo/{name}/context    → 确认索引正常
```

### 1. 代码探索 (理解代码)

```
1. READ gitnexus://repos                    → 发现已索引的仓库
2. READ gitnexus://repo/{name}/context       → 获取代码库概览和统计
3. gitnexus_query({query: "<概念>"})        → 查找相关的执行流程
4. gitnexus_context({name: "<符号>"})       → 深入查看特定符号
5. READ gitnexus://repo/{name}/process/{name} → 追踪完整执行流
```

### 2. 影响分析 (修改前)

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → 找出依赖者
2. READ gitnexus://repo/{name}/processes                   → 检查受影响的执行流程
3. gitnexus_detect_changes()                             → 基于 git diff 的影响分析
4. 评估风险并报告用户
```

### 3. 重构规划

```
1. gitnexus_impact({target: "目标符号", direction: "upstream"})
2. gitnexus_rename({symbol_name: "旧名称", new_name: "新名称", dry_run: true})
3. 审查变更，确认安全后执行
```

### 4. 调试追踪

```
1. gitnexus_query({query: "<错误相关概念>"})
2. gitnexus_context({name: "<可疑函数>"})  → 查看调用者/被调用者
3. READ process 获取完整调用链
```

## MCP 工具参考

| 工具 | 用途 | 示例 |
|------|------|------|
| `list_repos` | 列出所有已索引仓库 | `list_repos()` |
| `query` | 混合搜索 (BM25 + 语义) | `query({query: "auth middleware"})` |
| `context` | 360度符号视图 | `context({name: "validateUser"})` |
| `impact` | 影响范围分析 | `impact({target: "UserService", direction: "upstream"})` |
| `detect_changes` | Git diff 影响分析 | `detect_changes({scope: "staged"})` |
| `rename` | 多文件重命名 | `rename({symbol_name: "x", new_name: "y"})` |
| `cypher` | 原生图查询 | `cypher({query: "MATCH..."})` |

## MCP Resources

| Resource | 用途 |
|----------|------|
| `gitnexus://repos` | 列出所有已索引仓库 |
| `gitnexus://repo/{name}/context` | 代码库统计、索引状态 |
| `gitnexus://repo/{name}/clusters` | 所有功能集群及聚合分数 |
| `gitnexus://repo/{name}/processes` | 所有执行流程 |
| `gitnexus://repo/{name}/process/{name}` | 完整执行追踪 |
| `gitnexus://repo/{name}/schema` | 图查询 schema |

## 影响分析输出解读

| 深度 | 风险级别 | 含义 |
|------|----------|------|
| d=1 | **WILL BREAK** | 直接调用者/导入者 |
| d=2 | LIKELY AFFECTED | 间接依赖 |
| d=3 | MAY NEED TESTING | 传递效应 |

### 风险评估

| 影响范围 | 风险等级 |
|----------|----------|
| <5 符号，少量流程 | LOW |
| 5-15 符号，2-5 流程 | MEDIUM |
| >15 符号，多流程 | HIGH |
| 关键路径 (auth, payments) | CRITICAL |

## 示例对话

### "认证流程是怎么工作的?"

```
1. READ gitnexus://repo/my-app/context
   → 918 symbols, 45 processes

2. gitnexus_query({query: "authentication"})
   → LoginFlow, TokenRefresh, OAuthFlow

3. gitnexus_context({name: "validateUser"})
   → Incoming: loginHandler, apiMiddleware
   → Outgoing: checkToken, getUserById

4. Read src/auth/validate.ts 实现细节
```

### "修改 validateUser 函数会影响到什么?"

```
1. gitnexus_impact({target: "validateUser", direction: "upstream"})
   → d=1: loginHandler, apiMiddleware (WILL BREAK)
   → d=2: authRouter, sessionManager (LIKELY AFFECTED)

2. READ gitnexus://repo/my-app/processes
   → LoginFlow 和 TokenRefresh 涉及 validateUser

3. 风险: 2 个直接调用者，2 个流程 = MEDIUM
```

### "重命名这个函数"

```
gitnexus_rename({
  symbol_name: "validateUser",
  new_name: "verifyUser",
  dry_run: true
})

→ status: success
→ files_affected: 5
→ graph_edits: 6 (高置信度)
→ text_search_edits: 2 (需审查)
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| "Index is stale" | 运行 `npx gitnexus analyze` 重新索引 |
| 工具返回空 | 检查是否在正确的已索引仓库目录 |
| MCP 连接失败 | 运行 `npx gitnexus setup` 重新配置 |
| 多仓库冲突 | 使用 `repo` 参数指定目标仓库 |

## 运行时自愈机制

### 场景：工具返回 stale 警告

当 MCP 工具返回 `staleness` 警告时：

```
1. 立即停止当前操作
2. 执行: npx gitnexus analyze --skip-embeddings
3. 等待索引完成
4. 重新执行原工具调用
5. 确认结果正常后继续
```

### 场景：工具返回空结果

```
1. 检查: gitnexus://repo/{name}/context
2. 如果 symbols = 0 → 索引未完成 → 重新 analyze
3. 如果 symbols > 0 但结果空 → 尝试其他查询方式
```

## 配置 MCP (如需手动)

```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "npx",
      "args": ["-y", "gitnexus@latest", "mcp"]
    }
  }
}
```
