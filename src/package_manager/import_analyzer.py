"""
Import Analyzer - LLM-driven import quality analysis

参考行业最佳实践:
- E2B: 沙箱执行 + 代码分析
- Modal: 函数签名分析
- Jina: 语义分析
- Claude Code: 结构化理解 + 意图识别
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ImportAnalysis:
    """LLM 导入分析结果"""

    quality_score: float  # 0-1 质量分数
    missing_elements: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    compatibility_issues: list[str] = field(default_factory=list)
    skill_analysis: dict[str, Any] = field(default_factory=dict)
    mcp_analysis: dict[str, Any] = field(default_factory=dict)
    subagent_analysis: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"  # low, medium, high, critical


@dataclass
class GitHubFile:
    """GitHub 文件"""

    path: str
    content: str
    is_yaml: bool
    is_json: bool


@dataclass
class FlowSkill:
    """FlowSkill 配置 - Agent 执行流程"""

    name: str
    description: str
    trigger_conditions: list[str]
    required_skills: list[str]
    required_mcps: list[str]
    required_evaluations: list[str]
    subagent_calls: list[dict[str, Any]]


class ImportAnalyzer:
    """LLM 驱动的导入质量分析器

    参考行业最佳实践:
    - E2B: 沙箱执行 + 代码分析
    - Modal: 函数签名分析
    - Jina: 语义分析
    - Claude Code: 结构化理解 + 意图识别
    """

    def __init__(self):
        self.llm_client = None
        self._init_llm_client()

    def _init_llm_client(self):
        """初始化 LLM 客户端"""
        try:
            from src.llm.unified_client import get_unified_client

            self.llm_client = get_unified_client()
        except ImportError:
            # 备用方案：使用简单规则分析
            self.llm_client = None

    async def analyze_import(
        self,
        project_structure: dict[str, Any],
        config_result: dict[str, Any],
        repo_metadata: dict[str, Any] = None,
    ) -> ImportAnalysis:
        """综合分析导入质量

        Args:
            project_structure: 项目结构分析结果
            config_result: 配置文件解析结果
            repo_metadata: 仓库元数据

        Returns:
            ImportAnalysis: 详细的分析结果
        """
        analysis = ImportAnalysis(quality_score=0.5)

        # 1. 基础结构分析
        self._analyze_structure(project_structure, analysis)

        # 2. Skills 分析
        self._analyze_skills(config_result, analysis)

        # 3. MCPs 分析
        self._analyze_mcps(config_result, analysis)

        # 4. SubAgents 分析
        self._analyze_subagents(project_structure, analysis)

        # 5. LLM 深度分析（如果可用）
        if self.llm_client:
            await self._llm_deep_analysis(project_structure, config_result, analysis, repo_metadata)
        else:
            # 规则基础分析
            self._rule_based_analysis(project_structure, config_result, analysis)

        # 6. 计算综合分数
        self._calculate_quality_score(analysis)

        # 7. 生成建议
        self._generate_recommendations(analysis)

        return analysis

    def _analyze_structure(self, structure: dict[str, Any], analysis: ImportAnalysis):
        """分析项目结构"""
        # 检查关键文件
        if not structure.get("has_claude_md"):
            analysis.missing_elements.append("CLAUDE.md - 缺少主要的 agent 指令文件")
        if not structure.get("has_agents_md"):
            analysis.missing_elements.append("AGENTS.md - 缺少 agent 定义文档")

        # 检查语言
        languages = structure.get("languages", [])
        if not languages:
            analysis.missing_elements.append("无编程语言 - 可能不是有效的代码项目")

    def _analyze_skills(self, config_result: dict[str, Any], analysis: ImportAnalysis):
        """分析 Skills 配置"""
        skills = config_result.get("skills", [])

        analysis.skill_analysis = {
            "count": len(skills),
            "names": [s.get("config", {}).get("name", "unknown") for s in skills],
            "has_skills": len(skills) > 0,
        }

        if len(skills) == 0:
            analysis.missing_elements.append("Skills - 项目没有可用的 skills")
            analysis.recommendations.append("考虑从项目的 skills/ 目录提取 skill 定义")
        elif len(skills) < 3:
            analysis.recommendations.append(
                f"项目仅有 {len(skills)} 个 skill，可能需要更多来增强能力"
            )

    def _analyze_mcps(self, config_result: dict[str, Any], analysis: ImportAnalysis):
        """分析 MCP 配置"""
        mcps = config_result.get("mcps", [])

        analysis.mcp_analysis = {
            "count": len(mcps),
            "has_mcps": len(mcps) > 0,
        }

        if len(mcps) == 0:
            analysis.recommendations.append("项目没有 MCP 服务器配置，考虑添加以扩展能力")

    def _analyze_subagents(self, structure: dict[str, Any], analysis: ImportAnalysis):
        """分析 SubAgents"""
        subagents = structure.get("subagent_prompts", [])

        analysis.subagent_analysis = {
            "count": len(subagents),
            "names": [sa.get("name", "unknown") for sa in subagents[:5]],
            "has_subagents": len(subagents) > 0,
        }

    def _rule_based_analysis(
        self,
        structure: dict[str, Any],
        config_result: dict[str, Any],
        analysis: ImportAnalysis,
    ):
        """基于规则的深度分析"""
        # 检查是否有 skills 目录但未解析
        local_path = structure.get("local_path")
        if local_path and Path(local_path).exists():
            skills_dir = Path(local_path) / "skills"
            if skills_dir.exists():
                # 统计实际 skill 数量
                skill_files = list(skills_dir.rglob("SKILL.md"))
                if len(skill_files) > 0:
                    analysis.recommendations.append(
                        f"发现 {len(skill_files)} 个 SKILL.md 文件在 skills/ 目录中，建议手动配置"
                    )

    async def _llm_deep_analysis(
        self,
        structure: dict[str, Any],
        config_result: dict[str, Any],
        analysis: ImportAnalysis,
        repo_metadata: dict[str, Any],
    ):
        """LLM 深度分析"""
        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(structure, config_result, repo_metadata)

            # 调用 LLM
            response = await self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3,
            )

            # 解析响应
            result = response.choices[0].message.content
            self._parse_llm_analysis(result, analysis)

        except Exception as e:
            analysis.recommendations.append(f"LLM 分析失败: {str(e)[:50]}")

    def _build_analysis_prompt(
        self,
        structure: dict[str, Any],
        config_result: dict[str, Any],
        repo_metadata: dict[str, Any],
    ) -> str:
        """构建分析提示"""
        languages = structure.get("languages", [])
        skills_count = len(config_result.get("skills", []))
        subagents_count = len(structure.get("subagent_prompts", []))
        mcps_count = len(config_result.get("mcps", []))

        prompt = f"""分析以下 GitHub 仓库的导入质量，并提供改进建议:

