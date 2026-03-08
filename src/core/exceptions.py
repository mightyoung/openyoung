"""
OpenYoung 统一异常层次结构

参考: Django, FastAPI, SQLAlchemy 最佳实践
"""


class OpenYoungError(Exception):
    """OpenYoung 基础异常"""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __repr__(self):
        return f"[{self.code}] {self.message}"


# ====================
# Agent 相关异常
# ====================


class AgentError(OpenYoungError):
    """Agent 基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="AGENT_ERROR")


class AgentNotFoundError(AgentError):
    """Agent 未找到"""

    def __init__(self, agent_name: str):
        super().__init__(f"Agent not found: {agent_name}")
        self.code = "AGENT_NOT_FOUND"
        self.agent_name = agent_name


class AgentExecutionError(AgentError):
    """Agent 执行失败"""

    def __init__(self, agent_name: str, reason: str):
        super().__init__(f"Agent '{agent_name}' execution failed: {reason}")
        self.code = "AGENT_EXECUTION_ERROR"
        self.agent_name = agent_name
        self.reason = reason


class AgentTimeoutError(AgentError):
    """Agent 执行超时"""

    def __init__(self, agent_name: str, timeout: int):
        super().__init__(f"Agent '{agent_name}' timed out after {timeout}s")
        self.code = "AGENT_TIMEOUT"
        self.agent_name = agent_name
        self.timeout = timeout


# ====================
# 执行相关异常
# ====================


class ExecutionError(OpenYoungError):
    """执行基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="EXECUTION_ERROR")


class ToolExecutionError(ExecutionError):
    """工具执行失败"""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(f"Tool '{tool_name}' failed: {reason}")
        self.code = "TOOL_ERROR"
        self.tool_name = tool_name
        self.reason = reason


class PermissionDeniedError(ExecutionError):
    """权限被拒绝"""

    def __init__(self, action: str):
        super().__init__(f"Permission denied: {action}")
        self.code = "PERMISSION_DENIED"
        self.action = action


# ====================
# 评估相关异常
# ====================


class EvaluationError(OpenYoungError):
    """评估基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="EVALUATION_ERROR")


class EvaluationTimeoutError(EvaluationError):
    """评估超时"""

    def __init__(self, timeout: int):
        super().__init__(f"Evaluation timed out after {timeout}s")
        self.code = "EVALUATION_TIMEOUT"
        self.timeout = timeout


# ====================
# 配置相关异常
# ====================


class ConfigError(OpenYoungError):
    """配置基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="CONFIG_ERROR")


class ConfigNotFoundError(ConfigError):
    """配置项未找到"""

    def __init__(self, key: str):
        super().__init__(f"Config key not found: {key}")
        self.code = "CONFIG_NOT_FOUND"
        self.key = key


class ConfigValidationError(ConfigError):
    """配置验证失败"""

    def __init__(self, key: str, reason: str):
        super().__init__(f"Config '{key}' validation failed: {reason}")
        self.code = "CONFIG_VALIDATION_ERROR"
        self.key = key
        self.reason = reason


# ====================
# 数据相关异常
# ====================


class DataError(OpenYoungError):
    """数据基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="DATA_ERROR")


class DataNotFoundError(DataError):
    """数据未找到"""

    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}")
        self.code = "DATA_NOT_FOUND"
        self.resource = resource
        self.id = id


class DataValidationError(DataError):
    """数据验证失败"""

    def __init__(self, resource: str, reason: str):
        super().__init__(f"{resource} validation failed: {reason}")
        self.code = "DATA_VALIDATION_ERROR"
        self.resource = resource
        self.reason = reason


# ====================
# 网络相关异常
# ====================


class NetworkError(OpenYoungError):
    """网络基础异常"""

    def __init__(self, message: str):
        super().__init__(message, code="NETWORK_ERROR")


class APITimeoutError(NetworkError):
    """API 请求超时"""

    def __init__(self, endpoint: str, timeout: int):
        super().__init__(f"API request to {endpoint} timed out after {timeout}s")
        self.code = "API_TIMEOUT"
        self.endpoint = endpoint
        self.timeout = timeout


class APIResponseError(NetworkError):
    """API 响应错误"""

    def __init__(self, endpoint: str, status_code: int, message: str):
        super().__init__(f"API error {status_code} from {endpoint}: {message}")
        self.code = "API_RESPONSE_ERROR"
        self.endpoint = endpoint
        self.status_code = status_code
        self.message = message
