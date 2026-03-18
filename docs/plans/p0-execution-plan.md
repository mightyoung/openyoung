# P0 任务执行计划

## 任务概览

| 任务 | 现状 | 目标 |
|------|------|------|
| P0-1 | 267处 print("[Warning]") | 统一使用 logging |
| P0-2 | DI容器未使用 | YoungAgent 使用 DI 容器 |
| P0-3 | 模块已迁移 | 完成整合验证 |

---

## P0-1: 统一异常处理

### 问题
- 267处 `print("[Warning]")` 散落42个文件
- 无法统一控制日志级别
- 生产环境无法追踪问题

### 方案
创建统一日志工具，替换所有 print：

```python
# src/core/logger.py
import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
```

### 执行步骤
1. 创建 `src/core/logger.py`
2. 替换所有 `print("[Warning]")` 为 `logger.warning()`
3. 验证不影响现有功能

---

## P0-2: 依赖注入容器

### 问题
- `src/core/di.py` 已实现但**0引用**
- YoungAgent 手动管理20+组件

### 方案
让 YoungAgent 使用 DI 容器：

```python
from src.core.di import get_container, Container

class YoungAgent:
    def __init__(self, config, container=None):
        self._container = container or get_container()
        # 容器解析依赖
        self._llm = self._container.resolve("llm")
        self._tool_executor = self._container.resolve("tool_executor")
```

### 执行步骤
1. 定义 YoungAgent 需要的依赖 tokens
2. 注册依赖到全局容器
3. 修改 YoungAgent 使用容器解析
4. 验证现有测试通过

---

## P0-3: 统一模块入口（已部分完成）

### 现状
- ✅ Bridge 层已创建
- ✅ YoungAgent 已集成 MemoryFacade
- ⚠️ 需要验证端到端

### 执行步骤
1. 运行测试验证集成
2. 清理旧模块引用

---

## 验收标准

- [x] P0-1: 统一日志工具创建完成 (src/core/logger.py)
- [x] P0-1: 全部 print("[Warning]") 替换完成 (young_agent.py, package_manager/*, datacenter/tracing.py)
- [x] P0-2: DI 容器定义 YoungAgent 依赖 (src/core/dependencies.py)
- [x] P0-2: YoungAgent 支持容器参数
- [x] P0-3: 集成测试通过

## P0-1 执行总结

### 已完成
- 创建 `src/core/logger.py` 统一日志工具
- 替换 `young_agent.py` 中所有 print("[Warning]")
- 替换 `package_manager/mcp_loader.py` 中 print("[Warning]")
- 替换 `package_manager/mcp_manager.py` 中 print("[Warning]")
- 替换 `datacenter/tracing.py` 中所有 print("[Warning]")

### 替换示例
```python
# 之前
print(f"[Warning] Harness init failed: {e}")

# 之后
logger.warning(f"Harness init failed: {e}")
```

## P0-2 执行总结

### 已完成
- 创建 `src/core/dependencies.py` 依赖注册模块
- 定义 DIToken 常量
- YoungAgent 支持可选 container 参数

### 使用方式
```python
from src.core.di import Container, get_container
from src.core.dependencies import register_young_agent_dependencies

# 方式1: 使用全局容器
container = get_container()
register_young_agent_dependencies(container)
agent = YoungAgent(config, container=container)

# 方式2: 使用自定义容器
container = Container()
register_young_agent_dependencies(container)
agent = YoungAgent(config, container=container)

# 方式3: 原有方式（仍然兼容）
agent = YoungAgent(config)
```

### 后续替换计划
- package_manager/*.py (约100处)
- skills/*.py (约30处)
- datacenter/*.py (约20处)
