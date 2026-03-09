"""
Base Registry - 注册表基类
提供通用的注册表功能
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class BaseRegistry:
    """注册表基类

    提供通用功能：
    - 目录扫描
    - 文件加载
    - 使用追踪
    - 持久化存储
    """

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Any] = {}

    # ========== 通用工具方法 ==========

    def discover_items(self, pattern: str = "*") -> list[str]:
        """发现目录中的所有项

        Args:
            pattern: 匹配模式

        Returns:
            List[str]: 项名称列表
        """
        items = []
        if not self.base_dir.exists():
            return items

        for item in self.base_dir.iterdir():
            if item.is_dir():
                items.append(item.name)
            elif pattern == "*" or item.match(pattern):
                items.append(item.stem)

        return items

    def ensure_dir(self, *parts: str) -> Path:
        """确保目录存在"""
        path = self.base_dir.joinpath(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_item_path(self, name: str, filename: str = None) -> Path:
        """获取项的路径"""
        if filename:
            return self.base_dir / name / filename
        return self.base_dir / name

    def item_exists(self, name: str) -> bool:
        """检查项是否存在"""
        return (self.base_dir / name).exists()

    # ========== 使用追踪 ==========

    def track_usage(self, item_name: str, db_name: str = "usage.db") -> bool:
        """追踪使用

        Args:
            item_name: 项名称
            db_name: 数据库文件名

        Returns:
            bool: 是否成功
        """
        try:
            db_path = Path.home() / ".openyoung" / db_name
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # 创建表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    item_name TEXT PRIMARY KEY,
                    use_count INTEGER DEFAULT 1,
                    last_used TEXT,
                    created_at TEXT
                )
            """)

            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO usage (item_name, use_count, last_used, created_at)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(item_name) DO UPDATE SET
                    use_count = use_count + 1,
                    last_used = ?
            """,
                (item_name, now, now, now),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[BaseRegistry] Track usage error: {e}")
            return False

    def get_usage_stats(self, db_name: str = "usage.db", limit: int = 10) -> list[dict[str, Any]]:
        """获取使用统计

        Args:
            db_name: 数据库文件名
            limit: 返回数量

        Returns:
            List[Dict]: 统计列表
        """
        try:
            db_path = Path.home() / ".openyoung" / db_name
            if not db_path.exists():
                return []

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT item_name, use_count, last_used
                FROM usage
                ORDER BY use_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            results = []
            for row in cursor.fetchall():
                results.append({"name": row[0], "use_count": row[1], "last_used": row[2]})

            conn.close()
            return results
        except Exception as e:
            print(f"[BaseRegistry] Get stats error: {e}")
            return []

    # ========== 评分系统 ==========

    def rate_item(self, item_name: str, rating: float, db_name: str = "ratings.db") -> bool:
        """评分

        Args:
            item_name: 项名称
            rating: 评分 (0-5)

        Returns:
            bool: 是否成功
        """
        try:
            db_path = Path.home() / ".openyoung" / db_name
            db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ratings (
                    item_name TEXT PRIMARY KEY,
                    rating REAL,
                    rated_at TEXT
                )
            """)

            now = datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO ratings (item_name, rating, rated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(item_name) DO UPDATE SET
                    rating = ?,
                    rated_at = ?
            """,
                (item_name, rating, now, rating, now),
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[BaseRegistry] Rate error: {e}")
            return False

    def get_ratings(self, db_name: str = "ratings.db") -> dict[str, float]:
        """获取所有评分

        Returns:
            Dict[str, float]: 项名称 -> 评分
        """
        try:
            db_path = Path.home() / ".openyoung" / db_name
            if not db_path.exists():
                return {}

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT item_name, rating FROM ratings")
            ratings = {row[0]: row[1] for row in cursor.fetchall()}

            conn.close()
            return ratings
        except Exception as e:
            print(f"[BaseRegistry] Get ratings error: {e}")
            return {}
