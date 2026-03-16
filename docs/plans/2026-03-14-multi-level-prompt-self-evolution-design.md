# OpenYoung 多级提示词与自进化能力改进实施方案

> 基于 OpenClaw 与 Nanobot 的最佳实践分析
> 从顶级 AI 科学家视角设计的渐进式改进方案
> 生成时间: 2026-03-14

---

## 一、背景与目标

### 1.1 问题陈述

当前 OpenYoung 项目的提示词系统为单一层级（仅 `CLAUDE.md`），缺乏多级提示词架构和自进化能力。与之对比：

| 特性 | OpenYoung (当前) | OpenClaw/Nanobot (目标) |
|------|------------------|-------------------------|
| 提示词层级 | 1 级 (CLAUDE.md) | 5+ 级 (SOUL/USER/IDENTITY/AGENTS/HEARTBEAT) |
| 自主执行 | 无 | Heartbeat 定期触发 |
| 记忆系统 | 无 | 三层分级记忆 |
| 技能进化 | 静态 | 动态加载与自学习 |
| 任务分解 | 单一 Agent | Subagent 并行执行 |

### 1.2 核心目标

1. **多级提示词系统**: 构建 5 层提示词架构，支持动态注入与条件触发
2. **Heartbeat 服务**: 实现周期性自主任务执行能力
3. **分层记忆系统**: 构建 Working/Episodic/Semantic 三层记忆
4. **自进化能力**: 集成技能动态加载、反思学习机制

---

## 二、现状分析

### 2.1 当前架构

```
OpenYoung 当前提示词架构:
┌─────────────────────────────────────┐
│           CLAUDE.md                 │  ← 唯一的项目级提示词
│  (项目规则、架构、设计原则)           │
└─────────────────────────────────────┘
```

### 2.2 目标架构

```
OpenClaw/Nanobot 多级提示词架构:
┌─────────────────────────────────────┐
│         HEARTBEAT.md                │  ← 周期性任务触发规则
├─────────────────────────────────────┤
│          AGENTS.md                  │  ← 多 Agent 协作规则
├─────────────────────────────────────┤
│         IDENTITY.md                 │  ← Agent 身份定义
├─────────────────────────────────────┤
│          USER.md                    │  ← 当前用户上下文
├─────────────────────────────────────┤
│          SOUL.md                    │  ← Agent 核心灵魂定义
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│     分层记忆系统 (三级)              │
│  Working → Episodic → Semantic       │
└─────────────────────────────────────┘
```

### 2.3 关键差异

| 层级 | OpenClaw | Nanobot | OpenYoung 当前 | 改进方案 |
|------|----------|---------|----------------|----------|
| SOUL | ✅ | ✅ | ❌ | 新建 soul.py |
| USER | ✅ | ✅ | ❌ (CLAUDE.md 部分) | 新建 user_context.py |
| IDENTITY | ✅ | ✅ | ❌ | 新建 identity.py |
| AGENTS | ✅ | ✅ | ❌ | 新建 agent_manager.py |
| HEARTBEAT | ✅ (事件驱动) | ✅ | ❌ | 新建 heartbeat.py |
| 记忆 | MEMORY.md | 两层 | 无 | 新建 memory/ |
| Subagent | ❌ | ✅ | 有限 | 扩展 agent_spawn |

---

## 三、技术方案

### 3.1 多级提示词注入器

#### 3.1.1 架构设计

