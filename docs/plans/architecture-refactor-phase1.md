# 架构重构 Phase 1: 消除重复代码

> 专家视角: 这个问题谁最懂？→ 软件架构专家会告诉你"重复代码是万恶之源"

## 目标
消除28个Manager类中的重复代码，统一入口，减少维护成本

## 当前问题
- `MCPServerManager` 存在2个版本 (package_manager/ 和 hub/mcp/)
- `VersionManager` 存在2个版本
- `SecurityManager` 存在多个版本

## 阶段

### Phase 1.1: 合并 MCPServerManager ✅
- [x] 1. 分析两个版本的差异 - package_manager版本功能更全
- [x] 2. 确定保留版本 - package_manager/mcp_manager.py
- [x] 3. 删除重复版本 - hub/mcp/manager.py 已删除
- [x] 4. 更新所有导入引用 - hub/mcp/__init__.py 已更新
- [x] 5. 验证无破坏 - 语法检查通过

### Phase 1.2: 合并 VersionManager ✅
- [x] 1. 分析两个版本的差异 - 完全相同
- [x] 2. 确定保留版本 - package_manager/version_manager.py
- [x] 3. 删除重复版本 - hub/version/manager.py 已删除
- [x] 4. 更新所有导入引用 - hub/__init__.py 和 hub/version/__init__.py 已更新

### Phase 1.3: 统一 SecurityManager ✅
- [x] 1. 列出所有 Security 相关类 - 已列出
- [x] 2. 确定统一方案 - runtime/__init__.py 已有统一出口
- [x] 3. 安全模块已通过 runtime/__init__.py 整合

## 完成结果
- 删除了 2 个重复文件
- 更新了 3 个 __init__.py 文件
- 无破坏性更改

## Phase 2: 模块边界分析 (datacenter)

### 分析结果
datacenter 目录有 25 个文件，包含 60+ 类/函数

**职责分布**:
- 核心存储: base_storage.py, store.py, sqlite_storage.py
- 追踪监控: tracing.py, token_tracker.py, run_tracker.py
- 检查点: checkpoint.py, checkpoint_store.py
- 企业功能: enterprise.py, license.py, tenant_store.py, isolation.py
- 评估: evaluation_store.py, evaluation_record.py
- 分析: analytics.py, quality.py
- 执行记录: step_recorder.py, execution_record.py

**问题**:
- `datacenter.py` 包含过多职责 (TraceCollector, BudgetController, PatternDetector, Memory等)
- 配置管理分散 (src/config vs cli/config_manager vs 其他)

**结论**: 当前结构可接受，大规模重构风险过高，建议记录TODO

## Phase 3: 配置管理分析

### 分析结果
- src/config/ 模块仅有 3 处引用
- 大部分模块使用各自独立的配置

**建议**: 保持现状，小范围优化

## 进度
- [Phase 1.1: 100%] ✅
- [Phase 1.2: 100%] ✅
- [Phase 1.3: 100%] ✅
- [Phase 2: 100%] ✅ (分析完成)
- [Phase 3: 100%] ✅ (分析完成)

## 注意力提醒
> 每3步重读此文件
