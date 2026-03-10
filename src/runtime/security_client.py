"""
安全服务客户端

提供统一的 Python/Rust 服务接口
支持降级到本地 Python 实现
"""

import sys
import os
from typing import Optional, List, Dict, Any
import logging

# 添加 tests/rust 目录到 Python 路径
_rust_proto_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tests", "rust")
if os.path.exists(_rust_proto_dir):
    sys.path.insert(0, _rust_proto_dir)

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
        self._channel = None

        if use_rust:
            self._init_rust_client()

    def _init_rust_client(self):
        """初始化 Rust 客户端"""
        try:
            import grpc
            import security_pb2 as security__pb2
            import security_pb2_grpc as security__pb2_grpc

            # 创建 insecure channel（生产环境应使用 TLS）
            self._channel = grpc.insecure_channel(
                self._rust_endpoint,
                options=[
                    ('grpc.connect_timeout_ms', 5000),
                    ('grpc.max_receive_message_length', 10 * 1024 * 1024),
                ]
            )

            # 检查服务是否可用
            try:
                grpc.channel_ready_future(self._channel).result(timeout=5)
            except grpc.FutureTimeoutError:
                logger.warning(f"Rust service at {self._rust_endpoint} not reachable, falling back to Python")
                self._channel = None
                self._use_rust = False
                return
            except Exception as e:
                logger.warning(f"Rust service connection failed: {e}, falling back to Python")
                self._channel = None
                self._use_rust = False
                return

            self._rust_client = security__pb2_grpc.SecurityServiceStub(self._channel)
            logger.info(f"Connected to Rust security service at {self._rust_endpoint}")
        except ImportError as e:
            logger.warning(f"gRPC not available, falling back to Python: {e}")
            self._use_rust = False
        except Exception as e:
            logger.warning(f"Failed to connect to Rust service: {e}, falling back to Python")
            self._use_rust = False
            self._channel = None

    def _convert_prompt_response(self, response) -> Dict[str, Any]:
        """转换 Rust prompt injection 响应为 Python dict"""
        return {
            "is_malicious": response.is_malicious,
            "severity": response.severity,
            "matched_patterns": list(response.matched_patterns),
            "confidence": response.confidence,
            "sanitized_content": response.sanitized_content,
        }

    def _convert_secret_response(self, response) -> Dict[str, Any]:
        """转换 Rust secret scan 响应为 Python dict"""
        secrets = []
        for secret in response.secrets_found:
            secrets.append({
                "type": secret.type,
                "start": secret.start,
                "end": secret.end,
                "snippet": secret.snippet,
            })
        return {
            "has_secrets": response.has_secrets,
            "secrets_found": secrets,
            "redacted_content": response.redacted_content,
        }

    def _convert_code_response(self, response) -> Dict[str, Any]:
        """转换 Rust dangerous code 响应为 Python dict"""
        patterns = []
        for pattern in response.detected_patterns:
            patterns.append({
                "name": pattern.name,
                "level": pattern.level,
                "message": pattern.message,
            })
        return {
            "is_safe": response.is_safe,
            "level": response.level,
            "warnings": list(response.warnings),
            "detected_patterns": patterns,
        }

    def _convert_firewall_response(self, response) -> Dict[str, Any]:
        """转换 Rust firewall 响应为 Python dict"""
        return {
            "allowed": response.allowed,
            "action": response.action,
            "reason": response.reason,
        }

    def detect_prompt_injection(
        self,
        content: str,
        threshold: float = 0.8,
        allowed_patterns: List[str] = None,
        blocked_patterns: List[str] = None,
    ) -> Dict[str, Any]:
        """检测提示注入"""
        if self._use_rust and self._rust_client:
            try:
                import security_pb2 as security__pb2

                request = security__pb2.PromptInjectionRequest(
                    content=content,
                    threshold=threshold,
                    allowed_patterns=allowed_patterns or [],
                    blocked_patterns=blocked_patterns or [],
                )
                response = self._rust_client.DetectPromptInjection(request, timeout=5)
                return self._convert_prompt_response(response)
            except Exception as e:
                logger.warning(f"Rust service call failed: {e}, falling back to Python")

        # 降级到本地 Python 实现
        from src.runtime.security import PromptInjector

        detector = PromptInjector(
            block_threshold=threshold,
            allowed_patterns=allowed_patterns,
            blocked_patterns=blocked_patterns,
        )
        result = detector.detect(content)
        # 转换为字典
        return {
            "is_malicious": result.is_malicious,
            "severity": result.severity.value if hasattr(result.severity, 'value') else result.severity,
            "matched_patterns": result.matched_patterns,
            "confidence": result.confidence,
            "sanitized_content": result.sanitized_content or "",
        }

    def scan_secrets(self, content: str, redact: bool = False) -> Dict[str, Any]:
        """扫描敏感信息"""
        if self._use_rust and self._rust_client:
            try:
                import security_pb2 as security__pb2

                request = security__pb2.SecretScanRequest(
                    content=content,
                    redact=redact,
                )
                response = self._rust_client.ScanSecrets(request, timeout=5)
                return self._convert_secret_response(response)
            except Exception as e:
                logger.warning(f"Rust service call failed: {e}, falling back to Python")

        # 降级到本地 Python 实现
        from src.runtime.security import SecretScanner

        scanner = SecretScanner(redact=redact)
        result = scanner.scan(content)
        # 转换为字典
        return {
            "has_secrets": result.has_secrets,
            "secrets_found": [
                {
                    "type": s.type.value if hasattr(s.type, 'value') else s.type,
                    "start": s.position[0],
                    "end": s.position[1],
                    "snippet": s.snippet,
                }
                for s in result.secrets_found
            ],
            "redacted_content": result.redacted_content or "",
        }

    def detect_dangerous_code(
        self, code: str, language: str = "python", threshold: str = "high"
    ) -> Dict[str, Any]:
        """检测危险代码"""
        if self._use_rust and self._rust_client:
            try:
                import security_pb2 as security__pb2

                request = security__pb2.DangerousCodeRequest(
                    code=code,
                    language=language,
                    block_threshold=threshold,
                )
                response = self._rust_client.DetectDangerousCode(request, timeout=5)
                return self._convert_code_response(response)
            except Exception as e:
                logger.warning(f"Rust service call failed: {e}, falling back to Python")

        # 降级到本地 Python 实现
        from src.runtime.security import DangerousCodeDetector, DangerousLevel

        level_map = {
            "critical": DangerousLevel.CRITICAL,
            "high": DangerousLevel.HIGH,
            "medium": DangerousLevel.MEDIUM,
            "low": DangerousLevel.LOW,
        }

        detector = DangerousCodeDetector()
        result = detector.detect(code)
        is_blocked = detector.is_blocked(code, level_map.get(threshold, DangerousLevel.HIGH))

        return {
            "is_safe": not is_blocked,
            "level": result.level.value if hasattr(result.level, 'value') else result.level,
            "warnings": result.warnings,
            "detected_patterns": result.detected_patterns if hasattr(result, 'detected_patterns') else [],
        }

    def check_firewall(self, domain: str = None, ip: str = None, url: str = None) -> Dict[str, Any]:
        """防火墙检查"""
        if self._use_rust and self._rust_client:
            try:
                import security_pb2 as security__pb2

                request = security__pb2.FirewallRequest(
                    domain=domain or "",
                    ip=ip or "",
                    url=url or "",
                )
                response = self._rust_client.CheckFirewall(request, timeout=5)
                return self._convert_firewall_response(response)
            except Exception as e:
                logger.warning(f"Rust service call failed: {e}, falling back to Python")

        # 降级到本地 Python 实现
        from src.runtime.security import Firewall
        from src.runtime.security.firewall import FirewallConfig

        config = FirewallConfig()
        firewall = Firewall(config)

        # 统一返回格式
        if domain:
            allowed, reason = firewall.check_domain(domain)
            return {"allowed": allowed, "action": "allow" if allowed else "block", "reason": reason}
        elif ip:
            is_internal = firewall.is_internal_ip(ip)
            return {"allowed": not is_internal, "action": "block" if is_internal else "allow",
                    "reason": "Internal IP blocked" if is_internal else "Allowed"}
        elif url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            allowed, reason = firewall.check_domain(parsed.netloc or parsed.hostname or "")
            return {"allowed": allowed, "action": "allow" if allowed else "block", "reason": reason}

        return {"allowed": True, "action": "allow", "reason": "No check performed"}

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