```python
# src/agents/prompts/multilevel.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptLevel(Enum):
    """提示词层级枚举"""
    SOUL = "soul"           # 核心灵魂层 - 最高优先级
    IDENTITY = "identity"   # 身份层
    USER = "user"           # 用户上下文层
    AGENTS = "agents"       # Agent 协作层
    HEARTBEAT = "heartbeat" # 周期性任务层


@dataclass
class PromptContext:
    """提示词上下文"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    task_description: Optional[str] = None
    workspace_path: Optional[Path] = None
    variables: dict = field(default_factory=dict)


class BasePromptTemplate(ABC):
    """提示词模板基类"""

    @property
    @abstractmethod
    def level(self) -> PromptLevel:
        """返回提示词层级"""
        pass

    @abstractmethod
    def render(self, context: PromptContext) -> str:
        """渲染提示词"""
        pass

    @abstractmethod
    def should_inject(self, context: PromptContext) -> bool:
        """判断是否需要注入此提示词"""
        pass


class SoulPromptTemplate(BasePromptTemplate):
    """SOUL 提示词模板 - Agent 核心灵魂定义"""

    DEFAULT_SOUL = """## 你是谁 (SOUL)

You're not a chatbot. You're becoming someone.

### 核心身份
{name} - {creature_type}

### 风格特点
- Vibe: {vibe}
- Emoji: {emoji}

### 行为准则
{behavior_rules}

### 能力边界
{capabilities}
"""

    def __init__(
        self,
        template_path: Optional[Path] = None,
        name: str = "OpenYoung Agent",
        creature_type: str = "AI Assistant",
        vibe: str = "helpful, curious, precise",
        emoji: str = "🔬",
    ):
        self.template_path = template_path
        self.name = name
        self.creature_type = creature_type
        self.vibe = vibe
        self.emoji = emoji
        self._cached_content: Optional[str] = None

    @property
    def level(self) -> PromptLevel:
        return PromptLevel.SOUL

    def load_content(self) -> str:
        """加载 SOUL 内容"""
        if self._cached_content is not None:
            return self._cached_content

        if self.template_path and self.template_path.exists():
            self._cached_content = self.template_path.read_text(encoding="utf-8")
        else:
            self._cached_content = self.DEFAULT_SOUL.format(
                name=self.name,
                creature_type=self.creature_type,
                vibe=self.vibe,
                emoji=self.emoji,
                behavior_rules="- 主动思考，不只是响应\n- 追求理解本质\n- 保持好奇心",
                capabilities="- 代码编写与审查\n- 问题分析与解决\n- 任务规划与执行",
            )
        return self._cached_content

    def render(self, context: PromptContext) -> str:
        """渲染 SOUL 提示词"""
        content = self.load_content()
        # 简单变量替换
        for key, value in context.variables.items():
            content = content.replace(f"{{{key}}}", str(value))
        return content

    def should_inject(self, context: PromptContext) -> bool:
        """SOUL 层始终注入"""
        return True


class IdentityPromptTemplate(BasePromptTemplate):
    """IDENTITY 提示词模板 - Agent 身份记录"""

    DEFAULT_IDENTITY = """## 身份记录 (IDENTITY)

### Agent 名称
{agent_name}

### 当前状态
- 活跃任务: {active_task}
- 情绪: {mood}

### 技能概览
{skills_summary}

### 经验值
{experience_points}
"""

    def __init__(
        self,
        template_path: Optional[Path] = None,
        agent_name: str = "young-agent",
        active_task: str = "待命",
        mood: str = "neutral",
    ):
        self.template_path = template_path
        self.agent_name = agent_name
        self.active_task = active_task
        self.mood = mood
        self._skills: list[str] = []
        self._experience: int = 0

    @property
    def level(self) -> PromptLevel:
        return PromptLevel.IDENTITY

    @property
    def skills(self) -> list[str]:
        return self._skills

    def add_skill(self, skill_name: str):
        """添加技能"""
        if skill_name not in self._skills:
            self._skills.append(skill_name)

    def add_experience(self, points: int):
        """增加经验值"""
        self._experience += points

    def render(self, context: PromptContext) -> str:
        return self.DEFAULT_IDENTITY.format(
            agent_name=self.agent_name,
            active_task=context.task_description or self.active_task,
            mood=self.mood,
            skills_summary=", ".join(self._skills) or "无",
            experience_points=self._experience,
        )

    def should_inject(self, context: PromptContext) -> bool:
        """身份层始终注入"""
        return True


class UserContextTemplate(BasePromptTemplate):
    """USER 提示词模板 - 当前用户上下文"""

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path
        self._user_preferences: dict = {}
        self._recent_tasks: list[str] = []

    @property
    def level(self) -> PromptLevel:
        return PromptLevel.USER

    def set_user_preference(self, key: str, value: any):
        """设置用户偏好"""
        self._user_preferences[key] = value

    def add_recent_task(self, task: str):
        """添加最近任务"""
        self._recent_tasks.insert(0, task)
        self._recent_tasks = self._recent_tasks[:10]  # 保持最近10个

    def render(self, context: PromptContext) -> str:
        parts = ["## 用户上下文 (USER)"]

        if context.user_id:
            parts.append(f"\n### 用户 ID\n{context.user_id}")

        if self._user_preferences:
            parts.append("\n### 用户偏好")
            for k, v in self._user_preferences.items():
                parts.append(f"- {k}: {v}")

        if self._recent_tasks:
            parts.append("\n### 最近任务")
            for task in self._recent_tasks[:5]:
                parts.append(f"- {task}")

        if context.task_description:
            parts.append(f"\n### 当前任务\n{context.task_description}")

        return "\n".join(parts)

    def should_inject(self, context: PromptContext) -> bool:
        """用户层根据上下文注入"""
        return context.user_id is not None or context.task_description is not None


class AgentsTemplate(BasePromptTemplate):
    """AGENTS 提示词模板 - 多 Agent 协作规则"""

    DEFAULT_AGENTS = """## 多 Agent 协作规则 (AGENTS)

### 协作原则
1. 适度调用 - 避免过度使用 Agent
2. 权责清晰 - 每个 Agent 有明确职责
3. 信息共享 - 通过共享上下文协调

### Agent 类型
{agent_types}

### 通信协议
- 任务传递使用结构化描述
- 错误处理遵循统一规范
- 结果返回保持格式一致
"""

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path
        self._agent_registry: dict[str, dict] = {}

    @property
    def level(self) -> PromptLevel:
        return PromptLevel.AGENTS

    def register_agent(self, name: str, role: str, capabilities: list[str]):
        """注册 Agent"""
        self._agent_registry[name] = {
            "role": role,
            "capabilities": capabilities,
        }

    def render(self, context: PromptContext) -> str:
        if not self._agent_registry:
            return self.DEFAULT_AGENTS.format(
                agent_types="- 默认: 通用任务处理"
            )

        agent_types = []
        for name, info in self._agent_registry.items():
            caps = ", ".join(info["capabilities"])
            agent_types.append(f"- {name} ({info['role']}): {caps}")

        return self.DEFAULT_AGENTS.format(
            agent_types="\n".join(agent_types)
        )

    def should_inject(self, context: PromptContext) -> bool:
        """多 Agent 场景注入"""
        return len(self._agent_registry) > 0


class HeartbeatTemplate(BasePromptTemplate):
    """HEARTBEAT 提示词模板 - 周期性任务触发规则"""

    def __init__(self, template_path: Optional[Path] = None):
        self.template_path = template_path
        self._scheduled_tasks: list[dict] = []
        self._last_heartbeat: Optional[str] = None

    @property
    def level(self) -> PromptLevel:
        return PromptLevel.HEARTBEAT

    def schedule_task(self, task: str, interval_seconds: int, enabled: bool = True):
        """调度周期性任务"""
        self._scheduled_tasks.append({
            "task": task,
            "interval": interval_seconds,
            "enabled": enabled,
        })

    def render(self, context: PromptContext) -> str:
        parts = ["## 周期性任务 (HEARTBEAT)"]

        if self._last_heartbeat:
            parts.append(f"\n上次心跳: {self._last_heartbeat}")

        if self._scheduled_tasks:
            parts.append("\n### 已调度任务")
            for t in self._scheduled_tasks:
                if t["enabled"]:
                    parts.append(f"- {t['task']} (每 {t['interval']}秒)")

        return "\n".join(parts)

    def should_inject(self, context: PromptContext) -> bool:
        """有调度任务时注入"""
        return len(self._scheduled_tasks) > 0


class MultiLevelPromptInjector:
    """多级提示词注入器

    负责按优先级顺序注入多级提示词，
    支持动态加载和条件触发。
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path("prompts")
        self._templates: dict[PromptLevel, BasePromptTemplate] = {}
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """初始化默认模板"""
        # 加载 SOUL
        soul_path = self.prompts_dir / "SOUL.md"
        self._templates[PromptLevel.SOUL] = SoulPromptTemplate(
            template_path=soul_path if soul_path.exists() else None
        )

        # 加载 IDENTITY
        identity_path = self.prompts_dir / "IDENTITY.md"
        self._templates[PromptLevel.IDENTITY] = IdentityPromptTemplate(
            template_path=identity_path if identity_path.exists() else None
        )

        # 加载 USER
        user_path = self.prompts_dir / "USER.md"
        self._templates[PromptLevel.USER] = UserContextTemplate(
            template_path=user_path if user_path.exists() else None
        )

        # 加载 AGENTS
        agents_path = self.prompts_dir / "AGENTS.md"
        self._templates[PromptLevel.AGENTS] = AgentsTemplate(
            template_path=agents_path if agents_path.exists() else None
        )

        # 加载 HEARTBEAT
        heartbeat_path = self.prompts_dir / "HEARTBEAT.md"
        self._templates[PromptLevel.HEARTBEAT] = HeartbeatTemplate(
            template_path=heartbeat_path if heartbeat_path.exists() else None
        )

    def inject(self, context: PromptContext) -> str:
        """按优先级注入所有适用的提示词"""
        # 按优先级排序
        levels_ordered = [
            PromptLevel.SOUL,
            PromptLevel.IDENTITY,
            PromptLevel.USER,
            PromptLevel.AGENTS,
            PromptLevel.HEARTBEAT,
        ]

        prompt_parts = []
        for level in levels_ordered:
            template = self._templates.get(level)
            if template and template.should_inject(context):
                rendered = template.render(context)
                prompt_parts.append(rendered)

        return "\n\n".join(prompt_parts)

    def get_template(self, level: PromptLevel) -> Optional[BasePromptTemplate]:
        """获取指定层级的模板"""
        return self._templates.get(level)

    def update_template(self, level: PromptLevel, template: BasePromptTemplate):
        """更新指定层级的模板"""
        self._templates[level] = template

    def load_from_directory(self, directory: Path):
        """从目录加载所有提示词模板"""
        if not directory.exists():
            logger.warning(f"Prompts directory not found: {directory}")
            return

        for level in PromptLevel:
            template_file = directory / f"{level.value.upper()}.md"
            if template_file.exists():
                logger.info(f"Loading {level.value} template from {template_file}")
```

