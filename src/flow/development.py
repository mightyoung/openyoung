"""
DevelopmentFlow - 集成开发工作流
基于 integrated-dev-workflow 构建
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from .base import FlowSkill


class DevelopmentFlow(FlowSkill):
    """DevelopmentFlow - 完整的开发工作流编排

    基于 integrated-dev-workflow，实现:
    - Phase 1: Requirements & Design
    - Phase 2: Technical Planning
    - Phase 3: Implementation (TDD)
    - Phase 4: Testing & Review
    - Phase 5: Completion

    文件跟踪:
    - task_plan.md - 任务计划和进度
    - findings.md - 研究和决策
    - progress.md - 会话日志和测试结果
    """

    TRIGGER_PATTERNS = [
        "build",
        "implement",
        "create",
        "add",
        "develop",
        "新建",
        "实现",
        "创建",
        "开发",
        "feature",
        "refactor",
        "fix",
        "bug",
    ]

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self._current_phase = 1
        self._task_file = self.project_root / "task_plan.md"
        self._findings_file = self.project_root / "findings.md"
        self._progress_file = self.project_root / "progress.md"

    @property
    def name(self) -> str:
        return "development"

    @property
    def description(self) -> str:
        return "完整的开发工作流: 需求→规划→实现→测试→完成"

    @property
    def trigger_patterns(self) -> list[str]:
        return self.TRIGGER_PATTERNS

    async def pre_process(self, user_input: str, context: dict) -> str:
        """前置处理 - 检查会话恢复并初始化"""

        # Step 1: 检查会话恢复
        if await self._check_session_recovery(context):
            context["_flow_phase"] = self._current_phase
            context["_session_resumed"] = True
            return user_input

        # Step 2: 初始化跟踪文件
        await self._initialize_tracking(user_input, context)

        context["_flow_phase"] = 1
        context["_session_resumed"] = False

        return user_input

    async def post_process(self, agent_output: str, context: dict) -> str:
        """后置处理 - 更新进度"""

        phase = context.get("_flow_phase", 1)

        # 检查是否需要进入下一阶段
        if self._should_advance_phase(agent_output, context):
            phase += 1
            context["_flow_phase"] = min(phase, 5)

            # 更新任务文件
            await self._update_phase_progress(phase, context)

        # 记录到 progress.md
        await self._log_progress(agent_output, context)

        return agent_output

    async def should_delegate(self, task: str, context: dict) -> bool:
        """判断是否需要委托"""

        # 复杂任务需要分解
        keywords = ["complex", "multiple", "several", "复杂", "多个"]
        return any(k in task.lower() for k in keywords)

    async def get_subagent_type(self, task: str) -> Optional[str]:
        """获取合适的 SubAgent 类型"""

        if any(
            k in task.lower() for k in ["search", "find", "explore", "搜索", "查找"]
        ):
            return "explore"
        elif any(
            k in task.lower() for k in ["build", "create", "implement", "创建", "实现"]
        ):
            return "builder"
        elif any(k in task.lower() for k in ["review", "review", "审查"]):
            return "reviewer"

        return "general"

    # === 私有方法 ===

    async def _check_session_recovery(self, context: dict) -> bool:
        """检查是否有之前的会话需要恢复"""

        has_files = (
            self._task_file.exists()
            or self._findings_file.exists()
            or self._progress_file.exists()
        )

        if has_files:
            # 读取当前阶段
            try:
                if self._task_file.exists():
                    content = self._task_file.read_text()
                    match = re.search(r"Phase (\d+)", content)
                    if match:
                        self._current_phase = int(match.group(1))
            except Exception:
                pass

        return has_files

    async def _initialize_tracking(self, user_input: str, context: dict):
        """初始化跟踪文件"""

        timestamp = datetime.now().isoformat()

        # task_plan.md
        if not self._task_file.exists():
            task_content = f"""# Task Plan

## Goal
{user_input}

## Phases
- [ ] Phase 1: Requirements & Design
- [ ] Phase 2: Technical Planning
- [ ] Phase 3: Implementation
- [ ] Phase 4: Testing & Review
- [ ] Phase 5: Completion

## Current Phase
Phase 1: Requirements & Design

## Tasks (Phase 1)
- [ ] Define requirements with user
- [ ] Create specification
- [ ] Review and approve spec

## Decisions Made
-

## Blockers
-
"""
            self._task_file.write_text(task_content)

        # findings.md
        if not self._findings_file.exists():
            findings_content = """# Findings

## Research
-

## Technical Decisions
-

## Notes
-
"""
            self._findings_file.write_text(findings_content)

        # progress.md
        if not self._progress_file.exists():
            progress_content = f"""# Progress

## Session Log
- Started: {timestamp}
- Created tracking files

## Test Results
| Test | Status |
|------|--------|

## Errors Encountered
| Error | Resolution |
|-------|------------|
"""
            self._progress_file.write_text(progress_content)

    def _should_advance_phase(self, agent_output: str, context: dict) -> bool:
        """判断是否应该进入下一阶段"""

        phase_keywords = {
            1: ["requirement", "spec", "design", "需求", "设计", "specification"],
            2: ["plan", "task", "breakdown", "规划", "任务", "分解"],
            3: ["implement", "code", "complete", "完成", "实现", "写完"],
            4: ["test", "review", "verify", "测试", "审查", "验证"],
            5: ["merge", "pr", "done", "完成", "合并"],
        }

        current_phase = context.get("_flow_phase", 1)
        keywords = phase_keywords.get(current_phase, [])

        return any(k in agent_output.lower() for k in keywords)

    async def _update_phase_progress(self, phase: int, context: dict):
        """更新阶段进度"""

        if not self._task_file.exists():
            return

        phase_names = {
            1: "Phase 1: Requirements & Design",
            2: "Phase 2: Technical Planning",
            3: "Phase 3: Implementation",
            4: "Phase 4: Testing & Review",
            5: "Phase 5: Completion",
        }

        try:
            content = self._task_file.read_text()

            # 更新当前阶段标记
            old_phase = f"## Current Phase\n{phase_names.get(phase - 1, '')}"
            new_phase = f"## Current Phase\n{phase_names.get(phase, '')}"

            content = content.replace(old_phase, new_phase)

            self._task_file.write_text(content)
        except Exception:
            pass

    async def _log_progress(self, agent_output: str, context: dict):
        """记录进度到 progress.md"""

        if not self._progress_file.exists():
            return

        try:
            content = self._progress_file.read_text()

            timestamp = datetime.now().isoformat()
            log_entry = f"\n- {timestamp}: {agent_output[:100]}..."

            # 追加到 Session Log
            if "## Session Log" in content:
                content = content.replace(
                    "## Session Log", f"## Session Log{log_entry}"
                )

            self._progress_file.write_text(content)
        except Exception:
            pass


# === 便捷函数 ===


def create_development_flow(project_root: str = ".") -> DevelopmentFlow:
    """创建 DevelopmentFlow 实例"""
    return DevelopmentFlow(project_root)
