"""
EvalHub API - Evaluation Service REST API

提供评估服务的 HTTP API 接口:
- 评估执行端点
- 评估历史查询
- 评估包管理
- 健康检查

参考 LangSmith API 设计
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Optional

from .hub import EvaluationHub, create_evaluation_hub
from .plugins import get_registry


class EvalHubAPI:
    """EvalHub REST API 服务

    提供 RESTful 接口访问评估功能
    """

    def __init__(self, hub: Optional[EvaluationHub] = None):
        self._hub = hub or create_evaluation_hub()
        self._running = False

    @property
    def hub(self) -> EvaluationHub:
        """获取评估中心实例"""
        return self._hub

    # ========== Health Check ==========

    async def health_check(self) -> dict[str, Any]:
        """健康检查

        Returns:
            健康状态
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "eval-hub",
            "version": "1.0.0",
            "evaluators": list(self._hub._evaluators.keys()),
            "plugins": self._hub._plugin_registry.list_plugins() if self._hub._plugin_registry else [],
        }

    # ========== Evaluation Endpoints ==========

    def _convert_result(self, result: Any) -> dict[str, Any]:
        """转换评估结果为字典"""
        if result is None:
            return {}
        if isinstance(result, dict):
            return result
        if hasattr(result, "to_dict"):
            return result.to_dict()
        # 处理 EvaluationResult 等 dataclass
        if hasattr(result, "__dict__"):
            return {k: self._convert_result(v) for k, v in result.__dict__.items()}
        return {"result": str(result)}

    async def evaluate(
        self,
        metric: str,
        input_data: Any,
        evaluator_type: str = "task",
        task_description: Optional[str] = None,
    ) -> dict[str, Any]:
        """执行评估

        POST /evaluate

        Args:
            metric: 指标名称
            input_data: 输入数据
            evaluator_type: 评估器类型
            task_description: 任务描述 (可选)

        Returns:
            评估结果
        """
        # 如果提供了任务描述，先生成评估计划
        eval_plan = None
        if task_description:
            eval_plan = await self._hub.generate_plan(task_description)

        # 执行评估
        if eval_plan:
            # 使用 TaskCompletionEval 的 evaluate_with_plan
            task_eval = self._hub._evaluators.get("task")
            if task_eval and hasattr(task_eval, "evaluate_with_plan"):
                result = await task_eval.evaluate_with_plan(
                    task_description=task_description,
                    actual_result=input_data,
                    eval_plan=eval_plan,
                )
            else:
                # Fallback to regular evaluate
                result = await self._hub.evaluate(
                    metric=metric,
                    input_data=input_data,
                    evaluator_type=evaluator_type,
                )
        else:
            result = await self._hub.evaluate(
                metric=metric,
                input_data=input_data,
                evaluator_type=evaluator_type,
            )

        # 转换为字典
        return self._convert_result(result)

    async def evaluate_full(
        self,
        input_data: dict[str, Any],
        include_plugins: bool = True,
    ) -> dict[str, Any]:
        """全面评估

        POST /evaluate/full

        Args:
            input_data: 包含所有评估所需数据的字典
            include_plugins: 是否包含插件评估

        Returns:
            完整的评估报告
        """
        report = await self._hub.evaluate_full(input_data)

        # 如果启用插件评估
        if include_plugins and self._hub._plugin_registry:
            plugin_results = await self._hub.evaluate_with_plugins(input_data)
            report["plugin_results"] = [
                asdict(r) if hasattr(r, "__dict__") else r for r in plugin_results
            ]

        return report

    async def evaluate_with_plan(
        self,
        task_description: str,
        actual_result: Any,
    ) -> dict[str, Any]:
        """基于评估计划执行评估

        POST /evaluate/with-plan

        Args:
            task_description: 任务描述
            actual_result: 实际结果

        Returns:
            评估结果
        """
        # 生成评估计划
        eval_plan = await self._hub.generate_plan(task_description)

        # 执行评估
        result = await self._hub.evaluate_with_plan(
            task_description=task_description,
            actual_result=actual_result,
            eval_plan=eval_plan,
        )

        return result

    # ========== Evaluation History ==========

    async def get_evaluation_history(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """获取评估历史

        GET /history

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            评估历史
        """
        results = self._hub._results[offset : offset + limit]

        return {
            "items": [asdict(r) if hasattr(r, "__dict__") else r for r in results],
            "total": len(self._hub._results),
            "limit": limit,
            "offset": offset,
        }

    async def get_evaluation_result(self, index: int) -> dict[str, Any]:
        """获取指定评估结果

        GET /history/{index}

        Args:
            index: 结果索引

        Returns:
            评估结果
        """
        if 0 <= index < len(self._hub._results):
            result = self._hub._results[index]
            return asdict(result) if hasattr(result, "__dict__") else result
        return {"error": "Index out of range"}

    # ========== Plugins ==========

    async def list_plugins(self) -> dict[str, Any]:
        """列出所有插件

        GET /plugins

        Returns:
            插件列表
        """
        if not self._hub._plugin_registry:
            return {"plugins": [], "message": "Plugin registry not available"}

        plugins = self._hub._plugin_registry.list_plugins()
        return {
            "plugins": plugins,
            "total": len(plugins),
        }

    async def run_plugin_evaluation(
        self,
        plugin_name: str,
        context_data: dict[str, Any],
    ) -> dict[str, Any]:
        """运行指定插件评估

        POST /plugins/{plugin_name}/evaluate

        Args:
            plugin_name: 插件名称
            context_data: 上下文数据

        Returns:
            插件评估结果
        """
        if not self._hub._plugin_registry:
            return {"error": "Plugin registry not available"}

        plugin = self._hub._plugin_registry.get(plugin_name)
        if not plugin:
            return {"error": f"Plugin not found: {plugin_name}"}

        # 创建评估上下文
        from .plugins import EvalContext

        context = EvalContext(
            task_description=context_data.get("task_description", ""),
            task_type=context_data.get("task_type", "general"),
            input_data=context_data.get("input_data"),
            output_data=context_data.get("output_data"),
            expected_output=context_data.get("expected_output"),
            metadata=context_data.get("metadata", {}),
        )

        # 执行评估
        result = plugin.evaluate(context)

        return asdict(result)

    # ========== Eval Packages ==========

    async def list_eval_packages(
        self,
        dimension: Optional[str] = None,
        level: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """列出评估包

        GET /packages

        Args:
            dimension: 评估维度
            level: 评估级别
            tags: 标签过滤

        Returns:
            评估包列表
        """
        from .indexer import EvalDimension, EvalLevel

        dim = EvalDimension[dimension.upper()] if dimension else None
        lvl = EvalLevel[level.upper()] if level else None

        packages = self._hub.search_eval_packages(dim, lvl, tags)

        return {
            "packages": [
                {
                    "name": p.name,
                    "version": p.version,
                    "dimension": p.dimension.value if p.dimension else None,
                    "level": p.level.value if p.level else None,
                    "tags": p.tags,
                    "description": p.description,
                }
                for p in packages
            ],
            "total": len(packages),
        }

    async def get_eval_package(self, name: str) -> dict[str, Any]:
        """获取评估包详情

        GET /packages/{name}

        Args:
            name: 包名称

        Returns:
            评估包详情
        """
        package = self._hub.get_eval_package(name)

        if not package:
            return {"error": f"Package not found: {name}"}

        return {
            "name": package.name,
            "version": package.version,
            "dimension": package.dimension.value if package.dimension else None,
            "level": package.level.value if package.level else None,
            "tags": package.tags,
            "description": package.description,
            "metrics": package.metrics,
        }

    # ========== Metrics ==========

    async def get_metrics(self) -> dict[str, Any]:
        """获取可用指标

        GET /metrics

        Returns:
            指标列表
        """
        from .metrics import BUILTIN_METRICS

        return {
            "metrics": list(BUILTIN_METRICS.keys()),
            "total": len(BUILTIN_METRICS),
        }


# ========== ASGI App ==========

class EvalHubApp:
    """EvalHub ASGI 应用

    简单的 ASGI 接口，用于运行评估服务
    """

    def __init__(self):
        self.api = EvalHubAPI()

    async def __call__(self, scope, receive, send):
        """ASGI 调用"""
        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        # 健康检查
        if path == "/health" and method == "GET":
            await self._send_json(send, await self.api.health_check())
            return

        # 评估端点
        if path == "/evaluate" and method == "POST":
            body = await self._receive_json(receive)
            result = await self.api.evaluate(
                metric=body.get("metric", "default"),
                input_data=body.get("input_data"),
                evaluator_type=body.get("evaluator_type", "task"),
                task_description=body.get("task_description"),
            )
            await self._send_json(send, result)
            return

        if path == "/evaluate/full" and method == "POST":
            body = await self._receive_json(receive)
            result = await self.api.evaluate_full(body)
            await self._send_json(send, result)
            return

        if path == "/evaluate/with-plan" and method == "POST":
            body = await self._receive_json(receive)
            result = await self.api.evaluate_with_plan(
                task_description=body.get("task_description", ""),
                actual_result=body.get("actual_result"),
            )
            await self._send_json(send, result)
            return

        # 历史端点
        if path == "/history" and method == "GET":
            query = scope.get("query_string", b"").decode()
            params = dict(q.split("=") for q in query.split("&") if "=" in q)
            limit = int(params.get("limit", 10))
            offset = int(params.get("offset", 0))
            result = await self.api.get_evaluation_history(limit, offset)
            await self._send_json(send, result)
            return

        # 插件端点
        if path == "/plugins" and method == "GET":
            result = await self.api.list_plugins()
            await self._send_json(send, result)
            return

        # 包端点
        if path == "/packages" and method == "GET":
            query = scope.get("query_string", b"").decode()
            params = dict(q.split("=") for q in query.split("&") if "=" in q)
            dimension = params.get("dimension")
            level = params.get("level")
            tags = params.get("tags", "").split(",") if params.get("tags") else None
            result = await self.api.list_eval_packages(dimension, level, tags)
            await self._send_json(send, result)
            return

        # 指标端点
        if path == "/metrics" and method == "GET":
            result = await self.api.get_metrics()
            await self._send_json(send, result)
            return

        # 默认返回 404
        await self._send_json(send, {"error": "Not found"}, status=404)

    async def _receive_json(self, receive) -> dict:
        """接收 JSON body"""
        body = b""
        async for chunk in receive:
            body += chunk
        return json.loads(body) if body else {}

    async def _send_json(self, send, data: dict, status: int = 200):
        """发送 JSON 响应"""
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({
            "type": "http.response.body",
            "body": json.dumps(data).encode(),
        })


# ========== Convenience Functions ==========

def create_eval_hub_api() -> EvalHubAPI:
    """创建 EvalHub API 实例"""
    return EvalHubAPI()


def create_eval_hub_app() -> EvalHubApp:
    """创建 EvalHub ASGI 应用"""
    return EvalHubApp()


# ========== CLI Server ==========

async def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行评估服务

    Args:
        host: 主机地址
        port: 端口
    """
    import uvicorn

    app = EvalHubApp()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    import sys

    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000

    print(f"Starting EvalHub server on {host}:{port}")
    asyncio.run(run_server(host, port))
