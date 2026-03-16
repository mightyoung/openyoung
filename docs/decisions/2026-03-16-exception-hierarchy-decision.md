# 决策文档: 统一错误处理架构

> 日期: 2026-03-16
> 问题: 缺乏统一的错误处理
> 决策: A - 分层异常架构

---

## 1. 问题背景

现状每个模块自己 try/except，无统一模式：

```python
# 现状 - 分散的错误处理
src/agents/young_agent.py:
    try:
        result = await self.execute()
    except Exception as e:
        logger.error(e)

src/tools/executor.py:
    try:
        tool.execute()
    except Exception as e:
        return ErrorResult(e)
```

## 2. 调研结果

### 2.1 行业最佳实践

| 来源 | 关键洞见 |
|------|----------|
| Stack Overflow | 自定义异常类，避免字符串存储错误信息 |
| Augment Code | 企业级10大技巧：Fail Fast, Catch Narrow |
| FastAPI | 统一异常处理，HTTPException层次 |

### 2.2 核心原则

| 原则 | 描述 |
|------|------|
| Fail Fast | 尽快检测错误，不要传递错误数据 |
| Catch Narrow | 捕获具体异常，避免 bare except |
| Custom Exceptions | 为领域特定错误定义自定义异常 |
| 异常分层 | 按模块划分异常层次结构 |

## 3. 决策详情

### 3.1 异常层次结构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python 异常层次                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  BaseException                                                   │
│       │                                                          │
│       └── Exception                                             │
│                │                                                 │
│                ├── OpenYoungError (基础异常)                     │
│                │        │                                        │
│                │        ├── AgentError                           │
│                │        │    │                                   │
│                │        │    ├── AgentNotFoundError              │
│                │        │    ├── AgentExecutionError             │
│                │        │    └── AgentTimeoutError              │
│                │        │                                        │
│                │        ├── ExecutionError                       │
│                │        │    │                                   │
│                │        │    ├── SandboxError                   │
│                │        │    ├── ResourceLimitError             │
│                │        │    └── ExecutionTimeoutError         │
│                │        │                                        │
│                │        ├── EvaluationError                      │
│                │        │    │                                   │
│                │        │    ├── EvaluationTimeoutError         │
│                │        │    └── EvaluationFailedError          │
│                │        │                                        │
│                │        ├── ConfigurationError                  │
│                │        │    │                                   │
│                │        │    ├── ConfigNotFoundError           │
│                │        │    └── ConfigValidationError         │
│                │        │                                        │
│                │        └── StorageError                        │
│                │             │                                   │
│                │             ├── StorageNotFoundError           │
│                │             └── StorageConnectionError         │
│                │                                                 │
│                └── (其他标准异常)                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心接口

```python
# src/core/exceptions.py
class OpenYoungError(Exception):
    """OpenYoung 基础异常"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

class AgentError(OpenYoungError):
    """Agent 相关错误"""
    pass

class AgentNotFoundError(AgentError):
    """Agent 未找到"""
    pass

class AgentExecutionError(AgentError):
    """Agent 执行错误"""
    pass

class ExecutionError(OpenYoungError):
    """执行相关错误"""
    pass

class SandboxError(ExecutionError):
    """沙箱执行错误"""
    pass

class EvaluationError(OpenYoungError):
    """评估相关错误"""
    pass

class ConfigurationError(OpenYoungError):
    """配置相关错误"""
    pass

class StorageError(OpenYoungError):
    """存储相关错误"""
    pass
```

### 3.3 错误处理装饰器

```python
# src/core/exceptions.py
from functools import wraps
from typing import TypeVar, Callable
import logging

T = TypeVar('T')

def handle_errors(
    error_class: Type[OpenYoungError] = OpenYoungError,
    reraise: bool = True,
    default_return: T = None,
):
    """错误处理装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except OpenYoungError:
                raise
            except Exception as e:
                logging.error(f"Unexpected error in {func.__name__}: {e}")
                if reraise:
                    raise error_class(str(e)) from e
                return default_return
        return async_wrapper
    return decorator

    # 同步版本
    @wraps(func)
    def sync_wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except OpenYoungError:
            raise
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            if reraise:
                raise error_class(str(e)) from e
            return default_return
    return sync_wrapper
```

### 3.4 全局异常处理器

```python
# src/core/exception_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

async def openyoung_exception_handler(request: Request, exc: OpenYoungError):
    """全局异常处理"""
    return JSONResponse(
        status_code=_get_http_status(exc),
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "timestamp": exc.timestamp.isoformat(),
        }
    )

def _get_http_status(error: OpenYoungError) -> int:
    """异常到HTTP状态码映射"""
    mapping = {
        AgentNotFoundError: 404,
        AgentExecutionError: 500,
        SandboxError: 500,
        ConfigurationError: 400,
        StorageError: 500,
    }
    for error_type, status in mapping.items():
        if isinstance(error, error_type):
            return status
    return 500
```

## 4. 实施计划

| 阶段 | 任务 | 文件 |
|------|------|------|
| Phase 1 | 定义异常层次 | `src/core/exceptions.py` |
| Phase 2 | 异常处理工具 | `src/core/exception_handler.py` |
| Phase 3 | 迁移现有异常 | 各模块逐步迁移 |
| Phase 4 | 全局处理器 | `src/api/middleware.py` |

## 5. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 迁移破坏 | 现有代码报错 | 渐进迁移，保留兼容性 |
| 异常丢失 | 错误信息丢失 | 保留原始异常作为cause |

---

## 6. 参考实现

- FastAPI Exception Handling: https://fastapi.tiangolo.com/tutorial/handling-errors/
- Python Exception Best Practices: https://stackoverflow.com/questions/839636

---

**决策人**: Claude + User
**决策日期**: 2026-03-16
**状态**: 已批准
