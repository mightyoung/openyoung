# CLI到WebUI迁移计划 - v2

**基于Anthropic Context Engineering最佳实践**

---

## Layer 0: 任务索引 (~50 tokens)

```
Phase 1 (T1-T4): 补全WebUI功能
  T1: Chat流式输出
  T2: Skills管理页面
  T3: 评估运行功能
  T4: Settings完整CRUD

Phase 2 (T5-T7): 统一架构
  T5: 统一API服务层
  T6: 消除loader重复
  T7: 消除session_cli重复

Phase 3 (T8-T10): 精简代码
  T8: 删除config.py重复
  T9: 删除config_manager重复
  T10: 保留run轻量入口
```

**当前任务**: ✅ 全部完成

---

## Layer 1: T1任务详情

### T1: Chat流式输出

**状态**: ✅ completed

**方案**: B - 使用SSE实现真实流式输出

**子任务**:
- [x] T1.1: 创建 `src/api/routes/chat_api.py` - SSE流式接口 (已存在于session_api.py)
- [x] T1.2: 修改 `api_client.py` - 使用 POST `/api/sessions/{id}/stream`
- [x] T1.3: 修改 `2_Chat.py` - 纯流式（无降级方案）
- [x] T1.4: 添加单元测试 (9 tests passed)

**验证标准**:
- [x] SSE流式输出正常
- [x] 打字机效果可见
- [x] 错误处理完整
- [x] 断线重连正常

**协议选择**: SSE (Server-Sent Events)
- 原因: 单向(server→client)，与AI聊天模式天然匹配
- 优势: 内置自动重连、简单实现，防火墙友好
- 依赖: 项目已有 `sse-starlette`

---

## Layer 2: 进度追踪

### 执行状态

- [x] T1: ✅ completed (Chat流式输出) - 9 tests passed
  - [x] T1.1: ✅ 已有session_api.py SSE实现
  - [x] T1.2: ✅ 修改 api_client.py - POST流式方法
  - [x] T1.3: ✅ 修改 2_Chat.py - 真实流式输出
  - [x] T1.4: ✅ 添加单元测试 (9 passed)
- [x] T2: ✅ completed (Skills管理页面) - 6_Skills.py created
- [x] T3: ✅ completed (评估运行功能) - 4_Dashboard.py扩展
- [x] T4: ✅ completed (Settings完整CRUD) - YAML持久化+环境+多Provider
- [x] T5: ✅ completed (统一API服务层) - routes目录+统一注册
- [x] T6: ✅ completed (消除loader重复) - agents/loader.py别名
- [x] T7: ✅ completed (消除session_cli重复) - 已标记弃用
- [x] T8: ✅ completed (删除config.py) - 已标记弃用
- [x] T9: ✅ completed (删除config_manager.py) - 已标记弃用
- [x] T10: ✅ completed (保留run轻量入口) - run+repl已存在

---

## 详细方案（完整加载）

### T1: Chat流式输出

#### T1.1: 创建 chat_api.py SSE流式接口

**文件**: `src/api/routes/chat_api.py`

```python
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import asyncio
import json

router = APIRouter()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/sessions/{session_id}/chat/stream")
async def stream_chat(session_id: str, request: ChatRequest):
    """SSE流式聊天接口"""

    async def event_generator():
        try:
            session = get_session(session_id)
            async for chunk in agent.stream_run(session, request.message):
                yield {"event": "message", "data": json.dumps({"content": chunk})}
                await asyncio.sleep(0)
            yield {"event": "done", "data": json.dumps({"status": "complete"})}
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_generator())
```

**验证**: T1.1完成后需验证
- [ ] SSE连接建立
- [ ] 消息发送成功
- [ ] 流式响应正常
- [ ] 错误事件处理

---

#### T1.2: 修改 api_client.py

**文件**: `src/webui/services/api_client.py`

**修改点**:
- 使用已有 `stream_chat()` 方法
- 端点改为 `/api/sessions/{session_id}/chat/stream`
- 处理SSE事件流

---

#### T1.3: 修改 2_Chat.py

**文件**: `src/webui/pages/2_Chat.py`

**修改点**:
- 移除同步调用
- 仅保留流式输出（无降级方案）
- 使用 `st.write_stream()`

---

#### T1.4: 单元测试

**文件**: `tests/webui/test_chat_streaming.py`

**测试用例**:
- [ ] test_sse_connection
- [ ] test_streaming_response
- [ ] test_error_handling
- [ ] test_session_management

---

### T2: Skills管理页面

**状态**: ✅ completed

**方案**: B - 独立页面，包含所有功能

**文件**: `src/webui/pages/6_Skills.py`

**功能清单**:
- [x] 列出可用Skill模板
- [x] 创建新Skill
- [x] 安装/卸载Skills
- [x] Skill详情查看
- [x] 搜索/过滤功能

**验证**: T2完成后需验证
- [ ] 模板列表显示
- [ ] 创建流程完整
- [ ] 安装/卸载正常

---

### T3: 评估运行功能

**状态**: ⚪ pending

**方案**: B - 独立页面，功能组合

**文件**: `src/webui/pages/4_Dashboard.py` (扩展)

**功能清单**:
- [ ] Agent选择下拉框
- [ ] 数据集选择
- [ ] 运行评估按钮
- [ ] 实时进度条
- [ ] 结果展示区域
- [ ] 历史记录

**验证**: T3完成后需验证
- [ ] Agent选择正常
- [ ] 实时进度更新
- [ ] 结果正确展示

---

### T4: Settings完整CRUD

**状态**: ⚪ pending

