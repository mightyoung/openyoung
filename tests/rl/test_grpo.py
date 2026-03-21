"""
GRPO Engine Tests
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestGRPOConfig:
    """测试 GRPO 配置"""

    def test_default_config(self):
        """测试默认配置"""
        from src.agents.rl import GRPOConfig

        config = GRPOConfig()

        assert config.learning_rate == 1e-5
        assert config.clip_epsilon == 0.2
        assert config.kl_beta == 0.01
        assert config.group_size == 4
        assert config.batch_size == 8

    def test_custom_config(self):
        """测试自定义配置"""
        from src.agents.rl import GRPOConfig

        config = GRPOConfig(
            learning_rate=1e-4,
            clip_epsilon=0.3,
            kl_beta=0.02,
            group_size=8,
            batch_size=16,
        )

        assert config.learning_rate == 1e-4
        assert config.clip_epsilon == 0.3
        assert config.kl_beta == 0.02
        assert config.group_size == 8
        assert config.batch_size == 16


class TestGRPOEngine:
    """测试 GRPO 引擎"""

    def test_grpo_engine_init(self):
        """测试引擎初始化"""
        from src.agents.rl import GRPOEngine, GRPOConfig, HardwareSpec, ComputeBackend

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = GRPOEngine(config, hardware)

        assert engine.config == config
        assert engine.hardware == hardware

    def test_train_step_returns_dict(self):
        """测试训练步骤返回字典"""
        from src.agents.rl import GRPOEngine, GRPOConfig, HardwareSpec, ComputeBackend

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = GRPOEngine(config, hardware)

        # 模拟批次数据
        batch = {
            "log_probs": np.random.randn(8, 10),
            "new_log_probs": np.random.randn(8, 10),
            "advantages": np.random.randn(8, 10),
            "rewards": np.random.randn(8, 10),
            "mask": np.ones((8, 10)),
        }

        result = engine.train_step(batch)

        assert isinstance(result, dict)
        assert "total_loss" in result


class TestCreateGRPOEngine:
    """测试 GRPO 引擎工厂函数"""

    def test_create_with_cpu(self):
        """测试使用 CPU 创建引擎"""
        from src.agents.rl import create_grpo_engine, GRPOConfig, HardwareSpec, ComputeBackend

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = create_grpo_engine(config, hardware)

        assert engine is not None
        assert engine.hardware.backend == ComputeBackend.CPU
