"""
RL Engine Integration Tests
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestRLConfig:
    """测试 RL 配置"""

    def test_default_config(self):
        """测试默认配置"""
        from src.agents.rl import RLConfig, RLMode

        config = RLConfig()

        assert config.mode == RLMode.COLLECTION_ONLY
        assert config.enabled is True

    def test_grpo_mode(self):
        """测试 GRPO 模式配置"""
        from src.agents.rl import RLConfig, RLMode

        config = RLConfig(mode=RLMode.GRPO)

        assert config.mode == RLMode.GRPO
        assert config.grpo is not None
        assert config.grpo.learning_rate == 1e-5

    def test_gigpo_mode(self):
        """测试 GiGPO 模式配置"""
        from src.agents.rl import RLConfig, RLMode

        config = RLConfig(mode=RLMode.GIGPO)

        assert config.mode == RLMode.GIGPO
        assert config.gigpo is not None
        assert config.gigpo.episode_advantage_weight == 1.0


class TestRLMode:
    """测试 RL 模式枚举"""

    def test_mode_values(self):
        """测试模式值"""
        from src.agents.rl import RLMode

        assert RLMode.COLLECTION_ONLY.value == "collection_only"
        assert RLMode.GRPO.value == "grpo"
        assert RLMode.GIGPO.value == "gigpo"

    def test_mode_from_string(self):
        """测试从字符串创建模式"""
        from src.agents.rl import RLMode

        assert RLMode("collection_only") == RLMode.COLLECTION_ONLY
        assert RLMode("grpo") == RLMode.GRPO
        assert RLMode("gigpo") == RLMode.GIGPO


class TestRLEngine:
    """测试 RL 引擎"""

    def test_engine_collection_mode(self):
        """测试仅收集模式"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = RLEngine(config, hardware)

        assert engine.is_training_enabled is False
        assert engine.requires_gpu is False

    def test_engine_grpo_mode(self):
        """测试 GRPO 模式"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.MPS, device_name="mps", memory_gb=16.0)

        engine = RLEngine(config, hardware)

        assert engine.is_training_enabled is True
        # GRPO 可以在 CPU/MPS 上运行，但有 GPU 更好
        assert engine.requires_gpu is True  # GRPO 可以利用 GPU

    def test_engine_gigpo_mode(self):
        """测试 GiGPO 模式"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.GIGPO)
        hardware = HardwareSpec(backend=ComputeBackend.CUDA, device_name="cuda:0", memory_gb=8.0)

        engine = RLEngine(config, hardware)

        assert engine.is_training_enabled is True
        assert engine.requires_gpu is True

    def test_get_status(self):
        """测试获取状态"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = RLEngine(config, hardware)
        status = engine.get_status()

        assert "mode" in status
        assert "backend" in status
        assert "training_enabled" in status
        assert status["mode"] == "collection_only"

    def test_can_run_collection(self):
        """测试收集模式可运行"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = RLEngine(config, hardware)

        assert engine.can_run() is True

    def test_can_run_grpo(self):
        """测试 GRPO 可运行"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = RLEngine(config, hardware)

        assert engine.can_run() is True

    def test_can_run_gigpo_no_cuda(self):
        """测试 GiGPO 无 CUDA 不可运行"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.GIGPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = RLEngine(config, hardware)

        assert engine.can_run() is False

    def test_can_run_gigpo_with_cuda(self):
        """测试 GiGPO 有 CUDA 可运行"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.GIGPO)
        hardware = HardwareSpec(backend=ComputeBackend.CUDA, device_name="cuda:0", memory_gb=8.0)

        engine = RLEngine(config, hardware)

        assert engine.can_run() is True


class TestCreateRLEngine:
    """测试 RL 引擎工厂函数"""

    def test_create_default(self):
        """测试创建默认引擎"""
        from src.agents.rl import create_rl_engine, RLMode, RLEngine

        engine = create_rl_engine()

        assert isinstance(engine, RLEngine)
        assert engine.config.mode == RLMode.COLLECTION_ONLY

    def test_create_with_config(self):
        """测试使用配置创建"""
        from src.agents.rl import create_rl_engine, RLConfig, RLMode, HardwareSpec, ComputeBackend, RLEngine

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        engine = create_rl_engine(config, hardware)

        assert isinstance(engine, RLEngine)
        assert engine.config.mode == RLMode.GRPO


class TestGetRecommendedMode:
    """测试硬件推荐模式"""

    def test_recommend_cuda(self):
        """测试推荐 CUDA 使用 GiGPO"""
        from src.agents.rl import get_recommended_mode, HardwareSpec, ComputeBackend, RLMode

        hardware = HardwareSpec(backend=ComputeBackend.CUDA, device_name="cuda:0", memory_gb=24.0)

        mode = get_recommended_mode(hardware)

        assert mode == RLMode.GIGPO

    def test_recommend_mps(self):
        """测试推荐 MPS 使用 GRPO"""
        from src.agents.rl import get_recommended_mode, HardwareSpec, ComputeBackend, RLMode

        hardware = HardwareSpec(backend=ComputeBackend.MPS, device_name="mps", memory_gb=16.0)

        mode = get_recommended_mode(hardware)

        assert mode == RLMode.GRPO

    def test_recommend_cpu(self):
        """测试推荐 CPU 使用收集模式"""
        from src.agents.rl import get_recommended_mode, HardwareSpec, ComputeBackend, RLMode

        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=8.0)

        mode = get_recommended_mode(hardware)

        assert mode == RLMode.COLLECTION_ONLY


class TestLoadConfig:
    """测试配置加载"""

    def test_load_from_env(self):
        """测试从环境变量加载"""
        from src.agents.rl import load_config, RLMode

        with patch.dict("os.environ", {"RL_MODE": "grpo", "RL_ENABLED": "true"}):
            config = load_config()

            assert config.mode == RLMode.GRPO
            assert config.enabled is True


class TestIntegration:
    """集成测试"""

    def test_full_training_pipeline(self):
        """测试完整训练流程"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
            GRPOConfig, create_grpo_engine,
        )

        # 1. 创建配置
        config = RLConfig(
            mode=RLMode.GRPO,
            grpo=GRPOConfig(
                learning_rate=1e-4,
                group_size=4,
                batch_size=8,
            )
        )

        # 2. 创建硬件
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        # 3. 创建引擎
        engine = RLEngine(config, hardware)

        # 4. 检查状态
        status = engine.get_status()
        assert status["mode"] == "grpo"
        assert status["training_enabled"] is True

        # 5. 执行训练步骤
        batch = {
            "log_probs": np.random.randn(8, 10),
            "new_log_probs": np.random.randn(8, 10),
            "advantages": np.random.randn(8, 10),
            "rewards": np.random.randn(8, 10),
            "mask": np.ones((8, 10)),
        }

        result = engine.train_step(batch)
        assert "total_loss" in result

    def test_mode_switching(self):
        """测试模式切换"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)

        # 收集模式
        config1 = RLConfig(mode=RLMode.COLLECTION_ONLY)
        engine1 = RLEngine(config1, hardware)
        assert engine1.is_training_enabled is False

        # GRPO 模式
        config2 = RLConfig(mode=RLMode.GRPO)
        engine2 = RLEngine(config2, hardware)
        assert engine2.is_training_enabled is True

    def test_hardware_detection_integration(self):
        """测试硬件检测集成"""
        from src.agents.rl import create_rl_engine, HardwareDetector

        # 自动检测硬件
        hardware = HardwareDetector.detect()
        engine = create_rl_engine(hardware=hardware)

        assert engine is not None
        assert engine.hardware is not None
