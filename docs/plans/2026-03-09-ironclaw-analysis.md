# OpenYoung IronClaw 沙箱安全服务设计

> 研究 NearAI IronClaw 项目，探讨将其沙箱与安全机制包装为 Rust 服务
> Python 服务进行配置注入，实现 AI Docker 进一步设计

---

## 一、IronClaw 项目研究

### 1.1 项目概述

**来源**: https://github.com/nearai/ironclaw
**定位**: OpenClaw 的 Rust 实现，专注于隐私和安全
**理念**: "your AI assistant should work for you, not against you"
**技术栈**: Rust (91.2%), 8.4k stars

### 1.2 核心安全架构

```
WASM ──► Allowlist ──► Leak Scan ──► Credential ──► Execute ──► Leak Scan ──► WASM
 Validator (request) Injector Request (response)
```

**安全层次**:
1. **WASM 沙箱** - 能力-based 权限
2. **HTTP 白名单** - 只允许访问批准的主机/路径
3. **凭据注入** - 凭据在主机边界注入，从不暴露给 WASM 代码
4. **泄露检测** - 扫描请求和响应中的秘密泄露
5. **速率限制** - 每个工具的请求限制
6. **资源限制** - 内存、CPU，执行时间约束

### 1.3 提示注入防御

- 基于模式的注入尝试检测
- 内容清理和转义
- 策略规则：Block/Warn/Review/Sanitize
- 工具输出包装，安全注入 LLM 上下文

---

## 二、顶级专家视角分析

### 2.1 E2B 创始人视角

**E2B** 是最成功的 AI Agent 沙箱平台，其 CEO 说：

> "The sandbox is not just about isolation—it's about **observability and control**."

**会如何评价当前 OpenYoung 沙箱**:
- "这根本不是沙箱，只是 `exec()` 而已"
- 缺少 syscall 过滤
- 缺少网络隔离
- 缺少可观测性

### 2.2 IronClaw 团队视角

**IronClaw 团队在 README 中说**:
> "Defense in depth - multiple security layers against prompt injection and data exfiltration"

**设计原则**:
1. **数据主权** - 所有数据本地存储、加密，永不离开用户控制
2. **透明性** - 开源、可审计、无隐藏遥测
3. **自我扩展** - 无需供应商更新即可构建新工具
4. **纵深防御** - 多层安全防护

### 2.3 谷歌安全专家视角（Will Drewery）

**谷歌信息安全工程师 Will Drewery 说**:
> "You can't secure what you can't see. **Observability is security**."

**会建议**:
- 每次系统调用都应被记录
- 异常检测而非规则匹配
- 实时告警而非事后审计

---

## 三、架构设计方案

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OpenYoung Rust Security Service                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │   Python    │    │    gRPC     │    │   Config    │          │
│  │   Client    │───▶│   Server    │◀───│   Inject    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Security Orchestrator                         │      │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │      │
│  │  │Sandbox  │ │Prompt   │ │Network  │ │Secret   │      │      │
│  │  │Manager  │ │Detector │ │Firewall │ │Vault    │      │      │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │      │
│  └─────────────────────────────────────────────────────────┘      │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐      │
│  │              Telemetry Collector                          │      │
│  │  - syscalls  - network  - memory  - time  - leaks      │      │
│  └─────────────────────────────────────────────────────────┘      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件设计

#### 3.2.1 Rust 安全服务 (ironclaw-sandbox)

```rust
// 核心服务结构
pub struct SecurityService {
    sandbox_manager: SandboxManager,
    prompt_detector: PromptInjector,
    network_firewall: NetworkFirewall,
    secret_vault: SecretVault,
    telemetry: TelemetryCollector,
}

impl SecurityService {
    // 启动服务
    pub async fn start(&self, config: ServiceConfig) -> Result<(), Error>;

    // 创建沙箱实例
    pub async fn create_sandbox(&self, config: SandboxConfig) -> Result<SandboxId, Error>;

    // 执行代码
    pub async fn execute(&self, sandbox_id: SandboxId, code: Code) -> Result<ExecutionResult, Error>;

    // 检测提示注入
    pub fn detect_prompt_injection(&self, content: &str) -> DetectionResult;
}
```

#### 3.2.2 Python 配置注入

```python
# Python 客户端
class IronClawClient:
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = security_service_pb2_grpc.SecurityServiceStub(self.channel)

    def create_sandbox(self, config: SandboxConfig) -> SandboxHandle:
        request = CreateSandboxRequest(
            sandbox_type=config.sandbox_type,
            max_memory_mb=config.max_memory_mb,
            max_cpu_percent=config.max_cpu_percent,
            max_execution_time_seconds=config.max_execution_time_seconds,
            allowed_domains=config.allowed_domains,
            allowed_paths=config.allowed_paths,
            environment=config.environment,
        )
        return self.stub.CreateSandbox(request)

    def execute(self, sandbox_id: str, code: str, language: str) -> ExecutionResult:
        request = ExecuteRequest(
            sandbox_id=sandbox_id,
            code=code,
            language=language,
        )
        return self.stub.Execute(request)
```

### 3.3 gRPC 接口定义

