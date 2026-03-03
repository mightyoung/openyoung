# Evolver 设计 (v2.1)

> 基于 OpenClaw GEP 协议 + 融合方案
> 更新日期: 2026-03-02

---

## 1. 核心概念

| 概念 | 说明 |
|------|------|
| **Gene** | 可重用的进化策略单元，由信号触发 |
| **Capsule** | 成功执行的固化记录，可重放 |
| **EvolutionEvent** | 审计日志，记录每次进化 |
| **Personality** | Agent 个性状态，可演化 |

---

## 2. Gene 定义 (参照 OpenClaw GEP)

```yaml
# GENES/repair/gene_repair_from_errors.yaml
type: Gene
id: gene_repair_from_errors
version: "1.0.0"
category: repair  # repair | optimize | innovate

# 信号匹配 - 核心机制
signals_match:
  - error
  - exception
  - failed
  - unstable

# 前置条件
preconditions:
  - "signals contains error-related indicators"

# 策略步骤
strategy:
  - "Extract structured signals from logs"
  - "Select existing Gene by signals match"
  - "Estimate blast radius before editing"
  - "Apply smallest reversible patch"
  - "Validate; rollback on failure"
  - "Solidify: append EvolutionEvent"

# 约束
constraints:
  max_files: 20
  max_lines_per_file: 500
  forbidden_paths:
    - .git
    - node_modules
  allowed_operations:
    - edit
    - create
    - delete

# 验证命令 (白名单)
validation:
  commands:
    - python
    - pytest
    - ruff
    - mypy
  timeout_seconds: 180

# 元数据
metadata:
  author: evolver
  created_at: "2026-02-28T00:00:00Z"
  updated_at: "2026-02-28T00:00:00Z"
  success_rate: 0.85
  usage_count: 42
```

---

## 3. Capsule 定义

```yaml
# CAPSULES/capsule_20260228_001.yaml
type: Capsule
id: capsule_20260228_errfix_001
version: "1.0.0"

# 触发信号
trigger:
  - log_error
  - ImportError

# 引用的基因
gene_ref: gene_repair_from_errors
gene_version: "1.0.0"

# 摘要
summary: |
  Fixed ImportError by adding missing 'pydantic' dependency.

# 置信度
confidence: 0.92

# 影响范围
blast_radius:
  files: 1
  lines_added: 3
  lines_removed: 0

# 执行结果
outcome:
  status: success  # success | partial | failure
  score: 0.92
  duration_ms: 2340

# 环境指纹
env_fingerprint:
  python_version: "3.11"
  platform: darwin
  dependencies:
    fastapi: "0.109.0"
    pydantic: "2.5.0"

# 变更内容
changes:
  - type: edit
    file: requirements.txt
    diff: |
      --- a/requirements.txt
      +++ b/requirements.txt
      @@ -1,3 +1,4 @@
       fastapi==0.109.0
      +pydantic==2.5.0
       uvicorn==0.27.0

# 血缘
lineage:
  parent_capsule: null
  evolution_event_id: evt_20260228_001

# 时间戳
created_at: "2026-02-28T14:30:00Z"
```

---

## 4. EvolutionEvent 审计日志

```jsonl
# .mightyoung/evolved/events.jsonl
{"type":"EvolutionEvent","id":"evt_20260228_001","timestamp":"2026-02-28T14:30:00Z","parent":"evt_20260227_042","intent":"repair","signals":["ImportError","ModuleNotFoundError"],"genes_used":["gene_repair_from_errors"],"mutation_id":"mut_20260228_001","personality_state":{"rigor":0.75,"creativity":0.3,"risk_tolerance":0.2},"outcome":{"status":"success","score":0.92},"capsule_id":"capsule_20260228_errfix_001","duration_ms":2340}
{"type":"EvolutionEvent","id":"evt_20260228_002","timestamp":"2026-02-28T15:00:00Z","parent":"evt_20260228_001","intent":"optimize","signals":["perf_bottleneck"],"genes_used":["gene_optimize_performance"],"mutation_id":"mut_20260228_002","personality_state":{"rigor":0.75,"creativity":0.35,"risk_tolerance":0.25},"outcome":{"status":"success","score":0.88},"capsule_id":"capsule_20260228_perf_001","duration_ms":5600}
```

---

## 5. 进化机制流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Evolution Loop                            │
├─────────────────────────────────────────────────────────────┤
│  1. SCAN        → 读取 session logs, memory, user.md      │
│  2. EXTRACT     → 提取信号 (error, opportunity, patterns)  │
│  3. MATCH       → 信号匹配基因 (signals_match)             │
│  4. BUILD       → 构建 Mutation (intent, target, risk)      │
│  5. VALIDATE    → 执行验证命令 (白名单)                    │
│  6. EXECUTE     → 应用变更                                 │
│  7. SOLIDIFY    → 记录 EvolutionEvent + 创建 Capsule       │
│  8. UPDATE      → 更新 genes.json, personality.json        │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Evolver 配置

```yaml
# .mightyoung/config.yaml
evolver:
  # 进化频率 (动态)
  frequency:
    base: 10  # 每天 10 次
    dynamic:
      error_multiplier: 2.0      # 错误多时提高频率
      stable_multiplier: 0.5    # 稳定时降低频率
    limits:
      max_per_day: 50
      min_per_week: 1

  # 分层存储 - 进化版本优先
  layered_storage:
    priority:
      - agents/{agent}/evolved/    # Agent 特定进化
      - .mightyoung/evolved/      # 全局进化
      - .mightyoung/packages/      # 包 (只读)

  # 冲突解决 (auto 模式)
  merge_strategy: auto
  # auto: 时间戳优先 / 基因优先 / 静默合并

  # 约束
  constraints:
    require_approval: false
    dry_run_default: true
    whitelist_commands:
      - python
      - pytest
      - ruff
      - mypy

  # 个性演化
  personality:
    rigor: 0.7
    creativity: 0.35
    risk_tolerance: 0.4
    obedience: 0.85
```

---

## 7. 信号类型

### 错误类信号 (repair)
```yaml
signals_match:
  - error
  - exception
  - failed
  - unstable
  - panic
```

### 机会类信号 (optimize/innovate)
```yaml
signals_match:
  - perf_bottleneck
  - capability_gap
  - user_feature_request
  - external_opportunity
```

---

## 8. 目录结构

```
capsule-name/
├── CAPSULE.yaml              # Capsule 元数据
├── CAPSULE.md                # 文档
├── GENES/
│   ├── repair/              # 修复类基因
│   ├── optimize/            # 优化类基因
│   └── innovate/            # 创新类基因
├── CAPSULES/                # 成功执行记录
├── META/
│   ├── evolution-history.jsonl  # 审计日志
│   ├── personality.json        # 个性状态
│   └── signals.json           # 信号库
└── scripts/
    └── validate.sh           # 验证脚本
```

---

## 9. 与 Package Manager 集成

```
分层存储优先级:
1. agents/my-agent/evolved/    ← 最高 (Agent 特定进化)
2. .mightyoung/evolved/        ← 中   (全局进化)
3. .mightyoung/packages/       ← 低   (包只读)
```

---

## 10. 与 DataCenter 集成

Evolver 基于 DataCenter 提供的数据驱动自进化：

```
┌─────────────────────────────────────────────────────────────────┐
│           Evolver → DataCenter 数据流                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   DataCenter                                                     │
│   ┌─────────────────────────────────────────────────────────┐    │
│   │  Harness (数据获取)                                      │    │
│   │  - TraceLog → 执行轨迹                                 │    │
│   │  - Metrics → 质量指标                                   │    │
│   │  - FailurePattern → 错误模式                           │    │
│   └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼ (数据流)                         │
│   Evolver                                                      │
│   - Signal Extraction: 从 TraceLog 提取进化信号              │
│   - Experience Bank: 存储经验供进化使用                   │
│   - Quality Metrics: 基于 Metrics 评估进化效果             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. 与 Evaluation Hub 集成

Evolver 使用 Evaluation Hub 进行进化效果评估：

```
┌─────────────────────────────────────────────────────────────────┐
│           Evolver → Evaluation Hub 集成                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Evolver                                                      │
│   - 生成候选进化                                              │
│   - 提交给 Evaluation Hub 评估                                │
│                              │                                   │
│                              ▼                                 │
│   Evaluation Hub                                                │
│   - 多类型评估 (正确性/效率/安全/体验)                      │
│   - 多层级评估 (单元/集成/系统/E2E)                          │
│   - 评估结果反馈                                             │
│                              │                                   │
│                              ▼                                 │
│   Evolver                                                      │
│   - 根据评估结果选择进化                                      │
│   - 记录 EvolutionEvent                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 12. 统一数据源架构

Evolver、Training Pipeline、Evaluation Hub 共享 DataCenter 的统一数据源：

