"""
LangSmith 集成

提供可观测性支持，跟踪和调试 LangGraph 工作流
参考: LangSmith 官方文档
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LangSmithConfig:
    """LangSmith 配置"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project: str = "openyoung",
        endpoint: str = "https://api.smith.langchain.com",
        enabled: bool = True,
    ):
        self.api_key = api_key or os.getenv("LANGCHAIN_API_KEY")
        self.project = project
        self.endpoint = endpoint
        self.enabled = enabled and bool(self.api_key)

    @classmethod
    def from_env(cls) -> "LangSmithConfig":
        """从环境变量加载配置"""
        return cls(
            api_key=os.getenv("LANGCHAIN_API_KEY"),
            project=os.getenv("LANGCHAIN_PROJECT", "openyoung"),
            endpoint=os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
            enabled=os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true",
        )


class TraceLevel(str, Enum):
    """跟踪级别"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TraceSpan:
    """跟踪跨度

    对应 LangSmith 的 span 概念
    """

    id: str
    name: str
    span_type: str  # chain, llm, tool, agent
    start_time: datetime
    end_time: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    inputs: Optional[dict[str, Any]] = None
    outputs: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    parent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def duration_ms(self) -> Optional[float]:
        """获取持续时间(毫秒)"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None


class LangSmithClient:
    """LangSmith 客户端 (简化版)

    提供与 LangSmith API 兼容的跟踪功能
    完整版应直接使用 langchain.langsmith 包
    """

    def __init__(self, config: Optional[LangSmithConfig] = None):
        self.config = config or LangSmithConfig.from_env()
        self._spans: dict[str, TraceSpan] = {}
        self._current_span_id: Optional[str] = None

        if self.config.enabled:
            logger.info(f"LangSmith enabled, project: {self.config.project}")
        else:
            logger.info("LangSmith disabled or not configured")

    def start_span(
        self,
        name: str,
        span_type: str = "chain",
        inputs: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        parent_id: Optional[str] = None,
    ) -> str:
        """开始一个跟踪跨度"""
        import uuid

        span_id = str(uuid.uuid4())

        span = TraceSpan(
            id=span_id,
            name=name,
            span_type=span_type,
            start_time=datetime.now(),
            inputs=inputs,
            metadata=metadata or {},
            tags=tags or [],
            parent_id=parent_id or self._current_span_id,
        )

        self._spans[span_id] = span
        self._current_span_id = span_id

        if self.config.enabled:
            logger.debug(f"Started span: {name} ({span_id})")

        return span_id

    def end_span(
        self,
        span_id: str,
        outputs: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """结束一个跟踪跨度"""
        span = self._spans.get(span_id)
        if not span:
            logger.warning(f"Span not found: {span_id}")
            return

        span.end_time = datetime.now()
        span.outputs = outputs
        span.error = error

        if self.config.enabled:
            duration = span.duration_ms()
            logger.debug(f"Ended span: {span.name} ({span_id}), duration: {duration}ms")

        # 恢复父跨度
        self._current_span_id = span.parent_id

    def add_event(self, span_id: str, event: dict[str, Any]) -> None:
        """添加事件到跨度"""
        span = self._spans.get(span_id)
        if span:
            span.events.append(event)

    def get_trace(self, root_span_id: str) -> dict[str, Any]:
        """获取完整跟踪数据"""
        span = self._spans.get(root_span_id)
        if not span:
            return {}

        # 递归收集子跨度
        children = []
        for s in self._spans.values():
            if s.parent_id == root_span_id:
                children.append(self.get_trace(s.id))

        return {
            "id": span.id,
            "name": span.name,
            "type": span.span_type,
            "start_time": span.start_time.isoformat(),
            "end_time": span.end_time.isoformat() if span.end_time else None,
            "duration_ms": span.duration_ms(),
            "inputs": span.inputs,
            "outputs": span.outputs,
            "error": span.error,
            "metadata": span.metadata,
            "tags": span.tags,
            "events": span.events,
            "children": children,
        }

    async def upload_trace(self, trace: dict[str, Any]) -> bool:
        """上传跟踪数据到 LangSmith

        简化实现: 实际应使用 langchain.langsmith
        """
        if not self.config.enabled:
            return False

        try:
            # 实际实现需要 langchain 包
            # 这里只做日志记录
            logger.info(f"Would upload trace: {trace.get('name', 'unnamed')}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload trace: {e}")
            return False


# ====================
# LangGraph 集成
# ====================


class LangGraphTracer:
    """LangGraph 跟踪器

    集成到 LangGraph 工作流，记录每个节点的执行
    """

    def __init__(self, client: Optional[LangSmithClient] = None):
        self.client = client or LangSmithClient()
        self._root_span_id: Optional[str] = None

    def start_workflow(self, workflow_name: str, inputs: dict[str, Any]) -> str:
        """开始工作流跟踪"""
        self._root_span_id = self.client.start_span(
            name=workflow_name,
            span_type="agent",
            inputs=inputs,
            tags=["workflow"],
        )
        return self._root_span_id

    def start_node(self, node_name: str, inputs: dict[str, Any]) -> str:
        """开始节点跟踪"""
        return self.client.start_span(
            name=node_name,
            span_type="chain",
            inputs=inputs,
            parent_id=self._root_span_id,
        )

    def end_node(
        self,
        span_id: str,
        outputs: dict[str, Any],
        error: Optional[str] = None,
    ) -> None:
        """结束节点跟踪"""
        self.client.end_span(span_id, outputs, error)

    def end_workflow(self, outputs: dict[str, Any]) -> None:
        """结束工作流跟踪"""
        if self._root_span_id:
            self.client.end_span(self._root_span_id, outputs)

    def get_trace(self) -> dict[str, Any]:
        """获取完整跟踪"""
        if self._root_span_id:
            return self.client.get_trace(self._root_span_id)
        return {}


# ====================
# 便捷函数
# ====================


_default_client: Optional[LangSmithClient] = None


def get_langsmith_client() -> LangSmithClient:
    """获取全局 LangSmith 客户端"""
    global _default_client
    if _default_client is None:
        _default_client = LangSmithClient()
    return _default_client


def get_tracer() -> LangGraphTracer:
    """获取全局 LangGraph 跟踪器"""
    return LangGraphTracer(get_langsmith_client())


def configure_langsmith(
    api_key: Optional[str] = None,
    project: str = "openyoung",
    enabled: bool = True,
) -> LangSmithClient:
    """配置 LangSmith"""
    global _default_client

    config = LangSmithConfig(
        api_key=api_key,
        project=project,
        enabled=enabled,
    )
    _default_client = LangSmithClient(config)
    return _default_client