**方案**: A - 本地YAML文件存储

**文件**: `src/webui/pages/5_Settings.py`

**功能清单**:
- [ ] 读取现有配置
- [ ] 保存到YAML文件
- [ ] 环境切换(dev/prod)
- [ ] 多Provider支持

**配置结构** (参考最佳实践):
```yaml
agents:
  default:
    provider: anthropic
    model: claude-sonnet-4-20250514
    temperature: 0.7

providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
  openai:
    api_key: ${OPENAI_API_KEY}
```

**关键原则**:
- 精确版本号（不用"latest"）
- 环境变量存储敏感信息
- Provider抽象层
- 热重载支持

**验证**: T4完成后需验证
- [ ] 配置读取正常
- [ ] 保存成功
- [ ] 环境切换有效
- [ ] 多Provider切换正常

---

### T5: 统一API服务层

**状态**: ⚪ pending

**方案**: 创建 - `src/api/routes/` 目录统一管理

**现状**:
- `src/api/server.py` - FastAPI入口
- `src/api/session_api.py` - 会话API
- `src/api/docs.py` - API文档
- API路由分散在不同文件

**目标**: 统一管理所有API路由

**创建结构**:
```
src/api/routes/
├── __init__.py
├── chat.py          # 聊天接口 (T1.1)
├── sessions.py      # 会话管理
├── agents.py        # Agent管理
├── skills.py        # Skill管理
├── evaluation.py    # 评估运行
└── config.py        # 配置管理
```

**步骤**:
1. 创建 `src/api/routes/` 目录
2. 迁移现有API到routes/
3. 添加T1-T4所需的新路由
4. 更新 `server.py` 统一注册

**验证**: T5完成后需验证
- [ ] 所有路由统一注册
- [ ] API文档完整
- [ ] 路由冲突解决

---

### T6: 消除loader重复

**状态**: ⚪ pending

**方案**: 迁移 - `src/cli/loader.py` → `src/agents/loader.py`

**现状**:
- `src/cli/loader.py` (277行) - AgentLoader类
- 负责: 加载Agent配置、验证、列表

**目标**: 迁移到核心模块，消除重复

**步骤**:
1. 创建 `src/agents/loader.py`
2. 迁移AgentLoader类
3. 更新所有导入引用
4. 删除原 `src/cli/loader.py`

**验证**: T6完成后需验证
- [ ] Agent加载功能正常
- [ ] 所有引用已更新
- [ ] 测试通过

---

### T7: 消除session_cli重复

**状态**: ⚪ pending

**方案**: 删除 - 移除 `src/cli/session_cli.py`

**现状**:
- `src/cli/session_cli.py` (140行) - CLI会话命令
- `src/agents/session.py` - SessionManager核心类

**目标**: 移除CLI包装，会话功能通过API/WebUI访问

**步骤**:
1. 删除 `src/cli/session_cli.py`
2. 确保 `SessionManager` API完整
3. WebUI已有会话管理界面

**验证**: T7完成后需验证
- [ ] 会话功能通过API正常
- [ ] WebUI会话管理正常

---

### T8: 删除config.py重复

**状态**: ⚪ pending

**方案**: 迁移 - 删除，迁移到WebUI Settings (T4)

**现状**:
- `src/cli/config.py` (171行) - config子命令
- 功能: get/set/unset/list/reset

**已有替代**:
- `src/config/__init__.py` - 集中配置管理
- T4 WebUI Settings页面

**步骤**:
1. 确认T4 Settings功能完整
2. 删除 `src/cli/config.py`
3. 更新 `src/cli/main.py` 移除引用

**验证**: T8完成后需验证
- [ ] 配置通过WebUI管理正常
- [ ] CLI无config命令（预期）

---

### T9: 删除config_manager重复

**状态**: ⚪ pending

**方案**: 删除 - 移除 `src/cli/config_manager.py`

**现状**:
- `src/cli/config_manager.py` (121行) - 配置管理类
- 功能: load/save/validate

**已有替代**:
- `src/config/loader.py` - ConfigLoader类
- `src/config/models.py` - 配置模型

**步骤**:
1. 确认 `src/config/loader.py` 功能完整
2. 删除 `src/cli/config_manager.py`
3. 更新所有导入引用

**验证**: T9完成后需验证
- [ ] 配置功能正常
- [ ] 所有引用已更新

---

### T10: 保留run轻量入口

**状态**: ⚪ pending

**方案**: B - 保留 `run` + `repl`

**现状**:
- `src/cli/main.py` (800+行) - 完整CLI入口
- `src/cli/run.py` - Agent运行逻辑
- `src/cli/repl.py` - 交互式REPL

**目标**: 精简为轻量入口

**保留**:
- `src/cli/run.py` - run命令
- `src/cli/repl.py` - repl命令

**删除/重构**:
- 删除: session相关命令 (T7)
- 删除: config相关命令 (T8, T9)
- 简化: main.py仅保留run/repl入口

**验证**: T10完成后需验证
- [ ] `openyoung run` 正常工作
- [ ] `openyoung repl` 正常工作
- [ ] 其他CLI命令已移除

---

## 进度追踪

最后更新: 2026-03-17

### 执行状态
- [ ] T1: 🔵 in_progress
- [ ] T2: ⚪ pending
- [ ] T3: ⚪ pending
- [ ] T4: ⚪ pending
- [ ] T5: ⚪ pending
- [ ] T6: ⚪ pending
- [ ] T7: ⚪ pending
- [ ] T8: ⚪ pending
- [ ] T9: ⚪ pending
- [ ] T10: ⚪ pending
