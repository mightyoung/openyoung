"""企业功能单元测试"""
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, '.')

from src.datacenter.enterprise import EnterpriseManager, Permission

TEST_ENT = ".young/test_ent_unit"


@pytest.fixture
def em():
    # Cleanup before
    if Path(TEST_ENT).exists():
        shutil.rmtree(TEST_ENT)
    if Path(f"{TEST_ENT}.db").exists():
        Path(f"{TEST_ENT}.db").unlink()
    em = EnterpriseManager(TEST_ENT)
    yield em
    # Cleanup after
    if Path(TEST_ENT).exists():
        shutil.rmtree(TEST_ENT)
    if Path(f"{TEST_ENT}.db").exists():
        Path(f"{TEST_ENT}.db").unlink()


def test_create_tenant(em):
    """测试创建租户"""
    tenant = em.create_tenant("t1", "Test Company")
    assert tenant.tenant_id == "t1"
    assert tenant.name == "Test Company"


def test_get_tenant(em):
    """测试获取租户"""
    em.create_tenant("t2", "Company 2")
    tenant = em.get_tenant("t2")
    assert tenant is not None
    assert tenant.name == "Company 2"


def test_update_tenant(em):
    """测试更新租户"""
    em.create_tenant("t3", "Original")
    em.update_tenant("t3", name="Updated")
    tenant = em.get_tenant("t3")
    assert tenant.name == "Updated"


def test_list_tenants(em):
    """测试列出租户"""
    em.create_tenant("t4", "Company 4")
    em.create_tenant("t5", "Company 5")
    tenants = em.list_tenants()
    assert len(tenants) >= 2


def test_create_user(em):
    """测试创建用户"""
    em.create_tenant("t6", "Company")
    user = em.create_user(
        "u1", "t6", "admin", "admin@test.com",
        password="pass123", role="admin"
    )
    assert user.username == "admin"
    assert user.role == "admin"


def test_authenticate_success(em):
    """测试成功认证"""
    em.create_tenant("t7", "Company")
    em.create_user("u2", "t7", "user", "user@test.com", password="password123")
    auth = em.authenticate("user", "password123", "t7")
    assert auth is not None
    assert auth.username == "user"


def test_authenticate_failure(em):
    """测试失败认证"""
    em.create_tenant("t8", "Company")
    em.create_user("u3", "t8", "user", password="correct")
    auth = em.authenticate("user", "wrongpassword", "t8")
    assert auth is None


def test_check_permission_admin(em):
    """测试管理员权限"""
    em.create_tenant("t9", "Company")
    user = em.create_user("u4", "t9", "admin", role="admin", permissions=[Permission.ADMIN])
    assert em.check_permission(user, Permission.DELETE)


def test_check_permission_user_role(em):
    """测试用户角色权限"""
    em.create_tenant("t10", "Company")
    user = em.create_user("u5", "t10", "regular", role="user")
    assert em.check_permission(user, Permission.READ)
    assert not em.check_permission(user, Permission.ADMIN)


def test_audit_log(em):
    """测试审计日志"""
    em.log_audit("t11", "u6", "create", "agent", "a1")
    logs = em.query_audit_logs(tenant_id="t11")
    assert len(logs) >= 1
    assert logs[0].action == "create"


def test_audit_log_with_metadata(em):
    """测试带元数据的审计日志"""
    em.log_audit(
        "t12", "u7", "execute", "task", "task-1",
        metadata={"duration": 1000, "tokens": 500}
    )
    logs = em.query_audit_logs(tenant_id="t12")
    assert logs[0].metadata["duration"] == 1000


def test_audit_stats(em):
    """测试审计统计"""
    em.log_audit("t13", "u8", "read", "agent", "a1")
    em.log_audit("t13", "u8", "write", "agent", "a2")
    stats = em.get_audit_stats("t13")
    assert stats["total"] >= 2
    assert "by_action" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
