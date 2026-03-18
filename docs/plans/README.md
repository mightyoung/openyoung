# OpenYoung 任务索引

## 活跃计划 (核心3个)

1. **[CLI到WebUI迁移](./2026-03-17-cli-to-webui-migration-plan-v2.md)** - 全部完成 ✅
2. **[分层记忆系统实现](./hierarchical-memory-implementation-plan.md)** - 全部完成 ✅
3. **[记忆系统迁移计划](./memory-migration-plan.md)** - 新建

## 已完成归档

- 过去的技术设计文档请参考各 phase 计划文件

## 快速命令

```bash
# 查看当前任务
cat docs/plans/2026-03-17-cli-to-webui-migration-plan-v2.md | head -30

# 查看T1详情
sed -n '/## Layer 1/,/^## /p' docs/plans/2026-03-17-cli-to-webui-migration-plan-v2.md
```

## 进度

### Phase 1: 补全WebUI功能
- T1 (Chat流式输出): ✅ completed - 9 tests passed
  - T1.1: 已有session_api.py SSE实现 ✅
  - T1.2: api_client.py POST流式方法 ✅
  - T1.3: 2_Chat.py 真实流式输出 ✅
  - T1.4: 单元测试 ✅ (9 passed)
- T2 (Skills管理页面): ✅ completed - 6_Skills.py created
- T3 (评估运行功能): ✅ completed - 4_Dashboard扩展Run tab
- T4 (Settings完整CRUD): ✅ completed - YAML持久化+环境+Provider

### Phase 2: 统一架构
- T5 (统一API服务层): ✅ completed - routes目录+统一注册
- T6 (消除loader重复): ✅ completed - agents/loader.py别名
- T7 (消除session_cli重复): ✅ completed - 已标记弃用

### Phase 3: 精简代码
- T8 (删除config.py): ✅ completed - 已标记弃用
- T9 (删除config_manager.py): ✅ completed - 已标记弃用
- T10 (保留run轻量入口): ✅ completed - run+repl已存在
