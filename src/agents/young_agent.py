"""
YoungAgent - Main Agent Class with full system integration
"""

import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.types import (
    AgentConfig,
    Message,
    MessageRole,
    Task,
    TaskDispatchParams,
    SubAgentConfig,
)
from src.agents.permission import PermissionEvaluator
from src.agents.session import SessionManager
from src.package_manager.manager import PackageManager
from src.harness import Harness
from src.tools.executor import ToolExecutor


class SubAgent:
    def __init__(self, config: SubAgentConfig):
        self.config = config
        self.name = config.name
        self.type = config.type

    async def run(self, task: Task, context: dict) -> str:
        return f"SubAgent {self.name} executed"


class TaskDispatcher:
    def __init__(self, sub_agents):
        self._sub_agents = sub_agents
        self._session_manager = SessionManager()

    async def dispatch(self, params, parent_context, existing_task_id=None):
        session = self._session_manager.get_or_create(
            task_id=params.session_id or existing_task_id,
            parent_session_id=parent_context.get("session_id"),
            description=params.task_description,
            context=parent_context,
        )
        self._session_manager.update_session(session.session_id, status="running")
        sub_agent = self._sub_agents.get(params.subagent_type)
        if not sub_agent:
            return {"error": "Unknown subagent_type", "session_id": session.session_id}
        task = Task(
            id=params.session_id or session.session_id,
            description=params.task_description,
            input=params.task_description,
        )
        try:
            result = await sub_agent.run(task, {})
            self._session_manager.update_session(
                session.session_id, status="completed", result=result
            )
        except Exception as e:
            return {"error": str(e), "session_id": session.session_id}
        return {
            "output": result,
            "status": "completed",
            "session_id": session.session_id,
        }

    def get_session(self, session_id):
        return self._session_manager.get_session(session_id)

    def get_active_sessions(self):
        return self._session_manager.get_active_sessions()