```
┌─────────────────────────────────────────────────────────────────┐
│              统一数据源架构                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Runtime Traces (统一来源)                                    │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────┐              │
│   │           Signal Extraction                 │              │
│   │  - 错误检测    - 成功模式    - 质量评分   │              │
│   └────────────────────┬──────────────────────┘              │
│                        │                                       │
│                        ▼                                       │
│   ┌─────────────────────────────────────────────┐              │
│   │           Unified Knowledge Base             │              │
│   ├─────────────────────────────────────────────┤              │
│   │  Dataset:              │ Evolver:           │              │
│   │  - Training Samples    │ - Genes            │              │
│   │  - Examples           │ - Capsules         │              │
│   │  - Validation Sets    │ - Signals          │              │
│   └─────────────────────────────────────────────┘              │
│                        │                                       │
│        ┌─────────────┴─────────────┐                       │
│        ▼                             ▼                        │
│   ┌─────────────┐             ┌─────────────┐                 │
│   │ Prompt Opt  │             │ Gene Evolve │                 │
│   │ + Bootstrap │             │ + Mutation  │                 │
│   └─────────────┘             └─────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 13. 渐进式 Capsule 加载

采用渐进式加载策略，根据不同场景动态加载Capsule，避免上下文膨胀：

### 13.1 加载层级

```
┌─────────────────────────────────────────────────────────────────┐
│              渐进式 Capsule 加载策略                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Level 1: BASE CAPSULES (启动时加载)                          │
│   - 核心修复基因 (gene_repair_from_errors)                     │
│   - 通用优化基因 (gene_optimize_performance)                   │
│   - 安全检查基因 (gene_security_check)                         │
│                                                                  │
│   Level 2: ON-DEMAND CAPSULES (任务需要时加载)                │
│   - 根据任务类型动态加载相关Capsule                            │
│   - 任务上下文匹配 trigger 信号                               │
│   - 缓存已加载的Capsule供后续使用                              │
│                                                                  │
│   Level 3: AUTO-LOADING CAPSULES (基于预测自动加载)           │
│   - 分析用户意图预测可能需要的Capsule                          │
│   - 基于历史session模式预测                                   │
│   - 提前预加载高概率Capsule                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Capsule 元数据增强

```yaml
# CAPSULES/capsule_20260228_001.yaml
type: Capsule
id: capsule_20260228_errfix_001
version: "1.0.0"

# 加载层级
loading_level: base  # base | on_demand | auto

# 优先级 (数字越小越高)
priority: 1

# 触发信号
trigger:
  - log_error
  - ImportError

# 引用的基因
gene_ref: gene_repair_from_errors
gene_version: "1.0.0"

# 预加载条件
preload_conditions:
  - signal: error
    confidence: 0.7
  - signal: exception
    confidence: 0.6

# 使用统计
usage_stats:
  total_uses: 42
  success_rate: 0.92
  avg_duration_ms: 2340

# 最后更新时间
last_used: "2026-02-28T14:30:00Z"
```

### 13.3 加载决策引擎

```python
class CapsuleLoader:
    """Capsule 加载决策引擎"""

    def __init__(self, config: LoaderConfig):
        self.base_capsules = set()
        self.on_demand_cache = LRUCache(maxsize=100)
        self.prediction_model = PredictionModel()

    def load_level_1_base(self) -> List[Capsule]:
        """启动时加载基础Capsule"""
        return self.base_capsules

    def load_level_2_on_demand(self, task: Task) -> List[Capsule]:
        """根据任务上下文加载相关Capsule"""
        # 匹配 trigger 信号
        matching = self.match_triggers(task.signals)
        # 排序并返回 top-k
        return sorted(matching, key=lambda c: c.priority)[:5]

    def load_level_3_auto(self, session: Session) -> List[Capsule]:
        """基于预测自动加载"""
        # 预测可能需要的Capsule
        predicted = self.prediction_model.predict(session.history)
        # 预加载高概率Capsule
        return [c for c, prob in predicted if prob > 0.7]

    def match_triggers(self, signals: List[str]) -> List[Capsule]:
        """信号匹配Capsule"""
        # ... 实现信号匹配逻辑
        pass
```

---

## 14. 混合演进模式

Evolver 支持在线和离线两种演进模式，通过智能决策引擎选择：

### 14.1 模式对比

| 模式 | 触发条件 | 特点 | 适用场景 |
|------|---------|------|----------|
| **Online** | 实时错误/用户反馈 | 低延迟，即时修复 | 关键错误修复，安全漏洞 |
| **Offline** | 定时任务/手动触发 | 高吞吐量，深度分析 | 性能优化，模式识别 |

### 14.2 智能决策引擎

```python
class EvolutionDecisionEngine:
    """演进模式智能决策引擎"""

    def should_evolve_online(self, signal: Signal) -> bool:
        """判断是否触发在线演进"""
        # 关键信号：安全漏洞、致命错误
        critical_signals = ["security_vuln", "fatal_error", "data_loss"]
        if signal.type in critical_signals:
            return True
        
        # 错误频率阈值
        if signal.frequency > self.threshold:
            return True
        
        return False

    def schedule_offline_evolution(self) -> None:
        """调度离线演进任务"""
        # 定时任务：每天凌晨2点
        # 批量处理积累的进化候选
        pass

    def select_evolution_mode(self, signal: Signal) -> str:
        """选择演进模式"""
        if self.should_evolve_online(signal):
            return "online"
        else:
            return "offline"
```