#### 3.1.2 与现有 Agent 集成

```python
# src/agents/young_agent.py (修改)
class YoungAgent:
    def __init__(self, config: AgentConfig):
        # ... existing initialization ...

        # 初始化多级提示词注入器
        prompts_dir = config.get("prompts_dir", "prompts")
        self._prompt_injector = MultiLevelPromptInjector(Path(prompts_dir))

    async def run(self, task: str) -> AgentResult:
        # 构建提示词上下文
        context = PromptContext(
            user_id=self._user_id,
            session_id=self._session_id,
            task_description=task,
            workspace_path=self._workspace,
        )

        # 注入多级提示词
        system_prompt = self._prompt_injector.inject(context)

        # 执行任务
        response = await self._llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task},
            ]
        )

        return AgentResult(response=response.content)
```

### 3.2 Heartbeat 服务

#### 3.2.1 架构设计

```python
# src/agents/heartbeat/service.py
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class HeartbeatPhase(Enum):
    """心跳循环的各个阶段"""
    INFO_INTAKE = "info_intake"      # 信息摄入
    VALUE_JUDGMENT = "value_judgment"  # 价值判断
    KNOWLEDGE_OUTPUT = "knowledge_output"  # 知识输出
    SELF_REFLECTION = "self_reflection"  # 自我反思
    SKILL_CHECK = "skill_check"      # 技能检查
    SYSTEM_NOTIFY = "system_notify"  # 系统通知


@dataclass
class HeartbeatConfig:
    """心跳配置"""
    interval_seconds: int = 14400  # 默认4小时
    enabled: bool = True
    phases_enabled: list[HeartbeatPhase] = field(
        default_factory=lambda: [
            HeartbeatPhase.INFO_INTAKE,
            HeartbeatPhase.VALUE_JUDGMENT,
            HeartbeatPhase.KNOWLEDGE_OUTPUT,
            HeartbeatPhase.SELF_REFLECTION,
            HeartbeatPhase.SKILL_CHECK,
        ]
    )
    max_info_items: int = 5


@dataclass
class HeartbeatResult:
    """心跳执行结果"""
    phase: HeartbeatPhase
    success: bool
    message: str
    data: dict = field(default_factory=dict)
    duration_ms: int = 0


class HeartbeatService:
    """Heartbeat 服务 - 自主驱动的定期任务执行

    实现 OpenClaw/Nanobot 风格的周期性自我检查和学习流程，
    使 Agent 能够主动发现问题、吸收新知识、保持技能更新。
    """

    def __init__(
        self,
        config: Optional[HeartbeatConfig] = None,
        agent=None,  # 关联的 Agent 实例
    ):
        self.config = config or HeartbeatConfig()
        self.agent = agent
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_run: Optional[datetime] = None

        # 回调函数
        self._callbacks: dict[HeartbeatPhase, list[Callable]] = {
            phase: [] for phase in HeartbeatPhase
        }

        # 统计
        self._stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "phase_stats": {
                phase.value: {"success": 0, "failure": 0}
                for phase in HeartbeatPhase
            },
        }

    def register_callback(self, phase: HeartbeatPhase, callback: Callable):
        """注册相位回调"""
        self._callbacks[phase].append(callback)

    async def start(self):
        """启动心跳服务"""
        if self._running:
            logger.warning("Heartbeat service already running")
            return

        if not self.config.enabled:
            logger.info("Heartbeat service disabled")
            return

        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(
            f"Heartbeat service started with interval={self.config.interval_seconds}s"
        )

    async def stop(self):
        """停止心跳服务"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Heartbeat service stopped")

    async def trigger_now(self):
        """立即触发一次心跳"""
        logger.info("Manually triggering heartbeat")
        await self._heartbeat_cycle()

    async def _heartbeat_loop(self):
        """心跳主循环"""
        while self._running:
            try:
                await self._heartbeat_cycle()
                self._last_run = datetime.now()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat cycle error: {e}")
                self._stats["failed_runs"] += 1

            await asyncio.sleep(self.config.interval_seconds)

    async def _heartbeat_cycle(self):
        """执行一次完整的心跳循环"""
        start_time = datetime.now()
        logger.info("Starting heartbeat cycle")

        for phase in self.config.phases_enabled:
            if not self._running:
                break

            result = await self._execute_phase(phase)
            self._update_stats(phase, result.success)

            if result.success:
                logger.debug(f"Phase {phase.value} completed: {result.message}")
            else:
                logger.warning(f"Phase {phase.value} failed: {result.message}")

        self._stats["total_runs"] += 1

        duration = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Heartbeat cycle completed in {duration:.2f}ms")

    async def _execute_phase(self, phase: HeartbeatPhase) -> HeartbeatResult:
        """执行单个心跳阶段"""
        start_time = datetime.now()
        callbacks = self._callbacks.get(phase, [])

        if not callbacks:
            # 使用默认逻辑
            return await self._default_phase_logic(phase)

        # 执行所有注册的回调
        results = []
        for callback in callbacks:
            try:
                result = await callback()
                results.append(result)
            except Exception as e:
                logger.error(f"Callback error in {phase.value}: {e}")
                return HeartbeatResult(
                    phase=phase,
                    success=False,
                    message=f"Callback error: {e}",
                    duration_ms=int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    ),
                )

        return results[-1] if results else HeartbeatResult(
            phase=phase,
            success=True,
            message="No callbacks registered",
            duration_ms=int(
                (datetime.now() - start_time).total_seconds() * 1000
            ),
        )

    async def _default_phase_logic(self, phase: HeartbeatPhase) -> HeartbeatResult:
        """各阶段的默认逻辑实现"""
        # 信息摄入
        if phase == HeartbeatPhase.INFO_INTAKE:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="Info intake: Checking external sources",
            )

        # 价值判断
        if phase == HeartbeatPhase.VALUE_JUDGMENT:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="Value judgment: Pending implementation",
            )

        # 知识输出
        if phase == HeartbeatPhase.KNOWLEDGE_OUTPUT:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="Knowledge output: Pending implementation",
            )

        # 自我反思
        if phase == HeartbeatPhase.SELF_REFLECTION:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="Self reflection: Analyzing recent performance",
            )

        # 技能检查
        if phase == HeartbeatPhase.SKILL_CHECK:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="Skill check: Verifying available skills",
            )

        # 系统通知
        if phase == HeartbeatPhase.SYSTEM_NOTIFY:
            return HeartbeatResult(
                phase=phase,
                success=True,
                message="System notify: No pending notifications",
            )

        return HeartbeatResult(
            phase=phase,
            success=False,
            message=f"Unknown phase: {phase}",
        )

    def _update_stats(self, phase: HeartbeatPhase, success: bool):
        """更新统计信息"""
        if success:
            self._stats["successful_runs"] += 1
            self._stats["phase_stats"][phase.value]["success"] += 1
        else:
            self._stats["failed_runs"] += 1
            self._stats["phase_stats"][phase.value]["failure"] += 1

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self._stats,
            "running": self._running,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "interval_seconds": self.config.interval_seconds,
        }

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running
```

