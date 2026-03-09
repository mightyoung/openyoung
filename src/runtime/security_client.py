"""
安全服务客户端

提供统一的 Python/Rust 服务接口
支持降级到本地 Python 实现
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecurityServiceClient:
    """安全服务客户端

    优先使用 Rust gRPC 服务，降级到本地 Python 实现
    """

    def __init__(self, use_rust: bool = False, rust_endpoint: str = "localhost:50051"):
        """
        初始化客户端

        Args:
            use_rust: 是否使用 Rust 服务
            rust_endpoint: Rust 服务地址
        """
        self._use_rust = use_rust
        self._rust_endpoint = rust_endpoint
        self._rust_client = None

        if use_rust:
            self._init_rust_client()

    def _init_rust_client(self):
        """初始化 Rust 客户端"""
        try:
            # 延迟导入，避免在没有 Rust 服务时失败
            import grpc
            # 这里需要生成 proto 的 Python 代码
            # 目前先跳过
            logger.info("Rust client initialization deferred - run generate.sh first")
            self._rust_client = None
            self._use_rust = False
        except ImportError as e:
            logger.warning(f"gRPC not available, falling back to Python: {e}")
            self._use_rust = False

    def detect_prompt_injection(
        self,
        content: str,
        threshold: float = 0.8,
        allowed_patterns: list = None,
        blocked_patterns: list = None,
    ):
        """检测提示注入"""
        if self._use_rust and self._rust_client:
            # TODO: 调用 Rust 服务
            pass
        else:
            # 降级到本地 Python 实现
            from src.runtime.security import PromptInjector

            detector = PromptInjector(
                block_threshold=threshold,
                allowed_patterns=allowed_patterns,
                blocked_patterns=blocked_patterns,
            )
            return detector.detect(content)

    def scan_secrets(self, content: str, redact: bool = False):
        """扫描敏感信息"""
        if self._use_rust and self._rust_client:
            # TODO: 调用 Rust 服务
            pass
        else:
            # 降级到本地 Python 实现
            from src.runtime.security import SecretScanner

            scanner = SecretScanner(redact=redact)
            return scanner.scan(content)

    def detect_dangerous_code(
        self, code: str, language: str = "python", threshold: str = "high"
    ):
        """检测危险代码"""
        if self._use_rust and self._rust_client:
            # TODO: 调用 Rust 服务
            pass
        else:
            # 降级到本地 Python 实现
            from src.runtime.security import DangerousCodeDetector, DangerousLevel

            level_map = {
                "critical": DangerousLevel.CRITICAL,
                "high": DangerousLevel.HIGH,
                "medium": DangerousLevel.MEDIUM,
                "low": DangerousLevel.LOW,
            }

            detector = DangerousCodeDetector()
            is_blocked = detector.is_blocked(code, level_map.get(threshold, DangerousLevel.HIGH))

            return {
                "is_safe": not is_blocked,
                "result": detector.detect(code),
            }

    def check_firewall(self, domain: str = None, ip: str = None, url: str = None):
        """防火墙检查"""
        if self._use_rust and self._rust_client:
            # TODO: 调用 Rust 服务
            pass
        else:
            # 降级到本地 Python 实现
            from src.runtime.security import Firewall

            firewall = Firewall()
            return firewall.check(domain=domain, ip=ip, url=url)

    def batch_check(
        self,
        prompts: list = None,
        secrets: list = None,
        codes: list = None,
    ):
        """批量检查"""
        results = {
            "prompts": [],
            "secrets": [],
            "codes": [],
        }

        if prompts:
            for p in prompts:
                results["prompts"].append(self.detect_prompt_injection(**p))

        if secrets:
            for s in secrets:
                results["secrets"].append(self.scan_secrets(**s))

        if codes:
            for c in codes:
                results["codes"].append(self.detect_dangerous_code(**c))

        return results

    @property
    def is_using_rust(self) -> bool:
        """是否使用 Rust 服务"""
        return self._use_rust


# ========== Convenience Functions ==========


def create_security_client(use_rust: bool = False, rust_endpoint: str = "localhost:50051") -> SecurityServiceClient:
    """
    便捷函数：创建安全服务客户端

    Args:
        use_rust: 是否使用 Rust 服务
        rust_endpoint: Rust 服务地址

    Returns:
        SecurityServiceClient 实例
    """
    return SecurityServiceClient(use_rust=use_rust, rust_endpoint=rust_endpoint)
