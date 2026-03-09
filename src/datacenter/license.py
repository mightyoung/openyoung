"""
DataLicense - 数据版权管理
轻量级版权追踪
使用 BaseStorage 基类
"""

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base_storage import BaseStorage


@dataclass
class DataLicense:
    """数据许可证"""

    license_id: str = field(default_factory=lambda: f"lic_{uuid.uuid4().hex[:12]}")
    owner_id: str = ""
    license_type: str = "private"  # public / private / team
    team_id: str = ""
    usage_terms: str = ""
    watermark: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "license_id": self.license_id,
            "owner_id": self.owner_id,
            "license_type": self.license_type,
            "team_id": self.team_id,
            "usage_terms": self.usage_terms,
            "watermark": self.watermark,
            "created_at": self.created_at.isoformat(),
        }


class Watermark:
    """数据水印处理器

    支持两种水印：
    1. 可见水印：嵌入到数据中的可见标识
    2. 隐形水印：基于哈希的数字签名，可验证数据来源
    """

    @staticmethod
    def generate_watermark(data: Any, license_id: str, owner_id: str, metadata: dict = None) -> str:
        """生成水印标识

        Args:
            data: 原始数据
            license_id: 许可证 ID
            owner_id: 所有者 ID
            metadata: 额外元数据

        Returns:
            水印字符串
        """
        # 创建水印内容
        watermark_content = {
            "license_id": license_id,
            "owner_id": owner_id,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "metadata": metadata or {},
        }

        # 序列化并编码
        content_str = json.dumps(watermark_content, sort_keys=True)
        watermark_bytes = content_str.encode("utf-8")

        # 生成哈希签名
        hash_obj = hashlib.sha256(watermark_bytes)
        signature = hash_obj.hexdigest()

        # 组合最终水印
        final_watermark = base64.b64encode(
            json.dumps({"content": watermark_content, "signature": signature}).encode("utf-8")
        ).decode("utf-8")

        return final_watermark

    @staticmethod
    def embed_visible_watermark(
        data: Any, license_id: str, owner_id: str, metadata: dict = None
    ) -> dict:
        """嵌入可见水印

        Args:
            data: 原始数据（字典或列表）
            license_id: 许可证 ID
            owner_id: 所有者 ID
            metadata: 额外元数据

        Returns:
            嵌入水印后的数据
        """
        watermark = Watermark.generate_watermark(data, license_id, owner_id, metadata)

        # 如果数据是字典，添加水印字段
        if isinstance(data, dict):
            result = data.copy()
            result["_watermark"] = watermark
            result["_license_id"] = license_id
            result["_owner_id"] = owner_id
            return result
        elif isinstance(data, list):
            # 为列表中的每个字典添加水印
            return [
                {**item, "_watermark": watermark, "_license_id": license_id, "_owner_id": owner_id}
                if isinstance(item, dict)
                else item
                for item in data
            ]
        else:
            # 其他类型数据包装
            return {
                "_data": data,
                "_watermark": watermark,
                "_license_id": license_id,
                "_owner_id": owner_id,
            }

    @staticmethod
    def verify_watermark(
        data: Any, expected_license_id: str = None, expected_owner_id: str = None
    ) -> dict:
        """验证水印

        Args:
            data: 包含水印的数据
            expected_license_id: 期望的许可证 ID
            expected_owner_id: 期望的所有者 ID

        Returns:
            验证结果 {
                "valid": bool,
                "license_id": str,
                "owner_id": str,
                "timestamp": str,
                "error": str
            }
        """
        result = {
            "valid": False,
            "license_id": None,
            "owner_id": None,
            "timestamp": None,
            "error": None,
        }

        try:
            # 提取水印
            watermark_str = None
            if isinstance(data, dict):
                watermark_str = data.get("_watermark")
                result["license_id"] = data.get("_license_id")
                result["owner_id"] = data.get("_owner_id")
            else:
                result["error"] = "Data format not recognized"
                return result

            if not watermark_str:
                result["error"] = "Watermark not found"
                return result

            # 解码水印
            try:
                decoded = json.loads(
                    base64.b64decode(watermark_str.encode("utf-8")).decode("utf-8")
                )
            except Exception as e:
                result["error"] = f"Invalid watermark format: {e}"
                return result

            content = decoded.get("content", {})
            signature = decoded.get("signature", "")

            # 验证签名
            content_str = json.dumps(content, sort_keys=True)
            expected_signature = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

            if signature != expected_signature:
                result["error"] = "Invalid signature"
                return result

            # 验证许可证和所有者
            if expected_license_id and content.get("license_id") != expected_license_id:
                result["error"] = "License ID mismatch"
                return result

            if expected_owner_id and content.get("owner_id") != expected_owner_id:
                result["error"] = "Owner ID mismatch"
                return result

            result["valid"] = True
            result["license_id"] = content.get("license_id")
            result["owner_id"] = content.get("owner_id")
            result["timestamp"] = content.get("timestamp")

        except Exception as e:
            result["error"] = str(e)

        return result

    @staticmethod
    def remove_watermark(data: Any) -> Any:
        """移除水印

        Args:
            data: 包含水印的数据

        Returns:
            移除水印后的数据
        """
        if isinstance(data, dict):
            # 移除水印字段
            watermark_fields = ["_watermark", "_license_id", "_owner_id", "_data"]
            return {k: v for k, v in data.items() if k not in watermark_fields}
        elif isinstance(data, list):
            return [Watermark.remove_watermark(item) for item in data]
        else:
            return data


