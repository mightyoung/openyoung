"""
Evaluator gRPC Client - 评估器客户端

用于与 Rust 容器中的 Evaluator 服务通信
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import AsyncIterator, Optional, List, Dict, Any
from dataclasses import dataclass

# Add tests/ to path for protobuf imports (so we can import rust.evaluator_pb2)
_tests_path = str(Path(__file__).parent.parent.parent / "tests")
if _tests_path not in sys.path:
    sys.path.insert(0, _tests_path)

logger = logging.getLogger(__name__)


@dataclass
class EvalDimensionResult:
    """单维度评估结果"""
    dimension_name: str
    score: float
    passed: bool
    feedback: str


@dataclass
class EvalResponse:
    """评估响应"""
    task_id: str
    iteration: int
    passed: bool
    overall_score: float
    results: List[EvalDimensionResult]
    feedback: str
    should_continue: bool
    remaining_iterations: int
    current_iteration: int
    next_state: str
    can_shutdown: bool
    status: str


class EvaluatorClient:
    """评估器客户端

    用于与 Rust 容器中的 Evaluator 服务通信
    """

    def __init__(self, endpoint: str = "localhost:50051"):
        """
        初始化客户端

        Args:
            endpoint: Rust 服务地址
        """
        self._endpoint = endpoint
        self._channel = None
        self._stub = None

    async def connect(self) -> bool:
        """连接到 Rust 服务"""
        try:
            import grpc
            import rust.evaluator_pb2 as evaluator__pb2
            import rust.evaluator_pb2_grpc as evaluator__pb2_grpc

            # 使用同步 channel，因为异步流有兼容性问题
            # 同步 gRPC 更稳定，适合流式调用
            self._channel = grpc.insecure_channel(
                self._endpoint,
                options=[
                    ('grpc.connect_timeout_ms', 5000),
                    ('grpc.max_receive_message_length', 10 * 1024 * 1024),
                ]
            )

            # 等待连接就绪
            try:
                grpc.channel_ready_future(self._channel).result(timeout=5.0)
            except grpc.FutureTimeoutError:
                self._channel.close()
                raise ConnectionError(f"Connection timeout to {self._endpoint}")

            self._stub = evaluator__pb2_grpc.EvaluatorServiceStub(self._channel)
            logger.info(f"Connected to Evaluator service at {self._endpoint}")
            return True

        except ImportError as e:
            logger.warning(f"gRPC not available: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to connect to Evaluator service: {e}")
            return False
            return False

    def health_check(self) -> bool:
        """健康检查 (同步版本)"""
        if not self._stub:
            return False

        try:
            import rust.evaluator_pb2 as evaluator__pb2
            request = evaluator__pb2.EvaluatorHealthRequest()
            response = self._stub.HealthCheck(request)
            return response.healthy
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def evaluate_stream(
        self,
        task_id: str,
        session_id: str,
        plan_info: Dict[str, Any],
        results: List[Dict[str, Any]],
    ) -> AsyncIterator[EvalResponse]:
        """
        评估流：发送评估计划和执行结果，接收评估响应

        Args:
            task_id: 任务 ID
            session_id: 会话 ID
            plan_info: 评估计划
            results: 执行结果列表

        Yields:
            EvalResponse 评估响应
        """
        if not self._stub:
            logger.error("Not connected to Evaluator service")
            return

        try:
            import rust.evaluator_pb2 as evaluator__pb2

            # 创建事件生成器 (同步版本)
            def event_generator():
                # 发送评估计划
                plan_msg = self._create_plan_info(plan_info)
                event = evaluator__pb2.EvaluatorEvent(
                    task_id=task_id,
                    session_id=session_id,
                    iteration=0,
                )
                event.plan.CopyFrom(plan_msg)
                yield event

                # 发送执行结果
                for i, result in enumerate(results):
                    result_msg = self._create_execution_result(result)
                    event = evaluator__pb2.EvaluatorEvent(
                        task_id=task_id,
                        session_id=session_id,
                        iteration=i + 1,
                    )
                    event.result.CopyFrom(result_msg)
                    yield event

            # 发送流并接收响应 (同步 gRPC)
            responses = self._stub.EvaluateStream(event_generator())

            for response in responses:
                yield self._parse_eval_response(response)

        except Exception as e:
            logger.error(f"EvaluateStream failed: {e}")
            raise

    async def evaluate_iterate(
        self,
        task_id: str,
        session_id: str,
        plan_info: Dict[str, Any],
        execute_fn,  # async function that executes and returns result
        max_iterations: int = 5,
    ) -> EvalResponse:
        """
        多轮迭代评估：在 Rust 端闭环迭代控制

        这是推荐使用的方法，符合原始设计:
        "迭代控制在 Evaluator 内部闭环"

        流程:
        1. 发送评估计划
        2. 循环:
           - 执行任务 (execute_fn)
           - 发送执行结果
           - 接收评估响应
           - 如果 should_continue=False，退出循环
        3. 返回最终评估结果

        Args:
            task_id: 任务 ID
            session_id: 会话 ID
            plan_info: 评估计划
            execute_fn: 异步函数，执行任务并返回结果 dict
            max_iterations: 最大迭代次数

        Returns:
            EvalResponse: 最终评估响应
        """
        if not self._stub:
            logger.error("Not connected to Evaluator service")
            raise RuntimeError("Not connected to Evaluator service")

        import rust.evaluator_pb2 as evaluator__pb2

        try:
            # 收集所有事件 (因为 gRPC 流是同步的)
            events = []

            # 步骤1: 添加评估计划
            plan_msg = self._create_plan_info(plan_info)
            event = evaluator__pb2.EvaluatorEvent(
                task_id=task_id,
                session_id=session_id,
                iteration=0,
            )
            event.plan.CopyFrom(plan_msg)
            events.append(event)

            # 步骤2: 迭代循环 - 执行任务并收集结果
            for iteration in range(1, max_iterations + 1):
                logger.info(f"Iteration {iteration}: Executing task...")
                result = await execute_fn(iteration)

                # 创建事件
                result_msg = self._create_execution_result(result)
                event = evaluator__pb2.EvaluatorEvent(
                    task_id=task_id,
                    session_id=session_id,
                    iteration=iteration,
                )
                event.result.CopyFrom(result_msg)
                events.append(event)

            # 发送流并接收响应 (同步 gRPC)
            responses = self._stub.EvaluateStream(iter(events))

            # 收集所有响应，返回最后一个
            last_response = None
            for response in responses:
                logger.info(f"Received response: iteration={response.iteration}, "
                           f"passed={response.passed}, should_continue={response.should_continue}, "
                           f"next_state={response.next_state}")
                last_response = self._parse_eval_response(response)

                # 如果不应继续，提前退出
                if not last_response.should_continue:
                    logger.info(f"Evaluation complete at iteration {response.iteration}")
                    break

            return last_response

        except Exception as e:
            logger.error(f"EvaluateIterate failed: {e}")
            raise

    def _create_plan_info(self, plan_info: Dict[str, Any]):
        """创建评估计划消息"""
        import rust.evaluator_pb2 as evaluator__pb2

        dimensions = []
        for dim in plan_info.get("dimensions", []):
            dimensions.append(
                evaluator__pb2.EvalDimensionInfo(
                    name=dim.get("name", ""),
                    weight=dim.get("weight", 0.0),
                    threshold=dim.get("threshold", 0.0),
                    criteria=dim.get("criteria", ""),
                    evaluation_method=dim.get("evaluation_method", "llm_judge"),
                )
            )

        return evaluator__pb2.EvalPlanInfo(
            task_description=plan_info.get("task_description", ""),
            task_type=plan_info.get("task_type", "coding"),
            complexity=plan_info.get("complexity", "medium"),
            dimensions=dimensions,
            max_iterations=plan_info.get("max_iterations", 5),
            timeout_seconds=plan_info.get("timeout_seconds", 300),
        )

    def _create_execution_result(self, result: Dict[str, Any]):
        """创建执行结果消息"""
        import rust.evaluator_pb2 as evaluator__pb2

        traces = []
        for trace in result.get("traces", []):
            traces.append(
                evaluator__pb2.TraceEntry(
                    step=trace.get("step", 0),
                    action=trace.get("action", ""),
                    thought=trace.get("thought", ""),
                    observation=trace.get("observation", ""),
                )
            )

        return evaluator__pb2.ExecutionResult(
            step=result.get("step", 0),
            action=result.get("action", ""),
            thought=result.get("thought", ""),
            observation=result.get("observation", ""),
            output=result.get("output", ""),
            traces=traces,
        )

    def _parse_eval_response(self, response) -> EvalResponse:
        """解析评估响应"""
        results = []
        for r in response.results:
            results.append(
                EvalDimensionResult(
                    dimension_name=r.dimension_name,
                    score=r.score,
                    passed=r.passed,
                    feedback=r.feedback,
                )
            )

        return EvalResponse(
            task_id=response.task_id,
            iteration=response.iteration,
            passed=response.passed,
            overall_score=response.overall_score,
            results=results,
            feedback=response.feedback,
            should_continue=response.should_continue,
            remaining_iterations=response.remaining_iterations,
            current_iteration=response.current_iteration,
            next_state=response.next_state,
            can_shutdown=response.can_shutdown,
            status=response.status,
        )

    def stream_logs(
        self,
        session_id: str,
        task_id: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        订阅日志流

        Args:
            session_id: 会话 ID
            task_id: 任务 ID

        Yields:
            日志条目 dict
        """
        if not self._stub:
            logger.error("Not connected to Evaluator service")
            return

        import rust.evaluator_pb2 as evaluator__pb2

        try:
            request = evaluator__pb2.LogRequest(
                session_id=session_id,
                task_id=task_id,
            )

            # 获取日志流
            for log_entry in self._stub.StreamLogs(request):
                yield {
                    "timestamp": log_entry.timestamp,
                    "level": log_entry.level,
                    "component": log_entry.component,
                    "event": log_entry.event,
                    "message": log_entry.message,
                    "trace_id": log_entry.trace_id,
                    "session_id": log_entry.session_id,
                    "iteration": log_entry.iteration,
                    "data": dict(log_entry.data),
                }

        except Exception as e:
            logger.error(f"StreamLogs failed: {e}")
            raise

    def close(self):
        """关闭连接 (同步版本)"""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None


