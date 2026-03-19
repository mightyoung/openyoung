"""
Run Methods - Core execution methods extracted from YoungAgent

Contains the main run() method and its helper methods.
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, AsyncGenerator

if TYPE_CHECKING:
    from src.agents.components import file_validation
    from src.agents.components.file_validation import FileValidationResult
    from src.agents.dispatcher import TaskDispatcher
    from src.agents.evaluation_coordinator import EvaluationContext, EvaluationCoordinator
    from src.agents.eval_store import EvalStore
    from src.agents.sub_agent import SubAgent
    from src.core.events import Event, EventType, EventPriority, SystemEvents
    from src.core.heartbeat import HeartbeatScheduler
    from src.core.knowledge import KnowledgeManager
    from src.datacenter.datacenter import TraceRecord, TraceStatus
    from src.evolver.result_analyzer import ResultAnalyzer
    from src.hub.evaluate.harness import EvaluationHarness
    from src.runtime import AISandbox, SandboxPool


async def run(
    self,
    user_input: str,
) -> str:
    """Main execution method for YoungAgent."""
    from src.core.events import Event, EventType, EventPriority, SystemEvents

    # 启动 harness
    if self._harness:
        self._harness.start()

    # ========== Heartbeat: 启动调度器 (Phase 4) ==========
    if self._heartbeat and not self._heartbeat.is_running():
        try:
            await self._heartbeat.start()
        except Exception as e:
            print(f"[YoungAgent] Heartbeat start failed: {e}")

    # ========== EventBus: 任务开始事件 (Phase 4) ==========
    if self._event_bus:
        try:
            start_event = Event(
                type=EventType.TASK_STARTED,
                data={
                    "input": user_input[:200] if user_input else "",
                    "session_id": self._session_id,
                    "agent_name": self.config.name,
                },
                priority=EventPriority.NORMAL,
                source="young_agent",
            )
            self._event_bus.publish(start_event)
        except Exception as e:
            print(f"[YoungAgent] EventBus start event error: {e}")

    # ========== Hooks: pre_task ==========
    self._trigger_hooks("pre_task", {"input": user_input})

    if not await self._permission.can_run(user_input):
        return "Permission denied"

    # ========== FlowSkill 前置处理 ==========
    context = {"session_id": self._session_id}
    if self._flow_skill:
        try:
            user_input = await self._flow_skill.pre_process(user_input, context)
        except Exception as e:
            print(f"[FlowSkill] Pre-process error: {e}")

    task = await _parse_input(self, user_input)

    # EvalPlanner removed — use Harness BenchmarkTask + Grader pattern for evaluation

    # 记录开始时间
    start_time = datetime.now()

    # 使用 TaskExecutor 执行任务
    result = await self._task_executor.execute(task)

    # ========== FlowSkill 后置处理 ==========
    if self._flow_skill:
        try:
            result = await self._flow_skill.post_process(result, context)
        except Exception as e:
            print(f"[FlowSkill] Post-process error: {e}")

    # ========== Hooks: post_task ==========
    # 构建学习上下文
    hook_context = {
        "result": result,
        "task": task.description if task else "",
        "success": not result.startswith("Error") and not result.startswith("error"),
        "session_id": self._session_id,
        "tools_used": [m.role.value for m in self._history if m.role.value == "tool"],
        "result_summary": result[:200] if result else "",
    }
    self._trigger_hooks("post_task", hook_context)

    # 记录结束时间
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    # ========== EventBus: 任务完成事件 (Phase 4) ==========
    task_success = not result.startswith("Error") and not result.startswith("error")
    if self._event_bus:
        try:
            # 发送任务完成事件
            event = Event(
                type=EventType.TASK_COMPLETED,
                data={
                    "task": task.description if task else "",
                    "success": task_success,
                    "duration_ms": duration_ms,
                    "session_id": self._session_id,
                    "agent_name": self.config.name,
                },
                priority=EventPriority.HIGH if task_success else EventPriority.CRITICAL,
                source="young_agent",
            )
            self._event_bus.publish(event)

            # 如果失败，发送错误事件
            if not task_success:
                error_event = Event(
                    type=SystemEvents.ERROR,
                    data={
                        "task": task.description if task else "",
                        "error": result[:500] if result else "Unknown error",
                        "session_id": self._session_id,
                    },
                    priority=EventPriority.CRITICAL,
                    source="young_agent",
                )
                self._event_bus.publish(error_event)
        except Exception as e:
            print(f"[YoungAgent] EventBus error: {e}")

    # ========== 1. DataCenter - 记录 Trace ==========
    if self._datacenter:
        try:
            from src.datacenter.datacenter import TraceRecord, TraceStatus

            status = (
                TraceStatus.SUCCESS
                if result and not result.startswith("Error")
                else TraceStatus.FAILED
            )
            trace = TraceRecord(
                session_id=self._session_id,
                agent_name=self.config.name,
                duration_ms=duration_ms,
                status=status,
                error=result[:200] if status == TraceStatus.FAILED else "",
            )
            self._datacenter.record_trace(trace)
        except Exception as e:
            print(f"[DataCenter] Error: {e}")

    # ========== 2. EvaluationCoordinator - 质量评估 ==========
    # R1-1: 使用 EvaluationCoordinator 进行评估
    quality_score = 1.0
    if self._eval_coordinator and result:
        try:
            # 创建评估上下文
            total_tokens = self._stats.get("total_tokens", 0)
            model = self._stats.get("model", "unknown")

            eval_context = EvaluationContext(
                task_description=task.description,
                task_result=result,
                duration_ms=duration_ms,
                tokens_used=total_tokens,
                model=model,
                session_id=self._session_id,
            )

            # 使用协调器执行评估
            eval_report = await self._eval_coordinator.evaluate(eval_context)
            quality_score = eval_report.score

            print(f"[EvaluationCoordinator] Score: {quality_score:.2f}")
            print(f"[EvaluationCoordinator] Task type: {eval_report.task_type}")
            print(f"[EvaluationCoordinator] Completion rate: {eval_report.completion_rate:.2f}")

            # 文件验证（保留在 young_agent 中因为需要文件系统访问）
            from src.agents.components.file_validation import validate_file_creation

            file_validation = validate_file_creation(task.description, result)
            if not file_validation["verified"]:
                print(f"[FileValidation] {file_validation['message']}")
                quality_score *= 0.3  # 文件未创建，大幅降低
            elif file_validation["files_found"]:
                print(f"[FileValidation] Files verified: {file_validation['files_found']}")

            # 记录到轻量 eval store（Harness 系统使用 BenchmarkTask 评估）
            self._eval_store.add_result({
                "metric": "task_completion",
                "score": quality_score,
                "task_type": eval_report.task_type,
                "completion_rate": eval_report.completion_rate,
                "file_validation": file_validation,
            })

        except Exception as e:
            print(f"[EvaluationCoordinator] Error: {e}, using default score")
            quality_score = 0.9 if not result.startswith("Error") else 0.3

    # ========== 3. EvolutionEngine - 触发进化 ==========
    if self._evolver:
        try:
            signals = ["success"] if quality_score > 0.5 else ["failure"]
            gene = self._evolver.evolve(signals)
            if gene:
                # 创建 capsule
                capsule = self._evolver.create_capsule(
                    trigger=signals,
                    gene=gene,
                    summary=f"Task: {task.description[:50]}... Result: {result[:50]}...",
                )
                print(f"[Evolver] Created capsule: {capsule.id}")
        except Exception as e:
            print(f"[Evolver] Error: {e}")

    # ========== 4. Harness - 记录步骤 ==========
    if self._harness:
        self._harness.record_step(quality_score > 0.5)

    # 记录对话历史（带上限，防止内存泄漏）
    from src.core.types import Message, MessageRole

    self._history.append(Message(role=MessageRole.USER, content=user_input))
    self._history.append(Message(role=MessageRole.ASSISTANT, content=result))

    # 限制历史记录数量
    if len(self._history) > self._max_history:
        # 保留最近的对话，移除最老的
        self._history = self._history[-self._max_history :]

    # ========== 5. Auto-save all components ==========
    _save_all(self)

    # ========== 6. Result analysis ==========
    await _apply_result_analysis(self, result)

    # ========== 7. Checkpoint - 保存状态 ==========
    # 任务完成后自动保存 checkpoint
    await self._save_checkpoint(reason="task_complete")

    return result


async def run_streaming(
    self,
    user_input: str,
) -> AsyncGenerator[dict, None]:
    """Streaming execution method for YoungAgent.

    Yields partial results during execution to support streaming output.

    Args:
        self: YoungAgent instance
        user_input: User input string

    Yields:
        dict with partial result data including:
        - phase: Current execution phase
        - progress: Progress percentage (0.0-1.0)
        - iteration: Current iteration
        - status: Execution status
        - data: Phase-specific data
        - partial_output: Streaming text output if any
    """
    from src.core.events import Event, EventType, EventPriority, TaskProgress

    # Start harness
    if self._harness:
        self._harness.start()

    # Start heartbeat
    if self._heartbeat and not self._heartbeat.is_running():
        try:
            await self._heartbeat.start()
        except Exception as e:
            print(f"[YoungAgent] Heartbeat start failed: {e}")

    # Emit task started event
    if self._event_bus:
        try:
            start_event = Event(
                type=EventType.TASK_STARTED,
                data={
                    "input": user_input[:200] if user_input else "",
                    "session_id": self._session_id,
                    "agent_name": self.config.name,
                },
                priority=EventPriority.NORMAL,
                source="young_agent",
            )
            self._event_bus.publish(start_event)
        except Exception as e:
            print(f"[YoungAgent] EventBus start event error: {e}")

    # Check permission
    if not await self._permission.can_run(user_input):
        yield {
            "phase": "permission",
            "progress": 0.0,
            "iteration": 0,
            "status": "failed",
            "data": {},
            "partial_output": "Permission denied",
        }
        return

    # FlowSkill pre_process
    context = {"session_id": self._session_id}
    if self._flow_skill:
        try:
            user_input = await self._flow_skill.pre_process(user_input, context)
        except Exception as e:
            print(f"[FlowSkill] Pre-process error: {e}")

    # Parse input to Task
    task = await _parse_input(self, user_input)

    # Emit initial progress
    yield {
        "phase": "init",
        "progress": 0.1,
        "iteration": 0,
        "status": "running",
        "data": {"task_id": task.id},
        "partial_output": "Task initialized",
    }

    # Use TaskCompiler to compile task into HarnessGraph
    task_compiler = self._task_executor._flow_skill._task_compiler if hasattr(self._task_executor, '_flow_skill') and hasattr(self._task_executor._flow_skill, '_task_compiler') else None

    if task_compiler is None:
        # Fallback: execute directly without streaming
        result = await self._task_executor.execute(task)
        yield {
            "phase": "execute",
            "progress": 1.0,
            "iteration": 0,
            "status": "completed",
            "data": {"result": result},
            "partial_output": result,
        }
        return

    # Compile task to HarnessGraph
    try:
        harness_graph = task_compiler.compile(task)
    except Exception as e:
        print(f"[TaskCompiler] Compile error: {e}")
        # Fallback to direct execution
        result = await self._task_executor.execute(task)
        yield {
            "phase": "execute",
            "progress": 1.0,
            "iteration": 0,
            "status": "completed",
            "data": {"result": result},
            "partial_output": result,
        }
        return

    # Execute graph with streaming and capture actual result
    harness_result = None
    async for partial in harness_graph.run():
        # Emit TaskProgress event
        if self._event_bus:
            try:
                progress_event = TaskProgress(
                    task_id=task.id,
                    phase=partial.phase.value if hasattr(partial.phase, 'value') else str(partial.phase),
                    progress=partial.progress,
                    iteration=partial.iteration,
                    partial_output=partial.partial_output,
                )
                self._event_bus.publish(progress_event)
            except Exception as e:
                print(f"[EventBus] TaskProgress event error: {e}")

        # Capture actual result from harness execution (not the final "completed" marker)
        if partial.data.get("result") and partial.data.get("result") != "completed":
            harness_result = partial.data.get("result")

        # Yield to caller
        yield partial.to_dict()

    # Use harness result if available, otherwise fall back to direct execution
    if harness_result is not None:
        result = harness_result
    else:
        result = await self._task_executor.execute(task)

    # FlowSkill post_process
    if self._flow_skill:
        try:
            result = await self._flow_skill.post_process(result, context)
        except Exception as e:
            print(f"[FlowSkill] Post-process error: {e}")

    # Emit task completed event
    if self._event_bus:
        try:
            task_success = not result.startswith("Error") and not result.startswith("error")
            event = Event(
                type=EventType.TASK_COMPLETED,
                data={
                    "task": task.description if task else "",
                    "success": task_success,
                    "session_id": self._session_id,
                    "agent_name": self.config.name,
                },
                priority=EventPriority.HIGH if task_success else EventPriority.CRITICAL,
                source="young_agent",
            )
            self._event_bus.publish(event)
        except Exception as e:
            print(f"[YoungAgent] EventBus error: {e}")

    # Record history
    from src.core.types import Message, MessageRole
    self._history.append(Message(role=MessageRole.USER, content=user_input))
    self._history.append(Message(role=MessageRole.ASSISTANT, content=result))
    if len(self._history) > self._max_history:
        self._history = self._history[-self._max_history:]

    # Save all
    _save_all(self)

    # Checkpoint
    await self._save_checkpoint(reason="task_complete")

    # Final yield
    yield {
        "phase": "complete",
        "progress": 1.0,
        "iteration": 0,
        "status": "completed",
        "data": {"result": result},
        "partial_output": result,
    }


async def _apply_result_analysis(self, result: str) -> None:
    """Analyze execution result and generate FlowSkill suggestions.

    Refactored from _apply_evaluation_optimization — EvaluationHub
    config optimization removed (use Harness system instead).
    """
    try:
        from src.evolver.result_analyzer import ResultAnalyzer

        # 获取任务描述
        task_desc = ""
        if self._history:
            for msg in reversed(self._history):
                if msg.role.value == "user":
                    task_desc = msg.content
                    break

        analyzer = ResultAnalyzer()
        analysis = analyzer.analyze(task_desc, result)

        # 如果成功，生成 FlowSkill 配置建议
        if analysis.get("success"):
            flowskill_config = analyzer.generate_flowskill_config()
            if flowskill_config:
                print(f"[ResultAnalyzer] Generated FlowSkill: {flowskill_config.get('name')}")
                print(f"[ResultAnalyzer] Workflow: {flowskill_config.get('workflow', [])}")

                # 保存分析结果
                import os
                import json

                os.makedirs(self._data_dir, exist_ok=True)
                analysis_path = os.path.join(self._data_dir, "analysis.json")
                with open(analysis_path, "w") as f:
                    json.dump(analysis, f, indent=2, ensure_ascii=False)
                print(f"[ResultAnalyzer] Saved to {analysis_path}")
    except ImportError:
        pass  # ResultAnalyzer not available
    except Exception as e:
        print(f"[ResultAnalyzer] Error: {e}")


def _save_all(self):
    """保存所有组件数据到磁盘"""
    import os

    os.makedirs(self._data_dir, exist_ok=True)

    # 保存 DataCenter traces
    if self._datacenter:
        try:
            path = os.path.join(self._data_dir, "traces.json")
            self._datacenter.trace_collector.save(path)
            print(f"[DataCenter] Saved traces to {path}")
        except Exception as e:
            print(f"[DataCenter] Save error: {e}")

    # 保存 eval store results (lightweight — Harness system handles full evaluation)
    if self._eval_store:
        try:
            import json

            path = os.path.join(self._data_dir, "evaluations.json")
            with open(path, "w") as f:
                json.dump(self._eval_store._results, f, indent=2, default=str)
            print(f"[EvalStore] Saved {len(self._eval_store._results)} results to {path}")
        except Exception as e:
            print(f"[EvalStore] Save error: {e}")

    # 保存 EvolutionEngine genes and capsules
    if self._evolver:
        try:
            genes_path = os.path.join(self._data_dir, "genes.json")
            capsules_path = os.path.join(self._data_dir, "capsules.json")
            self._evolver.save(genes_path, capsules_path)
            print(f"[Evolver] Saved to {self._data_dir}")
        except Exception as e:
            print(f"[Evolver] Save error: {e}")

    # 保存 Harness status
    if self._harness:
        try:
            path = os.path.join(self._data_dir, "harness.json")
            self._harness.save(path)
            print(f"[Harness] Saved to {path}")
        except Exception as e:
            print(f"[Harness] Save error: {e}")


async def _parse_input(self, user_input: str) -> "Task":
    """解析用户输入 - 支持 @mention 触发 SubAgent"""
    import re
    from src.core.types import SubAgentType
    from src.core.types import Task

    # 参考 Claude Code Task 协议: @subagent task_description
    match = re.match(r"@(\w+)\s+(.+)", user_input.strip())
    if match:
        subagent_name = match.group(1)
        description = match.group(2)

        # 查找对应的 SubAgentType
        subagent_type = None

        # 首先检查是否匹配预定义类型
        for sat in SubAgentType:
            if sat.value == subagent_name:
                subagent_type = sat
                break

        # 如果没有匹配预定义类型，检查是否在已加载的 SubAgents 中
        if subagent_type is None and subagent_name in self._sub_agents:
            # 使用 GENERAL 类型作为占位符，实际委托时会查找具体 SubAgent
            subagent_type = SubAgentType.GENERAL

        return Task(
            id=str(uuid.uuid4()),
            description=description,
            input=description,
            subagent_type=subagent_type,
            custom_subagent=subagent_name
            if subagent_type == SubAgentType.GENERAL and subagent_name in self._sub_agents
            else None,
        )
    return Task(id=str(uuid.uuid4()), description=user_input, input=user_input)
