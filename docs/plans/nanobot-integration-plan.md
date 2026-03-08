# nanobot + OpenYoung 融合架构设计方案

## 决策确认

| 决策点 | 选择 |
|--------|------|
| Channel 模块位置 | `src/channels/` (独立目录) |
| Skill 格式 | SKILL.md + YAML frontmatter |
| 消息路由 | 事件驱动 (解耦) |

---

## 融合架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenYoung                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   Channels (src/channels/)                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │  │Telegram │ │ Discord │ │  QQ    │ │ 钉钉   │ ...  │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘      │  │
│  └───────┼──────────┼──────────┼──────────┼───────────────┘  │
│          │          │          │          │                    │
│          ▼          ▼          ▼          ▼                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Channel Manager (事件分发)                   │  │
│  │  - 消息标准化 (统一格式)                                  │  │
│  │  - 事件触发 (on_message, on_command)                   │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   YoungAgent (核心 Agent)                  │  │
│  │  - Permission System                                     │  │
│  │  - SubAgent (@mention)                                  │  │
│  │  - FlowSkill                                            │  │
│  │  - EvaluationHub                                        │  │
│  │  - Hooks                                                │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心模块设计

### 1. Channel 模块 (src/channels/)

```
src/channels/
├── __init__.py          # 导出 BaseChannel, ChannelManager
├── base.py              # BaseChannel 抽象类
├── manager.py           # ChannelManager 事件分发
├── telegram.py          # Telegram 适配器
├── discord.py           # Discord 适配器
├── qq.py               # QQ 适配器
├── dingtalk.py         # 钉钉适配器
├── feishu.py           # 飞书适配器
└── cli.py              # CLI 适配器 (保留现有)
```

**BaseChannel 接口**:
```python
class BaseChannel:
    async def connect(self): ...
    async def disconnect(self): ...
    async def send_message(self, message: Message): ...
    async def on_message(self, handler: Callable): ...  # 事件回调
    def get_platform(self) -> str: ...
```

### 2. Channel Manager

```python
class ChannelManager:
    def __init__(self, agent: YoungAgent):
        self._channels: Dict[str, BaseChannel] = {}
        self._agent = agent

    def register_channel(self, platform: str, channel: BaseChannel):
        """注册通道"""
        channel.on_message(self._handle_message)
        self._channels[platform] = channel

    async def _handle_message(self, message: Message):
        """处理接收到的消息"""
        # 转换为统一格式
        # 触发 YoungAgent.run()
        # 返回响应
        await self._agent.run(message.content)
```

### 3. Skill 格式 (SKILL.md + frontmatter)

```markdown
---
name: github
description: GitHub 操作技能
version: 1.0.0
always: false
requires:
  bins: [gh, git]
  env: [GH_TOKEN]
tools:
  - create_issue
  - create_pr
---

# GitHub Skills

提供 GitHub 操作能力...
```

### 4. SkillsLoader 改进

```python
class SkillsLoader:
    def _check_requirements(self, skill: Skill) -> bool:
        """检查依赖 (bins/env)"""
        # 检查 CLI 工具是否存在
        for bin in skill.requires.bins:
            if not shutil.which(bin):
                return False
        # 检查环境变量
        for env in skill.requires.env:
            if not os.getenv(env):
                return False
        return True
```

---

## 实现计划

### Phase 1: Channel 基础架构
- [x] 创建 src/channels/ 目录
- [x] 实现 BaseChannel 抽象类
- [x] 实现 ChannelManager
- [x] 迁移现有 CLI 到 Channel 适配器 ✅ 测试通过

### Phase 2: 平台适配器
- [x] 添加 Telegram 适配器 ✅
- [x] 添加 Discord 适配器 ✅
- [x] 添加 QQ 适配器 (Go-CQHTTP) ✅
- [x] 添加 钉钉 适配器 ✅
- [x] 添加 飞书 适配器 ✅

### Phase 3: Skill 格式升级
- [x] 改进 SkillsLoader 支持 frontmatter ✅
- [x] 添加依赖检查 (bins/env) ✅
- [x] 支持 always_skills ✅

### Phase 4: 一体化部署
- [x] 更新 Dockerfile ✅
- [x] 添加 docker-compose.yml ✅
- [x] 配置管理 ✅

---

## 保留的 OpenYoung 特性

| 特性 | 保留方式 |
|------|----------|
| Permission System | 通过 ChannelManager 传递 |
| SubAgent | 保持现有实现 |
| FlowSkill | 保持现有实现 |
| EvaluationHub | 保持现有实现 |
| Hooks | 扩展事件类型 (on_telegram_message, etc.) |

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 依赖冲突 | nanobot 作为独立子模块 |
| 复杂度增加 | 分阶段实现 |
| 破坏现有功能 | 保持 CLI 兼容 |
