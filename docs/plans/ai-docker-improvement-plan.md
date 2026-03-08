# OpenYoung AI Docker 改进计划

> 基于 E2B、Modal、Jina 等行业最佳实践

---

## 一、AI Docker 产品定义

### 1.1 核心概念

**E2B 联合创始人 Tomasz Tunguz** 说:

> "AI agents need a safe place to run code, access resources, and interact with the outside world."

**AI Docker = Agent 运行时容器化**

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenYoung AI Docker                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │  Agent A     │   │  Agent B     │   │  Agent C     │     │
│  │  (Python)    │   │  (Node.js)   │   │  (Bash)     │     │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘     │
│         │                   │                   │              │
│  ┌──────▼───────────────────▼───────────────────▼───────┐     │
│  │              Execution Runtime (沙箱)                   │     │
│  │  ├── 资源限制 (CPU/Memory/Time)                       │     │
│  │  ├── 网络隔离 (仅允许白名单)                          │     │
│  │  ├── 文件系统隔离 (只读/临时目录)                     │     │
│  │  └── 工具调用审计                                    │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              Data Layer (数据资产化)                  │     │
│  │  ├── 执行记录 → 评估 → 质量评分                       │     │
│  │  ├── 经验沉淀 → 知识图谱                             │     │
│  │  └── 可视化 / 导出                                   │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 对比现有方案

| 特性 | Docker | E2B | Modal | OpenYoung AI Docker |
|------|--------|------|-------|---------------------|
| 镜像 | OCI标准 | 自研VM | 容器 | 混合 |
| 启动时间 | 秒级 | 50ms | 100ms | 目标100ms |
| 资源限制 | ✅ | ✅ | ✅ | ✅ |
| 代码执行 | ❌ | ✅ | ✅ | ✅ |
| 评估集成 | ❌ | ❌ | ❌ | ✅ |
| 数据资产 | ❌ | ❌ | ❌ | ✅ |

---

## 二、关键架构设计

### 2.1 执行时设计 (参考 E2B)

```python
# src/runtime/sandbox.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import asyncio


class SandboxType(str, Enum):
    """沙箱类型"""
    EPHEMERAL = "ephemeral"      # 临时 - 每个任务
    PERSISTENT = "persistent"     # 持久 - 保持状态
    POOL = "pool"               # 池化 - 复用实例


@dataclass
class SandboxConfig:
    """沙箱配置"""
    sandbox_type: SandboxType = SandboxType.EPHEMERAL

    # 资源限制
    max_cpu_percent: float = 50.0
    max_memory_mb: int = 512
    max_execution_time_seconds: int = 300

    # 网络
    allow_network: bool = False
    allowed_domains: list[str] = None

    # 文件系统
    allowed_paths: list[str] = None
    read_only_paths: list[str] = None
    temp_dir: str = "/tmp/openyoung"

    # 环境
    environment: dict[str, str] = None


class ExecutionResult:
    """执行结果"""
    output: str
    error: str
    exit_code: int
    duration_ms: int
    tokens_used: int
    metadata: dict


class AISandbox:
    """AI Docker 核心沙箱"""

    async def create(
        self,
        agent_id: str,
        config: SandboxConfig,
    ) -> str:
        """创建沙箱实例"""
        pass

    async def execute(
        self,
        sandbox_id: str,
        code: str,
        language: str = "python",
    ) -> ExecutionResult:
        """在沙箱中执行代码"""
        pass

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
    ) -> ExecutionResult:
        """执行 shell 命令"""
        pass

    async def destroy(self, sandbox_id: str) -> None:
        """销毁沙箱"""
        pass

    # ========== 评估集成 ==========

    async def evaluate(
        self,
        sandbox_id: str,
        evaluation_plan: dict,
    ) -> dict:
        """执行评估"""
        pass
```

### 2.2 资源池设计 (参考 Modal)

```python
# src/runtime/pool.py

from typing import Optional
from dataclasses import dataclass
import asyncio


@dataclass
class PoolConfig:
    """资源池配置"""
    min_instances: int = 2
    max_instances: int = 10
    idle_timeout_seconds: int = 300
    scale_up_threshold: float = 0.7
    scale_down_threshold: float = 0.3


class SandboxPool:
    """沙箱实例池"""

    def __init__(self, config: PoolConfig):
        self.config = config
        self._available: asyncio.Queue = asyncio.Queue()
        self._active: dict[str, Sandbox] = {}
        self._lock = asyncio.Lock()

    async def acquire(self) -> Sandbox:
        """获取沙箱实例"""
        # 尝试从池中获取
        try:
            sandbox = self._available.get_nowait()
            self._active[sandbox.id] = sandbox
            return sandbox
        except asyncio.QueueEmpty:
            # 创建新实例
            if len(self._active) < self.config.max_instances:
                sandbox = await self._create_instance()
                self._active[sandbox.id] = sandbox
                return sandbox
            else:
                # 等待可用实例
                return await asyncio.wait_for(
                    self._available.get(),
                    timeout=30
                )

    async def release(self, sandbox: Sandbox) -> None:
        """释放沙箱实例回池"""
        async with self._lock:
            if sandbox.id in self._active:
                del self._active[sandbox.id]

                # 检查是否需要缩容
                utilization = len(self._active) / self.config.max_instances
                if utilization < self.config.scale_down_threshold:
                    await self._destroy_instance(sandbox)
                else:
                    await self._available.put(sandbox)

    async def scale(self) -> None:
        """自动扩缩容"""
        # 根据负载动态调整
        pass
```