### 14.3 演进流程对比

```
ONLINE 演进流程:                 OFFLINE 演进流程:
┌──────────────────┐           ┌──────────────────┐
│  检测到关键信号   │           │  定时触发/手动   │
└────────┬─────────┘           └────────┬─────────┘
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│  即时信号匹配     │           │  批量信号收集     │
└────────┬─────────┘           └────────┬─────────┘
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│  快速Gene选择    │           │  深度模式分析     │
└────────┬─────────┘           └────────┬─────────┘
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│  执行 + 验证     │           │  批量Gene生成     │
└────────┬─────────┘           └────────┬─────────┘
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│  即时固化记录    │           │  评估筛选 + 固化 │
└────────┬─────────┘           └────────┬─────────┘
         ▼                              ▼
┌──────────────────┐           ┌──────────────────┐
│  反馈给Agent    │           │  批量更新基因库   │
└──────────────────┘           └──────────────────┘
```

---

## 15. 增强进化机制

在基础进化流程上增加三层增强机制：

### 15.1 经验提取层 (Experience Extraction)

从成功和失败的执行中提取可复用的经验：

```python
class ExperienceExtractor:
    """经验提取器"""

    def extract_from_success(self, trace: Trace) -> Experience:
        """从成功执行中提取经验"""
        # 提取成功模式
        patterns = self.identify_patterns(trace.steps)
        # 提取关键决策点
        decisions = self.extract_decisions(trace.steps)
        # 生成经验摘要
        return Experience(patterns=patterns, decisions=decisions)

    def extract_from_failure(self, trace: Trace) -> FailureLesson:
        """从失败执行中提取教训"""
        # 识别失败原因
        root_cause = self.find_root_cause(trace.error)
        # 提取失败模式
        pattern = self.identify_failure_pattern(trace)
        # 生成教训记录
        return FailureLesson(root_cause=root_cause, pattern=pattern)
```

### 15.2 知识蒸馏层 (Knowledge Distillation)

将提取的经验转化为可复用的知识：

```python
class KnowledgeDistiller:
    """知识蒸馏器"""

    def distill_to_gene(self, experiences: List[Experience]) -> Gene:
        """将经验蒸馏为Gene"""
        # 合并相似经验
        merged = self.merge_experiences(experiences)
        # 提取通用策略
        strategy = self.extract_strategy(merged)
        # 生成Gene
        return Gene(
            id=f"gene_{uuid4()}",
            strategy=strategy,
            signals_match=self.infer_signals(strategy)
        )

    def distill_to_capsule(self, gene: Gene, execution: Execution) -> Capsule:
        """将执行结果蒸馏为Capsule"""
        # 提取变更内容
        changes = self.extract_changes(execution)
        # 计算置信度
        confidence = self.calculate_confidence(execution)
        # 生成Capsule
        return Capsule(
            gene_ref=gene.id,
            confidence=confidence,
            changes=changes
        )
```

### 15.3 能力迭代层 (Capability Iteration)

基于评估结果迭代优化能力：

```python
class CapabilityIterator:
    """能力迭代器"""

    def iterate(self, evaluation: Evaluation) -> IterationResult:
        """根据评估结果迭代"""
        if evaluation.score >= self.success_threshold:
            # 成功：强化该能力
            return self.strengthen(evaluation.gene)
        elif evaluation.score >= self.retry_threshold:
            # 可重试：优化策略
            return self.optimize(evaluation.gene, evaluation.feedback)
        else:
            # 失败：标记为低优先级
            return self.deprioritize(evaluation.gene)

    def strengthen(self, gene: Gene) -> IterationResult:
        """强化成功的能力"""
        # 增加使用计数
        gene.usage_count += 1
        # 提高置信度
        gene.confidence = min(1.0, gene.confidence * 1.1)
        return IterationResult(action="strengthen", gene=gene)

    def optimize(self, gene: Gene, feedback: str) -> IterationResult:
        """优化可改进的能力"""
        # 根据反馈调整策略
        adjusted_strategy = self.adjust_strategy(gene.strategy, feedback)
        gene.strategy = adjusted_strategy
        return IterationResult(action="optimize", gene=gene)

    def deprioritize(self, gene: Gene) -> IterationResult:
        """降低失败能力的优先级"""
        # 降低置信度
        gene.confidence *= 0.8
        # 标记为低优先级
        gene.priority = 999
        return IterationResult(action="deprioritize", gene=gene)
```

---

*本文档基于 OpenClaw GEP 协议设计*