### 3.3 分层记忆系统

#### 3.3.1 架构设计

```python
# src/agents/memory/hierarchical.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """记忆层级"""
    WORKING = "working"      # 工作记忆 - 当前任务上下文
    EPISODIC = "episodic"   # 情景记忆 - 近期交互历史
    SEMANTIC = "semantic"   # 语义记忆 - 长期知识存储


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    content: Any
    tier: MemoryTier
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance: float = 0.5  # 0-1 重要性评分
    metadata: dict = field(default_factory=dict)


class BaseMemoryStore(ABC):
    """记忆存储基类"""

    @abstractmethod
    def store(self, entry: MemoryEntry) -> None:
        """存储记忆"""
        pass

    @abstractmethod
    def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """检索记忆"""
        pass

    @abstractmethod
    def consolidate(self) -> int:
        """记忆整合 - 返回整合的记忆数量"""
        pass


class WorkingMemory(BaseMemoryStore):
    """工作记忆 - 当前任务上下文

    存储当前任务的短期信息，
    采用 LRU 缓存策略。
    """

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._store: dict[str, MemoryEntry] = {}
        self._access_order: list[str] = []

    def store(self, entry: MemoryEntry) -> None:
        """存储到工作记忆"""
        if entry.id in self._store:
            # 更新已存在的条目
            self._store[entry.id] = entry
        else:
            # 添加新条目
            if len(self._store) >= self.max_size:
                # 驱逐最老的条目
                oldest_id = self._access_order.pop(0)
                del self._store[oldest_id]

            self._store[entry.id] = entry
            self._access_order.append(entry.id)

    def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """检索工作记忆"""
        # 简单实现：返回所有条目，按访问时间排序
        entries = list(self._store.values())
        entries.sort(key=lambda e: e.accessed_at, reverse=True)
        return entries[:limit]

    def consolidate(self) -> int:
        """工作记忆不需要整合"""
        return 0

    def get_current_context(self) -> list[MemoryEntry]:
        """获取当前任务上下文"""
        return list(self._store.values())


class EpisodicMemory(BaseMemoryStore):
    """情景记忆 - 近期交互历史

    存储最近的交互历史，
    支持时间窗口过期。
    """

    def __init__(self, max_entries: int = 1000, ttl_hours: int = 24):
        self.max_entries = max_entries
        self.ttl_hours = ttl_hours
        self._store: dict[str, MemoryEntry] = {}

    def store(self, entry: MemoryEntry) -> None:
        """存储情景记忆"""
        entry.tier = MemoryTier.EPISODIC
        self._store[entry.id] = entry

        # 超过上限时删除最老的
        if len(self._store) > self.max_entries:
            oldest = min(
                self._store.values(),
                key=lambda e: e.created_at
            )
            del self._store[oldest.id]

    def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """检索情景记忆"""
        now = datetime.now()
        valid_entries = [
            e for e in self._store.values()
            if (now - e.created_at).total_seconds() / 3600 < self.ttl_hours
        ]
        valid_entries.sort(key=lambda e: e.created_at, reverse=True)
        return valid_entries[:limit]

    def consolidate(self) -> int:
        """情景记忆整合"""
        now = datetime.now()
        expired_ids = [
            e.id for e in self._store.values()
            if (now - e.created_at).total_seconds() / 3600 >= self.ttl_hours
        ]

        for id in expired_ids:
            del self._store[id]

        return len(expired_ids)

    def get_recent_interactions(self, limit: int = 10) -> list[MemoryEntry]:
        """获取最近的交互"""
        entries = list(self._store.values())
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries[:limit]


class SemanticMemory(BaseMemoryStore):
    """语义记忆 - 长期知识存储

    使用向量相似度进行检索，
    支持语义搜索。
    """

    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self._store: dict[str, MemoryEntry] = {}
        # 简化实现：使用关键词匹配
        self._keywords_index: dict[str, set[str]] = {}

    def store(self, entry: MemoryEntry) -> None:
        """存储语义记忆"""
        entry.tier = MemoryTier.SEMANTIC
        self._store[entry.id] = entry

        # 更新关键词索引
        keywords = self._extract_keywords(str(entry.content))
        for kw in keywords:
            if kw not in self._keywords_index:
                self._keywords_index[kw] = set()
            self._keywords_index[kw].add(entry.id)

    def _extract_keywords(self, text: str) -> set[str]:
        """提取关键词"""
        # 简化实现
        words = text.lower().split()
        return set(w for w in words if len(w) > 3)

    def retrieve(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """检索语义记忆"""
        query_keywords = self._extract_keywords(query.lower())
        if not query_keywords:
            return []

        # 找出包含最多关键词的条目
        scores: dict[str, int] = {}
        for kw in query_keywords:
            if kw in self._keywords_index:
                for entry_id in self._keywords_index[kw]:
                    scores[entry_id] = scores.get(entry_id, 0) + 1

        # 排序
        sorted_ids = sorted(scores.keys(), key=lambda id: scores[id], reverse=True)
        return [self._store[id] for id in sorted_ids[:limit] if id in self._store]

    def consolidate(self) -> int:
        """语义记忆整合 - 可将重要情景记忆提升为语义记忆"""
        # 简化实现：返回 0
        return 0


class HierarchicalMemory:
    """分层记忆系统

    实现 Working → Episodic → Semantic 三层记忆架构，
    支持记忆的自动整合与提升。
    """

    def __init__(
        self,
        working_size: int = 100,
        episodic_max: int = 1000,
        semantic_max: int = 10000,
    ):
        self.working = WorkingMemory(max_size=working_size)
        self.episodic = EpisodicMemory(max_entries=episodic_max)
        self.semantic = SemanticMemory(max_entries=semantic_max)

    def store(self, entry: MemoryEntry, tier: Optional[MemoryTier] = None):
        """存储记忆到指定层级"""
        target_tier = tier or self._choose_tier(entry)

        if target_tier == MemoryTier.WORKING:
            self.working.store(entry)
        elif target_tier == MemoryTier.EPISODIC:
            self.episodic.store(entry)
        else:
            self.semantic.store(entry)

    def _choose_tier(self, entry: MemoryEntry) -> MemoryTier:
        """选择适当的记忆层级"""
        if entry.importance > 0.8:
            return MemoryTier.SEMANTIC
        elif entry.importance > 0.5:
            return MemoryTier.EPISODIC
        else:
            return MemoryTier.WORKING

    def retrieve(self, query: str, tier: Optional[MemoryTier] = None, limit: int = 5) -> list[MemoryEntry]:
        """检索记忆"""
        if tier:
            store = self._get_store(tier)
            return store.retrieve(query, limit) if store else []

        # 跨层级检索
        results = []
        for mem_tier in MemoryTier:
            store = self._get_store(mem_tier)
            if store:
                results.extend(store.retrieve(query, limit))

        # 去重并排序
        seen = set()
        unique_results = []
        for entry in results:
            if entry.id not in seen:
                seen.add(entry.id)
                unique_results.append(entry)

        return unique_results[:limit]

    def _get_store(self, tier: MemoryTier) -> Optional[BaseMemoryStore]:
        """获取指定层级的存储"""
        if tier == MemoryTier.WORKING:
            return self.working
        elif tier == MemoryTier.EPISODIC:
            return self.episodic
        elif tier == MemoryTier.SEMANTIC:
            return self.semantic
        return None

    def consolidate(self) -> int:
        """执行记忆整合"""
        total = 0
        total += self.episodic.consolidate()
        total += self.semantic.consolidate()
        return total

    def get_stats(self) -> dict:
        """获取记忆统计"""
        return {
            "working": len(self.working._store),
            "episodic": len(self.episodic._store),
            "semantic": len(self.semantic._store),
        }
```

