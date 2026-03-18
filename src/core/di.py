"""
依赖注入容器

参考 FastAPI 依赖注入系统设计
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type, TypeVar

T = TypeVar("T")


@dataclass
class Dependency:
    """依赖项定义"""

    factory: Callable[..., Any]
    singleton: bool = True
    instance: Optional[Any] = None


class Container:
    """依赖注入容器"""

    def __init__(self):
        self._dependencies: dict[str, Dependency] = {}
        self._overrides: dict[str, Callable[..., Any]] = {}

    def register(
        self,
        token: str,
        factory: Callable[..., T],
        singleton: bool = True,
    ) -> None:
        """注册依赖

        Args:
            token: 依赖标识符
            factory: 工厂函数
            singleton: 是否单例
        """
        self._dependencies[token] = Dependency(
            factory=factory,
            singleton=singleton,
        )

    def register_instance(self, token: str, instance: T) -> None:
        """注册实例（单例模式）

        Args:
            token: 依赖标识符
            instance: 实例对象
        """
        self._dependencies[token] = Dependency(
            factory=lambda: instance,
            singleton=True,
            instance=instance,
        )

    def register_override(self, token: str, factory: Callable[..., T]) -> None:
        """注册覆盖（用于测试）

        Args:
            token: 依赖标识符
            factory: 覆盖的工厂函数
        """
        self._overrides[token] = factory

    def resolve(self, token: str) -> Any:
        """解析依赖

        Args:
            token: 依赖标识符

        Returns:
            依赖实例
        """
        # 检查覆盖
        if token in self._overrides:
            return self._overrides[token]()

        if token not in self._dependencies:
            raise KeyError(f"Dependency not registered: {token}")

        dep = self._dependencies[token]

        # 单例模式，直接返回实例
        if dep.singleton and dep.instance is not None:
            return dep.instance

        # 创建新实例
        instance = dep.factory()

        # 如果是单例，保存实例
        if dep.singleton:
            dep.instance = instance

        return instance

    def resolve_with_kwargs(
        self,
        token: str,
        **kwargs: Any,
    ) -> Any:
        """带参数解析依赖

        Args:
            token: 依赖标识符
            **kwargs: 额外参数

        Returns:
            依赖实例
        """
        # 检查覆盖
        if token in self._overrides:
            return self._overrides[token](**kwargs)

        if token not in self._dependencies:
            raise KeyError(f"Dependency not registered: {token}")

        dep = self._dependencies[token]

        # 单例模式，直接返回实例
        if dep.singleton and dep.instance is not None:
            return dep.instance

        # 创建新实例
        instance = dep.factory(**kwargs)

        # 如果是单例，保存实例
        if dep.singleton:
            dep.instance = instance

        return instance

    def clear(self) -> None:
        """清空容器"""
        self._dependencies.clear()
        self._overrides.clear()

    def clear_singletons(self) -> None:
        """清空单例缓存"""
        for dep in self._dependencies.values():
            dep.instance = None


# 全局容器实例
_container: Optional[Container] = None
_initialized = False


def _register_dependencies() -> None:
    """注册所有 YoungAgent 依赖"""
    global _container, _initialized
    if _initialized or _container is None:
        return

    try:
        from src.core.dependencies import register_young_agent_dependencies
        register_young_agent_dependencies(_container)
        _initialized = True
    except ImportError as e:
        # dependencies 模块可能不存在，静默失败
        pass


def get_container() -> Container:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = Container()
        # 首次创建容器时注册依赖
        _register_dependencies()
    return _container


def set_container(container: Container) -> None:
    """设置全局容器实例"""
    global _container
    _container = container


# 装饰器支持
def inject(**dependencies: str) -> Callable[[T], T]:
    """依赖注入装饰器

    Usage:
        @inject(storage=Storage, config=Config)
        def my_func(storage, config):
            ...
    """

    def decorator(func: T) -> T:
        # 保留原始函数签名
        return func  # 类型提示装饰器，不实际修改函数

    return decorator
