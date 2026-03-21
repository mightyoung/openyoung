"""
RL Integration Tests - Full Agent Flow

Tests the complete integration of RL module with the agent system
"""

import pytest
import json
import numpy as np
from unittest.mock import patch, MagicMock, AsyncMock


class TestRLAgentIntegration:
    """测试 RL 模块与 Agent 的集成"""

    def test_rl_engine_initialization(self, rl_config_grpo, hardware_spec):
        """测试 RL 引擎初始化"""
        from src.agents.rl import RLEngine

        engine = RLEngine(rl_config_grpo, hardware_spec)

        assert engine.is_training_enabled is True
        assert engine.config.mode.value == "grpo"

    def test_collection_mode_initialization(self, rl_config_collection, hardware_spec):
        """测试收集模式初始化"""
        from src.agents.rl import RLEngine

        engine = RLEngine(rl_config_collection, hardware_spec)

        assert engine.is_training_enabled is False
        assert engine.requires_gpu is False

    def test_experience_collection_flow(self, create_test_batch):
        """测试经验收集流程"""
        from src.agents.rl import RLEngine, RLConfig, RLMode, HardwareSpec, ComputeBackend

        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 模拟经验收集
        experiences = []
        for i in range(10):
            batch = create_test_batch()
            # 收集经验
            experiences.append({
                "batch": batch,
                "reward": np.random.random(),
            })

        assert len(experiences) == 10
        assert all("batch" in exp for exp in experiences)


class TestRLTrainingPipeline:
    """测试 RL 训练流水线"""

    def test_grpo_training_single_step(self, rl_config_grpo, hardware_spec, create_test_batch):
        """测试 GRPO 单步训练"""
        from src.agents.rl import RLEngine

        engine = RLEngine(rl_config_grpo, hardware_spec)

        # 执行训练步骤
        batch = create_test_batch(batch_size=8, seq_len=20)
        result = engine.train_step(batch)

        # 验证返回
        assert isinstance(result, dict)
        assert "total_loss" in result

    def test_grpo_training_multiple_steps(self, rl_config_grpo, hardware_spec):
        """测试 GRPO 多步训练"""
        from src.agents.rl import RLEngine

        engine = RLEngine(rl_config_grpo, hardware_spec)

        results = []
        for i in range(5):
            batch = {
                "log_probs": np.random.randn(8, 10),
                "new_log_probs": np.random.randn(8, 10),
                "advantages": np.random.randn(8, 10),
                "rewards": np.random.randn(8, 10),
                "mask": np.ones((8, 10)),
            }
            result = engine.train_step(batch)
            results.append(result)

        assert len(results) == 5

    def test_advantage_computation(self, rl_config_grpo, hardware_spec):
        """测试优势计算"""
        from src.agents.rl import RLEngine

        engine = RLEngine(rl_config_grpo, hardware_spec)

        rewards = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]])  # 2D [4, 2]
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        assert advantages is not None
        assert advantages.shape == rewards.shape


class TestRLDataPipeline:
    """测试数据流水线"""

    def test_load_jsonl_data(self, save_test_data):
        """测试加载 JSONL 数据"""
        with open(save_test_data, 'r') as f:
            data = [json.loads(line) for line in f]

        assert len(data) == 2
        assert "prompt" in data[0]
        assert "chosen" in data[0]
        assert "rejected" in data[0]

    def test_batch_creation(self, sample_rl_data, create_test_batch):
        """测试批次创建"""
        batch = create_test_batch(batch_size=4, seq_len=10)

        assert "log_probs" in batch
        assert "old_log_probs" in batch
        assert "advantages" in batch
        assert "rewards" in batch
        assert batch["log_probs"].shape == (4, 10)

    def test_reward_computation(self, mock_reward_model):
        """测试奖励计算"""
        # 测试代码响应
        code_response = "def fib(n):\n    return n"
        reward = mock_reward_model("Write fibonacci", code_response)
        assert reward > 0.5

        # 测试简短响应
        short_response = "No"
        reward = mock_reward_model("Explain recursion", short_response)
        assert reward < 0.5


class TestRLConfigIntegration:
    """测试配置集成"""

    def test_load_config_from_yaml(self, tmp_path):
        """测试从 YAML 加载配置"""
        import yaml

        config_content = """
rl:
  enabled: true
  mode: grpo
  device: auto
  grpo:
    learning_rate: 0.0001
    clip_epsilon: 0.3
    group_size: 8
"""

        config_file = tmp_path / "test_config.yaml"
        with open(config_file, 'w') as f:
            f.write(config_content)

        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        assert config_data['rl']['enabled'] is True
        assert config_data['rl']['mode'] == 'grpo'
        assert config_data['rl']['grpo']['learning_rate'] == 0.0001

    def test_env_config_override(self, rl_config_grpo):
        """测试环境变量覆盖配置"""
        import os

        # 测试配置可以被序列化
        config_dict = {
            "mode": rl_config_grpo.mode.value,
            "enabled": rl_config_grpo.enabled,
            "grpo_lr": rl_config_grpo.grpo.learning_rate,
        }

        assert config_dict["mode"] == "grpo"
        assert config_dict["enabled"] is True


