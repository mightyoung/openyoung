#YH|# EvaluationHub 设计 (v3.1)
#KM|
#WB|> EvaluationHub - 评估包仓库，仅提供包注册与加载，不执行评估任务
#SX|> 更新日期: 2026-03-01
#BT|
#SM|> 关联: evaluation-center-design.md 已删除，功能并入 Eval SubAgent

> EvaluationHub - 评估包仓库，仅提供包注册与加载，不执行评估任务
> 更新日期: 2026-03-01

---

## 1. 定位

### 设计原则

- **仅提供包仓库**：不执行评估任务，仅管理评估包元数据与加载
- **被调用方**：Eval SubAgent 负责执行，Hub 提供包
- **包版本管控**：由 Package Manager 管理版本与依赖

### 与 EvaluationCenter 区别

| 功能 | EvaluationCenter | EvaluationHub |
|------|------------------|---------------|
| 包注册 | ✅ | ✅ |
| 包加载 | ✅ | ✅ |
| 执行评估 | ✅ | ❌ |
| 并行执行 | ✅ | ❌ |
| 结果聚合 | ✅ | ❌ |

---

## 2. 评估类型（保留）

### 2.1 按维度分类

| 类型 | 说明 | 场景 |
|------|------|------|
| **正确性** | 输出是否正确完成任务 | 代码生成、问答 |
| **效率** | Token/时间消耗是否合理 | 资源敏感场景 |
| **安全性** | 输出是否安全无害 | 用户交互场景 |
| **用户体验** | 输出是否友好、易懂 | 对话场景 |

### 2.2 按层级分类

| 层级 | 说明 | 粒度 |
|------|------|------|
| **单元评估** | 单个工具输出 | Tool 级别 |
| **集成评估** | 多个工具组合 | Agent 级别 |
| **系统评估** | 完整业务流程 | System 级别 |

---

## 3. 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       EvaluationHub 架构                           │
│                    (仅包仓库，不执行评估)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Package Manager (管控 Evaluation 包)                      │    │
│  │  - 包版本管理                                           │    │
│  │  - 依赖解析                                             │    │
│  │  - 特征码注册                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  EvaluationHub                                           │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  Package Registry (包注册表)                      │   │    │
│  │  │  - register_package()                           │   │    │
│  │  │  - get_package()                               │   │    │
│  │  │  - list_packages()                             │   │    │
│  │  │  - search_by_dimension()                       │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                          │                               │    │
│  │                          ▼                               │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  Package Loader (包加载器)                        │   │    │
│  │  │  - load_package()                              │   │    │
│  │  │  - load_evaluator()                           │   │    │
│  │  │  - get_evaluator_class()                       │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                          │                               │    │
│  │                          ▼                               │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  Index Builder (索引构建器)                       │   │    │
│  │  │  - build_dimension_index()                      │   │    │
│  │  │  - build_level_index()                         │   │    │
│  │  │  - build_feature_index()                       │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              ▲                                   │
│                              │                                   │
│         ┌────────────────────┴────────────────────┐              │
│         │                                     │               │
│         ▼                                     ▼               │
│┌─────────────────────┐              ┌─────────────────────┐     │
│   Eval SubAgent      │              │    Evolver          │     │
│  - 执行评估逻辑       │◀─ 加载包 ──▶│  - 评估结果用于进化  │     │
│  - 并行执行          │              │                     │     │
│  - 结果聚合          │              │                     │     │
│└─────────────────────┘              └─────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 核心组件

### 4.1 数据结构（保留）

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EvalDimension(str, Enum):
    CORRECTNESS = "correctness"   # 正确性
    EFFICIENCY = "efficiency"    # 效率
    SAFETY = "safety"            # 安全性
    UX = "ux"                   # 用户体验


class EvalLevel(str, Enum):
    UNIT = "unit"           # 单元
    INTEGRATION = "integration"  # 集成
    SYSTEM = "system"       # 系统
    E2E = "e2e"           # 端到端


@dataclass
class EvalResult:
    """单项评估结果 - 由调用方执行后返回"""
    evaluator_name: str
    dimension: EvalDimension
    level: EvalLevel
    score: float  # 0-1
    passed: bool
    feedback: str
    execution_time_ms: int = 0
    error: Optional[str] = None


