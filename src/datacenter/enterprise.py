"""
Enterprise - 企业级功能
多租户支持、权限控制、审计日志
"""

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

# 从 isolation 模块导入
from .isolation import IsolationConfig, IsolationLevel, IsolationManager


class Permission(str, Enum):
    """权限类型"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"


class TenantStatus(str, Enum):
    """租户状态"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass
class Tenant:
    """租户"""

    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE

    # 配额
    max_agents: int = 10
    max_users: int = 100
    max_storage_mb: int = 1024  # 1GB

    # 使用统计
    agent_count: int = 0
    user_count: int = 0
    storage_used_mb: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class User:
    """用户"""

    user_id: str
    tenant_id: str
    username: str
    email: str = ""

    # 权限
    permissions: list[Permission] = field(default_factory=list)
    role: str = "user"  # admin, user, guest

    # 状态
    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None


@dataclass
class AuditLog:
    """审计日志"""

    log_id: str
    tenant_id: str
    user_id: str

    # 操作
    action: str  # create, read, update, delete, login, logout, execute
    resource_type: str  # agent, workspace, user, etc.
    resource_id: str = ""

    # 结果
    status: str = "success"  # success, failed
    error_message: str = ""

    # 上下文
    ip_address: str = ""
    user_agent: str = ""
    metadata: dict = field(default_factory=dict)

    created_at: datetime = field(default_factory=datetime.now)


