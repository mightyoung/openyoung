"""
凭据保险库

提供加密的凭据存储和管理
"""

import base64
import hashlib
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Optional

from cryptography.fernet import Fernet


@dataclass
class Credential:
    """凭据"""

    key: str
    value: str  # 加密后的值
    encrypted: bool = True

    # 加密元数据
    salt: Optional[str] = None
    iv: Optional[str] = None

    # 元数据
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    # 访问控制
    allowed_agents: list[str] = field(default_factory=list)
    max_uses: Optional[int] = None
    use_count: int = 0


class Vault:
    """凭据保险库

    提供凭据存储和检索
    使用 Fernet AES 加密、访问控制、过期时间
    """

    def __init__(self, master_key: Optional[str] = None):
        """
        初始化保险库

        Args:
            master_key: 主密钥，如果为 None 则生成随机密钥
        """
        self._master_key = master_key or self._generate_key()
        self._credentials: dict[str, Credential] = {}
        self._secret_cache: dict[str, str] = {}

    def _generate_key(self) -> str:
        """生成随机密钥"""
        return base64.b64encode(secrets.token_bytes(32)).decode()

    def _derive_key(self, key: str, salt: bytes) -> bytes:
        """派生加密密钥"""
        return hashlib.pbkdf2_hmac("sha256", key.encode(), salt, 100000, dklen=32)

    def _get_fernet(self, salt: bytes) -> Fernet:
        """
        从主密钥和盐值获取Fernet实例

        Args:
            salt: 用于派生密钥的盐值

        Returns:
            Fernet 实例
        """
        derived_key = self._derive_key(self._master_key, salt)
        fernet_key = base64.urlsafe_b64encode(derived_key)
        return Fernet(fernet_key)

    def _encrypt(self, plaintext: str) -> tuple[str, bytes, bytes]:
        """
        加密数据

        Returns:
            (encrypted_base64, salt, iv)
        """
        # 生成随机 salt
        salt = os.urandom(16)

        # 使用 Fernet AES 加密
        fernet = self._get_fernet(salt)
        encrypted = fernet.encrypt(plaintext.encode())

        return encrypted.decode(), salt, b""  # iv为空，Fernet内部处理

    def _decrypt(self, encrypted: str, salt: bytes, iv: bytes) -> str:
        """解密数据"""
        fernet = self._get_fernet(salt)
        decrypted = fernet.decrypt(encrypted.encode())
        return decrypted.decode()

    def store(self, key: str, value: str, **metadata) -> bool:
        """
        存储凭据

        Args:
            key: 凭据键
            value: 凭据值
            **metadata: 额外元数据 (expires_at, allowed_agents, max_uses)

        Returns:
            是否成功
        """
        encrypted_value, salt, iv = self._encrypt(value)

        credential = Credential(
            key=key,
            value=encrypted_value,
            salt=base64.b64encode(salt).decode(),
            iv=base64.b64encode(iv).decode() if iv else None,
            allowed_agents=metadata.get("allowed_agents", []),
            expires_at=metadata.get("expires_at"),
            max_uses=metadata.get("max_uses"),
        )

        self._credentials[key] = credential

        # 清除缓存
        if key in self._secret_cache:
            del self._secret_cache[key]

        return True

    def get(self, key: str, agent_id: Optional[str] = None) -> Optional[str]:
        """
        获取凭据

        Args:
            key: 凭据键
            agent_id: 请求的 agent ID

        Returns:
            解密后的凭据值，如果不存在或已过期返回 None
        """
        credential = self._credentials.get(key)
        if credential is None:
            return None

        # 检查过期
        if credential.expires_at and time.time() > credential.expires_at:
            return None

        # 检查访问控制
        if credential.allowed_agents and agent_id not in credential.allowed_agents:
            return None

        # 检查使用次数
        if credential.max_uses and credential.use_count >= credential.max_uses:
            return None

        # 检查缓存
        if key in self._secret_cache:
            credential.use_count += 1
            return self._secret_cache[key]

        # 解密
        salt = base64.b64decode(credential.salt)
        iv = base64.b64decode(credential.iv) if credential.iv else None

        try:
            decrypted = self._decrypt(credential.value, salt, iv)
            self._secret_cache[key] = decrypted
            credential.use_count += 1
            return decrypted
        except Exception:
            return None

    def delete(self, key: str) -> bool:
        """
        删除凭据

        Args:
            key: 凭据键

        Returns:
            是否成功
        """
        if key in self._credentials:
            del self._credentials[key]
            if key in self._secret_cache:
                del self._secret_cache[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """检查凭据是否存在"""
        return key in self._credentials

    def list_keys(self, agent_id: Optional[str] = None) -> list[str]:
        """
        列出可访问的凭据键

        Args:
            agent_id: 过滤特定 agent 可访问的凭据

        Returns:
            凭据键列表
        """
        keys = []
        for key, cred in self._credentials.items():
            # 检查过期
            if cred.expires_at and time.time() > cred.expires_at:
                continue

            # 检查访问控制
            if cred.allowed_agents and agent_id not in cred.allowed_agents:
                continue

            keys.append(key)

        return keys

    def rotate(self, key: str, new_value: str) -> bool:
        """
        轮换凭据

        Args:
            key: 凭据键
            new_value: 新值

        Returns:
            是否成功
        """
        if key not in self._credentials:
            return False

        # 清除旧缓存
        if key in self._secret_cache:
            del self._secret_cache[key]

        # 存储新值
        return self.store(key, new_value)

    def get_master_key(self) -> str:
        """获取主密钥（用于配置）"""
        return self._master_key

    def export_config(self) -> dict:
        """导出配置（不包含密钥）"""
        return {
            "credential_count": len(self._credentials),
            "cache_size": len(self._secret_cache),
        }


# ========== Convenience Functions ==========


def create_vault(master_key: Optional[str] = None) -> Vault:
    """
    便捷函数：创建保险库

    Args:
        master_key: 主密钥

    Returns:
        Vault 实例
    """
    return Vault(master_key=master_key)