@dataclass
class EvaluationReport:
    """评估报告 - 由调用方聚合"""
    request_id: str
    overall_score: float
    passed: bool
    blocking_failed: bool
    results: list[EvalResult]
    aggregated_at: str
    
    # 执行信息
    total_evaluators: int
    successful_evaluators: int
    failed_evaluators: int
    total_time_ms: int


@dataclass
class EvaluationSuggestion:
    """评估建议"""
    feature_code: str
    reason: str
    priority: int  # 1-5
```

### 4.2 评估器定义（保留，Hub 不执行）

```python
from abc import ABC, abstractmethod


class EvaluatorDefinition(ABC):
    """评估器定义 - 仅定义元数据，由 SubAgent 实例化执行"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def feature_codes(self) -> list[str]:
        """特征码 - 用于索引"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> EvalDimension:
        pass
    
    @property
    @abstractmethod
    def level(self) -> EvalLevel:
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> dict:
        """输入数据要求"""
        pass
    
    @abstractmethod
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        """执行评估 - 由调用方调用"""
        pass
```

### 4.3 包注册表

```python
@dataclass
class EvalPackage:
    """评估包定义"""
    name: str
    version: str
    description: str
    dimension: EvalDimension
    level: EvalLevel
    feature_codes: list[str]
    evaluator_classes: list[type[EvaluatorDefinition]]
    dependencies: list[str] = None
    
    @property
    def package_id(self) -> str:
        return f"{self.name}/{self.version}"


class PackageRegistry:
    """包注册表"""
    
    def __init__(self):
        self._packages: dict[str, EvalPackage] = {}
        self._name_index: dict[str, list[str]] = {}  # name -> [versions]
    
    def register(self, package: EvalPackage) -> None:
        """注册评估包"""
        self._packages[package.package_id] = package
        
        if package.name not in self._name_index:
            self._name_index[package.name] = []
        if package.version not in self._name_index[package.name]:
            self._name_index[package.name].append(package.version)
    
    def get(self, name: str, version: str = None) -> EvalPackage:
        """获取包"""
        if version is None:
            # 获取最新版本
            versions = self._name_index.get(name, [])
            if not versions:
                return None
            version = sorted(versions, reverse=True)[0]
        
        return self._packages.get(f"{name}/{version}")
    
    def list_packages(
        self, 
        dimension: EvalDimension = None,
        level: EvalLevel = None
    ) -> list[EvalPackage]:
        """列出包"""
        packages = list(self._packages.values())
        
        if dimension:
            packages = [p for p in packages if p.dimension == dimension]
        if level:
            packages = [p for p in packages if p.level == level]
        
        return packages
    
    def search_by_dimension(self, dimension: EvalDimension) -> list[EvalPackage]:
        """按维度搜索"""
        return [p for p in self._packages.values() if p.dimension == dimension]
    
    def search_by_feature_code(self, feature_code: str) -> list[EvalPackage]:
        """按特征码搜索"""
        return [
            p for p in self._packages.values() 
            if feature_code in p.feature_codes
        ]
```

### 4.4 包加载器

```python
class PackageLoader:
    """包加载器 - 从包中加载评估器类"""
    
    def __init__(self, registry: PackageRegistry):
        self.registry = registry
    
    def load_evaluators(
        self, 
        package: EvalPackage
    ) -> list[EvaluatorDefinition]:
        """加载包中的所有评估器"""
        evaluators = []
        
        for evaluator_class in package.evaluator_classes:
            evaluator = evaluator_class()
            evaluators.append(evaluator)
        
        return evaluators
    
    def load_evaluator(
        self, 
        package: EvalPackage, 
        evaluator_name: str
    ) -> EvaluatorDefinition:
        """加载指定评估器"""
        for evaluator_class in package.evaluator_classes:
            evaluator = evaluator_class()
            if evaluator.name == evaluator_name:
                return evaluator
        
        return None
    
    def get_evaluator_class(
        self, 
        package: EvalPackage, 
        evaluator_name: str
    ) -> type[EvaluatorDefinition]:
        """获取评估器类（延迟实例化）"""
        for evaluator_class in package.evaluator_classes:
            # 通过类属性获取名称（需要评估器类实现name属性）
            if getattr(evaluator_class, 'NAME', None) == evaluator_name:
                return evaluator_class
        
        return None
