"""
Package Manager Tests
"""

import pytest

from src.package_manager import AgentRegistry, PackageManager


class TestPackageManager:
    def test_package_manager_creation(self):
        pm = PackageManager()
        assert pm is not None

    def test_package_manager_has_storage(self):
        pm = PackageManager()
        assert hasattr(pm, "storage")


class TestAgentRegistry:
    def test_registry_creation(self):
        reg = AgentRegistry()
        assert reg is not None
