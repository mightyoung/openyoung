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

## 先决条件检查

在首次使用前，必须完成以下设置：

```bash
# 1. 安装 gitnexus CLI
npm install -g gitnexus

# 2. 在目标代码库建立索引
cd your-project
npx gitnexus analyze

# 3. (可选) 配置 MCP 自动启动
npx gitnexus setup
```

> 如果看到 "Index is stale" 警告，重新运行 `npx gitnexus analyze`

## 核心工作流

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
