"""
JSON-RPC 2.0 Protocol - JSON-RPC 2.0 协议处理

实现 JSON-RPC 2.0 消息的解析、序列化和错误处理
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 错误对象"""

    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JSONRPCError":
        """从字典创建"""
        return cls(
            code=data.get("code", -32603),
            message=data.get("message", "Internal error"),
            data=data.get("data"),
        )


# 预定义错误码
class JSONRPCErrorCode:
    """JSON-RPC 2.0 标准错误码"""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 请求对象"""

    method: str
    params: Optional[dict[str, Any] | list[Any]] = None
    id: Optional[str | int] = None

    @property
    def jsonrpc(self) -> str:
        """JSON-RPC 版本"""
        return "2.0"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.params is not None:
            result["params"] = self.params
        if self.id is not None:
            result["id"] = self.id
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JSONRPCRequest":
        """从字典创建"""
        return cls(
            method=data.get("method", ""),
            params=data.get("params"),
            id=data.get("id"),
        )


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 响应对象"""

    id: Optional[str | int]
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None

    @property
    def jsonrpc(self) -> str:
        """JSON-RPC 版本"""
        return "2.0"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error is not None:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JSONRPCResponse":
        """从字典创建"""
        error = None
        if "error" in data and data["error"]:
            error = JSONRPCError.from_dict(data["error"])
        return cls(
            id=data.get("id"),
            result=data.get("result"),
            error=error,
        )

    @classmethod
    def success(cls, id: Optional[str | int], result: Any) -> "JSONRPCResponse":
        """创建成功响应"""
        return cls(id=id, result=result)

    @classmethod
    def error_response(
        cls,
        id: Optional[str | int],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> "JSONRPCResponse":
        """创建错误响应"""
        return cls(id=id, error=JSONRPCError(code=code, message=message, data=data))


@dataclass
class JSONRPCMessage:
    """JSON-RPC 2.0 消息容器"""

    request: Optional[JSONRPCRequest] = None
    response: Optional[JSONRPCResponse] = None
    is_notification: bool = False

    def is_request(self) -> bool:
        """是否为请求"""
        return self.request is not None

    def is_response(self) -> bool:
        """是否为响应"""
        return self.response is not None


class JSONRPCProtocol:
    """JSON-RPC 2.0 协议处理器"""

    def __init__(self):
        self._request_handlers: dict[str, callable] = {}

    def register_handler(self, method: str, handler: callable):
        """注册请求处理器"""
        self._request_handlers[method] = handler

    def parse_message(self, raw: str) -> JSONRPCMessage:
        """解析 JSON-RPC 消息"""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return JSONRPCResponse.error(
                id=None,
                code=JSONRPCErrorCode.PARSE_ERROR,
                message=f"Parse error: {e}",
            )

        # 处理批量请求
        if isinstance(data, list):
            return self._parse_batch(data)

        # 处理单个请求
        return self._parse_single(data)

    def _parse_single(self, data: dict[str, Any]) -> JSONRPCMessage:
        """解析单个消息"""
        if "jsonrpc" not in data:
            return JSONRPCResponse.error(
                id=data.get("id"),
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Missing jsonrpc field",
            )

        # 响应消息
        if "result" in data or "error" in data:
            return JSONRPCMessage(response=JSONRPCResponse.from_dict(data))

        # 请求消息
        if "method" not in data:
            return JSONRPCResponse.error(
                id=data.get("id"),
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Missing method field",
            )

        request = JSONRPCRequest.from_dict(data)

        # 通知消息 (无 id)
        if request.id is None:
            return JSONRPCMessage(request=request, is_notification=True)

        return JSONRPCMessage(request=request)

    def _parse_batch(self, data: list) -> JSONRPCMessage:
        """解析批量消息"""
        # 简化实现：返回第一个消息的响应
        if not data:
            return JSONRPCResponse.error(
                id=None,
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message="Empty batch",
            )
        return self._parse_single(data[0])

    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """处理请求"""
        method = request.method
        handler = self._request_handlers.get(method)

        if handler is None:
            return JSONRPCResponse.error(
                id=request.id,
                code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                message=f"Method not found: {method}",
            )

        try:
            params = request.params or {}
            if isinstance(params, list):
                result = await handler(*params)
            else:
                result = await handler(**params)
            return JSONRPCResponse.success(id=request.id, result=result)
        except TypeError as e:
            return JSONRPCResponse.error(
                id=request.id,
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message=f"Invalid params: {e}",
            )
        except Exception as e:
            logger.exception(f"Handler error for {method}")
            return JSONRPCResponse.error(
                id=request.id,
                code=JSONRPCErrorCode.INTERNAL_ERROR,
                message=str(e),
            )

    def serialize_response(self, response: JSONRPCResponse) -> str:
        """序列化响应"""
        return json.dumps(response.to_dict())

    def serialize_error(self, error: JSONRPCError) -> str:
        """序列化错误"""
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "error": error.to_dict(),
                "id": None,
            }
        )
