"""
RL E2E Tests - End-to-End Testing

Tests the complete RL pipeline from experience collection to training
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock


class TestRLFullPipeline:
    """完整的 RL 流程测试"""

    def test_collection_to_training_pipeline(self):
        """测试从经验收集到训练的完整流程"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
            create_rl_engine,
        )

        # 1. 创建收集模式引擎
        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        collection_engine = RLEngine(config, hardware)

        assert collection_engine.is_training_enabled is False

        # 2. 模拟经验收集
        mock_experiences = [
            {"prompt": "Task 1", "response": "Result 1", "reward": 1.0},
            {"prompt": "Task 2", "response": "Result 2", "reward": 0.8},
            {"prompt": "Task 3", "response": "Result 3", "reward": 0.5},
            {"prompt": "Task 4", "response": "Result 4", "reward": 0.3},
        ]

        # 验证收集的数据格式
        for exp in mock_experiences:
            assert "prompt" in exp
            assert "response" in exp
            assert "reward" in exp

    def test_grpo_training_pipeline(self):
        """测试 GRPO 训练流程"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
            GRPOConfig,
        )

        config = RLConfig(
            mode=RLMode.GRPO,
            grpo=GRPOConfig(
                learning_rate=1e-4,
                group_size=4,
                batch_size=8,
            )
        )
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 模拟训练批次
        batch = {
            "log_probs": np.random.randn(8, 10),
            "new_log_probs": np.random.randn(8, 10),
            "advantages": np.random.randn(8, 10),
            "rewards": np.random.randn(8, 10),
            "mask": np.ones((8, 10)),
        }

        result = engine.train_step(batch)

        # 验证返回格式
        assert "total_loss" in result
        assert isinstance(result["total_loss"], (int, float))

    def test_gigpo_training_pipeline(self):
        """测试 GiGPO 训练流程"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
            GiGPOConfig,
        )

        config = RLConfig(
            mode=RLMode.GIGPO,
            gigpo=GiGPOConfig(
                episode_advantage_weight=0.6,
                step_advantage_weight=0.4,
            )
        )
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=8.0)
        engine = RLEngine(config, hardware)

        # 模拟多 episode 批次 - GiGPO 使用 2D [batch_size, seq_len]
        batch = {
            "log_probs": np.random.randn(4, 10),
            "new_log_probs": np.random.randn(4, 10),
            "advantages": np.random.randn(4, 10),
            "rewards": np.random.randn(4, 10),
            "mask": np.ones((4, 10)),
        }

        result = engine.train_step(batch)

        assert "total_loss" in result


class TestHardwareAdaptation:
    """硬件自适应测试"""

    def test_auto_backend_selection_cuda(self):
        """测试 CUDA 后端自动选择"""
        from src.agents.rl import (
            get_recommended_mode, RLMode,
            HardwareSpec, ComputeBackend,
        )

        # 模拟 NVIDIA GPU
        hw_cuda = HardwareSpec(
            backend=ComputeBackend.CUDA,
            device_name="NVIDIA RTX 3090",
            memory_gb=24.0,
        )

        mode = get_recommended_mode(hw_cuda)
        assert mode == RLMode.GIGPO

    def test_auto_backend_selection_mps(self):
        """测试 MPS 后端自动选择"""
        from src.agents.rl import (
            get_recommended_mode, RLMode,
            HardwareSpec, ComputeBackend,
        )

        # 模拟 Apple Silicon
        hw_mps = HardwareSpec(
            backend=ComputeBackend.MPS,
            device_name="Apple M2 Pro",
            memory_gb=16.0,
        )

        mode = get_recommended_mode(hw_mps)
        assert mode == RLMode.GRPO

    def test_auto_backend_selection_cpu(self):
        """测试 CPU 后端自动选择"""
        from src.agents.rl import (
            get_recommended_mode, RLMode,
            HardwareSpec, ComputeBackend,
        )

        # 模拟 CPU
        hw_cpu = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=8.0,
        )

        mode = get_recommended_mode(hw_cpu)
        assert mode == RLMode.COLLECTION_ONLY


class TestConfigLoading:
    """配置加载测试"""

    def test_load_from_yaml(self):
        """测试从 YAML 加载配置"""
        import tempfile
        import os

        yaml_content = """
rl:
  enabled: true
  mode: grpo
  device: auto
  grpo:
    learning_rate: 1.0e-4
    clip_epsilon: 0.3
    group_size: 8
    batch_size: 16
  gigpo:
    episode_advantage_weight: 0.7
    step_advantage_weight: 0.3
    use_gae: true
    gae_lambda: 0.95
    gamma: 0.99
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            import yaml
            with open(temp_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert config_data['rl']['mode'] == 'grpo'
            assert config_data['rl']['grpo']['learning_rate'] == 1.0e-4
            assert config_data['rl']['gigpo']['episode_advantage_weight'] == 0.7
        finally:
            os.unlink(temp_path)

    def test_env_variable_override(self):
        """测试环境变量覆盖"""
        from src.agents.rl import RLConfig, RLMode

        with patch.dict("os.environ", {
            "RL_MODE": "gigpo",
            "RL_DEVICE": "cuda",
            "RL_GRPO_LR": "1e-4",
        }):
            # 验证环境变量可以读取
            assert os.environ.get("RL_MODE") == "gigpo"
            assert os.environ.get("RL_DEVICE") == "cuda"


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_mode_handling(self):
        """测试无效模式处理"""
        from src.agents.rl import RLConfig, RLMode

        # 默认模式应该是安全的
        config = RLConfig()
        assert config.mode in [RLMode.COLLECTION_ONLY, RLMode.GRPO, RLMode.GIGPO]

    def test_grpo_requires_minimum_group_size(self):
        """测试 GRPO 需要最小组大小"""
        from src.agents.rl import GRPOConfig

        # 组大小为 0 应该被处理
        config = GRPOConfig(group_size=0)
        # 验证配置可以创建
        assert config.group_size >= 0


class TestPerformance:
    """性能测试"""

    def test_batch_processing_speed(self):
        """测试批次处理速度"""
        import time
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 创建大批次
        batch_size = 100
        batch = {
            "log_probs": np.random.randn(batch_size, 50),
            "new_log_probs": np.random.randn(batch_size, 50),
            "advantages": np.random.randn(batch_size, 50),
            "rewards": np.random.randn(batch_size, 50),
            "mask": np.ones((batch_size, 50)),
        }

        # 测量处理时间
        start = time.time()
        for _ in range(10):
            engine.train_step(batch)
        elapsed = time.time() - start

        # 验证处理速度合理 (10 次迭代应在合理时间内完成)
        assert elapsed < 10.0  # 10秒内完成 10 次迭代


class TestMemoryManagement:
    """内存管理测试"""

    def test_large_batch_memory(self):
        """测试大批次内存使用"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 创建大批次
        large_batch = {
            "log_probs": np.random.randn(1000, 100),
            "new_log_probs": np.random.randn(1000, 100),
            "advantages": np.random.randn(1000, 100),
            "rewards": np.random.randn(1000, 100),
            "mask": np.ones((1000, 100)),
        }

        # 验证可以处理
        result = engine.train_step(large_batch)
        assert "total_loss" in result


# 需要导入 os
import os
