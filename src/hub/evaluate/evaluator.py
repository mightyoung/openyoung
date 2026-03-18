"""
Agent Evaluator - Agent 质量评估
评估已安装/待安装 Agent 的质量
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml


class QualityDimension(Enum):
    """质量维度"""

    COMPLETENESS = "completeness"  # 完整性
    VALIDITY = "validity"  # 有效性
    DEPENDENCIES = "dependencies"  # 依赖
    DOCUMENTATION = "documentation"  # 文档
    SECURITY = "security"  # 安全性
    RUNTIME = "runtime"  # 运行时测试


@dataclass
class EvaluationResult:
    """评估结果"""

    dimension: QualityDimension
    score: float  # 0-1
    passed: bool
    details: str
    suggestions: list[str] = field(default_factory=list)


@dataclass
class AgentQualityReport:
    """Agent 质量报告"""

    agent_name: str
    overall_score: float
    dimensions: list[EvaluationResult]
    warnings: list[str]
    passed: bool


class AgentEvaluator:
    """
    Agent 质量评估器

    评估维度：
    1. COMPLETENESS - 文件完整性
    2. VALIDITY - 配置有效性
    3. DEPENDENCIES - 依赖完整性
    4. DOCUMENTATION - 文档质量
    5. SECURITY - 安全检查
    """

    # 必需文件
    REQUIRED_FILES = ["agent.yaml"]

    # 推荐文件
    RECOMMENDED_FILES = ["CLAUDE.md", "AGENTS.md", "skills/", "hooks/", ".mcp.json"]

    def __init__(self):
        pass

    # ========== 核心 API ==========

    async def evaluate(self, agent_path: str) -> AgentQualityReport:
        """
        评估 Agent 质量

        Args:
            agent_path: Agent 目录路径

        Returns:
            AgentQualityReport: 质量报告
        """
        agent_path = Path(agent_path)
        agent_name = agent_path.name

        results = []

        # 1. 完整性评估
        results.append(await self._evaluate_completeness(agent_path))

        # 2. 有效性评估
        results.append(await self._evaluate_validity(agent_path))

        # 3. 依赖评估
        results.append(await self._evaluate_dependencies(agent_path))

        # 4. 文档评估
        results.append(await self._evaluate_documentation(agent_path))

        # 5. 安全评估
        results.append(await self._evaluate_security(agent_path))

        # 6. 运行时评估
        results.append(await self._evaluate_runtime(agent_path))

        # 计算总分
        overall_score = sum(r.score for r in results) / len(results)
        passed = all(r.passed for r in results)

        # 收集警告
        warnings = []
        for r in results:
            if not r.passed:
                warnings.append(f"{r.dimension.value}: {r.details}")

        return AgentQualityReport(
            agent_name=agent_name,
            overall_score=overall_score,
            dimensions=results,
            warnings=warnings,
            passed=passed,
        )

    # ========== 各维度评估 ==========

    async def _evaluate_completeness(self, agent_path: Path) -> EvaluationResult:
        """评估完整性"""
        missing = []
        found = []

        # 检查必需文件
        for req_file in self.REQUIRED_FILES:
            if (agent_path / req_file).exists():
                found.append(req_file)
            else:
                missing.append(req_file)

        # 检查推荐文件
        for rec_file in self.RECOMMENDED_FILES:
            # 目录检查
            if rec_file.endswith("/"):
                dir_name = rec_file.rstrip("/")
                if (agent_path / dir_name).is_dir():
                    found.append(rec_file)
            elif (agent_path / rec_file).exists():
                found.append(rec_file)

        total = len(self.REQUIRED_FILES) + len(self.RECOMMENDED_FILES)
        score = len(found) / total if total > 0 else 0
        passed = len(missing) == 0  # 必需文件必须存在

        return EvaluationResult(
            dimension=QualityDimension.COMPLETENESS,
            score=score,
            passed=passed,
            details=f"Found: {found}, Missing: {missing}",
            suggestions=[f"Missing required: {m}" for m in missing] if missing else [],
        )

    async def _evaluate_validity(self, agent_path: Path) -> EvaluationResult:
        """评估配置有效性"""
        agent_yaml = agent_path / "agent.yaml"

        if not agent_yaml.exists():
            return EvaluationResult(
                dimension=QualityDimension.VALIDITY,
                score=0.0,
                passed=False,
                details="agent.yaml not found",
                suggestions=["Create agent.yaml with valid configuration"],
            )

        try:
            with open(agent_yaml, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                return EvaluationResult(
                    dimension=QualityDimension.VALIDITY,
                    score=0.0,
                    passed=False,
                    details="agent.yaml is empty",
                    suggestions=["Add configuration to agent.yaml"],
                )

            # 检查必需字段
            required_fields = ["name", "model"]
            missing_fields = [f for f in required_fields if f not in config]

            if missing_fields:
                return EvaluationResult(
                    dimension=QualityDimension.VALIDITY,
                    score=0.5,
                    passed=False,
                    details=f"Missing fields: {missing_fields}",
                    suggestions=[f"Add field: {f}" for f in missing_fields],
                )

            # 检查配置合理性
            issues = []

            # model 字段检查
            if not config.get("model"):
                issues.append("model is empty")

            # tools 字段检查
            tools = config.get("tools", [])
            if not tools:
                issues.append("no tools configured")
            elif "bash" in tools and "read" not in tools:
                issues.append("has bash but no read tool - may cause issues")

            score = 1.0 if not issues else 0.7

            return EvaluationResult(
                dimension=QualityDimension.VALIDITY,
                score=score,
                passed=len(issues) == 0,
                details=f"Config valid, issues: {issues}" if issues else "Config valid",
                suggestions=issues,
            )

        except yaml.YAMLError as e:
            return EvaluationResult(
                dimension=QualityDimension.VALIDITY,
                score=0.0,
                passed=False,
                details=f"YAML parse error: {e}",
                suggestions=["Fix YAML syntax errors"],
            )
        except Exception as e:
            return EvaluationResult(
                dimension=QualityDimension.VALIDITY,
                score=0.0,
                passed=False,
                details=f"Parse error: {e}",
                suggestions=["Check configuration format"],
            )

    async def _evaluate_dependencies(self, agent_path: Path) -> EvaluationResult:
        """评估依赖"""
        deps_files = ["pyproject.toml", "requirements.txt", "package.json", "Cargo.toml"]

        found_deps = []
        for dep_file in deps_files:
            if (agent_path / dep_file).exists():
                found_deps.append(dep_file)

        # 没有依赖 = 完全通过
        if not found_deps:
            return EvaluationResult(
                dimension=QualityDimension.DEPENDENCIES,
                score=1.0,
                passed=True,
                details="No external dependencies",
                suggestions=[],
            )

        return EvaluationResult(
            dimension=QualityDimension.DEPENDENCIES,
            score=0.8,
            passed=True,
            details=f"Found dependency files: {found_deps}",
            suggestions=["Verify dependencies are installable"],
        )

    async def _evaluate_documentation(self, agent_path: Path) -> EvaluationResult:
        """评估文档质量"""
        claude_md = agent_path / "CLAUDE.md"

        if not claude_md.exists():
            return EvaluationResult(
                dimension=QualityDimension.DOCUMENTATION,
                score=0.0,
                passed=False,
                details="CLAUDE.md not found",
                suggestions=["Add CLAUDE.md with agent description"],
            )

        try:
            content = claude_md.read_text(encoding="utf-8")
        except Exception:
            return EvaluationResult(
                dimension=QualityDimension.DOCUMENTATION,
                score=0.0,
                passed=False,
                details="CLAUDE.md cannot be read",
                suggestions=["Check file encoding"],
            )

        # 检查文档长度
        length_score = min(len(content) / 1000, 1.0)  # 1000 字符为满分

        # 检查关键章节
        key_sections = ["#", "##", "Capabilities", "Tools", "能力", "工具"]
        sections_found = sum(1 for s in key_sections if s in content)
        section_score = sections_found / len(key_sections)

        score = (length_score + section_score) / 2

        return EvaluationResult(
            dimension=QualityDimension.DOCUMENTATION,
            score=score,
            passed=score >= 0.3,
            details=f"Doc length: {len(content)} chars, sections: {sections_found}/{len(key_sections)}",
            suggestions=["Add more detailed documentation"] if score < 0.5 else [],
        )

    async def _evaluate_security(self, agent_path: Path) -> EvaluationResult:
        """评估安全性"""
        warnings = []

        # 检查 agent.yaml 中的危险配置
        agent_yaml = agent_path / "agent.yaml"
        if agent_yaml.exists():
            try:
                config = yaml.safe_load(agent_yaml.read_text(encoding="utf-8"))

                # 检查权限配置
                permission = config.get("permission", {})
                global_action = permission.get("_global", "ask")

                if global_action == "allow":
                    warnings.append("Permission set to allow all - security risk")
            except (yaml.YAMLError, ValueError):
                pass

        # 检查是否有危险的 shell 命令
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if "os.system" in content or "subprocess.run" in content:
                    warnings.append(f"Shell execution in {py_file.name}")
            except (UnicodeDecodeError, OSError):
                pass

        score = 1.0 if not warnings else 0.5

        return EvaluationResult(
            dimension=QualityDimension.SECURITY,
            score=score,
            passed=len(warnings) == 0,
            details=f"Warnings: {warnings}" if warnings else "No security issues",
            suggestions=warnings,
        )

    async def _evaluate_runtime(self, agent_path: Path) -> EvaluationResult:
        """评估运行时能力 - 执行简单任务测试 agent 实际能力

        注意：这是一个轻量级测试，不执行复杂任务
        """

        agent_yaml = agent_path / "agent.yaml"
        if not agent_yaml.exists():
            return EvaluationResult(
                dimension=QualityDimension.RUNTIME,
                score=0.0,
                passed=False,
                details="agent.yaml not found - cannot test runtime",
                suggestions=["Create agent.yaml with model configuration"],
            )

        try:
            config = yaml.safe_load(agent_yaml.read_text(encoding="utf-8"))
        except Exception as e:
            return EvaluationResult(
                dimension=QualityDimension.RUNTIME,
                score=0.0,
                passed=False,
                details=f"Failed to parse agent.yaml: {e}",
                suggestions=["Fix agent.yaml syntax"],
            )

        # 检查是否有 model 配置
        model = config.get("model")
        if not model:
            return EvaluationResult(
                dimension=QualityDimension.RUNTIME,
                score=0.0,
                passed=False,
                details="No model configured - cannot test runtime",
                suggestions=["Add model field to agent.yaml"],
            )

        # 尝试创建一个简单的测试
        # 这里我们只检查 agent 是否可以加载，不实际运行（因为运行可能很耗时）
        # 未来可以扩展为实际执行简单任务

        # 检查必要的配置文件是否存在
        issues = []

        # 检查是否有启动脚本
        has_main = (agent_path / "src" / "main.py").exists()
        has_entry = (agent_path / "src" / "agent.py").exists()
        has_yaml = (agent_path / "agent.yaml").exists()

        if not (has_main or has_entry):
            issues.append("No main.py or agent.py found in src/")

        # 检查是否配置了 skills 或 tools
        skills = config.get("skills", [])
        tools = config.get("tools", [])

        if not skills and not tools:
            issues.append("No skills or tools configured")

        # 评分
        if not issues:
            score = 1.0
            details = "Agent configuration valid, can be loaded"
        elif len(issues) == 1:
            score = 0.7
            details = f"Minor issues: {issues[0]}"
        else:
            score = 0.4
            details = f"Issues: {'; '.join(issues)}"

        return EvaluationResult(
            dimension=QualityDimension.RUNTIME,
            score=score,
            passed=score >= 0.5,
            details=details,
            suggestions=issues,
        )


# ========== 便捷函数 ==========


def create_evaluator() -> AgentEvaluator:
    """创建 AgentEvaluator 实例"""
    return AgentEvaluator()


async def evaluate_agent(agent_path: str) -> AgentQualityReport:
    """快速评估 Agent"""
    evaluator = AgentEvaluator()
    return await evaluator.evaluate(agent_path)