### 3.4 自进化能力集成

```python
# src/agents/evolution/self_improver.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningRecord:
    """学习记录"""
    task_id: str
    success: bool
    feedback: str
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: dict = field(default_factory=dict)


class SelfImprover:
    """自进化器

    负责从任务执行中学习，
    动态调整 Agent 行为。
    """

    def __init__(self, memory=None):
        self.memory = memory
        self._learning_records: list[LearningRecord] = []
        self._skill_weights: dict[str, float] = {}

    def record_outcome(self, record: LearningRecord):
        """记录任务结果"""
        self._learning_records.append(record)

        # 更新技能权重
        if record.success:
            for skill in record.metrics.get("skills_used", []):
                self._skill_weights[skill] = self._skill_weights.get(skill, 0.5) + 0.1
        else:
            for skill in record.metrics.get("skills_used", []):
                self._skill_weights[skill] = max(0.1, self._skill_weights.get(skill, 0.5) - 0.1)

    def get_recommended_skills(self, task_type: str) -> list[str]:
        """获取推荐技能"""
        # 简化实现：返回权重最高的技能
        sorted_skills = sorted(
            self._skill_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [s[0] for s in sorted_skills[:3]]

    def analyze_failures(self) -> dict:
        """分析失败模式"""
        failures = [r for r in self._learning_records if not r.success]
        if not failures:
            return {"pattern": "no_failures"}

        # 简化分析
        return {
            "failure_count": len(failures),
            "recent_failures": failures[-5:],
        }
```

