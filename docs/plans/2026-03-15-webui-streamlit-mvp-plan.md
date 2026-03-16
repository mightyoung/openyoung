# OpenYoung WebUI Streamlit MVP 实施计划

> 基于 Streamlit 最佳实践和项目现有架构
> 日期: 2026-03-15

---

## 一、项目概述

### 1.1 目标

使用 Streamlit 快速构建 OpenYoung WebUI MVP，为终端用户提供可视化的 Agent 对话体验，同时监控从 Agent 导入到任务产出的全流程。

### 1.2 技术栈选择

| 组件 | 技术选择 | 理由 |
|------|----------|------|
| 前端框架 | Streamlit | Python 原生，快速开发，与现有后端无缝集成 |
| 后端 | 复用现有 FastAPI | 已有 session_api.py, 避免重复开发 |
| 会话存储 | SQLite | 复用现有 datacenter 存储 |
| 实时流 | Server-Sent Events (SSE) | Streamlit 原生支持 |
| 认证 | 简化版 (API Key) | MVP 阶段简化 |

---

## 二、现有架构分析

### 2.1 现有组件

```
现有架构
├── src/agents/session.py        # Session, Message, SessionManager
├── src/api/session_api.py       # FastAPI 路由 (已实现)
├── src/datacenter/             # 数据存储
└── src/runtime/sandbox/        # 沙箱执行
```

### 2.2 现有 API 端点

| 方法 | 路径 | 状态 |
|------|------|------|
| POST | /api/sessions | ✅ 已实现 |
| GET | /api/sessions | ✅ 已实现 |
| GET | /api/sessions/{id} | ✅ 已实现 |
| POST | /api/sessions/{id}/messages | ✅ 已实现 |
| POST | /api/sessions/{id}/suspend | ⬜ 待实现 |
| POST | /api/sessions/{id}/resume | ⬜ 待实现 |
| WS | /api/ws/{id} | ⬜ 待实现 |

---

## 三、实施计划

### Phase 1: 项目初始化 (Week 1, Day 1-2)

#### 任务 1.1: 创建 Streamlit 项目结构

**目录结构**:
```
webui/
├── app.py                  # Streamlit 主应用
├── pages/
│   ├── 1_🤖_Agents.py     # Agent 列表页
│   ├── 2_💬_Chat.py       # 对话页
│   ├── 3_📊_Sessions.py    # 会话管理页
│   └── 4_⚙️_Settings.py   # 设置页
├── components/
│   ├── chat_widget.py      # 聊天组件
│   ├── agent_card.py       # Agent 卡片组件
│   └── session_list.py     # 会话列表组件
├── services/
│   ├── api_client.py       # API 客户端
│   └── session_service.py  # 会话服务
├── utils/
│   ├── config.py           # 配置管理
│   └── stream_utils.py    # 流式输出工具
└── requirements.txt        # 依赖
```

#### 任务 1.2: 安装依赖

```bash
pip install streamlit httpx sseclient-py
```

#### 任务 1.3: 创建基础配置

```python
# webui/utils/config.py
import os

class Config:
    """WebUI 配置"""

    # API 配置
    API_BASE_URL = os.getenv("OPENYOUNG_API_URL", "http://localhost:8000")
    API_KEY = os.getenv("OPENYOUNG_API_KEY", "")

    # Streamlit 配置
    PAGE_ICON = "🤖"
    LAYOUT = "wide"
    INITIAL_SIDEBAR_STATE = "expanded"

    # 会话配置
    MAX_MESSAGES = 100
    TYPING_SPEED = 0.02  # 秒/字符
```

---

### Phase 2: 核心页面开发 (Week 1, Day 3-5)

#### 任务 2.1: Agent 列表页

**功能**:
- 展示所有可用 Agent
- 支持语义搜索
- 显示 Agent 徽章 (Verified, Top Rated 等)