```protobuf
// security_service.proto
syntax = "proto3";

package ironclaw;

service SecurityService {
    // 沙箱管理
    rpc CreateSandbox(SandboxConfig) returns (SandboxHandle);
    rpc DestroySandbox(SandboxId) returns (Empty);
    rpc ListSandboxes(Empty) returns (SandboxList);

    // 执行
    rpc Execute(ExecuteRequest) returns (ExecutionResult);
    rpc ExecuteStream(ExecuteRequest) returns (stream ExecutionChunk);

    // 安全检测
    rpc DetectPromptInjection(Content) returns (DetectionResult);
    rpc ScanForSecrets(Content) returns (SecretScanResult);

    // 遥测
    rpc GetTelemetry(SandboxId) returns (Telemetry);
    rpc StreamTelemetry(SandboxId) returns (stream TelemetryEvent);
}

message SandboxConfig {
    SandboxType sandbox_type = 1;
    int32 max_memory_mb = 2;
    float max_cpu_percent = 3;
    int32 max_execution_time_seconds = 4;
    repeated string allowed_domains = 5;
    repeated string allowed_paths = 6;
    map<string, string> environment = 7;
    bool enable_prompt_injection_detection = 8;
    bool enable_secret_leak_detection = 9;
}

message ExecutionResult {
    string output = 1;
    string error = 2;
    int32 exit_code = 3;
    int64 duration_ms = 4;
    Telemetry telemetry = 5;
}

message Telemetry {
    repeated SyscallEntry syscalls = 1;
    repeated NetworkRequest network_requests = 2;
    repeated FileOperation file_operations = 3;
    repeated MemorySample memory_samples = 4;
    repeated CPUSample cpu_samples = 5;
}
```

---

## 四、实施方案

### 4.1 阶段一：Rust 基础服务

**目标**: 构建核心沙箱服务

| 任务 | 文件 | 描述 |
|------|------|------|
| 项目初始化 | `rust/ironclaw-sandbox/Cargo.toml` | 创建 Rust 项目 |
| gRPC 定义 | `rust/ironclaw-sandbox/proto/security.proto` | 定义接口 |
| 沙箱管理器 | `rust/ironclaw-sandbox/src/sandbox.rs` | 进程隔离 |
| 网络防火墙 | `rust/ironclaw-sandbox/src/firewall.rs` | HTTP 白名单 |
| 提示注入检测 | `rust/ironclaw-sandbox/src/prompt.rs` | 模式匹配 |

### 4.2 阶段二：安全增强

**目标**: 添加高级安全功能

| 任务 | 文件 | 描述 |
|------|------|------|
| 凭据保险库 | `rust/ironclaw-sandbox/src/vault.rs` | 加密存储 |
| 泄露检测 | `rust/ironclaw-sandbox/src/leak.rs` | 扫描敏感数据 |
| 遥测收集 | `rust/ironclaw-sandbox/src/telemetry.rs` | 系统调用追踪 |

### 4.3 阶段三：Python 集成

**目标**: Python 客户端

| 任务 | 文件 | 描述 |
|------|------|------|
| gRPC 客户端 | `src/runtime/ironclaw_client.py` | Python 客户端 |
| 配置适配器 | `src/runtime/config_adapter.py` | 配置转换 |
| 异常处理 | `src/runtime/exceptions.py` | 错误标准化 |

---

## 五、与 OpenYoung 集成

### 5.1 替换现有沙箱

```python
# 现有代码
from src.runtime.sandbox import SandboxInstance

# 新代码
from src.runtime.ironclaw_client import IronClawSandbox

class OpenYoungRuntime:
    def __init__(self):
        # 替换为 IronClaw 沙箱
        self.sandbox = IronClawSandbox(
            host="localhost",
            port=50051,
            default_config=SandboxConfig(
                sandbox_type="ephemeral",
                max_memory_mb=512,
                max_cpu_percent=50.0,
                max_execution_time_seconds=300,
            )
        )
```

### 5.2 配置示例

```python
# 生产配置
production_config = SandboxConfig(
    sandbox_type="pool",
    max_memory_mb=1024,
    max_cpu_percent=80.0,
    max_execution_time_seconds=600,
    allowed_domains=[
        "api.github.com",
        "api.openai.com",
    ],
    allowed_paths=[
        "/tmp/openyoung",
        "/Users/muyi/Downloads/dev/openyoung/output",
    ],
    enable_prompt_injection_detection=True,
    enable_secret_leak_detection=True,
)
```

---

## 六、关键技术选型

### 6.1 沙箱技术

| 技术 | 选型 | 理由 |
|------|------|------|
| 进程隔离 | subprocess + seccomp | 简单可靠 |
| 网络隔离 | iptables/nftables | 内核级 |
| 资源限制 | cgroups v2 | 容器标准 |
| WASM 沙箱 | wasmer | Rust 生态成熟 |

### 6.2 网络安全

| 技术 | 选型 | 理由 |
|------|------|------|
| HTTP 白名单 | domain + path 匹配 | 灵活 |
| DNS 过滤 | rustdns | 防止 DNS 隧道 |
| TLS 检查 | rustls | 内存安全 |

### 6.3 检测规则

| 类型 | 实现 | 性能 |
|------|------|------|
| 模式匹配 | regex + aho-corasick | O(n) |
| 语义检测 | 本地 LLM | 高延迟 |
| 泄露扫描 | entropy + pattern | O(n) |

---

## 七、总结

### 7.1 核心价值

1. **纵深防御** - 多层安全防护，而非单一边界
2. **可观测性** - 每个操作都可追踪和审计
3. **数据主权** - 凭据永不暴露给沙箱代码
4. **实时检测** - 提示注入和泄露在执行前阻断

### 7.2 与 OpenYoung 集成方式

| 组件 | 替换/新增 | 方式 |
|------|-----------|------|
| 沙箱执行 | 替换 | gRPC 调用 |
| 网络控制 | 新增 | Rust 服务 |
| 提示注入检测 | 新增 | Rust 服务 |
| 遥测收集 | 新增 | Rust 服务 |

---

*报告生成时间: 2026-03-09*
*参考资料: NearAI IronClaw, E2B, 谷歌安全最佳实践*
