"""
GiGPO Engine - GiGPO 强化学习引擎

基于 OpenManus-RL 的 Group-in-Group Policy Optimization
特点: 两层优势估计 (episode-level + step-level)，细粒度信用分配
"""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .hardware import ComputeBackend, DeviceManager, HardwareSpec

logger = logging.getLogger(__name__)

# 尝试导入 torch
try:
    import torch
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GiGPO engine will run in mock mode")


@dataclass
class GiGPOConfig:
    """GiGPO 配置"""

    episode_advantage_weight: float = 1.0
    step_advantage_weight: float = 0.5
    use_gae: bool = True
    gae_lambda: float = 0.95
    gamma: float = 0.99
    clip_epsilon: float = 0.2
    learning_rate: float = 1e-5
    kl_beta: float = 0.01


def to_hashable(x):
    """转换为可哈希类型"""
    if isinstance(x, (int, float, str, bool)):
        return x
    elif isinstance(x, (int, float)):
        return x.item() if hasattr(x, "item") else x
    elif isinstance(x, torch.Tensor):
        return x.item() if x.numel() == 1 else tuple(x.flatten().tolist())
    elif isinstance(x, (list, tuple)):
        return tuple(to_hashable(e) for e in x)
    elif isinstance(x, dict):
        return tuple(sorted((k, to_hashable(v)) for k, v in x.items()))
    else:
        return str(x)


