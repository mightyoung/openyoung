"""
RL Module - 强化学习模块

支持多后端硬件抽象和多种 RL 算法
"""

from .config import (
    CollectionConfig,
    GiGPOConfig,
    GRPOConfig,
    HardwareConfig,
    RewardConfig,
    RLConfig,
    RLMode,
    load_config,
)
from .engine import (
    RLEngine,
    create_rl_engine,
    get_recommended_mode,
)
from .gigpo_engine import (
    GiGPOEngine,
    create_gigpo_engine,
)
from .grpo_engine import (
    GRPOEngine,
    create_grpo_engine,
)
from .hardware import (
    ComputeBackend,
    DeviceManager,
    HardwareDetector,
    HardwareSpec,
    create_hardware_spec,
    get_backend_from_env,
)

__all__ = [
    # Config
    "RLConfig",
    "RLMode",
    "GRPOConfig",
    "GiGPOConfig",
    "HardwareConfig",
    "CollectionConfig",
    "RewardConfig",
    "load_config",
    # Hardware
    "ComputeBackend",
    "HardwareSpec",
    "HardwareDetector",
    "DeviceManager",
    "get_backend_from_env",
    "create_hardware_spec",
    # Engines
    "GRPOEngine",
    "create_grpo_engine",
    "GiGPOEngine",
    "create_gigpo_engine",
    # Main
    "RLEngine",
    "create_rl_engine",
    "get_recommended_mode",
]