### 2.3 安全隔离设计

```python
# src/runtime/security.py

from dataclasses import dataclass
from enum import Enum


class IsolationLevel(str, Enum):
    """隔离级别"""
    PROCESS = "process"       # 进程隔离
    CONTAINER = "container"  # 容器隔离
    VM = "vm"               # VM隔离 (E2B方式)


@dataclass
class SecurityPolicy:
    """安全策略"""
    isolation: IsolationLevel = IsolationLevel.PROCESS

    # 资源限制
    max_cpu_percent: float = 100.0
    max_memory_mb: int = 1024
    max_disk_mb: int = 5120

    # 访问控制
    allow_network: bool = True
    allow_file_write: bool = True
    allowed_commands: list[str] = None  # 白名单命令

    # 审计
    log_all_calls: bool = True
    record_screenshots: bool = False


class SecurityManager:
    """安全管理器"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def validate_code(self, code: str) -> bool:
        """验证代码安全性"""
        # 检查危险操作
        dangerous_patterns = [
            "import os; os.system",
            "subprocess",
            "eval(",
            "exec(",
            "__import__",
        ]
        return not any(p in code for p in dangerous_patterns)

    def validate_command(self, command: str) -> bool:
        """验证命令安全性"""
        if self.policy.allowed_commands:
            return command in self.policy.allowed_commands
        return True
```

---

## 三、与现有架构整合

### 3.1 整合 YoungAgent

```python
# 改进后的 YoungAgent

class YoungAgent:
    """带 AI Docker 支持的 Agent"""

    def __init__(self, config: AgentConfig):
        # 现有配置
        self.llm_client = create_llm_client(config.llm)

        # 新增: 沙箱运行时
        self.sandbox_pool = SandboxPool(config.sandbox)

        # 新增: 评估器
        self.evaluator = EvaluationCoordinator(config.evaluation)

        # 新增: 数据追踪
        self.data_tracker = DataTracker(config.data)

    async def run(self, task: str) -> AgentResult:
        """执行任务"""
        # 1. 获取或创建沙箱
        sandbox = await self.sandbox_pool.acquire()

        try:
            # 2. 生成评估计划
            eval_plan = await self.evaluator.generate_plan(task)

            # 3. 在沙箱中执行
            result = await sandbox.execute(
                code=self._generate_code(task),
                language="python",
            )

            # 4. 评估结果
            eval_result = await self.evaluator.evaluate_with_plan(
                task_description=task,
                actual_result=result.output,
                eval_plan=eval_plan,
            )

            # 5. 记录数据资产
            await self.data_tracker.record(
                task=task,
                result=result,
                evaluation=eval_result,
            )

            return AgentResult(
                output=result.output,
                evaluation=eval_result,
                metadata={
                    "sandbox_id": sandbox.id,
                    "duration_ms": result.duration_ms,
                }
            )
        finally:
            await self.sandbox_pool.release(sandbox)
```

### 3.2 整合评估系统

```python
# 新增: 运行时评估

class RuntimeEvaluator:
    """运行时评估器 - 对每次执行进行评估"""

    def __init__(self):
        self.quality_scorer = DataQualityScorer()

    async def evaluate_execution(
        self,
        task: str,
        result: ExecutionResult,
        context: dict,
    ) -> RuntimeEvaluation:
        """评估执行结果"""

        # 1. 基础质量检查
        quality_report = self.quality_scorer.score_run({
            "exit_code": result.exit_code,
            "duration_ms": result.duration_ms,
            "output_length": len(result.output),
            "error": result.error,
        })

        # 2. 任务完成度评估
        completion = self._evaluate_completion(task, result.output)

        # 3. 资源效率评估
        efficiency = self._evaluate_efficiency(result)

        return RuntimeEvaluation(
            quality=quality_report,
            completion=completion,
            efficiency=efficiency,
            overall_score=self._calculate_overall(
                quality_report,
                completion,
                efficiency
            )
        )
```

---

## 四、实施计划

### 阶段 1: 基础沙箱 (2周)

