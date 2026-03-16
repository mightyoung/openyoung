"""
Hardware Abstraction Layer Tests
"""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Check if torch is available
TORCH_AVAILABLE = True
try:
    import torch
except ImportError:
    TORCH_AVAILABLE = False
    pytestmark = pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")


class TestComputeBackend:
    """测试计算后端枚举"""

    def test_backend_values(self):
        """测试后端枚举值"""
        from src.agents.rl import ComputeBackend

        assert ComputeBackend.CUDA.value == "cuda"
        assert ComputeBackend.MPS.value == "mps"
        assert ComputeBackend.CPU.value == "cpu"
        assert ComputeBackend.VULKAN.value == "vulkan"

    def test_backend_from_env_cuda(self):
        """测试从环境变量识别 CUDA"""
        from src.agents.rl import get_backend_from_env, ComputeBackend

        with patch.dict("os.environ", {"RL_DEVICE": "cuda"}):
            backend = get_backend_from_env()
            assert backend == ComputeBackend.CUDA

    def test_backend_from_env_mps(self):
        """测试从环境变量识别 MPS"""
        from src.agents.rl import get_backend_from_env, ComputeBackend

        with patch.dict("os.environ", {"RL_DEVICE": "mps"}):
            backend = get_backend_from_env()
            assert backend == ComputeBackend.MPS

    def test_backend_from_env_auto(self):
        """测试自动检测"""
        from src.agents.rl import get_backend_from_env

        with patch.dict("os.environ", {"RL_DEVICE": "auto"}):
            backend = get_backend_from_env()
            assert backend is None  # Auto returns None to trigger automatic detection


class TestHardwareSpec:
    """测试硬件规格数据类"""

    def test_hardware_spec_creation(self):
        """测试硬件规格创建"""
        from src.agents.rl import HardwareSpec, ComputeBackend

        spec = HardwareSpec(
            backend=ComputeBackend.CUDA,
            device_name="NVIDIA GeForce RTX 3090",
            memory_gb=24.0,
            compute_capability="8.6",
            device_count=1,
        )

        assert spec.backend == ComputeBackend.CUDA
        assert spec.device_name == "NVIDIA GeForce RTX 3090"
        assert spec.memory_gb == 24.0

    def test_hardware_spec_defaults(self):
        """测试默认值"""
        from src.agents.rl import HardwareSpec, ComputeBackend

        spec = HardwareSpec(
            backend=ComputeBackend.CPU,
            device_name="cpu",
            memory_gb=0.0,
        )

        assert spec.backend == ComputeBackend.CPU
        assert spec.device_name == "cpu"
        assert spec.device_count == 1
        assert spec.memory_gb == 0.0


class TestHardwareDetector:
    """测试硬件自动检测"""

    def test_detect_cuda_available(self):
        """测试 CUDA 可用时的检测"""
        from src.agents.rl import HardwareDetector, ComputeBackend

        with patch("torch.cuda.is_available", return_value=True):
            with patch("torch.cuda.get_device_name", return_value="RTX 3090"):
                with patch("torch.cuda.get_device_properties") as mock_props:
                    mock_props.return_value = MagicMock(total_memory=24 * 1024**3)
                    spec = HardwareDetector.detect()

                    assert spec.backend == ComputeBackend.CUDA

    def test_detect_mps_available(self):
        """测试 MPS 可用时的检测"""
        from src.agents.rl import HardwareDetector, ComputeBackend

        with patch("torch.cuda.is_available", return_value=False):
            with patch("torch.backends.mps.is_available", return_value=True):
                spec = HardwareDetector.detect()

                assert spec.backend == ComputeBackend.MPS

    def test_detect_cpu_fallback(self):
        """测试 CPU 回退"""
        from src.agents.rl import HardwareDetector, ComputeBackend

        with patch("torch.cuda.is_available", return_value=False):
            with patch("torch.backends.mps.is_available", return_value=False):
                spec = HardwareDetector.detect()

                assert spec.backend == ComputeBackend.CPU


class TestDeviceManager:
    """测试设备管理器"""

    def test_device_manager_init(self):
        """测试设备管理器初始化"""
        from src.agents.rl import DeviceManager, HardwareSpec, ComputeBackend

        spec = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        manager = DeviceManager(spec)

        assert manager.spec == spec

    def test_device_context(self):
        """测试设备初始化"""
        from src.agents.rl import DeviceManager, HardwareSpec, ComputeBackend

        spec = HardwareSpec(backend=ComputeBackend.CPU, device_name="cpu", memory_gb=0.0)
        manager = DeviceManager(spec)

        # 设备应该成功初始化
        assert manager.device is not None


class TestCreateHardwareSpec:
    """测试硬件规格工厂函数"""

    def test_create_from_env(self):
        """测试从环境变量创建"""
        from src.agents.rl import create_hardware_spec, ComputeBackend

        with patch.dict("os.environ", {"RL_DEVICE": "cuda"}):
            with patch("torch.cuda.is_available", return_value=True):
                with patch("torch.cuda.get_device_name", return_value="RTX 3090"):
                    with patch("torch.cuda.get_device_properties") as mock_props:
                        mock_props.return_value = MagicMock(total_memory=24 * 1024**3)
                        spec = create_hardware_spec()

                        assert spec.backend in [ComputeBackend.CUDA, ComputeBackend.CPU]