仓库信息:
- 名称: {repo_metadata.get("name", "unknown") if repo_metadata else "unknown"}
- 描述: {repo_metadata.get("description", "")[:200] if repo_metadata else ""}
- 主要语言: {languages[0] if languages else "unknown"}

当前导入状态:
- Skills: {skills_count}
- SubAgents: {subagents_count}
- MCPs: {mcps_count}
- 有 CLAUDE.md: {structure.get("has_claude_md", False)}
- 有 AGENTS.md: {structure.get("has_agents_md", False)}

请分析:
1. 是否有重要的元素被遗漏?
2. 有什么潜在兼容性问题?
3. 风险等级 (low/medium/high/critical)?
4. 具体改进建议?

请用 JSON 格式返回分析结果，包含: missing_elements, compatibility_issues, risk_level, recommendations"""

        return prompt

    def _parse_llm_analysis(self, result: str, analysis: ImportAnalysis):
        """解析 LLM 分析结果"""
        try:
            # 尝试提取 JSON
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                if "missing_elements" in data:
                    analysis.missing_elements.extend(data["missing_elements"])
                if "compatibility_issues" in data:
                    analysis.compatibility_issues.extend(data["compatibility_issues"])
                if "risk_level" in data:
                    analysis.risk_level = data["risk_level"]
                if "recommendations" in data:
                    analysis.recommendations.extend(data["recommendations"])
        except Exception:
            # 解析失败，使用原始文本作为建议
            analysis.recommendations.append(result[:500])

    def _calculate_quality_score(self, analysis: ImportAnalysis):
        """计算综合质量分数"""
        score = 1.0

        # 缺失关键元素扣分
        for missing in analysis.missing_elements:
            if "CLAUDE.md" in missing:
                score -= 0.3
            elif "Skills" in missing:
                score -= 0.2
            elif "AGENTS.md" in missing:
                score -= 0.1

        # 有积极元素加分
        if analysis.skill_analysis.get("has_skills"):
            score += 0.1
        if analysis.subagent_analysis.get("has_subagents"):
            score += 0.1

        # 兼容性问题的风险调整
        if analysis.compatibility_issues:
            score -= 0.1 * len(analysis.compatibility_issues)

        # 风险等级调整
        risk_multipliers = {"low": 1.0, "medium": 0.9, "high": 0.7, "critical": 0.5}
        score *= risk_multipliers.get(analysis.risk_level, 1.0)

        analysis.quality_score = max(0, min(1.0, score))

    def _generate_recommendations(self, analysis: ImportAnalysis):
        """生成最终建议"""
        # 添加基于分数的建议
        if analysis.quality_score < 0.5:
            analysis.recommendations.insert(0, "⚠️ 导入质量较低，建议检查缺失元素")
        elif analysis.quality_score < 0.7:
            analysis.recommendations.insert(0, "📊 导入质量中等，建议关注上述改进点")

        # 去重
        analysis.recommendations = list(set(analysis.recommendations))
