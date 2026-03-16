"""
RL Engine - 强化学习引擎

统一入口，根据配置选择合适的 RL 模式
"""

import logging
from typing import Any, Dict, Optional

from .config import GiGPOConfig, GRPOConfig, RLConfig, RLMode
from .gigpo_engine import GiGPOEngine, create_gigpo_engine
from .grpo_engine import GRPOEngine, create_grpo_engine
from .hardware import ComputeBackend, HardwareDetector, HardwareSpec

logger = logging.getLogger(__name__)


class RLEngine:
    """
    RL 引擎主类

    根据配置自动选择合适的 RL 模式:
    - COLLECTION_ONLY: 仅收集经验 (无需 GPU)
    - GRPO: 轻量 GRPO (M1/中等 GPU)
    - GIGPO: 完整 GiGPO (需要 GPU)
    """

    def __init__(
        self,
        config: RLConfig,
        hardware: Optional[HardwareSpec] = None,
    ):
        self.config = config
        self.hardware = hardware or HardwareDetector.detect()

        logger.info(
            f"RLEngine initialized: mode={config.mode.value}, backend={self.hardware.backend.value}"
        )

        # 根据模式创建引擎
        self._engine = self._create_engine()

    def _create_engine(self):
        """根据配置创建引擎"""
        if self.config.mode == RLMode.COLLECTION_ONLY:
            logger.info("Using CollectionOnly mode (no training)")
            return None

        elif self.config.mode == RLMode.GRPO:
            logger.info("Creating GRPO engine")
            grpo_config = GRPOConfig(
                learning_rate=self.config.grpo.learning_rate,
                clip_epsilon=self.config.grpo.clip_epsilon,
                kl_beta=self.config.grpo.kl_beta,
                group_size=self.config.grpo.group_size,
                batch_size=self.config.grpo.batch_size,
            )
            return create_grpo_engine(grpo_config, self.hardware)

        elif self.config.mode == RLMode.GIGPO:
            logger.info("Creating GiGPO engine")
            gigpo_config = GiGPOConfig(
                episode_advantage_weight=self.config.gigpo.episode_advantage_weight,
                step_advantage_weight=self.config.gigpo.step_advantage_weight,
                use_gae=self.config.gigpo.use_gae,
                gae_lambda=self.config.gigpo.gae_lambda,
                gamma=self.config.gigpo.gamma,
            )
            return create_gigpo_engine(gigpo_config, self.hardware)

        else:
            raise ValueError(f"Unknown RL mode: {self.config.mode}")

    @property
    def is_training_enabled(self) -> bool:
        """是否启用训练"""
        return self.config.mode != RLMode.COLLECTION_ONLY

    @property
    def requires_gpu(self) -> bool:
        """是否需要 GPU"""
        return self.config.mode in (RLMode.GRPO, RLMode.GIGPO)

    def get_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "mode": self.config.mode.value,
            "backend": self.hardware.backend.value,
            "device_name": self.hardware.device_name,
            "memory_gb": self.hardware.memory_gb,
            "training_enabled": self.is_training_enabled,
            "requires_gpu": self.requires_gpu,
            "engine_type": type(self._engine).__name__ if self._engine else "None",
        }

    def can_run(self) -> bool:
        """
        检查是否可以在当前硬件上运行

        Returns:
            True: 可以运行
            False: 需要 GPU 但没有
        """
        if not self.is_training_enabled:
            return True

        if self.config.mode == RLMode.GRPO:
            # GRPO 可以在 CPU/MPS/CUDA 上运行
            return True

        elif self.config.mode == RLMode.GIGPO:
            # GiGPO 需要 CUDA
            return self.hardware.backend == ComputeBackend.CUDA

        return True

    def train_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """
        执行单步训练

        Args:
            batch: 训练批次

        Returns:
            loss_dict: 损失字典
        """
        if not self.is_training_enabled:
            return {"total_loss": 0.0}

        if self._engine is None:
            return {"total_loss": 0.0}

        return self._engine.train_step(batch)

    def compute_advantages(self, rewards, mask):
        """计算优势"""
        if self._engine is None:
            return rewards

        return self._engine.compute_advantages(rewards, mask)


def create_rl_engine(
    config: Optional[RLConfig] = None,
    hardware: Optional[HardwareSpec] = None,
) -> RLEngine:
    """
    RL 引擎工厂函数

    Args:
        config: RL 配置 (None 则从环境变量加载)
        hardware: 硬件规格 (None 则自动检测)

    Returns:
        RLEngine 实例
    """
    if config is None:
        from .config import load_config

        config = load_config()

    if hardware is None:
        hardware = HardwareDetector.detect()

    return RLEngine(config, hardware)


def get_recommended_mode(hardware: HardwareSpec) -> RLMode:
    """
    根据硬件推荐 RL 模式

    Args:
        hardware: 硬件规格

    Returns:
        推荐的 RL 模式
    """
    if hardware.backend == ComputeBackend.CUDA:
        # NVIDIA GPU: 可以运行完整的 GiGPO
        return RLMode.GIGPO

    elif hardware.backend == ComputeBackend.MPS:
        # Apple Silicon: 建议使用 GRPO
        return RLMode.GRPO

    else:
        # CPU: 只能收集经验
        return RLMode.COLLECTION_ONLY
