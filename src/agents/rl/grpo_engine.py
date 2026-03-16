"""
GRPO Engine - GRPO 强化学习引擎

基于 DeepSeek-R1 的 Group Relative Policy Optimization
特点: 无需价值函数，内存效率高，适合 M1/MPS 或中等 GPU
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from .hardware import ComputeBackend, DeviceManager, HardwareSpec

logger = logging.getLogger(__name__)

# 尝试导入 torch
try:
    import torch
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GRPO engine will run in mock mode")


@dataclass
class GRPOConfig:
    """GRPO 配置"""

    learning_rate: float = 1e-5
    clip_epsilon: float = 0.2
    kl_beta: float = 0.01  # KL 散度系数
    group_size: int = 4  # 每组采样数
    batch_size: int = 8
    max_steps: int = 100
    max_grad_norm: float = 1.0


class GRPOEngine:
    """
    GRPO (Group Relative Policy Optimization) 引擎

    核心算法:
    1. 对每个 prompt，采样 group_size 个响应
    2. 计算组内相对排名 advantage
    3. 使用 PPO-style 裁剪更新策略

    优点:
    - 无需价值函数，内存效率高
    - 适合 M1/MPS 或中等 GPU
    - 基于 DeepSeek-R1 方法
    """

    def __init__(
        self,
        config: GRPOConfig,
        hardware: HardwareSpec,
    ):
        self.config = config
        self.hardware = hardware
        self.device_mgr = DeviceManager(hardware)

        # 根据硬件配置优化
        self._configure_for_hardware()

        logger.info(f"GRPOEngine initialized with {hardware.backend.value}")

    def _configure_for_hardware(self):
        """根据硬件配置进行优化"""
        if not TORCH_AVAILABLE:
            return

        if self.hardware.backend == ComputeBackend.MPS:
            # Apple Silicon 优化
            # MPS 不完全支持混合精度
            self.use_mixed_precision = False
            logger.info("MPS: mixed precision disabled")

        elif self.hardware.backend == ComputeBackend.CUDA:
            # NVIDIA GPU 优化
            torch.backends.cudnn.benchmark = True
            self.use_mixed_precision = True
            logger.info("CUDA: mixed precision enabled")

        else:
            self.use_mixed_precision = False

    def compute_advantages(
        self,
        rewards,
        response_mask,
    ) -> "torch.Tensor":
        """
        计算组相对优势

        核心算法:
        1. 对每个 prompt，将 responses 分组
        2. 计算组内均值
        3. 优势 = 回报 - 组均值

        Args:
            rewards: 奖励张量, shape [batch_size, seq_len]
            response_mask: 响应掩码, shape [batch_size, seq_len]

        Returns:
            advantages: 优势张量, shape [batch_size, seq_len]
        """
        if not TORCH_AVAILABLE:
            return torch.zeros_like(torch.tensor(rewards))

        # Convert numpy arrays to torch tensors
        if isinstance(rewards, np.ndarray):
            rewards = torch.from_numpy(rewards)
        if isinstance(response_mask, np.ndarray):
            response_mask = torch.from_numpy(response_mask)

        # 计算每个序列的总回报
        returns = (rewards * response_mask).sum(dim=-1)  # [batch_size]

        # 重新整形为 [num_groups, group_size]
        batch_size = returns.shape[0]
        assert batch_size % self.config.group_size == 0, (
            f"Batch size {batch_size} must be divisible by group size {self.config.group_size}"
        )

        num_groups = batch_size // self.config.group_size

        # Reshape
        returns = returns.view(num_groups, self.config.group_size)

        # 组均值归一化 (核心算法)
        group_mean = returns.mean(dim=1, keepdim=True)  # [num_groups, 1]
        advantages = returns - group_mean  # [num_groups, group_size]

        # 扩展回原始形状
        advantages = advantages.view(-1, 1).expand(-1, rewards.shape[1])  # [batch_size, seq_len]

        # 应用掩码
        advantages = advantages * response_mask

        return advantages

    def update_policy(
        self,
        log_probs: "torch.Tensor",  # 旧策略 log π(a|s)
        new_log_probs: "torch.Tensor",  # 新策略 log π'(a|s)
        advantages: "torch.Tensor",
        mask: "torch.Tensor",
    ) -> Dict[str, float]:
        """
        PPO-style 策略更新

        裁剪目标:
        L^CLIP(θ) = E[ min(r(θ) * A, clip(r(θ), 1-ε, 1+ε) * A) ]

        其中 r(θ) = exp(log_π'(a|s) - log_π(a|s))

        Args:
            log_probs: 旧策略 log 概率
            new_log_probs: 新策略 log 概率
            advantages: 优势
            mask: 掩码

        Returns:
            loss_dict: 损失字典
        """
        if not TORCH_AVAILABLE:
            return {"policy_loss": 0.0, "kl_loss": 0.0, "total_loss": 0.0}

        # 重要性采样比率
        ratio = torch.exp(new_log_probs - log_probs)  # r(θ)

        # 裁剪
        clipped_ratio = torch.clamp(
            ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon
        )

        # 目标函数 (注意: advantage 可能为负)
        # 使用 original ratio 的符号来保持一致性
        policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages)
        policy_loss = (policy_loss * mask).sum() / mask.sum()

        # KL 散度惩罚 (简化版本)
        # KL = π_old * (log(π_old) - log(π_new))
        kl = (torch.exp(log_probs) * (log_probs - new_log_probs)).sum(dim=-1)
        kl_loss = kl.mean() * self.config.kl_beta

        # 总损失
        total_loss = policy_loss + kl_loss

        return {
            "policy_loss": policy_loss.item(),
            "kl_loss": kl_loss.item(),
            "total_loss": total_loss.item(),
        }

    def compute_kl(
        self,
        log_probs: "torch.Tensor",
        new_log_probs: "torch.Tensor",
    ) -> "torch.Tensor":
        """计算 KL 散度"""
        if not TORCH_AVAILABLE:
            return torch.tensor(0.0)

        # 近似 KL
        kl = (torch.exp(log_probs) * (log_probs - new_log_probs)).sum(dim=-1)
        return kl.mean()

    def train_step(
        self,
        batch: Dict[str, "torch.Tensor"],
    ) -> Dict[str, float]:
        """
        单步训练

        Args:
            batch: 包含以下键的字典:
                - rewards: 奖励 [batch_size, seq_len]
                - log_probs: 旧策略 log 概率 [batch_size, seq_len]
                - new_log_probs: 新策略 log 概率 [batch_size, seq_len]
                - mask: 掩码 [batch_size, seq_len]

        Returns:
            loss_dict: 损失字典
        """
        if not TORCH_AVAILABLE:
            return {"total_loss": 0.0}

        # 移动到设备
        rewards = self.device_mgr.to_device(batch["rewards"])
        log_probs = self.device_mgr.to_device(batch["log_probs"])
        new_log_probs = self.device_mgr.to_device(batch["new_log_probs"])
        mask = self.device_mgr.to_device(batch["mask"])

        # 计算优势
        advantages = self.compute_advantages(rewards, mask)

        # 归一化优势
        advantages = advantages / (advantages.std() + 1e-8)

        # 更新策略
        losses = self.update_policy(log_probs, new_log_probs, advantages, mask)

        return losses


class MockGRPOEngine:
    """Mock GRPO 引擎 (用于无 PyTorch 环境)"""

    def __init__(self, config: GRPOConfig, hardware: HardwareSpec):
        self.config = config
        self.hardware = hardware
        logger.warning("Running in mock mode (PyTorch not available)")

    def compute_advantages(self, rewards, response_mask):
        return rewards

    def update_policy(self, log_probs, new_log_probs, advantages, mask):
        return {"policy_loss": 0.0, "kl_loss": 0.0, "total_loss": 0.0}

    def train_step(self, batch):
        return {"total_loss": 0.0}


def create_grpo_engine(
    config: GRPOConfig,
    hardware: HardwareSpec,
) -> GRPOEngine:
    """GRPO 引擎工厂函数"""
    if TORCH_AVAILABLE:
        return GRPOEngine(config, hardware)
    else:
        return MockGRPOEngine(config, hardware)
