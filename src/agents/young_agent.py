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
        self._tool_executor = ToolExecutor(permission_evaluator=self._permission)
        self._max_tool_calls = 10

        self._init_builtin_subagents()
        self._load_skills()

    def _load_skills(self):
        """加载配置的 Skills - 参考 Anthropic SKILL.md 格式"""
        if not hasattr(self.config, 'skills') or not self.config.skills:
            return

        try:
            from src.skills.loader import SkillLoader
            from pathlib import Path
            import yaml
            import os

            # 从 packages/ 目录加载 skills (使用绝对路径)
            packages_dir = Path(__file__).parent.parent.parent / "packages"
            self._loaded_skills = {}

            # 加载配置的 skills
            for skill_name in self.config.skills:
                # 尝试从 packages/ 目录加载 (skill-xxx 或 xxx)
                skill_paths = [
                    packages_dir / f"skill-{skill_name}",
                    packages_dir / skill_name,
                ]

                skill_path = None
                for sp in skill_paths:
                    if sp.exists() and (sp / "skill.yaml").exists():
                        skill_path = sp / "skill.yaml"
                        break

                if skill_path:
                    with open(skill_path, "r", encoding="utf-8") as f:
                        skill_config = yaml.safe_load(f)

                    # 加载 skill 内容
                    skill_dir = skill_path.parent
                    entry_file = skill_config.get("entry", "skill.md")
                    content_file = skill_dir / entry_file

                    if content_file.exists():
                        content = content_file.read_text(encoding="utf-8")
                        self._loaded_skills[skill_name] = {
                            "config": skill_config,
                            "content": content,
                            "path": str(skill_dir),
                        }
                        print(f"[Skill] Loaded: {skill_name}")
                    else:
                        # 只加载配置
                        self._loaded_skills[skill_name] = {
                            "config": skill_config,
                            "content": "",
                            "path": str(skill_dir),
                        }
                        print(f"[Skill] Loaded (config only): {skill_name}")
                else:
                    print(f"[Skill] Not found: {skill_name}")

            # 构建 system prompt
            self._build_skill_prompt()

        except Exception as e:
            print(f"[Warning] Skill loading failed: {e}")

    def _build_skill_prompt(self):
        """构建包含 skills 的 system prompt"""
        if not self._loaded_skills:
            return

        skill_instructions = []
        for name, data in self._loaded_skills.items():
            config = data["config"]
            content = data["content"]

            desc = config.get("description", "")
            entry = config.get("entry", "skill.md")

            instruction = f"\n## Skill: {name}\n"
            instruction += f"Description: {desc}\n"
            instruction += f"Entry: {entry}\n"

            if content:
                instruction += f"\n{content[:500]}..."

            skill_instructions.append(instruction)

        # 追加到 system prompt
        skills_section = "\n\n".join(skill_instructions)
        self.config.system_prompt += f"\n\n# Available Skills\n{skills_section}\n"
        print(f"[Skill] Built system prompt with {len(self._loaded_skills)} skills")

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
        """初始化 SubAgents - 从配置加载，参考 Claude Code Task 协议"""
        from src.core.types import SubAgentType

        # 默认内置 SubAgents
        default_agents = [
            SubAgentConfig(name="explore", type=SubAgentType.EXPLORE,
                description="快速探索代码库，只读操作", model="deepseek-chat"),
            SubAgentConfig(name="general", type=SubAgentType.GENERAL,
                description="通用任务处理", model="deepseek-chat"),
            SubAgentConfig(name="search", type=SubAgentType.SEARCH,
                description="复杂搜索任务", model="deepseek-chat"),
            SubAgentConfig(name="builder", type=SubAgentType.BUILDER,
                description="构建和执行任务", model="deepseek-coder"),
            SubAgentConfig(name="reviewer", type=SubAgentType.REVIEWER,
                description="代码审查", model="deepseek-chat"),
            SubAgentConfig(name="eval", type=SubAgentType.EVAL,
                description="评估任务", model="deepseek-chat"),
        ]

        # 添加默认
        for sc in default_agents:
            self._sub_agents[sc.name] = SubAgent(sc)

        # 从配置加载用户定义的 SubAgents（覆盖默认）
        if hasattr(self.config, 'sub_agents') and self.config.sub_agents:
            for sc in self.config.sub_agents:
                self._sub_agents[sc.name] = SubAgent(sc)
                print(f"[SubAgent] Loaded: {sc.name} ({sc.type.value})")

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
                from src.evaluation.task_eval import TaskCompletionEval

                # 使用 Task 评估器
                evaluator = TaskCompletionEval()
                # 简单评估：task_description + expected(空) + actual_result
                eval_dict = await evaluator.evaluate(
                    task_description=task.description,
                    expected_result=None,
                    actual_result=result,
                )

                # 转换为 EvaluationResult
                eval_result = EvaluationResult(
                    metric="task_completion",
                    score=eval_dict.get("completion_rate", 0.9),
                    details=eval_dict,
                    evaluator="task_completion",
                )
                self._evaluation_hub._results.append(eval_result)
                quality_score = eval_result.score
                print(f"[EvaluationHub] Score: {quality_score:.2f}")
            except Exception as e:
                print(f"[EvaluationHub] Error: {e}, using default score")
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
        """解析用户输入 - 支持 @mention 触发 SubAgent"""
        import re

        # 参考 Claude Code Task 协议: @subagent task_description
        match = re.match(r"@(\w+)\s+(.+)", user_input.strip())
        if match:
            subagent_name = match.group(1)
            description = match.group(2)

            # 查找对应的 SubAgentType
            from src.core.types import SubAgentType
            subagent_type = None
            for sat in SubAgentType:
                if sat.value == subagent_name:
                    subagent_type = sat
                    break

            return Task(
                id=str(uuid.uuid4()),
                description=description,
                input=description,
                subagent_type=subagent_type
            )
        return Task(id=str(uuid.uuid4()), description=user_input, input=user_input)

    async def _delegate_to_subagent(self, task: Task) -> str:
        """委托任务给 SubAgent - 参考 Claude Code Task 协议"""
        subagent_type = task.subagent_type.value if task.subagent_type else None

        # 查找 SubAgent
        sub_agent = None
        for sa in self._sub_agents.values():
            if sa.type == task.subagent_type:
                sub_agent = sa
                break

        if not sub_agent:
            return f"[Error] SubAgent not found: {subagent_type}"

        print(f"[SubAgent] Delegating to @{subagent_type}: {task.description[:50]}...")

        # 创建子任务
        sub_task = Task(
            id=str(uuid.uuid4()),
            description=task.description,
            input=task.description,
        )

        # 构建子上下文
        context = {
            "session_id": self._session_id,
            "parent_summary": "",
            "task": task.description,
        }

        try:
            # 执行 SubAgent
            result = await sub_agent.run(sub_task, context)
            return result
        except Exception as e:
            return f"[Error] SubAgent execution failed: {str(e)}"

    async def _execute(self, task: Task) -> str:
        """执行任务 - 支持 SubAgent 委托"""
        # 如果是 SubAgent 调用，委托给对应 SubAgent
        if task.subagent_type:
            return await self._delegate_to_subagent(task)

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