class EnterpriseManager:
    """企业级管理器"""

    def __init__(self, data_dir: str = ".young"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "enterprise.db"
        self._init_db()

    def _init_db(self):
        """初始化企业数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 租户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                max_agents INTEGER DEFAULT 10,
                max_users INTEGER DEFAULT 100,
                max_storage_mb INTEGER DEFAULT 1024,
                agent_count INTEGER DEFAULT 0,
                user_count INTEGER DEFAULT 0,
                storage_used_mb REAL DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)

        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                username TEXT NOT NULL,
                email TEXT,
                password_hash TEXT,
                permissions TEXT,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)

        # 审计日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                status TEXT DEFAULT 'success',
                error_message TEXT,
                ip_address TEXT,
                user_agent TEXT,
                metadata TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
            )
        """)

        # 索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_logs(tenant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")

        conn.commit()
        conn.close()

    # ========== 租户管理 ==========

    def create_tenant(self, tenant_id: str, name: str, **kwargs) -> Tenant:
        """创建租户"""
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            max_agents=kwargs.get("max_agents", 10),
            max_users=kwargs.get("max_users", 100),
            max_storage_mb=kwargs.get("max_storage_mb", 1024),
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO tenants (tenant_id, name, status, max_agents, max_users, max_storage_mb, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                tenant.tenant_id,
                tenant.name,
                tenant.status.value,
                tenant.max_agents,
                tenant.max_users,
                tenant.max_storage_mb,
                tenant.created_at.isoformat(),
                tenant.updated_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        """获取租户"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Tenant(
            tenant_id=row["tenant_id"],
            name=row["name"],
            status=TenantStatus(row["status"]),
            max_agents=row["max_agents"],
            max_users=row["max_users"],
            max_storage_mb=row["max_storage_mb"],
            agent_count=row["agent_count"],
            user_count=row["user_count"],
            storage_used_mb=row["storage_used_mb"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def update_tenant(self, tenant_id: str, **kwargs) -> bool:
        """更新租户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = []
        params = []

        for key in ["name", "status", "max_agents", "max_users", "max_storage_mb"]:
            if key in kwargs:
                updates.append(f"{key} = ?")
                params.append(kwargs[key])

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(tenant_id)

        cursor.execute(
            f"""
            UPDATE tenants SET {", ".join(updates)} WHERE tenant_id = ?
        """,
            params,
        )

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def list_tenants(self, status: TenantStatus = None) -> list[Tenant]:
        """列出租户"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM tenants WHERE status = ?", (status.value,))
        else:
            cursor.execute("SELECT * FROM tenants")

        rows = cursor.fetchall()
        conn.close()

        return [
            Tenant(
                tenant_id=row["tenant_id"],
                name=row["name"],
                status=TenantStatus(row["status"]),
                max_agents=row["max_agents"],
                max_users=row["max_users"],
                max_storage_mb=row["max_storage_mb"],
                agent_count=row["agent_count"],
                user_count=row["user_count"],
                storage_used_mb=row["storage_used_mb"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )
            for row in rows
        ]

    # ========== 用户管理 ==========

    def create_user(
        self,
        user_id: str,
        tenant_id: str,
        username: str,
        email: str = "",
        password: str = None,
        role: str = "user",
        permissions: list[Permission] = None,
    ) -> User:
        """创建用户"""
        user = User(
            user_id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            role=role,
            permissions=permissions or [Permission.READ],
        )

        # 密码哈希
        password_hash = ""
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users (user_id, tenant_id, username, email, password_hash, permissions, role, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                user.user_id,
                user.tenant_id,
                user.username,
                user.email,
                password_hash,
                json.dumps([p.value for p in user.permissions]),
                user.role,
                1 if user.is_active else 0,
                user.created_at.isoformat(),
            ),
        )

        # 更新租户用户数
        cursor.execute(
            """
            UPDATE tenants SET user_count = user_count + 1 WHERE tenant_id = ?
        """,
            (tenant_id,),
        )

        conn.commit()
        conn.close()

        return user

    def authenticate(self, username: str, password: str, tenant_id: str = None) -> User | None:
        """验证用户"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if tenant_id:
            cursor.execute(
                """
                SELECT * FROM users
                WHERE username = ? AND password_hash = ? AND tenant_id = ?
            """,
                (username, password_hash, tenant_id),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM users
                WHERE username = ? AND password_hash = ?
            """,
                (username, password_hash),
            )

        row = cursor.fetchone()

        # 更新最后登录
        if row:
            cursor.execute(
                """
                UPDATE users SET last_login = ? WHERE user_id = ?
            """,
                (datetime.now().isoformat(), row["user_id"]),
            )

        conn.commit()
        conn.close()

        if not row:
            return None

        return User(
            user_id=row["user_id"],
            tenant_id=row["tenant_id"],
            username=row["username"],
            email=row["email"],
            permissions=[Permission(p) for p in json.loads(row["permissions"])],
            role=row["role"],
            is_active=bool(row["is_active"]),
            last_login=datetime.fromisoformat(row["last_login"]) if row["last_login"] else None,
        )

    def check_permission(self, user: User, permission: Permission) -> bool:
        """检查权限"""
        if Permission.ADMIN in user.permissions:
            return True

        if permission in user.permissions:
            return True

        # 角色权限
        role_permissions = {
            "admin": [
                Permission.READ,
                Permission.WRITE,
                Permission.DELETE,
                Permission.ADMIN,
                Permission.EXECUTE,
            ],
            "user": [Permission.READ, Permission.WRITE, Permission.EXECUTE],
            "guest": [Permission.READ],
        }

        return permission in role_permissions.get(user.role, [])

    # ========== 审计日志 ==========

    def log_audit(
        self,
        tenant_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str = "",
        status: str = "success",
        error_message: str = "",
        **kwargs,
    ):
        """记录审计日志"""
        import uuid

        log = AuditLog(
            log_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            error_message=error_message,
            ip_address=kwargs.get("ip_address", ""),
            user_agent=kwargs.get("user_agent", ""),
            metadata=kwargs.get("metadata", {}),
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_logs (
                log_id, tenant_id, user_id, action, resource_type, resource_id,
                status, error_message, ip_address, user_agent, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                log.log_id,
                log.tenant_id,
                log.user_id,
                log.action,
                log.resource_type,
                log.resource_id,
                log.status,
                log.error_message,
                log.ip_address,
                log.user_agent,
                json.dumps(log.metadata),
                log.created_at.isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return log

    def query_audit_logs(
        self,
        tenant_id: str = None,
        user_id: str = None,
        action: str = None,
        resource_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """查询审计日志"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        sql = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if tenant_id:
            sql += " AND tenant_id = ?"
            params.append(tenant_id)

        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)

        if action:
            sql += " AND action = ?"
            params.append(action)

        if resource_type:
            sql += " AND resource_type = ?"
            params.append(resource_type)

        if start_date:
            sql += " AND created_at >= ?"
            params.append(start_date.isoformat())

        if end_date:
            sql += " AND created_at <= ?"
            params.append(end_date.isoformat())

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            log = AuditLog(
                log_id=row["log_id"],
                tenant_id=row["tenant_id"],
                user_id=row["user_id"],
                action=row["action"],
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
                status=row["status"],
                error_message=row["error_message"],
                ip_address=row["ip_address"],
                user_agent=row["user_agent"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            result.append(log)

        return result

    def get_audit_stats(self, tenant_id: str = None, days: int = 30) -> dict:
        """获取审计统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        base_where = "WHERE created_at >= ?"
        params = [start_date]

        if tenant_id:
            base_where += " AND tenant_id = ?"
            params.append(tenant_id)

        # 总数
        cursor.execute(f"SELECT COUNT(*) FROM audit_logs {base_where}", params)
        total = cursor.fetchone()[0]

        # 按操作类型
        cursor.execute(
            f"""
            SELECT action, COUNT(*) as count
            FROM audit_logs {base_where}
            GROUP BY action
        """,
            params,
        )
        by_action = {row[0]: row[1] for row in cursor.fetchall()}

        # 按状态
        cursor.execute(
            f"""
            SELECT status, COUNT(*) as count
            FROM audit_logs {base_where}
            GROUP BY status
        """,
            params,
        )
        by_status = {row[0]: row[1] for row in cursor.fetchall()}

        # 按用户
        cursor.execute(
            f"""
            SELECT user_id, COUNT(*) as count
            FROM audit_logs {base_where}
            GROUP BY user_id
            ORDER BY count DESC
            LIMIT 10
        """,
            params,
        )
        by_user = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total": total,
            "by_action": by_action,
            "by_status": by_status,
            "by_user": by_user,
            "period_days": days,
        }


# ========== 便捷函数 ==========


def get_enterprise_manager(data_dir: str = ".young") -> EnterpriseManager:
    """获取企业级管理器"""
    return EnterpriseManager(data_dir)
