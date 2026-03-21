"""
Vault Tests - Phase 2.1
Tests for Credential Vault
"""

import pytest
import time
from src.runtime.security import Vault, Credential


class TestVault:
    """Vault 测试"""

    def test_store_and_get(self):
        """存储和获取测试"""
        vault = Vault()
        master_key = vault.get_master_key()

        # 存储凭据
        vault.store("api_key", "sk-secret-12345")

        # 获取凭据
        value = vault.get("api_key")
        assert value == "sk-secret-12345"

    def test_store_encrypted(self):
        """加密存储测试"""
        vault = Vault()
        vault.store("password", "MySecretPassword")

        # 凭据应该被加密存储
        # 不能通过直接访问内部获取明文
        assert vault.exists("password")

    def test_get_nonexistent(self):
        """获取不存在的凭据"""
        vault = Vault()

        value = vault.get("nonexistent")
        assert value is None

    def test_delete(self):
        """删除凭据"""
        vault = Vault()
        vault.store("key1", "value1")

        assert vault.exists("key1")
        vault.delete("key1")
        assert not vault.exists("key1")

    def test_list_keys(self):
        """列出凭据键"""
        vault = Vault()
        vault.store("key1", "value1")
        vault.store("key2", "value2")

        keys = vault.list_keys()
        assert "key1" in keys
        assert "key2" in keys

    def test_rotate(self):
        """轮换凭据"""
        vault = Vault()
        vault.store("api_key", "old_value")

        # 轮换
        vault.rotate("api_key", "new_value")

        value = vault.get("api_key")
        assert value == "new_value"

    def test_with_master_key(self):
        """使用指定主密钥"""
        vault = Vault(master_key="my-secret-key")
        vault.store("api_key", "secret")

        # 不同的 vault 实例有独立的存储
        # 只有同一个实例内才能共享凭据
        value = vault.get("api_key")
        assert value == "secret"

        # 新实例应该无法获取（独立的存储）
        vault2 = Vault(master_key="my-secret-key")
        assert vault2.get("api_key") is None


class TestVaultAccessControl:
    """访问控制测试"""

    def test_allowed_agents(self):
        """允许的 agent 列表"""
        vault = Vault()
        vault.store(
            "api_key",
            "secret",
            allowed_agents=["agent-1", "agent-2"]
        )

        # 允许的 agent 应该能获取
        assert vault.get("api_key", agent_id="agent-1") == "secret"

        # 不允许的 agent 不能获取
        assert vault.get("api_key", agent_id="agent-3") is None

    def test_max_uses(self):
        """最大使用次数"""
        vault = Vault()
        vault.store("api_key", "secret", max_uses=2)

        # 第一次使用
        assert vault.get("api_key") == "secret"

        # 第二次使用
        assert vault.get("api_key") == "secret"

        # 第三次使用 - 应该被拒绝
        assert vault.get("api_key") is None


class TestVaultExpiration:
    """过期时间测试"""

    def test_expired_credential(self):
        """已过期凭据"""
        vault = Vault()
        # 1秒后过期
        vault.store("api_key", "secret", expires_at=time.time() - 1)

        # 应该返回 None
        assert vault.get("api_key") is None

    def test_valid_credential(self):
        """有效凭据"""
        vault = Vault()
        # 1小时后过期
        vault.store("api_key", "secret", expires_at=time.time() + 3600)

        # 应该能获取
        assert vault.get("api_key") == "secret"


class TestVaultCache:
    """缓存测试"""

    def test_cache_cleared_on_delete(self):
        """删除时清除缓存"""
        vault = Vault()
        vault.store("api_key", "secret")

        # 获取以填充缓存
        vault.get("api_key")

        # 删除
        vault.delete("api_key")

        # 重新存储
        vault.store("api_key", "new_secret")

        # 应该获取新值
        assert vault.get("api_key") == "new_secret"


class TestCredential:
    """Credential 数据类测试"""

    def test_credential_creation(self):
        """创建凭据"""
        cred = Credential(
            key="test_key",
            value="encrypted_value",
        )

        assert cred.key == "test_key"
        assert cred.value == "encrypted_value"
        assert cred.use_count == 0


class TestVaultFernetEncryption:
    """Fernet AES 加密测试"""

    def test_fernet_encrypt_decrypt(self):
        """Fernet 加密解密测试"""
        vault = Vault()
        master_key = vault.get_master_key()

        # 存储凭据
        vault.store("fernet_key", "fernet_secret_data_12345")

        # 获取凭据
        value = vault.get("fernet_key")
        assert value == "fernet_secret_data_12345"

        # 验证加密后数据不是明文
        cred = vault._credentials["fernet_key"]
        assert cred.value != "fernet_secret_data_12345"
        assert cred.salt is not None

    def test_fernet_different_salts(self):
        """不同盐值生成不同加密结果"""
        vault = Vault()

        vault.store("key1", "same_value")
        vault.store("key2", "same_value")

        # 不同加密结果
        val1 = vault._credentials["key1"].value
        val2 = vault._credentials["key2"].value
        assert val1 != val2

    def test_fernet_rejects_tampered_data(self):
        """Fernet 拒绝篡改数据"""
        vault = Vault()
        vault.store("api_key", "secret")

        # 篡改加密数据
        cred = vault._credentials["api_key"]
        tampered_value = cred.value[:-5] + "XXXXX"
        cred.value = tampered_value

        # 解密应该失败
        result = vault.get("api_key")
        assert result is None

    def test_fernet_encrypted_value_is_base64(self):
        """Fernet 加密结果是有效的 base64"""
        vault = Vault()
        vault.store("api_key", "secret_value")

        import base64
        cred = vault._credentials["api_key"]

        # 应该能成功解码
        try:
            decoded = base64.b64decode(cred.value)
            assert len(decoded) > 0
        except Exception:
            assert False, "Fernet encrypted value should be valid base64"
