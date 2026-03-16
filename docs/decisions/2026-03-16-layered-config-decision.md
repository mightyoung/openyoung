# 决策文档: 分层配置管理

> 日期: 2026-03-16
> 问题: 配置管理分散
> 决策: B - 分层配置管理

---

## 1. 问题背景

现状配置分散在多个位置：

```
config/loader.py      - 运行时配置
agents/default.yaml   - Agent 默认配置
pyproject.toml       - 项目配置
.env                 - 环境变量/API keys
```

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| 12-Factor App | 配置与环境分离，环境变量优先级最高 |
| Pydantic | 类型安全的配置管理，嵌套配置 |
| Dynaconf | 分层配置，支持多格式 |

### 2.2 分层优先级

```
┌─────────────────────────────────────────────────────────────────┐
│                    配置优先级 (高 → 低)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CLI 参数          (最高优先级)                              │
│     └── --config=/path/to/config.yaml                           │
│                                                                  │
│  2. 环境变量          (用户自定义)                              │
│     └── OPENYOUNG_CONFIG=/path/to/config.yaml                   │
│                                                                  │
│  3. 本地配置文件      (项目级别)                                │
│     └── ./openyoung.yaml                                       │
│                                                                  │
│  4. 用户配置          (用户级别)                                │
│     └── ~/.config/openyoung/config.yaml                         │
│                                                                  │
│  5. 默认配置          (最低优先级)                              │
│     └── src/config/default.yaml                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 决策详情

### 3.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    配置加载流程                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                               │
│  │ ConfigLoader │ ◄── 单例入口                                   │
│  └──────┬──────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    LayeredConfig                           │  │
│  │                                                           │  │
│  │   ┌─────────┐                                             │  │
│  │   │   CLI   │ ──▶ 命令行参数                              │  │
│  │   └────┬────┘                                             │  │
│  │        │                                                   │  │
│  │   ┌────┴────┐                                             │  │
│  │   │   Env   │ ──▶ 环境变量 OY_*                          │  │
│  │   └────┬────┘                                             │  │
│  │        │                                                   │  │
│  │   ┌────┴────┐                                             │  │
│  │   │  Local  │ ──▶ ./openyoung.yaml                       │  │
│  │   └────┬────┘                                             │  │
│  │        │                                                   │  │
│  │   ┌────┴────┐                                             │  │
│  │   │  User   │ ──▶ ~/.config/openyoung/config.yaml       │  │
│  │   └────┬────┘                                             │  │
│  │        │                                                   │  │
│  │   ┌────┴────┐                                             │  │
│  │   │ Default │ ──▶ src/config/default.yaml                │  │
│  │   └─────────┘                                             │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MergedConfig (不可变)                         │  │
│  │                                                           │  │
│  │   - llm: LLMConfig                                      │  │
│  │   - sandbox: SandboxConfig                              │  │
│  │   - evaluation: EvalConfig                              │  │
│  │   - storage: StorageConfig                              │  │
│  │   - security: SecurityConfig                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心接口

```python
# src/config/base.py
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from enum import Enum

class ConfigSource(Enum):
    DEFAULT = "default"
    USER = "user"
    LOCAL = "local"
    ENV = "env"
    CLI = "cli"

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

class SandboxConfig(BaseModel):
    """沙箱配置"""
    max_execution_time_seconds: int = 300
    max_memory_mb: int = 512
    allow_network: bool = True
    allowed_domains: list[str] = []

class EvaluationConfig(BaseModel):
    """评估配置"""
    enabled: bool = True
    default_evaluator: str = "llm_judge"
    timeout_seconds: int = 60
    retry_count: int = 3

class OpenYoungConfig(BaseModel):
    """主配置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

    class Config:
        frozen = True  # 不可变
```

### 3.3 配置加载器

```python
# src/config/loader.py
from pathlib import Path
from typing import Optional
import os

class ConfigLoader:
    """分层配置加载器"""

    DEFAULT_CONFIG_PATHS = [
        Path("./openyoung.yaml"),
        Path("./openyoung.yml"),
        Path.home() / ".config" / "openyoung" / "config.yaml",
        Path(__file__).parent / "default.yaml",
    ]

    def __init__(self):
        self._config: Optional[OpenYoungConfig] = None

    def load(
        self,
        cli_path: Optional[Path] = None,
        env_prefix: str = "OY_",
    ) -> OpenYoungConfig:
        """加载配置"""

        # 1. 加载默认配置
        config = self._load_default()

        # 2. 合并用户配置
        config = self._merge(config, self._load_user())

        # 3. 合并本地配置
        config = self._merge(config, self._load_local())

        # 4. 合并环境变量
        config = self._merge(config, self._load_env(env_prefix))

        # 5. 合并CLI配置
        if cli_path:
            config = self._merge(config, self._load_file(cli_path))

        self._config = config
        return config

    def _merge(self, base: dict, override: dict) -> dict:
        """深度合并配置"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            elif value is not None:
                result[key] = value
        return result
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 配置模型定义 | `src/config/models.py` |
| Phase 2 | 分层加载器 | `src/config/loader.py` |
| Phase 3 | 环境变量解析 | `src/config/env.py` |
| Phase 4 | CLI 集成 | `src/cli/config.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 配置覆盖混乱 | 预期外的值 | 日志记录来源 |
| 密码泄露 | 安全风险 | 支持 env:// 前缀从环境变量读取 |

---

## 6. 参考实现

- 12-Factor App: https://12factor.net/config
- Pydantic Settings: https://docs.pydantic.dev/latest/usage/settings/
- Dynaconf: https://www.dynaconf.com/

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准