# 便捷函数
async def create_evaluator_client(endpoint: str = "localhost:50051") -> EvaluatorClient:
    """创建评估器客户端并连接"""
    client = EvaluatorClient(endpoint)
    await client.connect()
    return client


class LogConsumerContext:
    """日志消费者上下文管理器

    用于在评估过程中并行消费日志，不阻塞主流程

    用法:
        async with LogConsumerContext(evaluator, session_id, task_id) as logs:
            async for log in logs:
                print(log)
    """

    def __init__(self, evaluator: "EvaluatorClient", session_id: str, task_id: str):
        self.evaluator = evaluator
        self.session_id = session_id
        self.task_id = task_id
        self._logs: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self) -> AsyncIterator[Dict[str, Any]]:
        """启动日志消费者"""
        self._running = True
        self._task = asyncio.create_task(self._consume_logs())
        return self._log_generator()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """停止日志消费者"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _consume_logs(self):
        """后台消费日志"""
        try:
            for log in self.evaluator.stream_logs(self.session_id, self.task_id):
                if not self._running:
                    break
                await self._logs.put(log)
        except Exception as e:
            logger.error(f"Log consumer error: {e}")
        finally:
            self._running = False

    async def _log_generator(self) -> AsyncIterator[Dict[str, Any]]:
        """生成日志"""
        while self._running or not self._logs.empty():
            try:
                log = await asyncio.wait_for(self._logs.get(), timeout=0.5)
                yield log
            except asyncio.TimeoutError:
                continue


async def create_log_consumer(
    evaluator: "EvaluatorClient",
    session_id: str,
    task_id: str,
) -> LogConsumerContext:
    """创建日志消费者上下文"""
    return LogConsumerContext(evaluator, session_id, task_id)
