"""
TeamShare - 团队数据共享
支持团队内数据共享和权限控制
使用 BaseStorage 基类
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from .base_storage import BaseStorage


@dataclass
class TeamShare:
    """团队共享记录"""
    share_id: str
    data_id: str
    data_type: str  # run / agent / checkpoint
    team_id: str
    owner_id: str
    permission: str  # read / write / admin
    shared_at: datetime = field(default_factory=datetime.now)


class TeamShareManager(BaseStorage):
    """团队共享管理器"""

    def __init__(self, db_path: str = ".young/team_shares.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库"""
        # 团队表
        self._create_table(
            "teams",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "team_id": "TEXT NOT NULL UNIQUE",
                "name": "TEXT NOT NULL",
                "owner_id": "TEXT NOT NULL",
                "created_at": "TEXT NOT NULL"
            },
            indexes=[("idx_team", "team_id")]
        )

        # 团队成员表
        self._create_table(
            "team_members",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "team_id": "TEXT NOT NULL",
                "user_id": "TEXT NOT NULL",
                "role": "TEXT DEFAULT 'member'",
                "joined_at": "TEXT NOT NULL",
                "UNIQUE": "(team_id, user_id)"
            },
            indexes=[("idx_member_user", "user_id")]
        )

        # 数据共享表
        self._create_table(
            "data_shares",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "share_id": "TEXT NOT NULL UNIQUE",
                "data_id": "TEXT NOT NULL",
                "data_type": "TEXT NOT NULL",
                "team_id": "TEXT NOT NULL",
                "owner_id": "TEXT NOT NULL",
                "permission": "TEXT DEFAULT 'read'",
                "shared_at": "TEXT NOT NULL"
            },
            indexes=[
                ("idx_share_team", "team_id"),
                ("idx_share_data", "data_id")
            ]
        )

    # ===== 团队管理 =====

    def create_team(self, team_id: str, name: str, owner_id: str) -> str:
        """创建团队"""
        # 输入验证
        if not team_id or not team_id.strip():
            raise ValueError("team_id cannot be empty")
        if not name or not name.strip():
            raise ValueError("name cannot be empty")
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id cannot be empty")

        self._execute(
            """
            INSERT OR REPLACE INTO teams (team_id, name, owner_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (team_id, name, owner_id, datetime.now().isoformat())
        )

        # 自动添加创建者为管理员
        self._execute(
            """
            INSERT OR IGNORE INTO team_members (team_id, user_id, role, joined_at)
            VALUES (?, ?, ?, ?)
            """,
            (team_id, owner_id, 'admin', datetime.now().isoformat())
        )

        return team_id

    def get_team(self, team_id: str) -> dict | None:
        """获取团队信息"""
        result = self._execute(
            "SELECT * FROM teams WHERE team_id = ?",
            (team_id,),
            fetch=True
        )

        return result[0] if result else None

    def list_teams(self, user_id: str = None) -> list[dict]:
        """列出团队"""
        if user_id:
            result = self._execute("""
                SELECT t.* FROM teams t
                JOIN team_members tm ON t.team_id = tm.team_id
                WHERE tm.user_id = ?
            """, (user_id,), fetch=True)
        else:
            result = self._execute("SELECT * FROM teams", fetch=True)

        return result or []

    def add_member(self, team_id: str, user_id: str, role: str = "member") -> bool:
        """添加团队成员"""
        try:
            self._execute(
                """
                INSERT OR IGNORE INTO team_members (team_id, user_id, role, joined_at)
                VALUES (?, ?, ?, ?)
                """,
                (team_id, user_id, role, datetime.now().isoformat())
            )
            return True
        except Exception:
            return False

    def remove_member(self, team_id: str, user_id: str) -> bool:
        """移除团队成员"""
        result = self._execute(
            "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
            fetch=True
        )
        # sqlite3 在 delete 后 rowcount 不可用，这里简单返回 True
        return True

    def list_members(self, team_id: str) -> list[dict]:
        """列出团队成员"""
        result = self._execute(
            "SELECT * FROM team_members WHERE team_id = ?",
            (team_id,),
            fetch=True
        )
        return result or []

    # ===== 数据共享 =====

    def share_data(
        self,
        data_id: str,
        data_type: str,
        team_id: str,
        owner_id: str,
        permission: str = "read"
    ) -> str:
        """共享数据给团队"""
        share_id = f"share_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT INTO data_shares (share_id, data_id, data_type, team_id, owner_id, permission, shared_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (share_id, data_id, data_type, team_id, owner_id, permission, datetime.now().isoformat())
        )

        return share_id

    def revoke_share(self, share_id: str) -> bool:
        """撤销共享"""
        self._execute("DELETE FROM data_shares WHERE share_id = ?", (share_id,))
        return True

    def get_shared_data(self, team_id: str, data_type: str = None) -> list[dict]:
        """获取团队共享的数据"""
        query = "SELECT * FROM data_shares WHERE team_id = ?"
        params = [team_id]

        if data_type:
            query += " AND data_type = ?"
            params.append(data_type)

        result = self._execute(query, tuple(params), fetch=True)
        return result or []

    def check_access(self, team_id: str, user_id: str, data_id: str, required_permission: str = "read") -> bool:
        """检查用户是否有权访问数据

        Args:
            team_id: 团队 ID
            user_id: 用户 ID
            data_id: 数据 ID
            required_permission: 需要的权限 (read/write/admin)

        Returns:
            True 如果有权限
        """
        # 检查用户是否是团队成员
        member_result = self._execute(
            "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
            (team_id, user_id),
            fetch=True
        )

        if not member_result:
            return False

        user_role = member_result[0].get("role", "member")

        # admin 可以做任何操作
        if user_role == "admin":
            return True

        # 检查数据是否共享给团队
        share_result = self._execute(
            "SELECT permission FROM data_shares WHERE team_id = ? AND data_id = ?",
            (team_id, data_id),
            fetch=True
        )

        if not share_result:
            return False

        data_permission = share_result[0].get("permission", "read")

        # 权限检查
        permission_levels = {"read": 1, "write": 2, "admin": 3}
        required_level = permission_levels.get(required_permission, 1)
        data_level = permission_levels.get(data_permission, 1)

        # member 只能读取
        if user_role == "member":
            return required_permission == "read"

        return data_level >= required_level


# ========== 便捷函数 ==========

def get_team_share_manager(db_path: str = ".young/team_shares.db") -> TeamShareManager:
    """获取团队共享管理器"""
    return TeamShareManager(db_path)
