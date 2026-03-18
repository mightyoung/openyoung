"""
Vector Store - 向量存储封装
基于 SQLiteStorage 的 embedding 功能
"""

from typing import Any


class VectorStore:
    """向量存储 - 语义搜索核心

    功能：
    - 存储文本和对应的 embedding
    - 支持相似度搜索
    - 命名空间隔离
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/Users/muyi/Downloads/dev/openyoung/.young/data.db"
        self._storage = None
        self._embedding_client = None
        self._init_storage()

    def _init_storage(self):
        """初始化存储"""
        try:
            from src.datacenter.sqlite_storage import EmbeddingClient, SQLiteStorage

            self._storage = SQLiteStorage(self.db_path)
            self._embedding_client = EmbeddingClient()
        except Exception as e:
            print(f"[VectorStore] Init warning: {e}")

    def add(
        self,
        content: str,
        namespace: str = "default",
        tags: list[str] = None,
        importance: float = 0.5,
    ) -> bool:
        """添加文本到向量存储"""
        if not self._storage or not self._embedding_client:
            return False

        try:
            # 获取 embedding
            embeddings = self._embedding_client.embed([content])
            if embeddings:
                self._storage.add_memory(
                    content=content,
                    embedding=embeddings[0],
                    namespace=namespace,
                    tags=tags,
                    importance=importance,
                )
                return True
        except Exception as e:
            print(f"[VectorStore] Add error: {e}")
        return False

    def search(
        self, query: str, namespace: str = "default", limit: int = 5, threshold: float = 0.0
    ) -> list[dict[str, Any]]:
        """语义搜索"""
        if not self._storage or not self._embedding_client:
            return []

        try:
            # 获取查询的 embedding
            embeddings = self._embedding_client.embed([query])
            if not embeddings:
                return []

            # 搜索相似内容
            results = self._storage.search_memory(
                embedding=embeddings[0],
                namespace=namespace,
                limit=limit,
            )

            # 过滤低于阈值的结果
            if threshold > 0:
                results = [r for r in results if r.get("similarity", 0) >= threshold]

            return results
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            return []

    def list_namespaces(self) -> list[str]:
        """列出所有命名空间"""
        if not self._storage:
            return []

        # 尝试从数据库查询命名空间
        try:
            import sqlite3

            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT DISTINCT namespace FROM memory")
            namespaces = [row[0] for row in cursor.fetchall()]
            conn.close()
            return namespaces
        except Exception as e:
            print(f"[VectorStore] List namespaces error: {e}")
            return []

    def list(self, namespace: str = "default", limit: int = 10) -> list[dict[str, Any]]:
        """列出命名空间中的记忆条目"""
        if not self._storage:
            return []

        try:
            # 直接查询数据库获取记忆条目
            results = self._storage.search_memory(
                namespace=namespace,
                limit=limit,
            )
            return results
        except Exception as e:
            print(f"[VectorStore] List error: {e}")
            return []

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        if not self._storage:
            return {"status": "not_initialized"}

        try:
            namespaces = self.list_namespaces()
            return {
                "status": "ready",
                "namespaces": len(namespaces),
                "namespace_list": namespaces,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# 全局实例
_vector_store = None


def get_vector_store() -> VectorStore:
    """获取全局 VectorStore 实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
