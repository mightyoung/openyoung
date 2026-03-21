"""
Sandbox Evaluator - Evaluation methods for sandbox instances

Contains iterative evaluation, feedback-based refinement, and log consumption methods.
Delegates iterative evaluation to sandbox_evaluator_iterative module.
"""

import asyncio

from .sandbox_evaluator_iterative import (
    _consume_logs_background,
)

# Import iterative evaluation functions
from .sandbox_evaluator_iterative import (
    evaluate_iterative as _evaluate_iterative,
)


class SandboxEvaluator:
    """Evaluation mixin for SandboxInstance

    Provides methods for evaluating code execution with feedback loops.
    """

    async def evaluate(
        self,
        code: str,
        language: str = "python",
        task_description: str = "Code execution task",
    ) -> dict:
        """在沙箱中执行代码并评估结果"""
        if not self.config.enable_evaluator:
            result = await self.execute(code, language)
            return {
                "execution": result,
                "evaluation": None,
            }

        code_hash = self._get_code_hash(code)
        cached_result = self._get_eval_cache(code_hash)
        if cached_result is not None:
            self._logger.debug(f"Using cached evaluation for code hash: {code_hash}")
            execution_result = await self.execute(code, language)
            return {
                "execution": execution_result,
                "evaluation": cached_result.get("evaluation"),
                "logs": cached_result.get("logs", []),
                "cached": True,
            }

        execution_result = await self.execute(code, language)

        if execution_result.exit_code != 0:
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {execution_result.error}",
                },
            }

        try:
            from .evaluator_client import create_evaluator_client, create_log_consumer

            evaluator = await create_evaluator_client(self.config.evaluator_endpoint)

            log_consumer = create_log_consumer(evaluator, self.sandbox_id, self.sandbox_id)

            plan_info = {
                "task_description": task_description,
                "task_type": language,
                "complexity": "medium",
                "dimensions": [
                    {
                        "name": dim,
                        "weight": 1.0 / len(self.config.evaluator_dimensions),
                        "threshold": 0.5,
                    }
                    for dim in self.config.evaluator_dimensions
                ],
                "max_iterations": self.config.evaluator_max_iterations,
                "timeout_seconds": 60,
            }

            execution_data = {
                "step": 1,
                "action": "execute",
                "thought": f"Executing {language} code",
                "observation": execution_result.output,
                "output": execution_result.output,
                "traces": [],
            }

            collected_logs = []

            async with log_consumer as log_stream:
                responses = []
                async for response in evaluator.evaluate_stream(
                    task_id=self.sandbox_id,
                    session_id=self.sandbox_id,
                    plan_info=plan_info,
                    results=[execution_data],
                ):
                    responses.append(response)

                    try:
                        while True:
                            log = await asyncio.wait_for(log_stream.__anext__(), timeout=0.01)
                            collected_logs.append(log)
                    except StopAsyncIteration:
                        pass
                    except asyncio.TimeoutError:
                        pass

            await evaluator.close()

            if responses:
                response = responses[-1]
                eval_result = {
                    "passed": response.passed,
                    "score": response.overall_score,
                    "feedback": response.feedback,
                    "next_state": response.next_state,
                    "should_continue": response.should_continue,
                }
                self._set_eval_cache(
                    code_hash,
                    {
                        "evaluation": eval_result,
                        "logs": collected_logs,
                    },
                )
                return {
                    "execution": execution_result,
                    "evaluation": eval_result,
                    "logs": collected_logs,
                }
        except Exception as e:
            self._logger.warning(f"Evaluator error: {e}")
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": True,
                    "score": 1.0,
                    "feedback": f"Evaluator unavailable: {e}",
                },
            }

        return {
            "execution": execution_result,
            "evaluation": None,
        }

    async def evaluate_with_feedback(
        self,
        code: str,
        session_id: str,
        task_id: str,
        language: str = "python",
        task_description: str = "Code execution task",
    ) -> dict:
        """在沙箱中执行代码并评估结果 - 支持迭代反馈"""
        from .evaluator_client import create_evaluator_client, create_log_consumer

        log_queue: asyncio.Queue[dict] = asyncio.Queue()
        collected_logs: list[dict] = []

        execution_result = await self.execute(code, language)

        if execution_result.exit_code != 0:
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {execution_result.error}",
                    "should_continue": False,
                },
                "logs": [],
            }

        try:
            evaluator = await create_evaluator_client(self.config.evaluator_endpoint)

            log_consumer = create_log_consumer(evaluator, session_id, task_id)

            plan_info = {
                "task_description": task_description,
                "task_type": language,
                "complexity": "medium",
                "dimensions": [
                    {
                        "name": dim,
                        "weight": 1.0 / len(self.config.evaluator_dimensions),
                        "threshold": 0.5,
                    }
                    for dim in self.config.evaluator_dimensions
                ],
                "max_iterations": self.config.evaluator_max_iterations,
                "timeout_seconds": 60,
            }

            execution_data = {
                "step": 1,
                "action": "execute",
                "thought": f"Executing {language} code",
                "observation": execution_result.output,
                "output": execution_result.output,
                "traces": [],
            }

            log_task = asyncio.create_task(_consume_logs_background(self, log_consumer, log_queue))

            responses = []
            try:
                async for response in evaluator.evaluate_stream(
                    task_id=task_id,
                    session_id=session_id,
                    plan_info=plan_info,
                    results=[execution_data],
                ):
                    responses.append(response)

                    while not log_queue.empty():
                        try:
                            log = log_queue.get_nowait()
                            collected_logs.append(log)
                        except asyncio.QueueEmpty:
                            break

                while not log_queue.empty():
                    try:
                        log = log_queue.get_nowait()
                        collected_logs.append(log)
                    except asyncio.QueueEmpty:
                        break

            finally:
                log_task.cancel()
                try:
                    await log_task
                except asyncio.CancelledError:
                    pass

            await evaluator.close()

            if responses:
                response = responses[-1]
                return {
                    "execution": execution_result,
                    "evaluation": {
                        "passed": response.passed,
                        "score": response.overall_score,
                        "feedback": response.feedback,
                        "next_state": response.next_state,
                        "should_continue": response.should_continue,
                    },
                    "logs": collected_logs,
                }

        except Exception as e:
            self._logger.warning(f"Evaluator error: {e}")
            return {
                "execution": execution_result,
                "evaluation": {
                    "passed": True,
                    "score": 1.0,
                    "feedback": f"Evaluator unavailable: {e}",
                    "should_continue": False,
                },
                "logs": collected_logs,
            }

        return {
            "execution": execution_result,
            "evaluation": None,
            "logs": collected_logs,
        }

    async def _consume_logs_background(
        self,
        log_consumer,
        log_queue: asyncio.Queue,
    ) -> None:
        """后台消费日志 - delegates to module function"""
        return await _consume_logs_background(self, log_consumer, log_queue)

    async def evaluate_iterative(
        self,
        initial_code: str,
        refine_callback: callable,
        session_id: str,
        task_id: str,
        language: str = "python",
        task_description: str = "Code execution task",
        max_iterations: int = 5,
    ) -> dict:
        """迭代评估 - delegates to module function"""
        return await _evaluate_iterative(
            self,
            initial_code,
            refine_callback,
            session_id,
            task_id,
            language,
            task_description,
            max_iterations,
        )
