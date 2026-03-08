"""
E2E Tests Configuration for OpenYoung CLI

This module provides fixtures and configuration for E2E testing
of the OpenYoung CLI application.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def load_env():
    """Load .env file into environment variables"""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()
                        # Handle single-quoted JSON values in .env
                        if value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # Only set if not already set
                        if key not in os.environ:
                            os.environ[key] = value


# Load env at module import time
load_env()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def cli_path(project_root: Path) -> str:
    """Path to CLI entry point"""
    return str(project_root / "src" / "cli" / "main.py")


@pytest.fixture(scope="session")
def env_vars() -> Dict[str, Any]:
    """Environment variables from .env"""
    return dict(os.environ)


@pytest.fixture(scope="session")
def llm_config() -> Dict[str, Any]:
    """LLM provider configurations from .env"""
    import json

    configs = {}
    config_keys = [
        "DEEPSEEK_CONFIG",
        "MOONSHOT_CONFIG",
        "QWEN_CONFIG",
        "GLM_CONFIG",
        "GEMINI_CONFIG",
        "MINIMAX_CONFIG",
    ]

    for key in config_keys:
        value = os.environ.get(key)
        if value:
            try:
                configs[key] = json.loads(value)
            except json.JSONDecodeError:
                pass

    return configs


@pytest.fixture(scope="session")
def has_valid_llm_config(llm_config: Dict[str, Any]) -> bool:
    """Check if valid LLM config exists"""
    return len(llm_config) > 0


@pytest.fixture(scope="session")
def default_model(llm_config: Dict[str, Any]) -> Optional[str]:
    """Get default model from config"""
    if not llm_config:
        return None

    first_config = next(iter(llm_config.values()))
    prefixes = first_config.get("prefix", [])
    return prefixes[0] if prefixes else None