```

### 4.5 索引构建器

```python
class IndexBuilder:
    """索引构建器 - 构建多维索引"""
    
    def __init__(self, registry: PackageRegistry):
        self.registry = registry
        self._dimension_index: dict[EvalDimension, list[str]] = {}
        self._level_index: dict[EvalLevel, list[str]] = {}
        self._feature_index: dict[str, list[str]] = {}
    
    def build_all(self):
        """构建所有索引"""
        self.build_dimension_index()
        self.build_level_index()
        self.build_feature_index()
    
    def build_dimension_index(self):
        """按维度构建索引"""
        self._dimension_index = {}
        for pkg in self.registry.list_packages():
            dim = pkg.dimension
            if dim not in self._dimension_index:
                self._dimension_index[dim] = []
            self._dimension_index[dim].append(pkg.package_id)
    
    def build_level_index(self):
        """按层级构建索引"""
        self._level_index = {}
        for pkg in self.registry.list_packages():
            level = pkg.level
            if level not in self._level_index:
                self._level_index[level] = []
            self._level_index[level].append(pkg.package_id)
    
    def build_feature_index(self):
        """按特征码构建索引"""
        self._feature_index = {}
        for pkg in self.registry.list_packages():
            for fc in pkg.feature_codes:
                if fc not in self._feature_index:
                    self._feature_index[fc] = []
                self._feature_index[fc].append(pkg.package_id)
    
    def get_by_dimension(self, dimension: EvalDimension) -> list[str]:
        """通过维度获取包ID"""
        return self._dimension_index.get(dimension, [])
    
    def get_by_level(self, level: EvalLevel) -> list[str]:
        """通过层级获取包ID"""
        return self._level_index.get(level, [])
    
    def get_by_feature_code(self, feature_code: str) -> list[str]:
        """通过特征码获取包ID"""
        return self._feature_index.get(feature_code, [])
```

### 4.6 EvaluationHub 核心

```python
class EvaluationHub:
    """评估中心 - 仅包仓库，不执行评估"""
    
    def __init__(self, package_manager: PackageManager):
        self.package_manager = package_manager
        self.registry = PackageRegistry()
        self.loader = PackageLoader(self.registry)
        self.index_builder = IndexBuilder(self.registry)
    
    # ---------- 包管理 ----------
    
    async def register_package(self, package: EvalPackage):
        """注册评估包"""
        self.registry.register(package)
        self.index_builder.build_all()
    
    async def register_packages_from_manager(self):
        """从 Package Manager 加载所有评估包"""
        packages = await self.package_manager.list_packages(type="evaluation")
        
        for pkg in packages:
            await self.register_package(pkg)
    
    # ---------- 查询 ----------
    
    def get_package(self, name: str, version: str = None) -> EvalPackage:
        """获取包"""
        return self.registry.get(name, version)
    
    def list_packages(
        self, 
        dimension: EvalDimension = None,
        level: EvalLevel = None
    ) -> list[EvalPackage]:
        """列出包"""
        return self.registry.list_packages(dimension, level)
    
    def search(
        self,
        feature_codes: list[str] = None,
        dimension: EvalDimension = None,
        level: EvalLevel = None
    ) -> list[EvalPackage]:
        """多维搜索"""
        # 先按特征码筛选
        if feature_codes:
            package_ids = set()
            for fc in feature_codes:
                package_ids.update(self.index_builder.get_by_feature_code(fc))
            packages = [self.registry.get_by_id(pid) for pid in package_ids]
        else:
            packages = self.registry.list_packages()
        
        # 再按维度/层级筛选
        if dimension:
            packages = [p for p in packages if p.dimension == dimension]
        if level:
            packages = [p for p in packages if p.level == level]
        
        return [p for p in packages if p is not None]
    
    # ---------- 加载 ----------
    
    def load_evaluators(self, package: EvalPackage) -> list[EvaluatorDefinition]:
        """加载包中的评估器"""
        return self.loader.load_evaluators(package)
    
    def load_evaluator(
        self, 
        package: EvalPackage, 
        evaluator_name: str
    ) -> EvaluatorDefinition:
        """加载指定评估器"""
        return self.loader.load_evaluator(package, evaluator_name)
    
    # ---------- 建议 ----------
    
    def suggest_packages(self, task_type: str) -> list[str]:
        """推荐包 - 基于任务类型"""
        suggestions_map = {
            "code_generation": ["correctness", "syntax", "security", "efficiency"],
            "question_answering": ["correctness", "ux", "relevance"],
            "summarization": ["quality", "relevance", "fluency"],
            "conversation": ["ux", "helpfulness", "safety"],
        }
        
        feature_codes = suggestions_map.get(task_type, ["correctness"])
        packages = self.search(feature_codes=feature_codes)
        
        return [p.package_id for p in packages]
```

---

## 5. 与 Eval SubAgent 集成

### 5.1 SubAgent 调用 Hub

```python
class EvalSubAgent:
    """评估子代理 - 负责执行评估"""
    
    def __init__(self, evaluation_hub: EvaluationHub):
        self.hub = evaluation_hub
        self._evaluator_cache: dict[str, EvaluatorDefinition] = {}
    
    async def evaluate(
        self,
        feature_codes: list[str],
        input_data: dict,
        context: dict = None
    ) -> EvaluationReport:
        """执行评估"""
        
        # 1. 从 Hub 获取包
        packages = self.hub.search(feature_codes=feature_codes)
        
        # 2. 加载评估器
        evaluators = []
        for pkg in packages:
            for evaluator in self.hub.load_evaluators(pkg):
                evaluators.append(evaluator)
        
        # 3. 串行/并行执行（由 SubAgent 控制）
        results = await self._execute_parallel(evaluators, input_data, context)
        
        # 4. 聚合结果
        overall_score, passed, blocking_failed = self._aggregate(results)
        
        return EvaluationReport(
            request_id=str(uuid.uuid4()),
            overall_score=overall_score,
            passed=passed,
            blocking_failed=blocking_failed,
            results=results,
            aggregated_at=datetime.now().isoformat(),
            total_evaluators=len(evaluators),
            successful_evaluators=sum(1 for r in results if not r.error),
            failed_evaluators=sum(1 for r in results if r.error),
            total_time_ms=0  # 由 SubAgent 计算
        )
    
    async def _execute_parallel(
        self,
        evaluators: list[EvaluatorDefinition],
        input_data: dict,
        context: dict
    ) -> list[EvalResult]:
        """并行执行评估器"""
        # SubAgent 负责执行逻辑
        pass
    
    def _aggregate(self, results: list[EvalResult]) -> tuple[float, bool, bool]:
        """聚合结果"""
        # SubAgent 负责聚合逻辑
        pass
```

### 5.2 Primary Agent 调用 SubAgent

```python
class PrimaryAgent:
    """主代理"""
    
    async def execute_task(self, task: Task):
        # ... 执行任务 ...
        
        # 调用 Eval SubAgent
        eval_result = await self.eval_subagent.evaluate(
            feature_codes=["correctness", "security"],
            input_data={"output": task.output},
            context={"task_id": task.id}
        )
        
        if eval_result.passed:
            # 继续
            pass
        else:
            # 自修正
            await self.self_correct(task, eval_result)
```

---

## 6. 评估包结构

```yaml
# @mightyoung/eval-correctness/v1.0.0
name: eval-correctness
version: 1.0.0
type: evaluation

# 维度与层级
dimension: correctness
level: unit

# 特征码 - 用于 Hub 索引
feature_code:
  - correctness
  - exact-match
  - code-generation

# 评估器定义
evaluators:
  - name: exact_match
    class: ExactMatchEvaluator
    dimension: correctness
    level: unit
    
  - name: code_syntax
    class: CodeSyntaxEvaluator
    dimension: correctness
    level: unit

# 输入要求
input_schema:
  type: object
  required: [input, expected]
  properties:
    input:
      type: string
    expected:
      type: string
    context:
      type: object
```

---

## 7. 与其他组件关系

| 组件 | 关系 | 说明 |
|------|------|------|
| **Package Manager** | 管控 | 包版本、依赖、特征码注册 |
| **Eval SubAgent** | 被调用方 | 从 Hub 加载包并执行 |
| **Primary Agent** | 调用方 | 通过 SubAgent 调用评估 |
| **Evolver** | 消费者 | 评估结果用于进化决策 |

---

## 8. 配置

```yaml
# mightyoung.yaml
evaluation:
  # 包配置 (受 PM 管控)
  packages:
    - name: eval-correctness
      version: "1.0.0"
    - name: eval-efficiency
      version: "1.0.0"
  
  # EvaluationHub 配置
  hub:
    auto_index: true        # 启动时自动构建索引
    cache_evaluators: true  # 缓存评估器实例
  
  # Eval SubAgent 配置
  subagent:
    max_concurrency: 5     # 并行执行数
    timeout_seconds: 30.0   # 超时时间
    retry_on_failure: true  # 失败重试
  
  # 默认评估策略
  defaults:
    task_types:
      code_generation:
        - correctness
        - syntax
        - security
      conversation:
        - ux
        - safety
