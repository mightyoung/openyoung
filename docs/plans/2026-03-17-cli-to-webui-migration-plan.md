# CLI到WebUI迁移计划

## 顶层摘要（30秒理解）

**目标**: 用WebUI全面替换CLI功能，聚焦3个核心能力，删除冗余代码

**核心策略**: 增强缺失WebUI功能 → 统一API层 → 渐进式删除CLI

---

## 执行层（快速概览）

### 阶段1: 补全WebUI功能 [P0]
- [ ] 完善Chat页面流式输出
- [ ] 添加Skills管理页面
- [ ] 添加评估运行功能到Dashboard

### 阶段2: 统一架构 [P1]
- [ ] 创建统一API层
- [ ] 消除CLI/WebUI重复逻辑

### 阶段3: 精简代码 [P2]
- [ ] 删除冗余CLI代码
- [ ] 保留轻量CLI入口

---

## 任务层（可直接执行）

### Phase 1: 补全功能

| ID | 任务 | 状态 | 依赖 |
|----|------|------|------|
| T1 | 完善Chat流式输出 | - | - |
| T2 | 创建Skills管理页面 | - | - |
| T3 | 添加评估运行功能 | - | - |
| T4 | 完善Settings完整CRUD | - | - |

### Phase 2: 统一架构

| ID | 任务 | 状态 | 依赖 |
|----|------|------|------|
| T5 | 创建统一API服务层 | T1,T2,T3 | - |
| T6 | 消除loader重复代码 | - | - |
| T7 | 消除session_cli重复代码 | - | - |

### Phase 3: 精简代码

| ID | 任务 | 状态 | 依赖 |
|----|------|------|------|
| T8 | 删除config.py重复 | T5 | - |
| T9 | 删除config_manager重复 | T5 | - |
| T10 | 保留run命令轻量入口 | T5 | - |

---

## 详细方案（渐进载入）

### T1: 完善Chat流式输出

**当前问题**: WebUI Chat使用同步调用，CLI使用流式输出

**实现方案**:
```
src/webui/services/api_client.py
├── 添加 stream_chat() 方法
├── 使用 SSE (Server-Sent Events)
└── 在 2_Chat.py 中使用 st.write_stream()

src/cli/run.py (可参考)
├── AgentRunner.run() 方法
└── 使用 asyncio 生成器模式
```

**验证标准**:
- [ ] SSE流式输出正常
- [ ] 打字机效果可见
- [ ] 错误处理完整

---

### T2: 创建Skills管理页面

**文件结构**:
```
src/webui/pages/6_Skills.py  (新建)
```

**功能清单**:
- [ ] 列出可用Skill模板 (skills list)
- [ ] 创建新Skill (skills create)
- [ ] 安装/卸载Skills

**参考代码**:
```python
# 参考 src/skills/creator.py
from src.skills.creator import list_templates, create_skill
```

---

### T3: 添加评估运行功能

**当前状态**: CLI有 `eval run/report/compare`，Dashboard仅展示数据

**需要添加**:
```
src/webui/pages/4_Dashboard.py
├── 添加 "Run Evaluation" 按钮
├── 选择数据集下拉框
├── 显示实时进度
└── 保存结果到数据中心
```

**参考代码**:
```python
# 参考 src/cli/commands/eval.py
# 参考 src/evaluation/hub.py
```

---

### T4: 完善Settings完整CRUD

**当前问题**: 仅表单保存到session，未持久化

**需要添加**:
- [ ] 读取现有配置
- [ ] 保存到配置文件
- [ ] 切换环境(dev/prod)
- [ ] API端点配置

---

### T5: 创建统一API服务层

**目标**: WebUI和CLI共享同一套业务逻辑

**架构**:
```
src/api/                    (新建)
├── __init__.py
├── routes/
│   ├── agents.py          # Agent管理
│   ├── skills.py          # Skill管理
│   ├── sessions.py        # 会话管理
│   └── evaluation.py      # 评估运行
├── dependencies.py         # 依赖注入
└── main.py                # FastAPI入口

src/webui/services/api_client.py  → 调用 src/api/
src/cli/main.py                   → 调用 src/api/
```

**迁移策略**:
1. 先在 api/ 创建核心端点
2. WebUI通过HTTP调用
3. CLI改为调用API（保留本地fallback）

---

### T8-T10: 删除冗余代码

**CLI文件删除清单** (Phase 3):
- `src/cli/config.py` → 迁移到 src/config/
- `src/cli/config_manager.py` → 迁移到 src/config/
- `src/cli/session_cli.py` → 合并到 src/datacenter/
- `src/cli/loader.py` → 合并到 src/agents/

**保留文件**:
- `src/cli/main.py` → 仅保留 `run` 命令
- `src/cli/repl.py` → 保留交互式入口

---

## 关键依赖图

```
T1(Chat流式) ──┐
               ├──▶ T5(统一API) ──▶ T8(删除config)
T2(Skills) ───┤               ├──▶ T9(删除config_manager)
               │               └──▶ T10(保留run入口)
T3(评估运行) ──┘
T4(Settings) ──────────────▶ T5
```

---

## 进展追踪

最后更新: 2026-03-17

- [ ] Phase 1 完成
- [ ] Phase 2 完成
- [ ] Phase 3 完成

---

## 相关文档

- [2026-03-15-webui-streamlit-mvp-plan.md](./2026-03-15-webui-streamlit-mvp-plan.md) - 原有WebUI规划
- [src/cli/main.py](../src/cli/main.py) - CLI入口
- [src/webui/](../src/webui/) - WebUI源码
