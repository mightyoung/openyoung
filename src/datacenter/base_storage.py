"""
BaseStorage - 数据库存储基类
解决代码重复问题，统一错误处理
"""

import json
import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

# 获取模块级别的 logger，不配置全局日志
logger = logging.getLogger(__name__)


class BaseStorage:
    """数据库存储基类 - 解决代码重复问题"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """子类实现表结构初始化"""
        raise NotImplementedError("子类必须实现 _init_db 方法")

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接（自动管理）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _execute(self, query: str, params: tuple = None, fetch: bool = False) -> list[dict] | None:
        """执行 SQL 查询"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    conn.commit()
                    return None
            except sqlite3.Error as e:
                logger.error(f"SQL execution error: {e}")
                raise

    def _execute_many(self, query: str, params_list: list[tuple]) -> None:
        """批量执行"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Batch execution error: {e}")
                raise

    def _create_table(
        self, table_name: str, columns: dict[str, str], indexes: list[tuple] = None
    ) -> None:
        """创建表"""
        cols = ", ".join(f"{name} {dtype}" for name, dtype in columns.items())
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"

        with self._get_connection() as conn:
            conn.execute(query)

            # 创建索引
            if indexes:
                for idx_name, idx_cols in indexes:
                    conn.execute(
                        f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({idx_cols})"
                    )
            conn.commit()

    def _table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=?
        """
        result = self._execute(query, (table_name,), fetch=True)
        return len(result) > 0 if result else False

    def _json_serialize(self, data: Any) -> str:
        """JSON 序列化"""
        return json.dumps(data, ensure_ascii=False, default=str)

    def _json_deserialize(self, data: str) -> Any:
        """JSON 反序列化"""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    def close(self) -> None:
        """关闭连接（用于清理）"""
        # SQLite 连接会在 context manager 中自动关闭
        logger.info(f"Storage {self.db_path} closed")

    def execute_transaction(self, operations: list[tuple]) -> bool:
        """执行事务操作

        Args:
            operations: [(query, params), ...] 列表

        Returns:
            True 如果成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                for query, params in operations:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                conn.commit()
                return True
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Transaction error: {e}")
                raise

    @contextmanager
    def transaction(self):
        """事务上下文管理器

        Usage:
            with storage.transaction():
                storage._execute(query1, params1)
                storage._execute(query2, params2)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction error: {e}")
                raise


# ========== 便捷函数 ==========


def get_storage(db_path: str) -> BaseStorage:
    """获取存储实例"""
    return BaseStorage(db_path)