class DataLicenseManager(BaseStorage):
    """数据版权管理器"""

    def __init__(self, db_path: str = ".young/licenses.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库"""
        self._create_table(
            "licenses",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "license_id": "TEXT NOT NULL UNIQUE",
                "owner_id": "TEXT NOT NULL",
                "license_type": "TEXT NOT NULL",
                "team_id": "TEXT",
                "usage_terms": "TEXT",
                "watermark": "INTEGER DEFAULT 1",
                "created_at": "TEXT NOT NULL",
            },
            indexes=[("idx_owner", "owner_id"), ("idx_type", "license_type")],
        )

    def create_license(
        self,
        owner_id: str,
        license_type: str = "private",
        team_id: str = "",
        usage_terms: str = "",
        watermark: bool = True,
    ) -> str:
        """创建许可证"""
        # 输入验证
        if not owner_id or not owner_id.strip():
            raise ValueError("owner_id cannot be empty")
        if license_type not in ("public", "private", "team"):
            raise ValueError("license_type must be one of: public, private, team")

        license_id = f"lic_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT INTO licenses (license_id, owner_id, license_type, team_id, usage_terms, watermark, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                license_id,
                owner_id,
                license_type,
                team_id,
                usage_terms,
                1 if watermark else 0,
                datetime.now().isoformat(),
            ),
        )

        return license_id

    def get_license(self, license_id: str) -> dict | None:
        """获取许可证"""
        result = self._execute(
            "SELECT * FROM licenses WHERE license_id = ?", (license_id,), fetch=True
        )

        if not result:
            return None

        return result[0]

    def list_licenses(self, owner_id: str = None, license_type: str = None) -> list[dict]:
        """列出许可证"""
        query = "SELECT * FROM licenses"
        conditions = []
        params = []

        if owner_id:
            conditions.append("owner_id = ?")
            params.append(owner_id)
        if license_type:
            conditions.append("license_type = ?")
            params.append(license_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        result = self._execute(query, tuple(params), fetch=True)

        return result or []

    def check_access(self, license_id: str, requester_id: str, team_id: str = None) -> bool:
        """检查访问权限

        Args:
            license_id: 许可证 ID
            requester_id: 请求者 ID
            team_id: 团队 ID（team 类型许可证需要）

        Returns:
            True 如果有权限
        """
        license = self.get_license(license_id)
        if not license:
            return False

        # public: 所有人都可以访问
        if license["license_type"] == "public":
            return True

        # private: 只有所有者可以访问
        if license["license_type"] == "private":
            return license["owner_id"] == requester_id

        # team: 团队成员可以访问
        if license["license_type"] == "team":
            # 需要验证 team_id
            if not team_id:
                return False
            # 检查是否是团队成员或许可证所有者
            return license["owner_id"] == requester_id or license["team_id"] == team_id

        return False

    def check_permission(
        self, license_id: str, requester_id: str, required_permission: str
    ) -> bool:
        """检查特定权限

        Args:
            license_id: 许可证 ID
            requester_id: 请求者 ID
            required_permission: 需要的权限 (read/write/admin)

        Returns:
            True 如果有权限
        """
        license = self.get_license(license_id)
        if not license:
            return False

        # public 许可证只读
        if license["license_type"] == "public":
            return required_permission in ("read",)

        # private 只有所有者有完全权限
        if license["license_type"] == "private":
            if license["owner_id"] == requester_id:
                return required_permission in ("read", "write", "admin")
            return False

        # team 权限检查
        if license["license_type"] == "team":
            if license["owner_id"] == requester_id:
                return required_permission in ("read", "write", "admin")
            # 其他团队成员只有读取权限
            return required_permission == "read"

        return False


class AccessLog(BaseStorage):
    """访问日志"""

    def __init__(self, db_path: str = ".young/access_logs.db"):
        super().__init__(db_path)

    def _init_db(self) -> None:
        """初始化数据库"""
        self._create_table(
            "access_logs",
            {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "log_id": "TEXT NOT NULL UNIQUE",
                "data_id": "TEXT NOT NULL",
                "accessed_by": "TEXT NOT NULL",
                "access_type": "TEXT NOT NULL",
                "purpose": "TEXT",
                "license_id": "TEXT",
                "accessed_at": "TEXT NOT NULL",
            },
            indexes=[("idx_data", "data_id"), ("idx_user", "accessed_by")],
        )

    def log_access(
        self,
        data_id: str,
        accessed_by: str,
        access_type: str,  # read / export / share
        purpose: str = "",
        license_id: str = None,
    ) -> str:
        """记录访问"""
        log_id = f"log_{uuid.uuid4().hex[:12]}"

        self._execute(
            """
            INSERT INTO access_logs (log_id, data_id, accessed_by, access_type, purpose, license_id, accessed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log_id,
                data_id,
                accessed_by,
                access_type,
                purpose,
                license_id,
                datetime.now().isoformat(),
            ),
        )

        return log_id

    def get_logs(
        self, data_id: str = None, accessed_by: str = None, limit: int = 100
    ) -> list[dict]:
        """获取访问日志"""
        query = "SELECT * FROM access_logs"
        conditions = []
        params = []

        if data_id:
            conditions.append("data_id = ?")
            params.append(data_id)
        if accessed_by:
            conditions.append("accessed_by = ?")
            params.append(accessed_by)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY accessed_at DESC LIMIT {limit}"

        result = self._execute(query, tuple(params), fetch=True)

        return result or []


# ========== 便捷函数 ==========


def get_license_manager(db_path: str = ".young/licenses.db") -> DataLicenseManager:
    """获取许可证管理器"""
    return DataLicenseManager(db_path)


def get_access_log(db_path: str = ".young/access_logs.db") -> AccessLog:
    """获取访问日志"""
    return AccessLog(db_path)


def add_watermark(data: Any, license_id: str, owner_id: str, metadata: dict = None) -> Any:
    """便捷函数：添加水印"""
    return Watermark.embed_visible_watermark(data, license_id, owner_id, metadata)


def verify_watermark(data: Any, license_id: str = None, owner_id: str = None) -> dict:
    """便捷函数：验证水印"""
    return Watermark.verify_watermark(data, license_id, owner_id)


def remove_watermark(data: Any) -> Any:
    """便捷函数：移除水印"""
    return Watermark.remove_watermark(data)
