"""
Sandbox Evaluator Iterative - Iterative evaluation methods

Contains evaluate_iterative method for feedback-based refinement.
"""

import asyncio

from src.core.exception_handler import handle_exceptions


async def _consume_logs_background(
    self,
    log_consumer,
    log_queue: asyncio.Queue,
) -> None:
    """Background log consumer"""
    try:
        async with log_consumer as log_stream:
            async for log in log_stream:
                try:
                    log_queue.put_nowait(log)
                except asyncio.QueueFull:
                    pass
    except Exception as e:
        self._logger.debug(f"Log consumer finished: {e}")


@handle_exceptions(reraise=False, default={})
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
    """Iterative evaluation: supports Agent refining code based on feedback"""
    from .evaluator_client import create_evaluator_client, create_log_consumer

    log_queue: asyncio.Queue[dict] = asyncio.Queue()

    all_execution_results: list[dict] = []

    final_result = None

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
        "max_iterations": max_iterations,
        "timeout_seconds": 60,
    }

    current_code = initial_code

    for iteration in range(max_iterations):
        self._logger.info(f"Iteration {iteration + 1}/{max_iterations}")

        execution_result = await self.execute(current_code, language)
        all_execution_results.append(
            {
                "step": iteration + 1,
                "action": "execute",
                "thought": f"Executing {language} code (iteration {iteration + 1})",
                "observation": execution_result.output or execution_result.error or "",
                "output": execution_result.output,
                "traces": [],
            }
        )

        if execution_result.exit_code != 0:
            final_result = {
                "execution": execution_result,
                "evaluation": {
                    "passed": False,
                    "score": 0.0,
                    "feedback": f"Execution failed: {execution_result.error}",
                    "should_continue": False,
                },
                "iteration": iteration,
                "total_iterations": max_iterations,
            }
            break

        try:
            evaluator = await create_evaluator_client(self.config.evaluator_endpoint)
            log_consumer = create_log_consumer(evaluator, session_id, task_id)

            collected_logs: list[dict] = []

            log_task = asyncio.create_task(
                _consume_logs_background(self, log_consumer, log_queue)
            )

            responses = []
            try:
                async for response in evaluator.evaluate_stream(
                    task_id=task_id,
                    session_id=session_id,
                    plan_info=plan_info,
                    results=all_execution_results,
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

                final_result = {
                    "execution": execution_result,
                    "evaluation": {
                        "passed": response.passed,
                        "score": response.overall_score,
                        "feedback": response.feedback,
                        "next_state": response.next_state,
                        "should_continue": response.should_continue,
                        "remaining_iterations": response.remaining_iterations,
                    },
                    "logs": collected_logs,
                    "iteration": iteration,
                    "total_iterations": max_iterations,
                    "all_results": all_execution_results,
                }

                if response.should_continue and response.remaining_iterations > 0:
                    refined_code = refine_callback(
                        feedback=response.feedback,
                        score=response.overall_score,
                        iteration=iteration + 1,
                    )

                    if refined_code is None:
                        break

                    current_code = refined_code
                    continue
                else:
                    break

        except Exception as e:
            self._logger.warning(f"Evaluator error in iteration {iteration}: {e}")
            final_result = {
                "execution": execution_result,
                "evaluation": {
                    "passed": True,
                    "score": 1.0,
                    "feedback": f"Evaluator unavailable: {e}",
                    "should_continue": False,
                },
                "iteration": iteration,
                "total_iterations": max_iterations,
            }
            break

    if final_result is None:
        final_result = {
            "execution": execution_result,
            "evaluation": {
                "passed": False,
                "score": 0.0,
                "feedback": "Max iterations reached",
                "should_continue": False,
            },
            "iteration": max_iterations - 1,
            "total_iterations": max_iterations,
        }

    return final_result


__all__ = ["evaluate_iterative", "_consume_logs_background"]