class GiGPOEngine:
    """
    GiGPO (Group-in-Group Policy Optimization) 引擎

    核心创新 (来自 OpenManus-RL):
    1. Episode-level 优势: 任务级别的整体评估
    2. Step-level 优势: 步骤级别的细粒度评估
    3. 两层优势融合: A = A_episode + λ * A_step

    适用场景:
    - 需要细粒度信用分配的多步工具调用任务
    - 需要较强 GPU 的场景
    """

    def __init__(
        self,
        config: GiGPOConfig,
        hardware: HardwareSpec,
    ):
        self.config = config
        self.hardware = hardware
        self.device_mgr = DeviceManager(hardware)

        logger.info(f"GiGPOEngine initialized with {hardware.backend.value}")

    def train_step(self, batch: Dict[str, "torch.Tensor"]) -> Dict[str, float]:
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
        advantages = self.compute_combined_advantage(
            rewards,
            rewards.mean(dim=-1, keepdim=True).squeeze(-1),  # step_rewards
            mask,
            torch.arange(rewards.shape[0]),  # episode_ids
            [None] * rewards.shape[0],  # anchor_obs
        )

        # 归一化优势
        advantages = advantages / (advantages.std() + 1e-8)

        # 更新策略
        losses = self.update_policy(log_probs, new_log_probs, advantages, mask)

        return losses

    def build_step_group(
        self,
        anchor_obs: List[str],
        episode_ids: "torch.Tensor",
    ) -> "torch.Tensor":
        """
        构建步骤组

        对每个 episode，将相同的观察结果聚类
        相同观察 -> 同一组 -> 相同 advantage

        Args:
            anchor_obs: 观察列表
            episode_ids: Episode ID 列表

        Returns:
            step_group_uids: 步骤组 ID 列表
        """
        if not TORCH_AVAILABLE:
            return torch.zeros(len(anchor_obs))

        # 初始化结果数组
        step_group_uids = [None] * len(anchor_obs)

        # 获取唯一的 episode IDs
        unique_episodes = episode_ids.unique()

        for ep_id in unique_episodes:
            # 获取该 episode 的所有索引
            indices = (episode_ids == ep_id).nonzero(as_tuple=True)[0]
            obs_group = [anchor_obs[i] for i in indices]

            # 按观察结果聚类
            clusters = defaultdict(list)
            for i, obs in enumerate(obs_group):
                clusters[to_hashable(obs)].append(i)

            # 为每个聚类分配唯一的 step_group_uid
            for obs_hash, original_indices in clusters.items():
                uid = str(uuid.uuid4())
                for orig_idx in original_indices:
                    step_group_uids[indices[orig_idx].item()] = uid

        # 转换为 tensor
        result = torch.zeros(len(anchor_obs), dtype=torch.long)
        for i, uid in enumerate(step_group_uids):
            if uid:
                # 使用简单哈希作为 ID
                result[i] = hash(uid) % 1000000

        return result

    def compute_episode_advantage(
        self,
        token_rewards: "torch.Tensor",
        response_mask: "torch.Tensor",
        episode_ids: "torch.Tensor",
    ) -> "torch.Tensor":
        """
        Episode-level 优势估计

        对每个 episode，计算组内相对排名

        Args:
            token_rewards: token 级别奖励 [batch_size, seq_len]
            response_mask: 响应掩码 [batch_size, seq_len]
            episode_ids: Episode ID [batch_size]

        Returns:
            episode_advantages: Episode 级别优势 [batch_size, seq_len]
        """
        if not TORCH_AVAILABLE:
            return torch.zeros_like(token_rewards)

        # 计算每个序列的总回报
        returns = (token_rewards * response_mask).sum(dim=-1)  # [batch_size]

        # 按 episode 分组
        id2scores = defaultdict(list)
        for i, ep_id in enumerate(episode_ids):
            id2scores[ep_id.item()].append(returns[i])

        # 计算组内均值
        id2mean = {}
        for ep_id, scores in id2scores.items():
            if len(scores) > 1:
                id2mean[ep_id] = torch.stack(scores).mean()
            else:
                id2mean[ep_id] = torch.tensor(0.0)

        # 计算优势
        advantages = torch.zeros_like(returns)
        for i, ep_id in enumerate(episode_ids):
            advantages[i] = returns[i] - id2mean[ep_id.item()]

        # 扩展到序列长度
        seq_len = token_rewards.shape[1]
        advantages = advantages.unsqueeze(-1).expand(-1, seq_len) * response_mask

        return advantages

    def compute_step_advantage(
        self,
        step_rewards: "torch.Tensor",
        step_group_uids: "torch.Tensor",
    ) -> "torch.Tensor":
        """
        Step-level 优势估计

        对每个步骤组，计算组内相对排名

        Args:
            step_rewards: 步骤级别奖励 [batch_size]
            step_group_uids: 步骤组 ID [batch_size]

        Returns:
            step_advantages: Step 级别优势 [batch_size]
        """
        if not TORCH_AVAILABLE:
            return torch.zeros_like(step_rewards)

        # 按步骤组分组
        id2scores = defaultdict(list)
        for i, group_id in enumerate(step_group_uids):
            id2scores[group_id.item()].append(step_rewards[i])

        # 计算组内均值
        id2mean = {}
        for group_id, scores in id2scores.items():
            if len(scores) > 1:
                id2mean[group_id] = torch.stack(scores).mean()
            else:
                id2mean[group_id] = torch.tensor(0.0)

        # 计算优势
        advantages = torch.zeros_like(step_rewards)
        for i, group_id in enumerate(step_group_uids):
            advantages[i] = step_rewards[i] - id2mean[group_id.item()]

        return advantages

    def compute_gae(
        self,
        rewards: "torch.Tensor",
        values: "torch.Tensor",
        mask: "torch.Tensor",
    ) -> "torch.Tensor":
        """
        GAE (Generalized Advantage Estimation)

        Args:
            rewards: 奖励 [batch_size, seq_len]
            values: 价值 [batch_size, seq_len]
            mask: 掩码 [batch_size, seq_len]

        Returns:
            advantages: GAE 优势 [batch_size, seq_len]
        """
        if not TORCH_AVAILABLE:
            return torch.zeros_like(rewards)

        batch_size, seq_len = rewards.shape
        advantages = torch.zeros_like(rewards)

        gae = 0
        for t in reversed(range(seq_len - 1)):
            # TD 目标
            td_target = rewards[:, t] + self.config.gamma * values[:, t + 1] * mask[:, t + 1]
            # TD 误差
            td_error = td_target - values[:, t]
            # GAE 累积
            gae = td_error + self.config.gamma * self.config.gae_lambda * mask[:, t] * gae
            advantages[:, t] = gae

        # 最后一个位置
        advantages[:, -1] = rewards[:, -1] - values[:, -1]

        return advantages

    def compute_combined_advantage(
        self,
        token_rewards: "torch.Tensor",
        step_rewards: "torch.Tensor",
        response_mask: "torch.Tensor",
        episode_ids: "torch.Tensor",
        anchor_obs: List[str],
    ) -> "torch.Tensor":
        """
        两层优势融合

        A_combined = A_episode + λ * A_step

        Args:
            token_rewards: Token 级别奖励
            step_rewards: Step 级别奖励
            response_mask: 响应掩码
            episode_ids: Episode ID
            anchor_obs: 观察列表

        Returns:
            combined_advantages: 融合后的优势
        """
        if not TORCH_AVAILABLE:
            return torch.zeros_like(token_rewards)

        # Episode-level 优势
        episode_adv = self.compute_episode_advantage(token_rewards, response_mask, episode_ids)

        # Step-level 优势
        step_group_uids = self.build_step_group(anchor_obs, episode_ids)
        step_adv = self.compute_step_advantage(step_rewards, step_group_uids)

        # 扩展到序列长度
        seq_len = token_rewards.shape[1]
        step_adv_expanded = step_adv.unsqueeze(-1).expand(-1, seq_len) * response_mask

        # 融合
        combined = (
            self.config.episode_advantage_weight * episode_adv
            + self.config.step_advantage_weight * step_adv_expanded
        )

        return combined

    def update_policy(
        self,
        log_probs: "torch.Tensor",
        new_log_probs: "torch.Tensor",
        advantages: "torch.Tensor",
        mask: "torch.Tensor",
    ) -> Dict[str, float]:
        """
        策略更新 (与 GRPO 相同)

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
        ratio = torch.exp(new_log_probs - log_probs)

        # 裁剪
        clipped_ratio = torch.clamp(
            ratio, 1 - self.config.clip_epsilon, 1 + self.config.clip_epsilon
        )

        # 目标函数
        policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages)
        policy_loss = (policy_loss * mask).sum() / mask.sum()

        # KL 散度惩罚
        kl = (torch.exp(log_probs) * (log_probs - new_log_probs)).sum(dim=-1)
        kl_loss = kl.mean() * self.config.kl_beta

        total_loss = policy_loss + kl_loss

        return {
            "policy_loss": policy_loss.item(),
            "kl_loss": kl_loss.item(),
            "total_loss": total_loss.item(),
        }


class MockGiGPOEngine:
    """Mock GiGPO 引擎 (用于无 PyTorch 环境)"""

    def __init__(self, config: GiGPOConfig, hardware: HardwareSpec):
        self.config = config
        self.hardware = hardware
        logger.warning("Running in mock mode (PyTorch not available)")

    def compute_episode_advantage(self, rewards, mask, episode_ids):
        return rewards

    def compute_step_advantage(self, rewards, step_group_uids):
        return rewards

    def compute_combined_advantage(
        self, token_rewards, step_rewards, mask, episode_ids, anchor_obs
    ):
        return token_rewards

    def update_policy(self, log_probs, new_log_probs, advantages, mask):
        return {"policy_loss": 0.0, "kl_loss": 0.0, "total_loss": 0.0}

    def train_step(self, batch):
        """Mock 训练步骤"""
        return {"total_loss": 0.0, "policy_loss": 0.0, "kl_loss": 0.0}

    def compute_advantages(self, rewards, mask):
        """Mock 优势计算"""
        return rewards


def create_gigpo_engine(
    config: GiGPOConfig,
    hardware: HardwareSpec,
) -> GiGPOEngine:
    """GiGPO 引擎工厂函数"""
    if TORCH_AVAILABLE:
        return GiGPOEngine(config, hardware)
    else:
        return MockGiGPOEngine(config, hardware)