```

---

## 9. 目录结构

```
eval-hub/
├── __init__.py
├── registry.py           # 包注册表
├── loader.py            # 包加载器
├── indexer.py          # 索引构建器
├── hub.py              # Hub 核心
├── types.py            # 数据类型定义
├── packages/           # 内置评估包
│   ├── __init__.py
│   ├── correctness/    # 正确性评估包
│   │   ├── __init__.py
│   │   ├── exact_match.py
│   │   ├── code_syntax.py
│   │   └── package.yaml
│   ├── efficiency/    # 效率评估包
│   │   └── ...
│   ├── safety/        # 安全性评估包
│   │   └── ...
│   └── ux/           # 用户体验评估包
│       └── ...
└── examples/          # 使用示例
    └── eval_subagent_example.py
```

---

*本文档定义 EvaluationHub 详细设计 v3.0*
*核心变化：移除执行逻辑，仅保留包仓库功能*

---

## 10. 内置评估包设计

### 10.1 设计原则

| 原则 | 说明 |
|------|------|
| **YAML 配置 + Python 类** | 元数据在 YAML，逻辑在 Python 类 |
| **YAML 配置阈值** | 阈值通过配置文件管理 |
| **内置 + 外部混合** | 核心评估器内置，扩展评估器外部加载 |

### 10.2 包格式

```yaml
# eval-correctness/package.yaml
name: eval-correctness
version: 1.0.0

dimension: correctness
level: unit

feature_codes:
  - correctness
  - exact-match
  - code-generation

evaluators:
  - name: exact_match
    class: ExactMatchEvaluator
    config:
      match_type: exact
      threshold: 1.0
      
  - name: syntax_check
    class: SyntaxCheckEvaluator
    config:
      language: python
      threshold: 1.0

dependencies: []
```

### 10.3 正确性评估包

#### ExactMatchEvaluator

```python
class ExactMatchEvaluator:
    """精确匹配评估器"""
    
    NAME = "exact_match"
    DIMENSION = EvalDimension.CORRECTNESS
    LEVEL = EvalLevel.UNIT
    FEATURE_CODES = ["correctness", "exact-match", "code-generation"]
    
    def __init__(self, match_type: str = "exact", case_sensitive: bool = True):
        self.match_type = match_type
        self.case_sensitive = case_sensitive
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        actual = input_data.get("output", "")
        expected = input_data.get("expected", "")
        
        # 匹配逻辑...
        passed = ...
        
        return EvalResult(
            evaluator_name=self.NAME,
            dimension=self.DIMENSION,
            level=self.LEVEL,
            score=1.0 if passed else 0.0,
            passed=passed,
            feedback=f"Exact match: {'PASS' if passed else 'FAIL'}"
        )
```

#### SyntaxCheckEvaluator

```python
class SyntaxCheckEvaluator:
    """语法检查评估器"""
    
    NAME = "syntax_check"
    DIMENSION = EvalDimension.CORRECTNESS
    LEVEL = EvalLevel.UNIT
    FEATURE_CODES = ["correctness", "syntax", "code-generation"]
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        code = input_data.get("output", "")
        
        # Python: ast.parse()
        # JavaScript: node --check
        # ...
        
        return EvalResult(...)
```

#### SemanticJudgeEvaluator

```python
class SemanticJudgeEvaluator:
    """语义正确性 - LLM-as-Judge"""
    
    NAME = "semantic_correctness"
    DIMENSION = EvalDimension.CORRECTNESS
    LEVEL = EvalLevel.INTEGRATION
    
    DEFAULT_RUBRIC = """评估输出是否正确完成了任务。
评分标准:
- 5: 完全正确
- 4: 基本正确
- 3: 部分正确
- 2: 大部分错误
- 1: 完全错误"""
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # 调用 LLM 评估
        # 解析分数 (1-5) → score (0-1)
        # threshold: 4.0/5.0
        
        return EvalResult(...)