| 任务 | 描述 | 工作量 |
|------|------|--------|
| S1.1 | 创建 runtime 模块结构 | 1天 |
| S1.2 | 实现进程级沙箱 | 2天 |
| S1.3 | 实现资源限制 (CPU/Memory) | 2天 |
| S1.4 | 实现命令白名单 | 1天 |
| S1.5 | 集成到 ToolExecutor | 2天 |

### 阶段 2: 高级隔离 (2周)

| 任务 | 描述 | 工作量 |
|------|------|--------|
| S2.1 | 容器级隔离 (Docker in Docker) | 3天 |
| S2.2 | 网络访问控制 | 2天 |
| S2.3 | 文件系统隔离 | 2天 |
| S2.4 | 安全审计日志 | 1天 |

### 阶段 3: 池化与弹性 (2周)

| 任务 | 描述 | 工作量 |
|------|------|--------|
| S3.1 | 实现沙箱实例池 | 2天 |
| S3.2 | 自动扩缩容 | 2天 |
| S3.3 | 状态持久化 | 2天 |
| S3.4 | 性能优化 | 2天 |

### 阶段 4: 评估集成 (2周)

| 任务 | 描述 | 工作量 |
|------|------|--------|
| S4.1 | 运行时评估器 | 2天 |
| S4.2 | 质量评分集成 | 1天 |
| S4.3 | 数据资产化增强 | 2天 |
| S4.4 | 可视化仪表板 | 1天 |

---

## 五、技术选型

### 5.1 沙箱技术对比

| 方案 | 启动时间 | 隔离性 | 复杂度 | 推荐 |
|------|----------|--------|--------|------|
| ptrace | 10ms | 低 | 低 | ✅ MVP |
| gvisor | 50ms | 中 | 中 | 未来 |
| Firecracker | 100ms | 高 | 高 | V2 |
| Docker | 500ms | 高 | 中 | 备选 |

**决策**: MVP 使用 ptrace + 资源限制，后续迁移 gvisor

### 5.2 关键技术栈

```toml
# pyproject.toml 新增依赖

[dependencies]
# 沙箱/隔离
gvisor = "0.9.0"          # 可选，生产级
psutil = "5.9.0"          # 资源监控

# 容器 (可选)
docker = "7.0.0"          # Docker SDK

# 安全
seccomp = "0.4.0"         # 系统调用过滤
bwrap = "0.8.0"           # Bubblewrap (Linux)

# 性能
aiodocker = "0.24.0"      # 异步 Docker
```

---

## 六、API 设计

### 6.1 Sandbox API

```yaml
# OpenAPI 3.0

paths:
  /api/v1/sandboxes:
    post:
      summary: 创建沙箱
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                agent_id:
                  type: string
                config:
                  $ref: '#/components/schemas/SandboxConfig'
      responses:
        '201':
          description: 沙箱已创建
          content:
            application/json:
              schema:
                properties:
                  sandbox_id:
                    type: string

  /api/v1/sandboxes/{id}/execute:
    post:
      summary: 执行代码
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                code:
                  type: string
                language:
                  type: string
                  enum: [python, nodejs, bash]
      responses:
        '200':
          description: 执行结果
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExecutionResult'
```

---

## 七、监控与可观测性

### 7.1 关键指标

| 指标 | 描述 | 告警阈值 |
|------|------|----------|
| sandbox.create.latency | 沙箱创建延迟 | >1s |
| sandbox.execute.duration | 执行时长 | >5min |
| sandbox.pool.utilization | 池利用率 | >90% |
| sandbox.error.rate | 错误率 | >5% |
| execution.quality.score | 执行质量分 | <0.6 |

### 7.2 追踪上下文

```python
# 使用 OpenTelemetry 追踪
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("sandbox.execute")
async def execute_code(sandbox_id: str, code: str):
    span = trace.get_current_span()
    span.set_attribute("sandbox.id", sandbox_id)
    span.set_attribute("code.length", len(code))

    # 执行
    result = await sandbox.execute(code)

    # 记录结果
    span.set_attribute("result.exit_code", result.exit_code)
    span.set_attribute("result.duration_ms", result.duration_ms)

    return result
```

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 沙箱逃逸 | 高 | 分层隔离 + 监控 |
| 资源耗尽 | 中 | 严格限制 + 熔断 |
| 启动延迟 | 中 | 实例池预热 |
| 数据泄露 | 高 | 审计 + 加密 |

---

## 九、参考资源

- **E2B**: https://e2b.dev - AI agent sandbox
- **Modal**: https://modal.com - Serverless ML
- **gvisor**: https://gvisor.dev - Sandbox container runtime
- **Firecracker**: https://firecracker-microvm.io - Lightweight VMs

---

*本计划基于 E2B、Modal 等行业最佳实践制定*
