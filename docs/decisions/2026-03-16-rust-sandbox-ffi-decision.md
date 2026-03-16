# 决策文档: Rust Sandbox 深度集成

> 日期: 2026-03-16
> 问题: Rust Sandbox 深度集成
> 决策: B - FFI桥接 (PyO3/Maturin)

---

## 1. 问题背景

Rust sandbox 已有基础实现，需要与 Python 深度集成。

## 2. 调研结果

### 2.1 Rust-Python 集成技术对比

| 技术 | 成熟度 | 性能 | 开发成本 | 适用场景 |
|------|--------|------|----------|----------|
| **PyO3 + Maturin** | ⭐⭐⭐⭐⭐ | 极高 | 中等 | Python模块级别集成 |
| ctypes FFI | ⭐⭐⭐ | 高 | 低 | 简单函数调用 |
| gRPC | ⭐⭐⭐⭐ | 中等 | 高 | 进程隔离服务 |
| wasmtime | ⭐⭐⭐ | 高 | 高 | WebAssembly沙箱 |

### 2.2 沙箱安全最佳实践（2026）

| 层级 | 技术 | 描述 |
|------|------|------|
| 进程隔离 | gVisor, Kata Containers | 微VM隔离 |
| 防御深度 | Zero Trust | 多层验证 |
| 文件隔离 | 工作目录限制 | 防止路径穿越 |
| 网络隔离 | 无网络模式 | 外部工具代理 |

> **关键洞见**：容器不是沙箱！需要microVMs或gVisor实现真正隔离。

### 2.3 推荐方案

**PyO3 + Maturin** - 理由：
1. **成熟度最高** - Rust官方维护，3000+ GitHub stars
2. **性能最优** - 零拷贝内存共享
3. **开发效率** - 一键构建，Python直接import
4. **安全可控** - Rust编译器保证内存安全

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│              推荐架构：PyO3 FFI 桥接                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Python 层                  Rust 层 (PyO3)                        │
│  ┌───────────┐          ┌──────────────────┐                  │
│  │ Sandbox    │  ◄─────► │ ironclaw-sandbox │                  │
│  │ Client    │   FFI    │                  │                  │
│  └───────────┘          │ - 沙箱隔离       │                  │
│                         │ - 资源限制       │                  │
│                         │ - 安全策略       │                  │
│                         └──────────────────┘                  │
│                                                                  │
│  优势：                                                          │
│  • 内存零拷贝（通过PyO3）                                       │
│  • 编译期类型检查                                                │
│  • Rust安全保证                                                  │
│  • 独立Python包安装                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Rust 实现 (PyO3)

```rust
// rust/ironclaw-sandbox/src/lib.rs
use pyo3::prelude::*;
use pyo3::wrap_pyfunction;

#[pyclass]
pub struct SandboxInstance {
    config: SandboxConfig,
    working_dir: PathBuf,
}

#[pymethods]
impl SandboxInstance {
    #[new]
    fn new(config: SandboxConfig) -> Self {
        SandboxInstance {
            config,
            working_dir: std::env::temp_dir(),
        }
    }

    fn execute(&self, code: &str, language: &str) -> PyResult<ExecutionResult> {
        // 执行代码
        Ok(ExecutionResult {
            output: "...".to_string(),
            exit_code: 0,
            duration_ms: 100,
        })
    }

    fn check_security(&self, code: &str) -> PyResult<SecurityCheckResult> {
        // 安全检查
        Ok(SecurityCheckResult {
            safe: true,
            warnings: vec![],
        })
    }
}

#[pyclass]
#[derive(Debug, Clone)]
pub struct SandboxConfig {
    max_execution_time_ms: u64,
    max_memory_mb: u64,
    allow_network: bool,
}

#[pymodule]
fn ironclaw_sandbox(m: &PyModule) -> PyResult<()> {
    m.add_class::<SandboxInstance>()?;
    m.add_class::<SandboxConfig>()?;
    Ok(())
}
```

### 3.3 Python 包装

```python
# src/runtime/sandbox/rust_wrapper.py
import ironclaw_sandbox
from typing import Optional
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    output: str
    exit_code: int
    duration_ms: int
    error: Optional[str] = None

@dataclass
class SecurityCheckResult:
    safe: bool
    warnings: list[str]
    blocked: bool = False

class RustSandbox:
    """Rust 沙箱包装器"""

    def __init__(
        self,
        max_execution_time_ms: int = 300000,
        max_memory_mb: int = 512,
        allow_network: bool = False,
    ):
        config = ironclaw_sandbox.SandboxConfig(
            max_execution_time_ms=max_execution_time_ms,
            max_memory_mb=max_memory_mb,
            allow_network=allow_network,
        )
        self._instance = ironclaw_sandbox.SandboxInstance(config)

    def execute(self, code: str, language: str) -> ExecutionResult:
        """执行代码"""
        result = self._instance.execute(code, language)
        return ExecutionResult(
            output=result.output,
            exit_code=result.exit_code,
            duration_ms=result.duration_ms,
            error=result.error,
        )

    def check_security(self, code: str) -> SecurityCheckResult:
        """安全检查"""
        result = self._instance.check_security(code)
        return SecurityCheckResult(
            safe=result.safe,
            warnings=list(result.warnings),
            blocked=result.blocked,
        )
```

### 3.4 构建配置

```toml
# rust/ironclaw-sandbox/Cargo.toml
[package]
name = "ironclaw-sandbox"
version = "0.1.0"
edition = "2021"

[lib]
name = "ironclaw_sandbox"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

[build-dependencies]
pyo3-build-config = "0.20"

[profile.release]
opt-level = 3
lto = true
```

### 3.5 Maturin 配置

```toml
# rust/ironclaw-sandbox/maturin.toml
[tool.maturin]
features = ["extension-module"]
python-source = "."
module-name = "ironclaw_sandbox"
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 定义 Rust API | `rust/ironclaw-sandbox/src/lib.rs` |
| Phase 2 | PyO3 绑定 | `rust/ironclaw-sandbox/src/bindings.rs` |
| Phase 3 | Python 包装 | `src/runtime/sandbox/rust_wrapper.py` |
| Phase 4 | 构建配置 | `rust/ironclaw-sandbox/Cargo.toml` |
| Phase 5 | 测试验证 | `tests/test_rust_sandbox.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 编译失败 | 无法使用 | 保留 Python 实现作为后备 |
| 内存泄漏 | 进程崩溃 | Rust 所有权系统保证安全 |
| 版本不兼容 | 运行时错误 | 严格版本范围 |

---

## 6. 参考实现

- PyO3 Official: https://pyo3.rs/
- Maturin: https://maturin.rs/
- Northflank Sandbox: https://northflank.com/blog/how-to-sandbox-ai-agents

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准
