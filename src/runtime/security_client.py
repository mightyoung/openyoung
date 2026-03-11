"""
安全服务客户端

提供统一的 Python/Rust 服务接口
支持降级到本地 Python 实现
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional

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
                    ("grpc.connect_timeout_ms", 5000),
                    ("grpc.max_receive_message_length", 10 * 1024 * 1024),
                ],
            )

            # 检查服务是否可用
            try:
                grpc.channel_ready_future(self._channel).result(timeout=5)
            except grpc.FutureTimeoutError:
                logger.warning(
                    f"Rust service at {self._rust_endpoint} not reachable, falling back to Python"
                )
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
            secrets.append(
                {
                    "type": secret.type,
                    "start": secret.start,
                    "end": secret.end,
                    "snippet": secret.snippet,
                }
            )
        return {
            "has_secrets": response.has_secrets,
            "secrets_found": secrets,
            "redacted_content": response.redacted_content,
        }

    def _convert_code_response(self, response) -> Dict[str, Any]:
        """转换 Rust dangerous code 响应为 Python dict"""
        patterns = []
        for pattern in response.detected_patterns:
            patterns.append(
                {
                    "name": pattern.name,
                    "level": pattern.level,
                    "message": pattern.message,
                }
            )
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
            "severity": result.severity.value
            if hasattr(result.severity, "value")
            else result.severity,
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
                    "type": s.type.value if hasattr(s.type, "value") else s.type,
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
            "level": result.level.value if hasattr(result.level, "value") else result.level,
            "warnings": result.warnings,
            "detected_patterns": result.detected_patterns
            if hasattr(result, "detected_patterns")
            else [],
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
            return {
                "allowed": not is_internal,
                "action": "block" if is_internal else "allow",
                "reason": "Internal IP blocked" if is_internal else "Allowed",
            }
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


def create_security_client(
    use_rust: bool = False, rust_endpoint: str = "localhost:50051"
) -> SecurityServiceClient:
    """
    便捷函数：创建安全服务客户端

    Args:
        use_rust: 是否使用 Rust 服务
        rust_endpoint: Rust 服务地址

    Returns:
        SecurityServiceClient 实例
    """
    return SecurityServiceClient(use_rust=use_rust, rust_endpoint=rust_endpoint)


# ========== Agent Control Service Client ==========


class AgentControlClient:
    """Agent 控制服务客户端

    用于与 Rust 容器中的 Agent 服务通信
    """

    def __init__(self, endpoint: str = "localhost:50051"):
        """
        初始化客户端

        Args:
            endpoint: gRPC 服务地址
        """
        self._endpoint = endpoint
        self._channel = None
        self._stub = None

    def connect(self) -> bool:
        """连接到 gRPC 服务"""
        try:
            import agent_control_pb2 as agent_control__pb2
            import agent_control_pb2_grpc as agent_control__pb2_grpc
            import grpc

            self._channel = grpc.insecure_channel(
                self._endpoint,
                options=[
                    ("grpc.connect_timeout_ms", 5000),
                    ("grpc.max_receive_message_length", 10 * 1024 * 1024),
                ],
            )

            # 检查服务是否可用
            try:
                grpc.channel_ready_future(self._channel).result(timeout=5)
            except grpc.FutureTimeoutError:
                logger.warning(f"Agent service at {self._endpoint} not reachable")
                return False

            self._stub = agent_control__pb2_grpc.AgentControlServiceStub(self._channel)
            logger.info(f"Connected to Agent control service at {self._endpoint}")
            return True
        except ImportError as e:
            logger.warning(f"gRPC not available: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to agent service: {e}")
            return False

    def start_agent(
        self,
        task_id: str,
        task_description: str,
        eval_plan: dict = None,
        config: dict = None,
    ) -> Dict[str, Any]:
        """启动 Agent 并获取状态流"""
        if not self._stub:
            if not self.connect():
                return {"error": "Not connected to agent service"}

        try:
            import agent_control_pb2 as agent_control__pb2

            # 构建请求
            request = agent_control__pb2.AgentRequest(
                task_id=task_id,
                task_description=task_description,
            )

            # 添加评估计划
            if eval_plan:
                request.eval_plan.task_type = eval_plan.get("task_type", "")
                request.eval_plan.complexity = eval_plan.get("complexity", "medium")
                request.eval_plan.skip_evaluation = eval_plan.get("skip_evaluation", False)
                request.eval_plan.max_iterations = eval_plan.get("max_iterations", 100)
                request.eval_plan.timeout_seconds = eval_plan.get("timeout_seconds", 300)

            # 添加配置
            if config:
                request.config.agent_type = config.get("agent_type", "default")
                request.config.model = config.get("model", "claude-sonnet-4-20250514")
                request.config.max_steps = config.get("max_steps", 100)

            # 调用服务并获取流
            responses = self._stub.StartAgent(request, timeout=60)

            states = []
            for response in responses:
                states.append(
                    {
                        "task_id": response.task_id,
                        "status": response.status,
                        "current_step": response.current_step,
                        "current_action": response.current_action,
                        "traces": [
                            {
                                "step": t.step,
                                "action": t.action,
                                "thought": t.thought,
                                "observation": t.observation,
                                "tool_used": t.tool_used,
                            }
                            for t in response.traces
                        ],
                        "output": response.output,
                        "timestamp": response.timestamp,
                    }
                )

            return {"success": True, "states": states}
        except Exception as e:
            logger.error(f"StartAgent failed: {e}")
            return {"error": str(e)}

    def submit_evaluation_result(
        self,
        task_id: str,
        overall_score: float,
        passed: bool,
        blocking_failed: bool = False,
        results: list = None,
        feedback: str = "",
    ) -> Dict[str, Any]:
        """提交评估结果"""
        if not self._stub:
            if not self.connect():
                return {"error": "Not connected to agent service"}

        try:
            import agent_control_pb2 as agent_control__pb2

            request = agent_control__pb2.EvaluationResultRequest(
                task_id=task_id,
                overall_score=overall_score,
                passed=passed,
                blocking_failed=blocking_failed,
                feedback=feedback,
            )

            # 添加维度结果
            if results:
                for r in results:
                    dim_result = request.results.add()
                    dim_result.dimension_name = r.get("dimension_name", "")
                    dim_result.score = r.get("score", 0.0)
                    dim_result.passed = r.get("passed", False)
                    dim_result.feedback = r.get("feedback", "")

            response = self._stub.SubmitEvaluationResult(request, timeout=10)

            return {
                "accepted": response.accepted,
                "message": response.message,
                "can_shutdown": response.can_shutdown,
            }
        except Exception as e:
            logger.error(f"SubmitEvaluationResult failed: {e}")
            return {"error": str(e)}

    def request_shutdown(
        self,
        task_id: str,
        reason: int = 1,
        message: str = "",
    ) -> Dict[str, Any]:
        """请求关闭容器"""
        if not self._stub:
            if not self.connect():
                return {"error": "Not connected to agent service"}

        try:
            import agent_control_pb2 as agent_control__pb2

            request = agent_control__pb2.ShutdownRequest(
                task_id=task_id,
                reason=reason,
                message=message,
            )

            response = self._stub.RequestShutdown(request, timeout=10)

            return {
                "success": response.success,
                "message": response.message,
                "exit_code": response.exit_code,
            }
        except Exception as e:
            logger.error(f"RequestShutdown failed: {e}")
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self._stub:
            if not self.connect():
                return {"healthy": False, "status": "Not connected"}

        try:
            import agent_control_pb2 as agent_control__pb2

            request = agent_control__pb2.HealthCheckRequest()
            response = self._stub.HealthCheck(request, timeout=5)

            return {
                "healthy": response.healthy,
                "status": response.status,
            }
        except Exception as e:
            logger.error(f"HealthCheck failed: {e}")
            return {"healthy": False, "status": str(e)}

    def close(self):
        """关闭连接"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None


def create_agent_client(endpoint: str = "localhost:50051") -> AgentControlClient:
    """
    便捷函数：创建 Agent 控制客户端

    Args:
        endpoint: gRPC 服务地址

    Returns:
        AgentControlClient 实例
    """
    return AgentControlClient(endpoint=endpoint)
