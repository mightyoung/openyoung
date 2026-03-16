"""
RL Test Fixtures

Pytest fixtures for RL testing
"""

import pytest
import os
import json
import tempfile
from pathlib import Path


@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary data directory for tests"""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_rl_data():
    """Sample RL training data"""
    return [
        {
            "prompt": "Write a fibonacci function",
            "chosen": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
            "rejected": "I don't know",
            "reward_chosen": 1.0,
            "reward_rejected": 0.0,
        },
        {
            "prompt": "Explain recursion",
            "chosen": "Recursion is when a function calls itself...",
            "rejected": "Skip",
            "reward_chosen": 1.0,
            "reward_rejected": 0.0,
        },
    ]


@pytest.fixture
def save_test_data(sample_rl_data, test_data_dir):
    """Save sample data to file"""
    data_file = test_data_dir / "train.jsonl"
    with open(data_file, 'w') as f:
        for item in sample_rl_data:
            f.write(json.dumps(item) + '\n')
    return data_file


@pytest.fixture
def gpu_available():
    """Check if GPU is available"""
    try:
        import torch
        return torch.cuda.is_available() or torch.backends.mps.is_available()
    except ImportError:
        return False


@pytest.fixture
def torch_available():
    """Check if PyTorch is available"""
    try:
        import torch
        return True
    except ImportError:
        return False


@pytest.fixture
def mock_reward_model():
    """Mock reward model for testing"""
    def compute_reward(prompt, response):
        # Simple rule-based reward
        length = len(response)
        if length < 10:
            return 0.0
        elif "def " in response or "class " in response:
            return 0.8  # Code-like response
        elif response != "I don't know":
            return 0.5  # Normal response
        return 0.0

    return compute_reward


@pytest.fixture
def create_test_batch():
    """Factory to create test batches"""
    import numpy as np

    def _create_batch(batch_size=4, seq_len=10):
        return {
            "log_probs": np.random.randn(batch_size, seq_len),
            "new_log_probs": np.random.randn(batch_size, seq_len),
            "old_log_probs": np.random.randn(batch_size, seq_len),
            "advantages": np.random.randn(batch_size),
            "rewards": np.random.randn(batch_size, seq_len),
            "mask": np.ones((batch_size, seq_len)),
        }

    return _create_batch


@pytest.fixture
def hardware_spec():
    """Create test hardware spec"""
    from src.agents.rl import HardwareSpec, ComputeBackend

    return HardwareSpec(
        backend=ComputeBackend.CPU,
        device_name="cpu",
        memory_gb=8.0,
    )


@pytest.fixture
def grpo_config():
    """Create GRPO config for testing"""
    from src.agents.rl import GRPOConfig

    return GRPOConfig(
        learning_rate=1e-4,
        clip_epsilon=0.2,
        kl_beta=0.01,
        group_size=4,
        batch_size=8,
    )


@pytest.fixture
def gigpo_config():
    """Create GiGPO config for testing"""
    from src.agents.rl import GiGPOConfig

    return GiGPOConfig(
        episode_advantage_weight=0.6,
        step_advantage_weight=0.4,
        use_gae=True,
        gae_lambda=0.95,
        gamma=0.99,
    )


@pytest.fixture
def rl_config_collection():
    """Create RL config for collection mode"""
    from src.agents.rl import RLConfig, RLMode

    return RLConfig(
        mode=RLMode.COLLECTION_ONLY,
        enabled=True,
    )


@pytest.fixture
def rl_config_grpo():
    """Create RL config for GRPO mode"""
    from src.agents.rl import RLConfig, RLMode, GRPOConfig

    return RLConfig(
        mode=RLMode.GRPO,
        enabled=True,
        grpo=GRPOConfig(
            learning_rate=1e-4,
            group_size=4,
        )
    )


@pytest.fixture
def rl_config_gigpo():
    """Create RL config for GiGPO mode"""
    from src.agents.rl import RLConfig, RLMode, GiGPOConfig

    return RLConfig(
        mode=RLMode.GIGPO,
        enabled=True,
        gigpo=GiGPOConfig(
            episode_advantage_weight=0.6,
            step_advantage_weight=0.4,
        )
    )