**实现**:
```python
# webui/pages/1_🤖_Agents.py
import streamlit as st
from webui.services.api_client import APIClient

def main():
    st.set_page_config(page_title="Agents", page_icon="🤖")
    st.title("🤖 Available Agents")

    # 搜索栏
    query = st.text_input("🔍 Search agents", placeholder="Describe what you need...")

    # 获取 Agent 列表
    client = APIClient()
    agents = client.list_agents(search=query)

    # 展示 Agent 卡片
    for agent in agents:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(agent.name)
                st.write(agent.description)
            with col2:
                if st.button("Chat", key=agent.id):
                    st.session_state.target_agent = agent.id
                    st.switch_page("pages/2_💬_Chat.py")

if __name__ == "__main__":
    main()
```

#### 任务 2.2: 对话页面 (核心)

**功能**:
- 聊天界面
- 流式输出
- 会话历史
- 代码块高亮

**实现**:
```python
# webui/pages/2_💬_Chat.py
import streamlit as st
import asyncio
from webui.services.api_client import APIClient

def main():
    st.set_page_config(page_title="Chat", page_icon="💬")

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 侧边栏: 会话管理
    with st.sidebar:
        st.title("💬 Sessions")
        if st.button("New Chat"):
            st.session_state.messages = []

    # 聊天历史
    for msg in st.session_state.messages:
        with st.chat_message(msg.role):
            st.markdown(msg.content)

    # 输入框
    if prompt := st.chat_input("Message your agent..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 发送消息并流式显示
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            # 调用 API (流式)
            client = APIClient()
            for chunk in client.send_message_stream(prompt):
                full_response += chunk
                placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        # 保存响应
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
```

#### 任务 2.3: 会话管理页

**功能**:
- 列出所有持久会话
- 显示会话状态 (idle, running, suspended)
- 支持暂停/恢复

---

### Phase 3: 后端增强 (Week 2, Day 1-3)

#### 任务 3.1: 完善 Session API

**新增端点**:
```python
# src/api/session_api.py 扩展

@app.post("/api/sessions/{session_id}/suspend")
async def suspend_session(session_id: str):
    """暂停会话"""
    session = session_manager.suspend_session(session_id)
    return SessionResponse(...)

@app.post("/api/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    """恢复会话"""
    session = session_manager.resume_session(session_id)
    return SessionResponse(...)

@app.websocket("/api/ws/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """WebSocket 实时通信"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # 处理消息...
    except WebSocketDisconnect:
        pass
```

#### 任务 3.2: 流式输出支持

**SSE 实现**:
```python
# src/api/stream_api.py
from sse_starlette.sse import EventStreamResponse

@app.get("/api/stream/{task_id}")
async def stream_task(task_id: str):
    """Server-Sent Events 流式输出"""

    async def event_generator():
        while True:
            # 获取最新输出
            output = await get_task_output(task_id)
            if output:
                yield {"event": "message", "data": output}

            if is_task_complete(task_id):
                break

            await asyncio.sleep(0.5)

    return EventStreamResponse(event_generator())
```

---

### Phase 4: 高级功能 (Week 2, Day 4-7)

#### 任务 4.1: 执行日志/审计

**功能**:
- 实时显示执行日志
- 显示 Agent 推理过程
- 错误追踪

**UI 组件**:
```python
# webui/components/log_viewer.py
import streamlit as st

def log_viewer(logs: list[dict]):
    """日志查看器组件"""

    with st.expander("📋 Execution Logs", expanded=True):
        for log in logs:
            color = {
                "info": "blue",
                "warning": "yellow",
                "error": "red",
                "success": "green"
            }.get(log.level, "gray")

            st.markdown(
                f":{color}[{log.timestamp}] **{log.level}**: {log.message}"
            )
```

#### 任务 4.2: 评估结果展示

**功能**:
- 显示评估分数
- 趋势图
- 对比视图

---

## 四、集成架构

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenYoung WebUI                          │
│                      (Streamlit)                            │
├─────────────────────────────────────────────────────────────┤
│  Pages:                                                   │
│  ├── Agents    │  Chat    │  Sessions  │  Settings         │
├─────────────────────────────────────────────────────────────┤
│  Components:                                               │
│  ├── chat_widget  │  agent_card  │  session_list           │
├─────────────────────────────────────────────────────────────┤
│  Services:                                                │
│  ├── api_client       │  session_service                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
├─────────────────────────────────────────────────────────────┤
│  /api/sessions/*        → SessionManager                   │
│  /api/agents/*         → AgentRegistry                    │
│  /api/stream/*         → SSE Stream                       │
│  /api/ws/*            → WebSocket                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Center                             │
├─────────────────────────────────────────────────────────────┤
│  Session Storage    → SQLite                               │
│  Execution Logs    → SQLite                               │
│  Evaluation Results → SQLite                               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流

```
User Input → Streamlit → FastAPI → YoungAgent → Sandbox
                ↑                        │
                │                        ▼
            SSE Stream           ExecutionResult
                │                        │
                └────────────┬───────────┘
                             ▼
                      SQLite (存储)
```

---

## 五、验收标准

### 5.1 MVP 验收

| 功能 | 验收条件 | 优先级 |
|------|----------|--------|
| Agent 列表 | 显示所有可用 Agent，支持搜索 | P0 |
| 对话界面 | 可以发送消息，接收响应 | P0 |
| 流式输出 | 逐字显示响应 | P0 |
| 会话管理 | 创建、列出、查看会话 | P0 |
| 执行日志 | 显示任务执行日志 | P1 |
| 评估展示 | 显示评估分数 | P2 |

### 5.2 质量标准

- [ ] 页面加载时间 < 2秒
- [ ] 流式输出延迟 < 500ms
- [ ] 支持 100+ 条消息历史
- [ ] 响应式布局

---

## 六、里程碑

| 周 | 里程碑 | 交付物 | 状态 |
|----|--------|--------|------|
| W1 Day 1-2 | 项目初始化 | 项目结构，依赖安装 | ✅ 已完成 |
| W1 Day 3-5 | 核心页面 | Agent 列表、对话界面 | ✅ 已完成 |
| W2 Day 1-3 | 后端增强 | Session API 完善，SSE 支持 | ✅ 已完成 |
| W2 Day 4-7 | 高级功能 | 日志查看、评估展示 | ✅ 已完成 |

## 八、实施记录

### 2026-03-16 实现完成

**项目结构**:
```
webui/
├── app.py                     # Streamlit 主应用 ✅
├── pages/
│   ├── 1_🤖_Agents.py       # Agent 列表页 ✅
│   ├── 2_💬_Chat.py          # 对话页面 ✅
│   ├── 3_📋_Sessions.py      # 会话管理页 ✅
│   ├── 4_📊_Dashboard.py     # 评估仪表板 ✅
│   └── 5_⚙️_Settings.py      # 设置页 ✅
├── components/
│   └── chat_widget.py         # 聊天组件 ✅
├── services/
│   ├── api_client.py          # API 客户端 ✅
│   └── session_service.py     # 会话服务 ✅
└── utils/
    └── config.py               # 配置管理 ✅
```

**Docker 集成**:
- 添加 Streamlit 依赖到 Dockerfile
- 暴露 8501 端口
- 添加 webui 服务到 docker-compose.yml
- WebUI 依赖 CLI 服务 (端口 8080)

**部署**:
```bash
# 启动 CLI 服务
docker-compose up -d openyoung

# 启动 WebUI
docker-compose up -d webui

# 访问 WebUI
# http://localhost:8501
```

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Streamlit 实时性 | 流式输出可能有延迟 | 使用 st.empty() + 异步 |
| 状态管理 | 多用户会话隔离 | 使用 session_state 隔离 |
| 扩展性 | Streamlit 定制化有限 | MVP 阶段接受限制 |

---

*计划生成时间: 2026-03-15*
*技术栈: Streamlit + FastAPI + SQLite*
