# OpenYoung CLI 完整测试计划

> 模拟：Kent Beck + Martin Fowler 的测试哲学
> 核心理念：快速反馈、测试隔离、持续集成

## 测试策略总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           测试金字塔                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│                        E2E 用户场景测试 (10%)                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│   │ 完整工作流测试  │  │ 端到端集成测试  │  │ 用户路径测试    │          │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘          │
│                                                                         │
│                     集成测试 (30%)                                        │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│   │ 命令组合测试    │  │ 模块交互测试    │  │ 数据流测试      │          │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘          │
│                                                                         │
│                     单元测试 (60%)                                        │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│   │ 命令解析测试    │  │ 参数验证测试    │  │ 错误处理测试    │          │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 测试执行命令

```bash
# 运行所有测试
pytest tests/e2e/test_cli_e2e.py -v

# 运行特定命令组测试
pytest tests/e2e/test_cli_e2e.py::TestCLICommands -v

# 运行带覆盖率
pytest tests/e2e/test_cli_e2e.py --cov=src.cli --cov-report=html
```

---

## 一、run 命令测试用例

### 1.1 基本功能测试

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| RUN-001 | 默认Agent执行 | `run default "hello"` | 返回非空响应 | P0 |
| RUN-002 | 指定Agent执行 | `run default "你好"` | 返回中文响应 | P0 |
| RUN-003 | 无任务执行 | `run default` (无参数) | 启动交互模式或报错 | P1 |
| RUN-004 | 多轮对话 | 连续执行多个任务 | 保持上下文 | P1 |

### 1.2 选项参数测试

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| RUN-010 | 交互模式 | `run default -i` | 进入交互模式 | P0 |
| RUN-011 | GitHub克隆 | `run default --github https://github.com/...` | 克隆并分析 | P1 |
| RUN-012 | 沙箱执行 | `run default "task" --sandbox` | 沙箱内执行 | P0 |
| RUN-013 | 网络访问 | `run default "task" --sandbox --allow-network` | 允许网络 | P1 |
| RUN-014 | 内存限制 | `run default "task" --max-memory 256` | 限制生效 | P1 |
| RUN-015 | 时间限制 | `run default "task" --max-time 60` | 超时终止 | P1 |

### 1.3 边界条件测试

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| RUN-020 | 超长任务描述 | 10万字符任务 | 正确处理/截断 | P2 |
| RUN-021 | 特殊字符任务 | `"<script>alert(1)</script>"` | 正确转义 | P2 |
| RUN-022 | 空任务 | `run default ""` | 给出提示 | P2 |
| RUN-023 | 空格任务 | `run default "   "` | 给出提示 | P2 |
| RUN-024 | 换行任务 | `run default "line1\nline2"` | 正确处理 | P2 |

### 1.4 错误场景测试

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| RUN-030 | 不存在的Agent | `run notexist "task"` | 友好错误提示 | P0 |
| RUN-031 | Agent配置错误 | Agent配置格式错误 | 详细错误信息 | P1 |
| RUN-032 | 模型不可用 | API key无效 | 明确错误 | P1 |
| RUN-033 | 网络超时 | 模拟网络超时 | 重试/超时提示 | P2 |

---

## 二、agent 命令测试用例

### 2.1 agent list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-LIST-001 | 列出所有Agent | `agent list` | 返回Agent列表 | P0 |
| AGENT-LIST-002 | 列出带统计 | `agent list --stats` | 显示使用统计 | P1 |
| AGENT-LIST-003 | 空列表 | 无Agent时 | 友好提示 | P2 |

### 2.2 agent info

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-INFO-001 | 查看默认Agent | `agent info default` | 显示完整配置 | P0 |
| AGENT-INFO-002 | 查看不存在Agent | `agent info notexist` | 友好错误 | P1 |
| AGENT-INFO-003 | JSON输出 | `agent info default --json` | 有效JSON | P1 |

### 2.3 agent search

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-SEARCH-001 | 关键词搜索 | `agent search "code"` | 返回相关Agent | P0 |
| AGENT-SEARCH-002 | 无结果搜索 | `agent search "xyz123"` | 空结果提示 | P1 |
| AGENT-SEARCH-003 | 语义搜索 | `agent search "写代码"` | 语义匹配 | P1 |

### 2.4 agent compare

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-CMP-001 | 对比两个Agent | `agent compare default code` | 显示对比表 | P0 |
| AGENT-CMP-002 | 对比不存在Agent | `agent compare notexist code` | 错误提示 | P1 |
| AGENT-CMP-003 | 对比自身 | `agent compare default default` | 提示相同 | P2 |

### 2.5 agent evaluate

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-EVAL-001 | 评估默认Agent | `agent evaluate default` | 返回评估结果 | P0 |
| AGENT-EVAL-002 | 评估指定任务 | `agent evaluate default --task "写代码"` | 任务级评估 | P1 |
| AGENT-EVAL-003 | 多指标评估 | `agent evaluate default --metrics quality,speed` | 多维度结果 | P1 |

