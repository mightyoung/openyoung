"""
CheckpointManager - 检查点管理器
基于 SQLite 存储，符合 LangGraph 风格
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class CheckpointManager:
    """Checkpoint 管理器

    基于 SQLite 存储，负责创建、恢复和列出文件检查点
    符合 LangGraph 风格 CheckpointSaver 协议
    """

    def __init__(
        self, checkpoint_dir: str = ".young/checkpoints", db_path: str = ".young/checkpoints.db"
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = 10
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 检查点表（存储文件内容快照）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_id TEXT NOT NULL UNIQUE,
                original_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                content_path TEXT NOT NULL,
                reason TEXT DEFAULT 'edit',
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 元数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkpoint_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (checkpoint_id) REFERENCES file_checkpoints(checkpoint_id)
            )
        """)

        # 索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_original_path ON file_checkpoints(original_path)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON file_checkpoints(created_at)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_checkpoint_id ON checkpoint_metadata(checkpoint_id)"
        )

        conn.commit()
        conn.close()

    def _get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    async def create_checkpoint(self, file_path: str, reason: str = "edit") -> str | None:
        """创建检查点

        Args:
            file_path: 文件路径
            reason: 创建原因

        Returns:
            checkpoint_id 或 None（文件不存在）
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # 生成唯一 ID
        checkpoint_id = f"{file_path.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 存储文件副本
        content_path = self.checkpoint_dir / checkpoint_id
        content_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, content_path / file_path.name)

        # 保存到数据库
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO file_checkpoints
            (checkpoint_id, original_path, file_name, content_path, reason, file_size)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                checkpoint_id,
                str(file_path),
                file_path.name,
                str(content_path / file_path.name),
                reason,
                file_path.stat().st_size,
            ),
        )

        conn.commit()
        conn.close()

        # 清理旧检查点
        await self._cleanup_old_checkpoints(file_path.name)

        return checkpoint_id

    async def restore_checkpoint(self, checkpoint_id: str, target_path: str | None = None) -> bool:
        """恢复检查点

        Args:
            checkpoint_id: 检查点 ID
            target_path: 目标路径（可选）

        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT original_path, content_path, file_name
            FROM file_checkpoints
            WHERE checkpoint_id = ?
        """,
            (checkpoint_id,),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        original_path = target_path or row[0]
        content_path = row[1]
        file_name = row[2]

        # 恢复文件
        shutil.copy2(content_path, original_path)

        return True

    async def list_checkpoints(self, file_path: str | None = None) -> list[dict[str, Any]]:
        """列出检查点

        Args:
            file_path: 可选的过滤文件路径

        Returns:
            检查点列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        if file_path:
            cursor.execute(
                """
                SELECT checkpoint_id, original_path, file_name, reason, file_size, created_at
                FROM file_checkpoints
                WHERE original_path = ?
                ORDER BY created_at DESC
            """,
                (file_path,),
            )
        else:
            cursor.execute("""
                SELECT checkpoint_id, original_path, file_name, reason, file_size, created_at
                FROM file_checkpoints
                ORDER BY created_at DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "checkpoint_id": row[0],
                "original_path": row[1],
                "file_name": row[2],
                "reason": row[3],
                "file_size": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取文件路径
        cursor.execute(
            "SELECT content_path FROM file_checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        content_path = row[0]

        # 删除文件
        content_file = Path(content_path)
        if content_file.exists():
            content_file.unlink()

        # 删除目录
        checkpoint_dir = content_file.parent
        if checkpoint_dir.exists() and not any(checkpoint_dir.iterdir()):
            checkpoint_dir.rmdir()

        # 删除数据库记录
        cursor.execute("DELETE FROM checkpoint_metadata WHERE checkpoint_id = ?", (checkpoint_id,))
        cursor.execute("DELETE FROM file_checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))

        conn.commit()
        conn.close()

        return True

    async def _cleanup_old_checkpoints(self, file_name: str):
        """清理旧检查点"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 获取该文件的检查点，按时间排序
        cursor.execute(
            """
            SELECT checkpoint_id FROM file_checkpoints
            WHERE file_name = ?
            ORDER BY created_at DESC
        """,
            (file_name,),
        )

        rows = cursor.fetchall()
        conn.close()

        # 删除超过限制的旧检查点
        if len(rows) > self.max_checkpoints:
            for row in rows[self.max_checkpoints :]:
                await self.delete_checkpoint(row[0])

    def get_stats(self) -> dict[str, Any]:
        """获取检查点统计"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM file_checkpoints")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT original_path) FROM file_checkpoints")
        files = cursor.fetchone()[0]

        conn.close()

        return {"total_checkpoints": total, "total_files": files}
