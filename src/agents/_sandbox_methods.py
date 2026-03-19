"""
YoungAgent Sandbox Methods

提取自 young_agent.py 的 AI Docker Sandbox 相关方法。
"""

from src.runtime import AISandbox, PoolConfig, SandboxConfig, SandboxPool


def enable_sandbox(
    self,
    max_memory_mb: int = 512,
    max_execution_time_seconds: int = 300,
    allow_network: bool = False,
) -> None:
    """启用 AI Docker 沙箱

    Args:
        max_memory_mb: 最大内存限制 (MB)
        max_execution_time_seconds: 最大执行时间 (秒)
        allow_network: 是否允许网络访问
    """
    if self._sandbox or self._sandbox_pool:
        print("[YoungAgent] Sandbox already enabled")
        return

    # 创建沙箱配置
    config = SandboxConfig(
        max_memory_mb=max_memory_mb,
        max_execution_time_seconds=max_execution_time_seconds,
        allow_network=allow_network,
    )

    # 创建沙箱
    self._sandbox = AISandbox(config)
    self._tool_executor.set_sandbox(self._sandbox)

    print(
        f"[YoungAgent] Sandbox enabled: memory={max_memory_mb}MB, timeout={max_execution_time_seconds}s"
    )


def enable_sandbox_pool(
    self,
    min_size: int = 2,
    max_size: int = 10,
    max_memory_mb: int = 512,
    max_execution_time_seconds: int = 300,
) -> None:
    """启用 AI Docker 沙箱池

    Args:
        min_size: 最小实例数
        max_size: 最大实例数
        max_memory_mb: 最大内存限制 (MB)
        max_execution_time_seconds: 最大执行时间 (秒)
    """
    if self._sandbox or self._sandbox_pool:
        print("[YoungAgent] Sandbox already enabled")
        return

    # 创建配置
    sandbox_config = SandboxConfig(
        max_memory_mb=max_memory_mb,
        max_execution_time_seconds=max_execution_time_seconds,
    )
    pool_config = PoolConfig(
        min_size=min_size,
        max_size=max_size,
        sandbox_config=sandbox_config,
    )

    # 创建沙箱池
    self._sandbox_pool = SandboxPool(pool_config)
    self._tool_executor.set_sandbox_pool(self._sandbox_pool)

    print(f"[YoungAgent] Sandbox pool enabled: size={min_size}-{max_size}")