class YoungAgent:
    def __init__(
        self,
        config,
        package_manager=None,
    ):
        self.config = config
        self.mode = config.mode
        self._session_id = str(uuid.uuid4())
        self._history = []
        self._sub_agents = {}
        self._permission = PermissionEvaluator(config.permission)
        self._dispatcher = TaskDispatcher(self._sub_agents)
        self._flow_skill = config.flow_skill
        self._package_manager = package_manager or PackageManager()

        # Initialize components
        self._harness = None
        self._datacenter = None
        self._evaluation_hub = None
        self._evolver = None
        self._evolver = None
        
        # Data persistence directory
        import os
        self._data_dir = os.path.join(os.path.expanduser("~"), ".young")
        try:
            from src.harness import Harness

            self._harness = Harness()
        except Exception as e:
            print(f"[Warning] Harness init failed: {e}")

        try:
            from src.datacenter.datacenter import DataCenter

            self._datacenter = DataCenter()
        except Exception as e:
            print(f"[Warning] DataCenter init failed: {e}")

        try:
            from src.evaluation.hub import EvaluationHub

            self._evaluation_hub = EvaluationHub()
        except Exception as e:
            print(f"[Warning] EvaluationHub init failed: {e}")

        try:
            from src.evolver.engine import EvolutionEngine

            self._evolver = EvolutionEngine()
            # 预加载一些基础 genes
            self._init_default_genes()
        except Exception as e:
            print(f"[Warning] EvolutionEngine init failed: {e}")

        self._packages = {}
        self._loaded_skills = {}
        self._tools = {}
        self._tool_executor = ToolExecutor()
        self._max_tool_calls = 10

        self._init_builtin_subagents()

    def _init_default_genes(self):
        """初始化默认 genes"""
        try:
            from src.evolver.models import Gene, GeneCategory

            # 创建默认 gene
            gene = Gene(
                id=f"default_gene_{datetime.now().strftime('%Y%m%d')}",
                version="1.0.0",
                category=GeneCategory.REPAIR,
                signals=["success", "failure", "task_complete"],
                preconditions=[],
                strategy=["analyze_result", "improve_if_needed"],
                constraints={},
            )
            self._evolver._matcher.register_gene(gene)
        except Exception as e:
            print(f"[Warning] Default genes init failed: {e}")

    def _init_builtin_subagents(self):
        from src.core.types import SubAgentType

        builtin = [
            SubAgentConfig(
                name="general", type=SubAgentType.GENERAL, description="General"
            )
        ]
        for sc in builtin:
            self._sub_agents[sc.name] = SubAgent(sc)

    async def run(self, user_input: str) -> str:
        # 启动 harness
        if self._harness:
            self._harness.start()

        if not await self._permission.can_run(user_input):
            return "Permission denied"

        task = await self._parse_input(user_input)

        # 记录开始时间
        start_time = datetime.now()

        result = await self._execute(task)

        # 记录结束时间
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

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

        # ========== 2. EvaluationHub - 质量评估 ==========
        quality_score = 1.0
        if self._evaluation_hub and result:
            try:
                from src.evaluation.hub import EvaluationResult

                # 使用 task 评估器
                eval_result = EvaluationResult(
                    metric="task_completion",
                    score=0.9 if not result.startswith("Error") else 0.3,
                    details={"task": task.description, "result_length": len(result)},
                    evaluator="task",
                )
                self._evaluation_hub._results.append(eval_result)
                quality_score = eval_result.score
            except Exception as e:
                print(f"[EvaluationHub] Error: {e}")

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

        self._history.append(Message(role=MessageRole.USER, content=user_input))
        self._history.append(Message(role=MessageRole.ASSISTANT, content=result))

        self._history.append(Message(role=MessageRole.USER, content=user_input))
        self._history.append(Message(role=MessageRole.ASSISTANT, content=result))
        
        # ========== 5. Auto-save all components ==========
        self._save_all()
        
        return result
    
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
        
        # 保存 EvaluationHub results
        if self._evaluation_hub:
            try:
                path = os.path.join(self._data_dir, "evaluations.json")
                self._evaluation_hub.save_results(path)
                print(f"[EvaluationHub] Saved results to {path}")
            except Exception as e:
                print(f"[EvaluationHub] Save error: {e}")
        
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

    async def _parse_input(self, user_input: str) -> Task:
        import re

        match = re.match(r"@(\w+)\s+(.+)", user_input.strip())
        if match:
            return Task(
                id=str(uuid.uuid4()), description=match.group(2), input=match.group(2)
            )
        return Task(id=str(uuid.uuid4()), description=user_input, input=user_input)

    async def _execute(self, task: Task) -> str:
        messages = []
        system_prompt = (
            self.config.system_prompt
            or """你是一个有帮助的AI助手。你可以通过执行代码来完成任务。可用工具：bash, write, edit, read, glob, grep"""
        )
        messages.append({"role": "system", "content": system_prompt})
        for msg in self._history[-10:]:
            messages.append({"role": msg.role.value, "content": msg.content})
        messages.append({"role": "user", "content": task.description})
        tools = self._tool_executor.get_tool_schemas()

        try:
            from src.llm.client import LLMClient

            client = LLMClient()
            for i in range(self._max_tool_calls):
                response = await client.chat(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=tools,
                )
                message = response["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                if not tool_calls:
                    await client.close()
                    return content
                for tool_call in tool_calls:
                    func = tool_call["function"]
                    tool_name = func["name"]
                    arguments = json.loads(func["arguments"])
                    print(f"\n[执行工具] {tool_name}: {arguments}")
                    result = await self._tool_executor.execute(tool_name, arguments)
                    messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                            "tool_calls": [tool_call],
                        }
                    )
                    tool_result = (
                        result.result if result.success else f"错误: {result.error}"
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.get("id", f"call_{i}"),
                            "content": tool_result,
                        }
                    )
                    print(f"[工具结果] {tool_result[:200]}...")
            await client.close()
            return "已达到最大工具调用次数"
        except Exception as e:
            return f"Error: {str(e)}"

    # ===== 获取各组件数据的方法 =====

    def get_harness_stats(self) -> Dict[str, Any]:
        if self._harness:
            return self._harness.get_status()
        return {}

    def get_datacenter_traces(self) -> List:
        if self._datacenter:
            return self._datacenter.trace_collector._traces
        return []

    def get_evaluation_results(self) -> List:
        if self._evaluation_hub:
            return self._evaluation_hub._results
        return []

    def get_evolver_genes(self) -> List:
        if self._evolver:
            return list(self._evolver._matcher._genes.values())
        return []

    def get_evolver_capsules(self) -> List:
        if self._evolver:
            return self._evolver.get_capsules()
        return []

    def get_all_stats(self) -> Dict[str, Any]:
        return {
            "harness": self.get_harness_stats(),
            "datacenter_traces_count": len(self.get_datacenter_traces()),
            "evaluation_results_count": len(self.get_evaluation_results()),
            "evolver_genes_count": len(self.get_evolver_genes()),
            "evolver_capsules_count": len(self.get_evolver_capsules()),
        }
