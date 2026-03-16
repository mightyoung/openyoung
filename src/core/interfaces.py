"""
OpenYoung 核心接口定义

使用 Python Protocol 实现 Duck Typing，参考 Django 和 FastAPI 最佳实践
"""

from datetime import datetime
from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class BaseStorage(Protocol):
    """存储基础接口"""

    def save(self, key: str, value: Any) -> bool:
        """保存数据"""
        ...

    def load(self, key: str) -> Optional[Any]:
        """加载数据"""
        ...

    def delete(self, key: str) -> bool:
        """删除数据"""
        ...

    def exists(self, key: str) -> bool:
        """检查存在"""
        ...


@runtime_checkable
class BaseAgent(Protocol):
    """Agent 基础接口"""

    @property
    def name(self) -> str:
        """Agent 名称"""
        ...

    @property
    def description(self) -> str:
        """Agent 描述"""
        ...

    @property
    def capabilities(self) -> list[str]:
        """Agent 能力列表"""
        ...

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """执行任务"""
        ...

    async def validate(self, input_data: dict[str, Any]) -> bool:
        """验证输入"""
        ...


@runtime_checkable
class BaseEvaluator(Protocol):
    """评估器基础接口"""

    @property
    def name(self) -> str:
        """评估器名称"""
        ...

    @property
    def criteria(self) -> dict[str, float]:
        """评估标准及权重"""
        ...

    async def evaluate(self, result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
        """评估结果"""
        ...

    async def score(self, evaluation: dict[str, Any]) -> float:
        """计算分数"""
        ...


@runtime_checkable
class BaseTask(Protocol):
    """任务基础接口"""

    @property
    def task_id(self) -> str:
        """任务ID"""
        ...

    @property
    def status(self) -> str:
        """任务状态"""
        ...

    @property
    def created_at(self) -> datetime:
        """创建时间"""
        ...

    async def execute(self) -> dict[str, Any]:
        """执行任务"""
        ...

    async def cancel(self) -> bool:
        """取消任务"""
        ...


@runtime_checkable
class BaseRegistry(Protocol):
    """注册表基础接口"""

    def register(self, key: str, value: Any) -> None:
        """注册项"""
        ...

    def unregister(self, key: str) -> bool:
        """注销项"""
        ...

    def get(self, key: str) -> Optional[Any]:
        """获取项"""
        ...

    def list(self) -> list[Any]:
        """列出所有项"""
        ...

    def exists(self, key: str) -> bool:
        """检查存在"""
        ...


@runtime_checkable
class BaseConfig(Protocol):
    """配置基础接口"""

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        ...

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        ...

    def validate(self) -> bool:
        """验证配置"""
        ...
