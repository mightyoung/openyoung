# Task Plan

## Goal
OpenYoung Agent 系统增强：实现 Always Skills 机制、技能发现、智能路由等功能

## Phases
- [x] Phase 1: Always Skills 核心机制实现
- [x] Phase 2: 技能加载与测试
- [x] Phase 3: 文档更新
- [x] Phase 4: 智能路由 (DevelopmentFlow 增强)
- [x] Phase 5: agent-import skill 更新 (智能路由优化)
- [x] Phase 6: CLI 命令与手册更新
- [x] Phase 7: 新模块实现 (AgentRetriever, AgentEvaluator, ImportManager)
- [x] Phase 8: TaskCompletionEval 改进 (评估计划生成)

## Current Phase
Phase 9 & 10: Agent 对比功能与质量徽章系统已完成

## Completed Tasks
- [x] 修复 young_agent.py 缩进错误
- [x] 添加 always_skills 字段到 AgentConfig (types.py)
- [x] 添加 always_skills 解析到 AgentLoader (main.py)
- [x] 修复 default.yaml skill 名称 (github-import)
- [x] 验证 skills 正确加载 (6个技能)
- [x] 测试 find-skills 和 summarize 技能
- [x] 更新 user-manual.md (v1.1.0)
- [x] 更新 configuration-manual.md (v1.1.0)
- [x] 实现 EvalPlanner 评估计划生成器 (planner.py)
- [x] 集成评估计划到 EvaluationHub (hub.py)
- [x] 实现 TaskCompletionEval.evaluate_with_plan() (task_eval.py)
- [x] 集成评估计划到 YoungAgent (young_agent.py)
- [x] 实现语义搜索 (AgentRetriever)
  - 添加 index_agent() 到 AgentRegistry
  - 实现真正的 _semantic_search() 使用 VectorStore
  - 实现 _hybrid_search() 混合关键词和向量搜索
  - 修复 JSON tags 解析问题
- [x] Agent 质量评估增强
  - 添加 RUNTIME 评估维度
  - 实现 _evaluate_runtime() 检查 agent 可加载性
  - 评估配置文件、主入口、skills/tools 配置
- [x] 使用追踪功能
  - 添加 track_usage() 到 AgentRegistry
  - 添加 get_usage_stats() 获取使用统计
  - 添加 agent stats CLI 命令

- [x] Registry 统一
  - 创建 base_registry.py 基类
  - AgentRegistry 继承 BaseRegistry
  - SubAgentRegistry 继承 BaseRegistry
  - TemplateRegistry 继承 BaseRegistry
  - 提取通用方法：discover_items, ensure_dir, track_usage, get_usage_stats, rate_item

- [x] LLM 意图理解
  - 创建 intent_analyzer.py
  - 实现 IntentType 枚举（code, review, research, debug 等）
  - 实现关键词快速匹配
  - 实现 LLM 深度分析（可选）
  - 集成到 agent search 命令
  - 添加 agent intent CLI 命令

## Decisions Made
- Always Skills 从 src/skills/ 目录加载
- Regular Skills 从 packages/ 目录加载
- 使用 skill.yaml 格式定义技能元数据

## Blockers
- None

## Next Steps

### Phase 9: Agent 对比功能
- [x] 创建 agent_compare.py 模块
- [x] 实现 compare_agents() 函数
- [x] 添加 agent compare CLI 命令

### Phase 10: 质量徽章系统
- [x] 创建 badge_system.py 模块
- [x] 实现徽章类型枚举
- [x] 实现趋势分数计算
- [x] 集成徽章显示到 agent list

### Phase 11: 版本管理
- [x] 创建 version_manager.py 模块
- [x] 实现 SemVer 解析
- [x] 实现版本历史
- [x] 添加 agent versions CLI 命令