### 2.6 agent intent

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| AGENT-INTENT-001 | 意图分析 | `agent intent "帮我写个网站"` | 推荐Agent | P0 |
| AGENT-INTENT-002 | 多意图 | `agent intent "写代码+测试"` | 多推荐 | P1 |

---

## 三、package 命令测试用例

### 3.1 package list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| PKG-LIST-001 | 列出已安装 | `package list` | 返回包列表 | P0 |
| PKG-LIST-002 | 空包列表 | 无包时 | 友好提示 | P1 |

### 3.2 package create

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| PKG-CREATE-001 | 从模板创建 | `package create my-agent` | 创建成功 | P0 |
| PKG-CREATE-002 | 覆盖已存在 | `package create default` | 提示覆盖 | P1 |

---

## 四、config 命令测试用例

### 4.1 config list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| CFG-LIST-001 | 列出所有配置 | `config list` | 返回配置列表 | P0 |
| CFG-LIST-002 | 分类显示 | `config list --category llm` | 分类结果 | P1 |

### 4.2 config get

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| CFG-GET-001 | 获取单值 | `config get llm.model` | 返回配置值 | P0 |
| CFG-GET-002 | 获取嵌套值 | `config get agent.default.flow` | 嵌套值 | P1 |
| CFG-GET-003 | 获取不存在 | `config get not.exist` | 友好错误 | P1 |

### 4.3 config set

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| CFG-SET-001 | 设置新值 | `config set test.key "value"` | 设置成功 | P0 |
| CFG-SET-002 | 覆盖已有值 | `config set llm.model "gpt-4"` | 覆盖成功 | P1 |
| CFG-SET-003 | 特殊字符值 | `config set test.key "a=b;c=d"` | 正确处理 | P2 |

---

## 五、memory 命令测试用例

### 5.1 memory list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| MEM-LIST-001 | 列出记忆 | `memory list` | 返回记忆列表 | P0 |
| MEM-LIST-002 | 分类显示 | `memory list --type episodic` | 分类结果 | P1 |
| MEM-LIST-003 | 分页显示 | `memory list --page 2 --size 10` | 分页结果 | P1 |

### 5.2 memory search

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| MEM-SEARCH-001 | 语义搜索 | `memory search "Python教程"` | 相关结果 | P0 |
| MEM-SEARCH-002 | 无结果搜索 | `memory search "xyz"` | 空结果 | P1 |
| MEM-SEARCH-003 | 限制结果数 | `memory search "code" --limit 5` | 限制生效 | P1 |

### 5.3 memory stats

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| MEM-STATS-001 | 显示统计 | `memory stats` | 返回统计信息 | P0 |

---

## 六、eval 命令测试用例

### 6.1 eval run

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| EVAL-RUN-001 | 运行评估 | `eval run "写排序算法"` | 返回评估结果 | P0 |
| EVAL-RUN-002 | 指定指标 | `eval run "task" --metrics quality` | 指定指标 | P1 |
| EVAL-RUN-003 | 输出到文件 | `eval run "task" --output result.json` | 文件生成 | P1 |
| EVAL-RUN-004 | 指定格式 | `eval run "task" --format json` | JSON输出 | P1 |

### 6.2 eval compare

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| EVAL-CMP-001 | 对比评估 | `eval compare result1 result2` | 对比结果 | P0 |

### 6.3 eval list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| EVAL-LIST-001 | 列出指标 | `eval list` | 指标列表 | P0 |

### 6.4 eval history

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| EVAL-HIST-001 | 查看历史 | `eval history` | 历史记录 | P1 |

---

## 七、llm 命令测试用例

### 7.1 llm list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| LLM-LIST-001 | 列出提供商 | `llm list` | 提供商列表 | P0 |
| LLM-LIST-002 | 显示详细信息 | `llm list --verbose` | 详细信息 | P1 |

### 7.2 llm add/remove

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| LLM-ADD-001 | 添加提供商 | `llm add openai --api-key xxx` | 添加成功 | P0 |
| LLM-REM-001 | 移除提供商 | `llm remove openai` | 移除成功 | P0 |
| LLM-REM-002 | 移除不存在 | `llm remove notexist` | 错误提示 | P1 |

### 7.3 llm use

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| LLM-USE-001 | 设置默认 | `llm use deepseek` | 设置成功 | P0 |
| LLM-USE-002 | 设置不存在 | `llm use notexist` | 错误提示 | P1 |

---

## 八、mcp 命令测试用例

### 8.1 mcp servers

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| MCP-LIST-001 | 列出服务器 | `mcp servers` | 服务器列表 | P0 |

### 8.2 mcp start/stop

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| MCP-START-001 | 启动服务器 | `mcp start filesystem` | 启动成功 | P0 |
| MCP-STOP-001 | 停止服务器 | `mcp stop filesystem` | 停止成功 | P0 |

---

## 九、import 命令测试用例

