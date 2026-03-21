"""
GiGPO Engine Tests
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestGiGPOConfig:
    """测试 GiGPO 配置"""

    def test_default_config(self):
        """测试默认配置"""
        from src.agents.rl import GiGPOConfig

        config = GiGPOConfig()

        assert config.episode_advantage_weight == 1.0
        assert config.step_advantage_weight == 0.5
        assert config.use_gae is True
        assert config.gae_lambda == 0.95
        assert config.gamma == 0.99

    def test_custom_config(self):
        """测试自定义配置"""
        from src.agents.rl import GiGPOConfig

        config = GiGPOConfig(
            episode_advantage_weight=0.8,
            step_advantage_weight=0.6,
            use_gae=False,
            gae_lambda=0.9,
            gamma=0.995,
        )

        assert config.episode_advantage_weight == 0.8
        assert config.step_advantage_weight == 0.6
        assert config.use_gae is False
        assert config.gae_lambda == 0.9
        assert config.gamma == 0.995


class TestGiGPOEngine:
    """测试 GiGPO 引擎"""

    def test_gigpo_engine_init(self):
        """测试引擎初始化"""
        from src.agents.rl import GiGPOEngine, GiGPOConfig, HardwareSpec, ComputeBackend

        config = GiGPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CUDA, device_name="cuda:0", memory_gb=8.0)

        engine = GiGPOEngine(config, hardware)

        assert engine.config == config
        assert engine.hardware == hardware

    def test_train_step_returns_dict(self):
        """测试训练步骤返回字典"""
        from src.agents.rl import create_gigpo_engine, GiGPOConfig, HardwareSpec, ComputeBackend

        config = GiGPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=8.0)
        engine = create_gigpo_engine(config, hardware)

        # 模拟批次数据 - GiGPO 使用 2D [batch_size, seq_len]
        batch = {
            "log_probs": np.random.randn(4, 10),
            "new_log_probs": np.random.randn(4, 10),
            "advantages": np.random.randn(4, 10),
            "rewards": np.random.randn(4, 10),
            "mask": np.ones((4, 10)),
        }

        result = engine.train_step(batch)

        assert isinstance(result, dict)
        assert "total_loss" in result


class TestCreateGiGPOEngine:
    """测试 GiGPO 引擎工厂函数"""

    def test_create_with_cuda(self):
        """测试使用 CUDA 创建引擎"""
        from src.agents.rl import create_gigpo_engine, GiGPOConfig, HardwareSpec, ComputeBackend

        config = GiGPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CUDA, device_name="cuda:0", memory_gb=8.0)

        engine = create_gigpo_engine(config, hardware)

        assert engine is not None
        assert engine.hardware.backend == ComputeBackend.CUDA

    def test_create_requires_cuda(self):
        """测试 GiGPO 需要 CUDA"""
        from src.agents.rl import create_gigpo_engine, GiGPOConfig, HardwareSpec, ComputeBackend

        config = GiGPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        # CPU 模式下应该创建引擎但不实际运行
        engine = create_gigpo_engine(config, hardware)

        assert engine is not None