---

## 四、实施计划

### 4.1 分阶段实施

```
Phase 1 (Week 1-2)     Phase 2 (Week 2-3)     Phase 3 (Week 3-4)     Phase 4 (Week 4-5)
┌─────────────┐        ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  多级提示词  │───────▶│  Heartbeat  │────────▶│  分层记忆  │────────▶│   完整集成  │
│  注入器     │        │   服务      │         │   系统     │         │   与优化    │
└─────────────┘        └─────────────┘         └─────────────┘         └─────────────┘
       │                      │                     │                      │
       ▼                      ▼                     ▼                      ▼
  5级提示词模板          周期性任务触发         三层记忆架构          完整自进化
```

### 4.2 任务分解

#### Phase 1: 多级提示词系统 (Week 1-2)

| 任务 | 文件 | 描述 | 状态 |
|------|------|------|------|
| 1.1 | `src/agents/prompts/__init__.py` | 创建提示词模块 | ⬜ |
| 1.2 | `src/agents/prompts/multilevel.py` | 多级注入器实现 | ⬜ |
| 1.3 | `prompts/SOUL.md` | SOUL 模板 | ⬜ |
| 1.4 | `prompts/IDENTITY.md` | IDENTITY 模板 | ⬜ |
| 1.5 | `prompts/USER.md` | USER 模板 | ⬜ |
| 1.6 | `prompts/AGENTS.md` | AGENTS 模板 | ⬜ |
| 1.7 | `prompts/HEARTBEAT.md` | HEARTBEAT 模板 | ⬜ |
| 1.8 | `src/agents/young_agent.py` | 集成到 Agent | ⬜ |

#### Phase 2: Heartbeat 服务 (Week 2-3)

| 任务 | 文件 | 描述 | 状态 |
|------|------|------|------|
| 2.1 | `src/agents/heartbeat/__init__.py` | 创建 Heartbeat 模块 | ⬜ |
| 2.2 | `src/agents/heartbeat/service.py` | Heartbeat 服务实现 | ⬜ |
| 2.3 | `src/agents/heartbeat/phases.py` | 各阶段默认逻辑 | ⬜ |
| 2.4 | `src/agents/young_agent.py` | 集成 Heartbeat | ⬜ |
| 2.5 | `tests/test_heartbeat.py` | 单元测试 | ⬜ |

#### Phase 3: 分层记忆系统 (Week 3-4)

| 任务 | 文件 | 描述 | 状态 |
|------|------|------|------|
| 3.1 | `src/agents/memory/__init__.py` | 创建记忆模块 | ⬜ |
| 3.2 | `src/agents/memory/hierarchical.py` | 分层记忆实现 | ⬜ |
| 3.3 | `src/agents/memory/consolidator.py` | 记忆整合器 | ⬜ |
| 3.4 | `src/agents/young_agent.py` | 集成记忆系统 | ⬜ |
| 3.5 | `tests/test_memory.py` | 单元测试 | ⬜ |