```

### 10.4 安全性评估包

#### PIIDetector

```python
class PIIDetector:
    """PII 检测器"""
    
    NAME = "pii_detector"
    DIMENSION = EvalDimension.SAFETY
    LEVEL = EvalLevel.UNIT
    
    PII_PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "credit_card": r'\b\d{16}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    }
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # 正则匹配 PII
        # threshold: 1.0 (零容忍)
        
        return EvalResult(...)
```

#### InjectionDetector

```python
class InjectionDetector:
    """提示注入检测器"""
    
    NAME = "injection_check"
    DIMENSION = EvalDimension.SAFETY
    LEVEL = EvalLevel.UNIT
    
    INJECTION_PATTERNS = [
        r'ignore\s+previous\s+instructions',
        r'disregard\s+instructions',
        r'system\s+prompt',
        # ...
    ]
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # 正则匹配注入模式
        # threshold: 1.0 (零容忍)
        
        return EvalResult(...)
```

### 10.5 效率评估包

#### TokenCounter

```python
class TokenCounter:
    """Token 使用计数"""
    
    NAME = "token_usage"
    DIMENSION = EvalDimension.EFFICIENCY
    LEVEL = EvalLevel.UNIT
    
    DEFAULT_LIMITS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
    }
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # 使用 tiktoken 计数
        # score = 1 - (used / limit)
        # threshold: 0.8 (80%)
        
        return EvalResult(...)
```

#### LatencyMeasurer

```python
class LatencyMeasurer:
    """延迟测量"""
    
    NAME = "latency"
    DIMENSION = EvalDimension.EFFICIENCY
    LEVEL = EvalLevel.UNIT
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # 测量执行时间
        # threshold: 30s (80%)
        
        return EvalResult(...)
```

### 10.6 UX 评估包

#### ClarityEvaluator

```python
class ClarityEvaluator:
    """清晰度评估 - LLM-as-Judge"""
    
    NAME = "response_clarity"
    DIMENSION = EvalDimension.UX
    LEVEL = EvalLevel.INTEGRATION
    
    DEFAULT_RUBRIC = """评估输出是否清晰易懂。
评分标准:
- 5: 非常清晰
- 4: 比较清晰
- 3: 一般
- 2: 不太清晰
- 1: 很不清晰"""
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # LLM 评估
        # threshold: 3.5/5.0
        
        return EvalResult(...)
```

#### HelpfulnessEvaluator

```python
class HelpfulnessEvaluator:
    """有用性评估 - LLM-as-Judge"""
    
    NAME = "helpfulness"
    DIMENSION = EvalDimension.UX
    LEVEL = EvalLevel.INTEGRATION
    
    async def evaluate(self, input_data: dict, context: dict = None) -> EvalResult:
        # LLM 评估
        # threshold: 3.5/5.0
        
        return EvalResult(...)
```

### 10.7 阈值配置

```yaml
# config/eval-defaults.yaml

dimensions:
  correctness:
    threshold: 0.8
    blocking: true
    metrics:
      exact_match: 1.0
      syntax_check: 1.0
      semantic_correctness: 4.0/5.0
      
  safety:
    threshold: 0.95
    blocking: true
    metrics:
      pii_detector: 1.0
      injection_check: 1.0
      
  efficiency:
    threshold: 0.7
    blocking: false
    metrics:
      token_usage: 0.8
      latency: 0.8
      
  ux:
    threshold: 0.6
    blocking: false
    metrics:
      response_clarity: 3.5/5.0
      helpfulness: 3.5/5.0

task_types:
  code_generation:
    required:
      - exact_match
      - syntax_check
    optional:
      - semantic_correctness
      
  conversation:
    required:
      - response_clarity
      - helpfulness
    optional:
      - safety_judge
```

### 10.8 扩展方式

```python
# 内置 + 外部混合模式

# 1. 内置评估器 (builtins)
from eval_hub.packages.builtins.correctness import CORRECTNESS_EVALUATORS

# 2. 外部包 (从 Package Manager 加载)
# @mightyoung/eval-custom/v1.0.0

# 3. 工作区评估器 (项目特定)
# ./eval/my_evaluator.py
```

---

*本章定义内置评估包详细设计*