"""
Hardware Abstraction Layer - 硬件抽象层

支持多后端：CUDA (NVIDIA) / MPS (Apple Silicon) / CPU / Vulkan (ARM)
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from unittest.mock import MagicMock

import numpy as np

logger = logging.getLogger(__name__)


class ComputeBackend(Enum):
    """计算后端"""

    CUDA = "cuda"  # NVIDIA GPU (CUDA)
    MPS = "mps"  # Apple Silicon (Metal Performance Shaders)
    CPU = "cpu"  # CPU only
    VULKAN = "vulkan"  # ARM GPU (RK3588 等)


@dataclass
class HardwareSpec:
    """硬件规格"""

    backend: ComputeBackend
    device_name: str
    memory_gb: float
    compute_capability: Optional[str] = None  # CUDA capability, e.g., "8.0"
    device_count: int = 1


class HardwareDetector:
    """
    硬件检测器

    自动检测可用硬件并返回最佳计算后端
    """

    @staticmethod
    def detect() -> HardwareSpec:
        """
        自动检测可用硬件

        检测顺序: CUDA -> MPS -> Vulkan -> CPU
        """
        # 1. 检测 NVIDIA GPU (CUDA)
        try:
            import torch

            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                total_memory = torch.cuda.get_device_properties(0).total_memory
                compute_capability = f"{torch.cuda.get_device_capability(0)[0]}.{torch.cuda.get_device_capability(0)[1]}"

                logger.info(f"Detected CUDA: {device_name} x {device_count}")

                return HardwareSpec(
                    backend=ComputeBackend.CUDA,
                    device_name=device_name,
                    memory_gb=total_memory / (1024**3),
                    compute_capability=compute_capability,
                    device_count=device_count,
                )
        except ImportError:
            logger.debug("torch not available, skipping CUDA detection")

        # 2. 检测 Apple Silicon (MPS)
        try:
            import torch

            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                # 尝试获取内存信息 (MPS 不完全支持)
                memory_gb = HardwareDetector._get_apple_memory()

                logger.info("Detected Apple Silicon (MPS)")

                return HardwareSpec(
                    backend=ComputeBackend.MPS,
                    device_name="Apple Silicon",
                    memory_gb=memory_gb,
                    device_count=1,
                )
        except ImportError:
            logger.debug("torch not available, skipping CUDA detection")

        # 3. 检测 Vulkan (ARM GPU)
        # 注意: 需要 vulkan-py 或通过环境变量检测
        if os.environ.get("RL_ENABLE_VULKAN", "false").lower() == "true":
            logger.info("Vulkan backend enabled via config")
            return HardwareSpec(
                backend=ComputeBackend.VULKAN,
                device_name="Vulkan Device",
                memory_gb=8.0,  # 估算
                device_count=1,
            )

        # 4. Fallback to CPU
        logger.info("Using CPU backend")

        # 尝试获取系统内存
        memory_gb = HardwareDetector._get_system_memory()

        return HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="CPU",
            memory_gb=memory_gb,
            device_count=1,
        )

    @staticmethod
    def _get_apple_memory() -> float:
        """获取 Apple 设备内存"""
        try:
            import subprocess

            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return int(result.stdout.strip()) / (1024**3)
        except Exception as e:
            logger.warning(f"Failed to get Apple memory: {e}")
        return 16.0  # 默认估算

    @staticmethod
    def _get_system_memory() -> float:
        """获取系统内存"""
        try:
            import subprocess

            if os.uname().sysname == "Darwin":
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return int(result.stdout.strip()) / (1024**3)
            elif os.uname().sysname == "Linux":
                # 读取 /proc/meminfo
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            return int(line.split()[1]) / (1024**2)
        except Exception as e:
            logger.warning(f"Failed to get system memory: {e}")
        return 8.0  # 默认估算


class DeviceManager:
    """
    设备管理器

    负责张量设备迁移和内存管理
    """

    def __init__(self, spec: HardwareSpec):
        self.spec = spec
        self.device = self._init_device()
        self._configure()

    def _init_device(self):
        """初始化设备"""
        try:
            import torch
        except ImportError:
            # 没有 torch 时返回 CPU 设备对象
            logger.warning("PyTorch not available, using mock device")
            return MagicMock()

        try:
            if self.spec.backend == ComputeBackend.CUDA:
                return torch.device("cuda")
            elif self.spec.backend == ComputeBackend.MPS:
                return torch.device("mps")
            elif self.spec.backend == ComputeBackend.VULKAN:
                # Vulkan 支持需要额外配置
                logger.warning("Vulkan backend not fully implemented, falling back to CPU")
                return torch.device("cpu")
            else:
                return torch.device("cpu")
        except Exception as e:
            logger.warning(f"Failed to initialize device: {e}, using mock device")
            return MagicMock()

    def _configure(self):
        """根据硬件配置进行优化"""
        try:
            import torch
        except ImportError:
            logger.warning("PyTorch not available, skipping device configuration")
            return

        if self.spec.backend == ComputeBackend.CUDA:
            # NVIDIA GPU 优化
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.enabled = True
            logger.info("CUDA optimizations enabled")

        elif self.spec.backend == ComputeBackend.MPS:
            # Apple Silicon 优化
            # 注意: MPS 有一些限制
            logger.info("MPS backend configured (limitations apply)")

        elif self.spec.backend == ComputeBackend.CPU:
            # CPU 优化
            torch.set_num_threads(os.cpu_count() or 4)
            logger.info(f"CPU configured with {os.cpu_count() or 4} threads")

    def to_device(self, tensor) -> "torch.Tensor":
        """将张量移动到设备"""
        import torch

        # Handle numpy arrays
        if isinstance(tensor, np.ndarray):
            tensor = torch.from_numpy(tensor)
        return tensor.to(self.device)

    def allocate(self, shape, dtype=None) -> "torch.Tensor":
        """在设备上分配张量"""
        import torch

        if dtype is None:
            dtype = torch.float32
        return torch.empty(shape, device=self.device, dtype=dtype)

    def empty_cache(self):
        """清空缓存 (仅 CUDA)"""
        if self.spec.backend == ComputeBackend.CUDA:
            import torch

            torch.cuda.empty_cache()

    @property
    def supports_fp16(self) -> bool:
        """是否支持半精度"""
        return self.spec.backend in (ComputeBackend.CUDA, ComputeBackend.MPS)

    @property
    def supports_bf16(self) -> bool:
        """是否支持 bfloat16"""
        # MPS 暂不支持 bf16
        return self.spec.backend == ComputeBackend.CUDA


def get_backend_from_env() -> ComputeBackend:
    """从环境变量获取后端"""
    device = os.environ.get("RL_DEVICE", "auto").lower()

    if device == "auto":
        return None  # 使用自动检测

    mapping = {
        "cuda": ComputeBackend.CUDA,
        "nvidia": ComputeBackend.CUDA,
        "mps": ComputeBackend.MPS,
        "metal": ComputeBackend.MPS,
        "apple": ComputeBackend.MPS,
        "cpu": ComputeBackend.CPU,
        "vulkan": ComputeBackend.VULKAN,
        "arm": ComputeBackend.VULKAN,
    }

    return mapping.get(device, ComputeBackend.CPU)


def create_hardware_spec(backend: Optional[str] = None) -> HardwareSpec:
    """创建硬件规格 (用于测试或强制指定)"""
    if backend:
        env_backend = get_backend_from_env()
        if env_backend:
            backend = env_backend

    if backend:
        # 强制使用指定后端
        mapping = {
            "cuda": ComputeBackend.CUDA,
            "mps": ComputeBackend.MPS,
            "cpu": ComputeBackend.CPU,
            "vulkan": ComputeBackend.VULKAN,
        }
        spec_backend = mapping.get(backend, ComputeBackend.CPU)

        return HardwareSpec(
            backend=spec_backend,
            device_name=f"Force: {backend}",
            memory_gb=16.0,  # 估算
        )

    # 自动检测
    return HardwareDetector.detect()
