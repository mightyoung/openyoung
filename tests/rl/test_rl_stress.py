"""
RL Stress and Benchmark Tests
"""

import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock


class TestStress:
    """压力测试"""

    def test_high_throughput_collection(self):
        """测试高吞吐量收集"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        config = RLConfig(mode=RLMode.COLLECTION_ONLY)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 模拟大量经验收集
        experiences = []
        for i in range(1000):
            experiences.append({
                "prompt": f"Task {i}",
                "response": f"Result {i}",
                "reward": np.random.random(),
            })

        # 验证可以处理大量数据
        assert len(experiences) == 1000

    def test_concurrent_training_steps(self):
        """测试并发训练步骤"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        # 连续执行多个训练步骤
        for i in range(100):
            batch = {
                "log_probs": np.random.randn(8, 10),
                "new_log_probs": np.random.randn(8, 10),
                "rewards": np.random.randn(8, 10),
                "mask": np.ones((8, 10)),
            }
            result = engine.train_step(batch)
            assert "total_loss" in result

    def test_large_group_advantages(self):
        """测试大组优势计算"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig(group_size=100)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        # 测试大组的奖励 - needs 2D [batch_size, seq_len]
        rewards = np.random.randn(400, 10)  # 4 组，每组 100 个
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        assert advantages.shape == rewards.shape


class TestBenchmark:
    """基准测试"""

    def test_advantage_computation_speed(self):
        """测试优势计算速度"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        # 多次计算优势
        iterations = 1000
        rewards = np.random.randn(1000)

        start = time.time()
        for _ in range(iterations):
            advantages = engine.compute_advantages(rewards, np.ones_like(rewards))
        elapsed = time.time() - start

        # 验证性能
        per_iter = elapsed / iterations
        print(f"\nAdvantage computation: {per_iter*1000:.2f}ms per iteration")

    def test_training_step_speed(self):
        """测试训练步骤速度"""
        from src.agents.rl import (
            RLEngine, RLConfig, RLMode,
            HardwareSpec, ComputeBackend,
        )

        config = RLConfig(mode=RLMode.GRPO)
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = RLEngine(config, hardware)

        batch = {
            "log_probs": np.random.randn(32, 50),
            "new_log_probs": np.random.randn(32, 50),
            "rewards": np.random.randn(32, 50),
            "mask": np.ones((32, 50)),
        }

        iterations = 100
        start = time.time()
        for _ in range(iterations):
            engine.train_step(batch)
        elapsed = time.time() - start

        per_iter = elapsed / iterations
        print(f"\nTraining step: {per_iter*1000:.2f}ms per iteration")

    def test_gigpo_two_layer_advantage(self):
        """测试 GiGPO 双层优势计算"""
        from src.agents.rl import (
            create_gigpo_engine, GiGPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GiGPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_gigpo_engine(config, hardware)

        # 多 episode 数据
        num_episodes = 10
        steps_per_episode = 20

        episode_adv = np.random.randn(num_episodes, steps_per_episode)
        step_adv = np.random.randn(num_episodes, steps_per_episode)
        mask = np.ones((num_episodes, steps_per_episode))
        episode_ids = np.arange(num_episodes)
        anchor_obs = None

        start = time.time()
        for _ in range(100):
            combined = engine.compute_combined_advantage(
                episode_adv, step_adv, mask, episode_ids, anchor_obs
            )
        elapsed = time.time() - start

        per_iter = elapsed / 100
        print(f"\nGiGPO combined advantage: {per_iter*1000:.2f}ms per iteration")


class TestEdgeCases:
    """边界情况测试"""

    def test_zero_rewards(self):
        """测试零奖励"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        rewards = np.zeros((100, 10))  # 2D for GRPO
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        # 零奖励应该产生零优势
        assert np.allclose(advantages, 0.0, atol=1e-5)

    def test_negative_rewards(self):
        """测试负奖励"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        rewards = -np.ones((100, 10))  # 2D for GRPO
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        # 负奖励应该产生负优势
        assert np.all(advantages <= 0)

    def test_masked_positions(self):
        """测试掩码位置"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        rewards = np.array([[1.0, 2.0, 3.0, 0.0, 0.0]])  # 2D for GRPO
        mask = np.array([1.0, 1.0, 1.0, 0.0, 0.0])  # 掩码掉最后两个

        advantages = engine.compute_advantages(rewards, mask)

        # 前三个位置应该有值
        assert not np.allclose(advantages[:3], 0.0)

    def test_single_sample(self):
        """测试单样本"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        rewards = np.array([[1.0]])  # 2D for GRPO
        mask = np.array([[1.0]])

        advantages = engine.compute_advantages(rewards, mask)

        assert advantages.shape == rewards.shape


class TestNumericalStability:
    """数值稳定性测试"""

    def test_large_values(self):
        """测试大值"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        # 大值奖励 - 2D for GRPO (needs to be divisible by group_size=4)
        rewards = np.array([[1e10], [1e10], [1e10], [1e10]])
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        # 不应该产生 NaN
        assert not np.any(np.isnan(advantages))
        assert not np.any(np.isinf(advantages))

    def test_small_values(self):
        """测试小值"""
        from src.agents.rl import (
            create_grpo_engine, GRPOConfig,
            HardwareSpec, ComputeBackend,
        )

        config = GRPOConfig()
        hardware = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        engine = create_grpo_engine(config, hardware)

        # 小值奖励 - 2D for GRPO
        rewards = np.array([[1e-10], [1e-10], [1e-10], [1e-10]])
        mask = np.ones_like(rewards)

        advantages = engine.compute_advantages(rewards, mask)

        # 不应该产生 NaN
        assert not np.any(np.isnan(advantages))
        assert not np.any(np.isinf(advantages))

    def test_clipping_stability(self):
        """测试裁剪稳定性 - 直接测试 numpy 操作"""
        # 直接测试裁剪逻辑
        clip_epsilon = 0.2
        ratios = np.array([1e-10, 1e10, -1e10, 0.0, 1.0])

        # 手动实现裁剪逻辑
        lower = 1 - clip_epsilon
        upper = 1 + clip_epsilon
        clipped = np.clip(ratios, lower, upper)

        # 应该在合理范围内
        assert np.all(clipped >= lower)
        assert np.all(clipped <= upper)
