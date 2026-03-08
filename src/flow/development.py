"""
DevelopmentFlow - 集成开发工作流
基于 integrated-dev-workflow 构建
"""

import re
from datetime import datetime
from pathlib import Path

from .base import FlowSkill


class DevelopmentFlow(FlowSkill):
    """DevelopmentFlow - 完整的开发工作流编排

    基于 integrated-dev-workflow，实现:
    - Phase 1: Requirements & Design
    - Phase 2: Technical Planning
    - Phase 3: Implementation (TDD)
    - Phase 4: Testing & Review
    - Phase 5: Completion

    智能路由:
    - URL 检测 → 自动使用 summarize 技能
    - "如何做" / "how to" → 自动使用 find-skills 技能
    - 其他 → 正常开发流程

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

    # 智能路由模式
    URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE)

    HOW_TO_PATTERNS = [
        r"如何",
        r"怎么做",
        r"怎么写",
        r"how to",
        r"how do i",
        r"how can i",
        r"ways to",
        r"帮我找",
        r"找一个",
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
        """前置处理 - 智能路由 + 会话恢复"""

        # Step 1: 智能路由检测
        route_result = await self._smart_route(user_input, context)
        if route_result:
            # 设置路由标记，Agent 会自动使用对应技能
            context["_routed_skill"] = route_result["skill"]
            context["_route_reason"] = route_result["reason"]
            # 返回路由后的输入
            return route_result["processed_input"]

        # Step 2: 检查会话恢复
        if await self._check_session_recovery(context):
            context["_flow_phase"] = self._current_phase
            context["_session_resumed"] = True
            return user_input

        # Step 3: 初始化跟踪文件
        await self._initialize_tracking(user_input, context)

        context["_flow_phase"] = 1
        context["_session_resumed"] = False

        return user_input

    async def _smart_route(self, user_input: str, context: dict) -> dict[str, str] | None:
        """智能路由 - 检测 URL 或 how-to 模式并路由到对应技能"""

        # 检查用户意图关键词
        user_input_lower = user_input.lower()

        # 导入意图关键词 - 不路由到 summarize，让 github-import 处理
        import_keywords = [
            "导入",
            "import",
            "克隆",
            "clone",
            "下载",
            "download",
            "安装",
            "install",
            "配置成",
            "配置为",
            "设置为",
        ]

        has_import_intent = any(k in user_input_lower for k in import_keywords)

        # 1. URL 检测
        urls = self.URL_PATTERN.findall(user_input)
        if urls:
            # 如果有导入意图，路由到 github-import
            if has_import_intent:
                return None  # 让正常流程处理，github-import skill 会处理

            # 否则路由到 summarize
            url = urls[0]
            return {
                "skill": "summarize",
                "reason": "检测到 URL，自动使用 summarize 技能",
                "processed_input": f'summarize "{url}"',
            }

        # 2. How-to 模式检测 → find-skills 技能
        for pattern in self.HOW_TO_PATTERNS:
            if re.search(pattern, user_input, re.IGNORECASE):
                # 提取关键信息
                return {
                    "skill": "find-skills",
                    "reason": "检测到学习意图，自动使用 find-skills 技能",
                    "processed_input": user_input,
                }

        # 3. 技能请求检测
        skill_request_patterns = [
            (r"找.*技能", "find-skills"),
            (r"skill.*搜索", "find-skills"),
            (r"搜索.*技能", "find-skills"),
            (r"总结.*(url|网址|网页|文章)", "summarize"),
        ]

        for pattern, skill in skill_request_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "skill": skill,
                    "reason": f"检测到技能请求，自动使用 {skill} 技能",
                    "processed_input": user_input,
                }

        # 无需路由
        return None

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

    async def get_subagent_type(self, task: str) -> str | None:
        """获取合适的 SubAgent 类型"""

        # 探索/研究类型
        if any(
            k in task.lower()
            for k in [
                "search",
                "find",
                "explore",
                "research",
                "调查",
                "搜索",
                "查找",
                "研究",
                "分析",
                "what is",
                "how does",
            ]
        ):
            return "explorer"

        # 构建/实现类型
        if any(
            k in task.lower()
            for k in [
                "build",
                "create",
                "implement",
                "add",
                "develop",
                "创建",
                "实现",
                "开发",
                "新建",
                "feature",
            ]
        ):
            return "builder"

        # 审查/评审类型
        if any(
            k in task.lower()
            for k in ["review", "check", "audit", "analyze", "审查", "检查", "分析"]
        ):
            return "reviewer"

        # 测试类型
        if any(
            k in task.lower() for k in ["test", "testing", "verify", "测试", "验证", "单元测试"]
        ):
            return "tester"

        # 修复 bug 类型
        if any(k in task.lower() for k in ["fix", "bug", "error", "issue", "修复", "错误", "问题"]):
            return "fixer"

        # 重构类型
        if any(
            k in task.lower() for k in ["refactor", "optimize", "improve", "重构", "优化", "改进"]
        ):
            return "refactorer"

        # 文档类型
        if any(k in task.lower() for k in ["doc", "document", "readme", "文档", "说明"]):
            return "documenter"

        return None

    # === 私有方法 ===

    async def _check_session_recovery(self, context: dict) -> bool:
        """检查是否有之前的会话需要恢复"""

        has_files = (
            self._task_file.exists() or self._findings_file.exists() or self._progress_file.exists()
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
                content = content.replace("## Session Log", f"## Session Log{log_entry}")

            self._progress_file.write_text(content)
        except Exception:
            pass


# === 便捷函数 ===


def create_development_flow(project_root: str = ".") -> DevelopmentFlow:
    """创建 DevelopmentFlow 实例"""
    return DevelopmentFlow(project_root)
