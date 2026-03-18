"""
CLI Tests Configuration

Fixtures and configuration for CLI command tests.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@pytest.fixture(scope="session")
def project_root():
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture
def cli_runner():
    """Provide a Click CLI tester"""
    import click.testing

    return click.testing.CliRunner()


@pytest.fixture
def tmp_user_config(tmp_path, monkeypatch):
    """Create temporary user config directory"""
    config_dir = tmp_path / ".openyoung"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text("{}")

    # Point to temp config
    monkeypatch.setenv("OPENYOUNG_CONFIG_DIR", str(config_dir))

    yield config_dir