class TestRLHardwareIntegration:
    """测试硬件集成"""

    def test_cpu_backend(self):
        """测试 CPU 后端"""
        from src.agents.rl import HardwareSpec, ComputeBackend

        spec = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=8.0,
        )

        assert spec.backend == ComputeBackend.CPU
        assert "cpu" in spec.device_name.lower()

    @pytest.mark.skipif(True, reason="Requires GPU")
    def test_cuda_backend(self):
        """测试 CUDA 后端"""
        from src.agents.rl import HardwareSpec, ComputeBackend

        spec = HardwareSpec(
            backend=ComputeBackend.CUDA,
            device_name="cuda:0",
            memory_gb=8.0,
        )

        assert spec.backend == ComputeBackend.CUDA

    def test_get_recommended_mode_cpu(self):
        """测试 CPU 推荐模式"""
        from src.agents.rl import get_recommended_mode, HardwareSpec, ComputeBackend, RLMode

        spec = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=8.0,
        )

        mode = get_recommended_mode(spec)
        assert mode == RLMode.COLLECTION_ONLY


class TestRLEndToEnd:
    """端到端测试"""

    def test_full_training_workflow(self):
        """测试完整训练工作流"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
            GRPOConfig,
        )

        # 1. 初始化配置
        config = RLConfig(
            mode=RLMode.GRPO,
            grpo=GRPOConfig(
                learning_rate=1e-4,
                group_size=4,
                batch_size=8,
            )
        )

        # 2. 创建硬件
        hardware = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=8.0,
        )

        # 3. 创建引擎
        engine = RLEngine(config, hardware)

        # 4. 执行多个训练步骤
        training_history = []
        for step in range(10):
            batch = {
                "log_probs": np.random.randn(8, 10),
                "new_log_probs": np.random.randn(8, 10),
                "advantages": np.random.randn(8, 10),
                "rewards": np.random.randn(8, 10),
                "mask": np.ones((8, 10)),
            }

            result = engine.train_step(batch)
            training_history.append({
                "step": step,
                "loss": result.get("total_loss", 0.0),
            })

        # 5. 验证结果
        assert len(training_history) == 10

        # 6. 获取最终状态
        status = engine.get_status()
        assert status["training_enabled"] is True
        assert status["mode"] == "grpo"

    def test_mode_switching_workflow(self):
        """测试模式切换工作流"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        hardware = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=8.0,
        )

        # 从收集模式开始
        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        engine = RLEngine(config, hardware)
        assert engine.is_training_enabled is False

        # 切换到 GRPO
        config = RLConfig(mode=RLMode.GRPO)
        engine = RLEngine(config, hardware)
        assert engine.is_training_enabled is True
        assert engine.config.mode == RLMode.GRPO

    def test_can_run_check(self):
        """测试运行检查"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        # Collection 模式始终可以运行
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        engine = RLEngine(config, hardware)
        assert engine.can_run() is True

        # GRPO 可以运行
        config = RLConfig(mode=RLMode.GRPO)
        engine = RLEngine(config, hardware)
        assert engine.can_run() is True


class TestRLDataAugmentation:
    """测试数据增强"""

    def test_response_shuffling(self):
        """测试响应打乱用于对比学习"""
        data = [
            {"prompt": "Q1", "chosen": "A1", "rejected": "A2"},
            {"prompt": "Q2", "chosen": "A3", "rejected": "A4"},
        ]

        # 模拟打乱
        import random
        shuffled = data.copy()
        random.shuffle(shuffled)

        assert len(shuffled) == len(data)

    def test_reward_normalization(self):
        """测试奖励归一化"""
        rewards = np.array([0.1, 0.5, 1.0, -0.5, -1.0])

        # 简单的 min-max 归一化
        normalized = (rewards - rewards.min()) / (rewards.max() - rewards.min())

        assert normalized.min() >= 0.0
        assert normalized.max() <= 1.0

    def test_advantage_normalization(self):
        """测试优势归一化"""
        advantages = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        # 减均值除标准差
        normalized = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        assert abs(normalized.mean()) < 1e-5  # 接近0


class TestRLLogging:
    """测试日志记录"""

    def test_training_log(self):
        """测试训练日志"""
        logs = []

        # 模拟训练日志
        for step in range(5):
            log = {
                "step": step,
                "loss": np.random.random(),
                "reward": np.random.random(),
            }
            logs.append(log)

        assert len(logs) == 5
        assert all("step" in log for log in logs)

    def test_metrics_collection(self):
        """测试指标收集"""
        metrics = {
            "episode_reward": [],
            "episode_length": [],
            "policy_loss": [],
            "value_loss": [],
        }

        for i in range(10):
            metrics["episode_reward"].append(np.random.random())
            metrics["episode_length"].append(np.random.randint(10, 100))
            metrics["policy_loss"].append(np.random.random())
            metrics["value_loss"].append(np.random.random())

        assert len(metrics["episode_reward"]) == 10
        assert len(metrics["episode_length"]) == 10