### 9.1 import github

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| IMP-GH-001 | 导入公开仓库 | `import github bytedance/deer-flow` | 导入成功 | P0 |
| IMP-GH-002 | 导入私有仓库 | `import github private/repo` (无权限) | 权限错误 | P1 |
| IMP-GH-003 | 导入不存在仓库 | `import github notexist/notexist` | 不存在错误 | P1 |
| IMP-GH-004 | 导入带分支 | `import github user/repo --branch main` | 指定分支 | P1 |

---

## 十、skills 命令测试用例

### 10.1 skills list

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| SKILL-LIST-001 | 列出Skills | `skills list` | Skills列表 | P0 |
| SKILL-LIST-002 | 分类显示 | `skills list --category coding` | 分类结果 | P1 |

### 10.2 skills create

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| SKILL-CREATE-001 | 创建Skill | `skills create my-skill` | 创建成功 | P0 |

---

## 十一、集成测试用例

### 11.1 完整工作流

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| WF-001 | 导入+运行工作流 | import → run | 完整执行 | P0 |
| WF-002 | 评估工作流 | run → eval | 评估结果 | P0 |
| WF-003 | 配置+运行 | config set → run | 配置生效 | P1 |

### 11.2 错误恢复

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| ERR-001 | Agent失败恢复 | Agent错误后重试 | 恢复执行 | P1 |
| ERR-002 | 网络超时恢复 | 模拟超时后重试 | 正常完成 | P1 |

---

## 十二、压力测试用例

### 12.1 并发测试

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| STRESS-001 | 并发Agent运行 | 10个并发run | 无死锁 | P1 |
| STRESS-002 | 并发配置修改 | 并发config set | 数据一致 | P2 |

### 12.2 资源限制

| 用例ID | 测试名称 | 测试步骤 | 预期结果 | 优先级 |
|--------|----------|----------|----------|--------|
| STRESS-010 | 大量记忆搜索 | 1000+记忆条目搜索 | 响应合理 | P2 |
| STRESS-011 | 长任务执行 | 1小时运行 | 内存不泄漏 | P2 |

---

## 十三、测试数据准备

### 13.1 Agent配置

```yaml
# tests/fixtures/agents/test-agent.yaml
name: "test-agent"
version: "1.0.0"
model:
  provider: "deepseek"
  model: "deepseek-chat"
tools:
  - read
  - write
  - edit
  - bash
```

### 13.2 测试任务集

```python
# tests/fixtures/tasks/simple_tasks.py
SIMPLE_TASKS = [
    "你好",
    "1+1等于几",
    "写一个hello world",
]

COMPLEX_TASKS = [
    "实现一个排序算法",
    "帮我写一个用户登录功能",
    "分析这个代码的性能",
]

EDGE_CASE_TASKS = [
    "",  # 空任务
    " " * 10000,  # 超长空白
    "<script>alert(1)</script>",  # XSS
    "🎉🚀⭐",  # emoji
    "你好\\n换行",  # 换行符
]
```

---

## 十四、测试执行计划

### Phase 1: 冒烟测试 (优先级P0)

```bash
# 每天执行
pytest tests/e2e/test_cli_e2e.py -m smoke -v
```

### Phase 2: 完整测试 (所有优先级)

```bash
# 每周执行
pytest tests/e2e/test_cli_e2e.py -v --tb=short
```

### Phase 3: 压力测试

```bash
# 每月执行
pytest tests/e2e/test_cli_e2e.py -m stress -v --tb=long
```

---

## 十五、测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| run 命令 | 90% |
| agent 命令 | 85% |
| package 命令 | 80% |
| config 命令 | 90% |
| memory 命令 | 85% |
| eval 命令 | 85% |
| llm 命令 | 80% |
| mcp 命令 | 75% |
| import 命令 | 85% |
| skills 命令 | 80% |

---

## 十六、测试框架配置

```python
# pytest.ini
[pytest]
markers =
    smoke: 冒烟测试
    integration: 集成测试
    e2e: 端到端测试
    stress: 压力测试
    slow: 慢速测试
asyncio_mode = auto
timeout = 300
testpaths = tests/e2e
```

---

## 附录：测试用例矩阵

| 命令组 | P0用例 | P1用例 | P2用例 | 总计 |
|--------|--------|--------|--------|------|
| run | 6 | 9 | 6 | 21 |
| agent | 10 | 6 | 2 | 18 |
| package | 2 | 1 | 0 | 3 |
| config | 2 | 3 | 1 | 6 |
| memory | 3 | 3 | 0 | 6 |
| eval | 3 | 4 | 0 | 7 |
| llm | 3 | 2 | 0 | 5 |
| mcp | 2 | 0 | 0 | 2 |
| import | 1 | 3 | 0 | 4 |
| skills | 1 | 1 | 0 | 2 |
| 集成测试 | 3 | 2 | 0 | 5 |
| 压力测试 | 0 | 1 | 2 | 3 |
| **总计** | **36** | **35** | **11** | **82** |
