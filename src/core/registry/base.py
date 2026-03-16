"""
泛型注册表基类

参考 Django Model Registry 和 FastAPI 依赖注入设计
"""

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class RegistryItem:
    """注册项元数据"""

    key: str
    item: Any
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"
    metadata: dict = field(default_factory=dict)


class BaseRegistry(Generic[T]):
    """泛型注册表基类"""

    def __init__(self, name: str):
        self.name = name
        self._items: dict[str, RegistryItem] = {}
        self._listeners: list[Callable] = []
        self._lock = Lock()

    def register(
        self,
        key: str,
        item: T,
        metadata: dict = None,
        version: str = "1.0.0",
    ) -> None:
        """注册项"""
        with self._lock:
            now = datetime.now()
            self._items[key] = RegistryItem(
                key=key,
                item=item,
                created_at=now,
                updated_at=now,
                version=version,
                metadata=metadata or {},
            )
        self._notify("register", key, item)

    def unregister(self, key: str) -> bool:
        """注销项"""
        with self._lock:
            if key in self._items:
                item = self._items.pop(key)
                self._notify("unregister", key, item)
                return True
        return False

    def get(self, key: str) -> Optional[T]:
        """获取项"""
        registry_item = self._items.get(key)
        return registry_item.item if registry_item else None

    def get_metadata(self, key: str) -> Optional[RegistryItem]:
        """获取项元数据"""
        return self._items.get(key)

    def list(self) -> list[T]:
        """列出所有项"""
        return [ri.item for ri in self._items.values()]

    def list_with_metadata(self) -> list[RegistryItem]:
        """列出所有项（含元数据）"""
        return list(self._items.values())

    def exists(self, key: str) -> bool:
        """检查存在"""
        return key in self._items

    def search(self, query: str) -> list[T]:
        """搜索"""
        query_lower = query.lower()
        return [
            ri.item
            for ri in self._items.values()
            if query_lower in str(ri.item).lower()
            or query_lower in str(getattr(ri.item, "__name__", "")).lower()
        ]

    def filter(self, predicate: Callable[[T], bool]) -> list[T]:
        """过滤"""
        return [item for item in self.list() if predicate(item)]

    def count(self) -> int:
        """获取项数量"""
        return len(self._items)

    def clear(self) -> None:
        """清空注册表"""
        with self._lock:
            self._items.clear()
        self._notify("clear", "", None)

    def _notify(self, event: str, key: str, item: Any):
        """通知监听器"""
        for listener in self._listeners:
            try:
                listener(event, key, item)
            except Exception:
                pass  # 不应阻止其他监听器

    def add_listener(self, listener: Callable[[str, str, Any], None]) -> None:
        """添加监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[str, str, Any], None]) -> None:
        """移除监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