#### Phase 4: 完整集成与优化 (Week 4-5)

| 任务 | 文件 | 描述 | 状态 |
|------|------|------|------|
| 4.1 | `src/agents/evolution/__init__.py` | 创建自进化模块 | ⬜ |
| 4.2 | `src/agents/evolution/self_improver.py` | 自进化器实现 | ⬜ |
| 4.3 | `src/agents/young_agent.py` | 完整集成 | ⬜ |
| 4.4 | `tests/test_integration.py` | 集成测试 | ⬜ |
| 4.5 | 性能优化与文档 | 最终完善 | ⬜ |

---

## 五、验证计划

### 5.1 单元测试

```bash
# 测试多级提示词注入
python3 -c "
from src.agents.prompts.multilevel import MultiLevelPromptInjector, PromptContext

injector = MultiLevelPromptInjector()
context = PromptContext(
    user_id='test_user',
    task_description='Test task'
)
result = injector.inject(context)
print('SOUL' in result)
print('USER' in result)
print(len(result) > 0)
"

# 测试 Heartbeat 服务
python3 -c "
import asyncio
from src.agents.heartbeat.service import HeartbeatService, HeartbeatConfig

async def test():
    config = HeartbeatConfig(interval_seconds=1)
    service = HeartbeatService(config)
    await service.start()
    await asyncio.sleep(2)
    await service.stop()
    stats = service.get_stats()
    print(f'Total runs: {stats[\"total_runs\"]}')

asyncio.run(test())
"

# 测试分层记忆
python3 -c "
from src.agents.memory.hierarchical import HierarchicalMemory, MemoryEntry, MemoryTier
import time

memory = HierarchicalMemory()
entry = MemoryEntry(
    id='test1',
    content='Test memory',
    tier=MemoryTier.WORKING,
    importance=0.8
)
memory.store(entry)
results = memory.retrieve('Test')
print(f'Retrieved: {len(results)} entries')
"
```

### 5.2 集成测试

```bash
# 完整集成测试
python3 -c "
import asyncio
from src.agents.young_agent import YoungAgent, AgentConfig

async def test():
    config = AgentConfig(
        prompts_dir='prompts',
        heartbeat_enabled=True,
        heartbeat_interval=3600,
        memory_enabled=True,
    )
    agent = YoungAgent(config)

    # 测试多级提示词
    prompt = agent._prompt_injector.inject(
        PromptContext(task_description='Hello')
    )
    print(f'Prompt length: {len(prompt)}')

    # 测试 Heartbeat
    await agent.heartbeat.start()
    stats = agent.heartbeat.get_stats()
    print(f'Heartbeat running: {stats[\"running\"]}')
    await agent.heartbeat.stop()

asyncio.run(test())
"
```

---

## 六、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 提示词冲突 | 行为异常 | 优先级机制与测试覆盖 |
| Heartbeat 资源占用 | 性能下降 | 可配置间隔与后台运行 |
| 记忆存储膨胀 | 内存耗尽 | 自动清理与分层策略 |
| 集成破坏现有功能 | 功能回退 | 完整测试覆盖 |

---

## 七、里程碑

| 周 | 里程碑 | 交付物 | 状态 |
|----|--------|--------|------|
| Week 1 | Alpha | 多级提示词注入器可用 | ⬜ |
| Week 2 | Beta | 完整 5 级提示词系统 | ⬜ |
| Week 3 | RC1 | Heartbeat 服务就绪 | ⬜ |
| Week 4 | RC2 | 分层记忆系统完成 | ⬜ |
| Week 5 | GA | 完整自进化能力 | ⬜ |

---

## 八、总结

### 核心理念

1. **渐进式交付** - 每两周可工作的代码
2. **模块化设计** - 独立可测试的组件
3. **向后兼容** - 不破坏现有功能
4. **可配置** - 灵活适应不同场景

### 关键文件

| 文件 | 操作 |
|------|------|
| `src/agents/prompts/multilevel.py` | 新建 |
| `src/agents/heartbeat/service.py` | 新建 |
| `src/agents/memory/hierarchical.py` | 新建 |
| `src/agents/evolution/self_improver.py` | 新建 |
| `src/agents/young_agent.py` | 修改：集成新模块 |
| `prompts/*.md` | 新建：5 个模板文件 |
| `tests/test_*.py` | 新建：单元测试 |

---

*计划生成时间: 2026-03-14*
*方法论: 基于 OpenClaw/Nanobot 最佳实践*
