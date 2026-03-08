# R2-3 DataCenter 存储统一设计

> 生成时间: 2026-03-07

## 背景

**问题**: DataCenter 模块存在多个数据模型，存储方式不统一

**现有模型**:
| 模型 | 文件 | 级别 | 存储方式 |
|------|------|------|----------|
| TraceRecord | datacenter.py | session | SQLite |
| RunRecord | run_tracker.py | run | BaseStorage |
| StepRecord | step_recorder.py | step | BaseStorage |
| VectorRecord | sqlite_storage.py | vector | 独立 SQLite |

**问题分析**:
1. 概念重复: session_id / run_id / step_id 层级不清晰
2. 存储分散: 4 个独立存储，无法跨表查询
3. 扩展困难: 新增字段需要修改多个地方

---

## 架构设计

### 方案: 统一 ExecutionRecord 模型

```
┌─────────────────────────────────────────────────────────────┐
│                    ExecutionRecord                          │
├─────────────────────────────────────────────────────────────┤
│ 层级字段                                                     │
│   - execution_id: str (顶层执行单元)                         │
│   - run_id: str (可空，对应旧 RunRecord)                    │
│   - step_id: str (可空，对应旧 StepRecord)                  │
├─────────────────────────────────────────────────────────────┤
│ 时间字段                                                     │
│   - start_time: datetime                                   │
│   - end_time: datetime                                     │
│   - duration_ms: int                                        │
├─────────────────────────────────────────────────────────────┤
│ Token 字段                                                  │
│   - prompt_tokens: int                                      │
│   - completion_tokens: int                                  │
│   - total_tokens: int                                      │
│   - cost_usd: float                                        │
├─────────────────────────────────────────────────────────────┤
│ 状态字段                                                    │
│   - status: str (pending/running/success/failed)           │
│   - error: str                                             │
├─────────────────────────────────────────────────────────────┤
│ 扩展字段                                                    │
│   - metadata: Dict[str, Any] (JSON)                       │
│   - traces: List[Trace] (内嵌)                             │
│   - steps: List[Step] (内嵌)                              │
└─────────────────────────────────────────────────────────────┘
```

### 兼容性设计

保留现有模型，通过适配器转换:
```python
# 适配器模式
class RecordAdapter:
    @staticmethod
    def to_execution(trade_record: TraceRecord) -> ExecutionRecord: ...
    @staticmethod
    def to_execution(run_record: RunRecord) -> ExecutionRecord: ...
    @staticmethod
    def to_execution(step_record: StepRecord) -> ExecutionRecord: ...
```

---

## 数据流

```
YoungAgent 执行
    │
    ▼
ExecutionRecorder.record_start()  ← 创建 execution_id
    │
    ▼
ExecutionRecorder.record_step()   ← 添加 step (可选)
    │
    ▼
ExecutionRecorder.record_end()    ← 更新状态和统计
    │
    ▼
统一存储到 SQLite
```

---

## 向后兼容

1. **保留现有 API**: 旧代码无需修改
2. **渐进迁移**: 新代码使用 ExecutionRecord
3. **数据迁移脚本**: 一次性迁移历史数据

---

## 验收标准

1. 统一的数据模型支持层级追溯
2. 现有模块通过适配器保持兼容
3. 支持跨执行单元查询和分析
4. 单元测试覆盖核心功能
