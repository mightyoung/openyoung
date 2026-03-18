# EventBus 与 Heartbeat 合并计划

## 目标
1. 删除 heartbeat 重复代码，迁移到 core
2. 保留并增强 agent 知识和经验沉淀功能

## 当前问题分析

### 重复的 EventBus
```
src/core/events.py              → 基础实现，简洁
src/agents/heartbeat/event_bus.py → 高级实现（优先级队列）
```

### 重复的 Heartbeat
```
src/skills/heartbeat.py        → 完整实现，7阶段
src/agents/heartbeat/hybrid.py → 简化版，3阶段
```

### 知识沉淀机制
```
src/skills/learnings.py        → LearningsManager (文件存储)
```

## 阶段计划

### Phase 1: 合并 EventBus (P0)

#### 1.1 分析差异
- core/events.py: EventType枚举，简单同步/异步处理
- heartbeat/event_bus.py: string事件，优先级队列，异步处理循环

#### 1.2 设计统一方案
保留 heartbeat 版本的高级功能：
- [ ] 添加 `EventPriority` 枚举 (LOW, NORMAL, HIGH, CRITICAL)
- [ ] 添加异步处理队列
- [ ] 保留事件历史记录

#### 1.3 迁移步骤
- [ ] 更新 `src/core/events.py` 添加优先级和队列功能
- [ ] 更新 `src/agents/heartbeat/event_bus.py` 导入自 core
- [ ] 更新 `src/core/events.py` __all__ 导出

### Phase 2: 合并 Heartbeat (P0)

#### 2.1 设计统一架构
保留 skills/heartbeat.py 的完整功能：
- 7 个心跳阶段
- 外部信息源获取
- 统计功能

整合 agents/heartbeat 的特性：
- 事件驱动触发
- 与 EventBus 集成

#### 2.2 迁移步骤
- [ ] 将 `src/skills/heartbeat.py` 移至 `src/core/heartbeat.py`
- [ ] 更新 EventBus 集成
- [ ] 更新 `src/skills/__init__.py` 导入
- [ ] 删除 `src/agents/heartbeat/hybrid.py`

### Phase 3: 增强知识沉淀 (P1)

#### 3.1 扩展 Event 添加知识相关事件
```python
class EventType(Enum):
    # ... 现有事件 ...

    # 知识沉淀
    KNOWLEDGE_STORED = "knowledge_stored"
    EXPERIENCE_COLLECTED = "experience_collected"
    PATTERN_DETECTED = "pattern_detected"
```

#### 3.2 集成 LearningsManager
- [ ] 将 LearningsManager 集成到 Heartbeat
- [ ] 阶段执行结果自动记录为学习

#### 3.3 添加持久化增强
- [ ] 支持向量存储 (已有 src/memory/vector_store.py)
- [ ] 支持经验检索

### Phase 4: 集成到 Agent 生命周期 (P2)

#### 4.1 创建 Agent 生命周期集成
- [ ] 在 Agent 启动时初始化 Heartbeat
- [ ] 任务完成时触发事件
- [ ] 配置 Heartbeat 回调

## 验收标准

- [x] 无重复代码 (EventBus 唯一，Heartbeat 唯一)
- [x] EventBus 保留优先级队列功能
- [x] Heartbeat 保留 7 阶段功能 (已合并)
- [x] EventBus 集成完成（知识沉淀事件已支持）
- [x] 知识沉淀正常工作 (LearningsManager + VectorStore 集成)
- [x] 阶段结果自动记录为学习
- [x] 向量存储支持（语义搜索）
- [x] 所有导入正常工作
- [x] Agent 生命周期集成完成
  - [x] YoungAgent 初始化时自动创建 Heartbeat
  - [x] 任务开始时触发 TASK_STARTED 事件
  - [x] 任务完成时触发 TASK_COMPLETED 事件
  - [x] 任务失败时触发 ERROR 事件
  - [x] 支持配置启用/禁用 Heartbeat

## 进度

- [Phase 1: 100%] ✅ EventBus 合并完成
  - [x] 添加 EventPriority 枚举
  - [x] 添加优先级订阅支持
  - [x] 添加异步队列处理
  - [x] 添加知识沉淀事件类型
  - [x] 添加 SystemEvents 兼容类
  - [x] 更新 heartbeat/event_bus.py 导入 core
  - [x] 验证所有导入正常工作
- [Phase 2: 100%] ✅ Heartbeat 合并完成
  - [x] 创建 src/core/heartbeat.py（完整 7 阶段 + EventBus 集成）
  - [x] 更新 src/core/__init__.py 导出
  - [x] 更新 src/skills/__init__.py 从 core 导入
  - [x] 删除 agents/heartbeat/hybrid.py（简化版）
  - [x] 验证所有导入正常工作
- [Phase 3: 100%] ✅ 知识沉淀增强完成
  - [x] 创建 src/core/knowledge.py（整合 LearningsManager + VectorStore）
  - [x] 更新 Heartbeat 集成 KnowledgeManager
  - [x] 阶段执行结果自动记录为学习
  - [x] 心跳周期完成自动记录
  - [x] 向量存储支持（语义搜索）
  - [x] 更新 core 和 skills 导出
  - [x] 验证所有导入正常工作
- [Phase 4: 100%] ✅ Agent 生命周期集成完成
  - [x] 添加 EventBus 和 Heartbeat 到 YoungAgent 初始化
  - [x] 添加 TASK_STARTED 事件（在任务开始时触发）
  - [x] 添加 TASK_COMPLETED 事件（在任务完成时触发）
  - [x] 添加 ERROR 事件（在任务失败时触发）
  - [x] Heartbeat 调度器自动启动
  - [x] 配置支持（heartbeat_enabled, heartbeat_interval, heartbeat_config）
  - [x] 验证所有导入正常工作
