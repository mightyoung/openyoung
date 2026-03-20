"""
RL Configuration - 强化学习配置

统一配置管理，支持 YAML 和环境变量
"""

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RLMode(Enum):
    """RL 运行模式"""

    COLLECTION_ONLY = "collection_only"  # 仅收集经验
    GRPO = "grpo"  # 轻量 GRPO
    GIGPO = "gigpo"  # 完整 GiGPO


@dataclass
class HardwareConfig:
    """硬件配置"""

    auto_detect: bool = True

    # NVIDIA
    nvidia_enabled: bool = True
    cuda_devices: list = field(default_factory=lambda: [0])

    # Apple Silicon
    apple_silicon_enabled: bool = True
    use_mps: bool = True

    # ARM (RK3588)
    rockchip_enabled: bool = False


@dataclass
class GRPOConfig:
    """GRPO 配置"""

    learning_rate: float = 1e-5
    clip_epsilon: float = 0.2
    kl_beta: float = 0.01
    group_size: int = 4
    batch_size: int = 8
    max_steps: int = 100


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


@dataclass
class CollectionConfig:
    """经验收集配置"""

    buffer_size: int = 10000
    min_samples_for_training: int = 100
    embedding_batch_size: int = 100


@dataclass
class RewardConfig:
    """奖励配置"""

    task_completion_positive: float = 1.0
    task_completion_negative: float = -0.5
    evaluation_weight: float = 0.3
    efficiency_weight: float = 0.2
    error_penalty: float = -0.1


@dataclass
class RLConfig:
    """
    RL 统一配置

    支持从环境变量和 YAML 加载
    """

    # 基础配置
    enabled: bool = True
    mode: RLMode = RLMode.COLLECTION_ONLY
    device: str = "auto"  # auto/nvidia/metal/cpu

    # 子配置
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    grpo: GRPOConfig = field(default_factory=GRPOConfig)
    gigpo: GiGPOConfig = field(default_factory=GiGPOConfig)
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)

    @classmethod
    def from_env(cls) -> "RLConfig":
        """从环境变量加载配置"""
        config = cls()

        # 基础配置
        config.enabled = os.environ.get("RL_ENABLED", "true").lower() == "true"

        mode_str = os.environ.get("RL_MODE", "collection_only").lower()
        config.mode = (
            RLMode(mode_str) if mode_str in [m.value for m in RLMode] else RLMode.COLLECTION_ONLY
        )

        config.device = os.environ.get("RL_DEVICE", "auto")

        # GRPO 配置
        config.grpo.learning_rate = float(os.environ.get("RL_GRPO_LR", "1e-5"))
        config.grpo.clip_epsilon = float(os.environ.get("RL_GRPO_CLIP", "0.2"))
        config.grpo.kl_beta = float(os.environ.get("RL_GRPO_KL", "0.01"))
        config.grpo.group_size = int(os.environ.get("RL_GRPO_GROUP", "4"))

        # 经验收集配置
        config.collection.buffer_size = int(os.environ.get("RL_BUFFER_SIZE", "10000"))
        config.collection.min_samples_for_training = int(os.environ.get("RL_MIN_SAMPLES", "100"))

        logger.info(f"RL config loaded: mode={config.mode.value}, device={config.device}")

        return config

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "enabled": self.enabled,
            "mode": self.mode.value,
            "device": self.device,
            "grpo": {
                "learning_rate": self.grpo.learning_rate,
                "clip_epsilon": self.grpo.clip_epsilon,
                "kl_beta": self.grpo.kl_beta,
                "group_size": self.grpo.group_size,
            },
            "gigpo": {
                "episode_advantage_weight": self.gigpo.episode_advantage_weight,
                "step_advantage_weight": self.gigpo.step_advantage_weight,
                "use_gae": self.gigpo.use_gae,
            },
            "collection": {
                "buffer_size": self.collection.buffer_size,
                "min_samples_for_training": self.collection.min_samples_for_training,
            },
        }


def load_config(config_path: Optional[str] = None) -> RLConfig:
    """加载配置"""
    # 优先从环境变量加载
    config = RLConfig.from_env()

    # TODO: 支持从 YAML 文件加载

    return config
