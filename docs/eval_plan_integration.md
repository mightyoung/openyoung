# 评估计划集成计划

## 目标
将评估计划生成器 (EvalPlanner) 集成到任务评估流程中，使开放式任务也能获得有效评估分数

## 问题背景
- TaskCompletionEval 需要 expected_result 参数
- 开放式任务没有明确的 expected_result，导致评分总是 0
- EvalPlanner 已存在但未与 TaskCompletionEval 集成

## 实现方案

### Phase 1: 扩展 TaskCompletionEval 支持评估计划
- [x] 1.1 在 TaskCompletionEval 添加 evaluate_with_plan() 方法
- [x] 1.2 添加基于 EvalPlan 的动态评估逻辑
- [x] 1.3 测试 evaluate_with_plan() 功能 ✅ 3 tests passed

### Phase 2: 集成到 EvaluationHub
- [x] 2.1 在 EvaluationHub 添加 generate_plan() 便捷方法
- [x] 2.2 修改 evaluate() 支持传入 EvalPlan
- [x] 2.3 测试 Hub 集成 ✅ 12 tests passed

### Phase 3: 集成到 YoungAgent
- [x] 3.1 YoungAgent 已包含评估计划生成逻辑
- [x] 3.2 run() 方法已集成评估计划
- [x] 3.3 基于计划执行评估（智能匹配）
- [x] 3.4 端到端测试 ✅ 已实现

---

## 当前状态
- EvalPlanner: ✅ 已实现
- TaskCompletionEval: ✅ evaluate_with_plan() 已添加
- EvaluationHub: ✅ generate_plan() 和 eval_plan 支持
- YoungAgent: ✅ 已有完整集成

## 实现细节 (YoungAgent)
- 使用 EvalPlanner 生成评估计划
- 基于 success_criteria 智能匹配评估
- 特殊处理 web_scraping 等任务类型
- 检查预期输出文件是否存在
- 合并评分生成最终 quality_score
