"""
CLI Commands E2E Tests

Real CLI tests using subprocess - NOT function calls.
Based on Kent Beck TDD principles:
- Tests are examples, not verification checklists
- Each test is independent
- Clear failure messages
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


# Test constants
TEST_GITHUB_URL = "https://github.com/Fosowl/agenticSeek"


class TestCLIBasics:
    """Test basic CLI functionality"""

    def test_cli_help(self, project_root):
        """Example: User runs 'openyoung --help'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "--help"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"CLI help failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "OpenYoung" in result.stdout

    def test_cli_version(self, project_root):
        """Example: User runs 'openyoung --version'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "--version"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should either succeed or show version
        assert result.returncode == 0 or "version" in result.stdout.lower()


class TestCLIImport:
    """Test 'openyoung import' command"""

    def test_import_github_basic(self, project_root, temp_agent_dir):
        """Example: User imports agent from GitHub"""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.cli.main",
                "import", "github",
                TEST_GITHUB_URL,
                "--no-validate"
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=180,
        )

        # Should either succeed or show clear error
        # Note: import may fail due to network/validation, but CLI shouldn't crash
        assert result.returncode in [0, 1], (
            f"Import command crashed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_import_github_with_name(self, project_root):
        """Example: User imports with custom agent name"""
        result = subprocess.run(
            [
                sys.executable, "-m", "src.cli.main",
                "import", "github",
                TEST_GITHUB_URL,
                "test-agent",
                "--no-validate"
            ],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=120,
        )

        # Should not crash
        assert result.returncode in [0, 1]  # 0=success, 1=expected error (network, etc)


class TestCLIAgent:
    """Test 'openyoung agent' commands"""

    def test_agent_list(self, project_root):
        """Example: User runs 'openyoung agent list'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "agent", "list"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Agent list failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_agent_info_default(self, project_root):
        """Example: User runs 'openyoung agent info default'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "agent", "info", "default"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Agent info failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestCLILlm:
    """Test 'openyoung llm' commands"""

    def test_llm_list(self, project_root):
        """Example: User runs 'openyoung llm list'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "llm", "list"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"LLM list failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_llm_info(self, project_root):
        """Example: User runs 'openyoung llm info'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "llm", "info"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"LLM info failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestCLIConfig:
    """Test 'openyoung config' commands"""

    def test_config_list(self, project_root):
        """Example: User runs 'openyoung config list'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "config", "list"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Config list failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_config_get(self, project_root):
        """Example: User runs 'openyoung config get llm.model'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "config", "get", "llm.model"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Config get failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


class TestCLIEval:
    """Test 'openyoung eval' commands"""

    def test_eval_list(self, project_root):
        """Example: User runs 'openyoung eval list'"""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.main", "eval", "list"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Eval list failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


# ==================== Fixtures ====================

@pytest.fixture
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_agent_dir(tmp_path):
    """Create temporary agent directory"""
    agent_dir = tmp_path / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir
