"""
Enhanced GitHub Importer - Main importer orchestrator

Handles git clone + agent analysis for GitHub, GitLab, Gitee repositories.
Uses modular components for fetching, analysis, and config generation.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Any

from .agent_config_builder import AgentConfigBuilder
from .flowskill_generator import FlowSkillGenerator
from .git_importer import GitImporterFactory
from .github_fetcher import GitHubFetcher
from .import_analyzer import ImportAnalyzer
from .project_analyzer import ProjectAnalyzer
from .subagent_discovery import SubAgentDiscovery


class EnhancedGitHubImporter:
    """Enhanced GitHub/GitLab/Gitee repository importer"""

    def __init__(self, packages_dir: str = "packages", subagents_dir: str = "subagents"):
        self.packages_dir = Path(packages_dir)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.subagents_dir = Path(subagents_dir)
        self.subagents_dir.mkdir(parents=True, exist_ok=True)

        self.temp_dir = Path("/tmp") / "openyoung_imports"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.fetcher = GitHubFetcher()
        self.analyzer = ProjectAnalyzer()
        self.subagent_discovery = SubAgentDiscovery()
        self.flowskill_generator = FlowSkillGenerator()
        self.config_builder = AgentConfigBuilder(packages_dir, subagents_dir)

    async def import_from_url(
        self,
        url: str,
        agent_name: str = None,
        use_git_clone: bool = True,
        analyze_with_agent: bool = True,
        validate: bool = True,
        lazy_clone: bool = False,
    ) -> dict[str, Any]:
        """Import from Git/GitLab/Gitee URL

        Args:
            url: Repository URL (GitHub/GitLab/Gitee)
            agent_name: Optional agent name
            use_git_clone: Whether to use git clone (more complete)
            analyze_with_agent: Whether to analyze code with agent
            validate: Whether to validate after import
            lazy_clone: Whether to delay clone (metadata only)

        Returns:
            Import result
        """
        # Use generic Git importer factory
        factory_result = GitImporterFactory.from_url(url)
        if not factory_result:
            return {"error": f"Unsupported repository URL: {url}"}

        importer, host, owner, repo = factory_result

        if not agent_name:
            agent_name = repo

        print(f"[{host.capitalize()}] Importing {owner}/{repo} as '{agent_name}'...")

        # Step 1: Get repository metadata (API first, fast)
        metadata = self.fetcher.fetch_repo_metadata(host, owner, repo)
        if metadata:
            print(
                f"[{host.capitalize()}] Repository: {metadata.get('name', repo)} - {metadata.get('description', '')[:50]}..."
            )

        # Step 2: If lazy_clone, return metadata only
        if lazy_clone:
            return {
                "agent_name": agent_name,
                "host": host,
                "owner": owner,
                "repo": repo,
                "metadata": metadata,
                "status": "lazy_mode",
                "message": "Use execute_imported_agent() to trigger full clone",
            }

        # Step 3: Get repository files
        local_path = None
        # Save to packages directory under agent name
        agent_repo_dir = self.packages_dir / agent_name / "original"
        agent_repo_dir.mkdir(parents=True, exist_ok=True)

        if use_git_clone:
            temp_path = importer.clone(owner, repo)
            if not temp_path:
                return {"error": "Failed to clone repository"}

            for item in temp_path.iterdir():
                dest = agent_repo_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
            local_path = agent_repo_dir
            print(f"[{host.capitalize()}] Cloned to: {local_path}")
        else:
            # API mode needs subclass implementation
            local_path = self.fetcher.fetch_repo_files(host, owner, repo)
            if not local_path:
                return {"error": "Failed to fetch repository files"}

        # Step 4: Analyze project structure
        project_structure = self.analyzer.analyze_structure(local_path)
        print(f"[{host.capitalize()}] Project structure: {project_structure}")

        # Discover subagents
        project_structure["subagent_prompts"] = self.subagent_discovery.discover_all(local_path)

        # Step 5: Generate FlowSkill (if agent analysis enabled)
        flowskill = None
        if analyze_with_agent:
            flowskill = self.flowskill_generator.generate(local_path, project_structure, repo)
            if flowskill:
                print(f"[{host.capitalize()}] Generated FlowSkill: {flowskill.name}")

        # Step 6: Parse configuration files
        config_result = self.analyzer.parse_configs(local_path)

        # Step 7: Create agent config
        result = self.config_builder.build(
            host, owner, repo, agent_name, project_structure, flowskill, config_result
        )

        # Step 8: Import validation
        if validate:
            validation_result = self._validate_import(agent_name, project_structure, config_result)
            result["validation"] = validation_result

        # Step 9: LLM deep analysis (if enabled)
        if analyze_with_agent:
            llm_analysis = await self._run_llm_analysis(project_structure, config_result, metadata)
            result["llm_analysis"] = llm_analysis

            # Print analysis results
            if llm_analysis:
                print(f"[LLM Analysis] Quality Score: {llm_analysis.get('quality_score', 0):.2f}")
                missing = llm_analysis.get("missing_elements", [])
                if missing:
                    print(f"[LLM Analysis] Missing: {', '.join(missing[:3])}")
                recommendations = llm_analysis.get("recommendations", [])
                if recommendations:
                    print(f"[LLM Analysis] Recommendation: {recommendations[0][:80]}")

        # Save local_path for later use
        result["local_path"] = local_path
        result["host"] = host
        result["owner"] = owner
        result["repo"] = repo

        return result

    async def execute_imported_agent(self, agent_name: str, task: str) -> str:
        """Execute imported agent

        Args:
            agent_name: Agent name
            task: Task description

        Returns:
            Execution result
        """
        from src.agents.young_agent import YoungAgent
        from src.core.types import AgentConfig, AgentMode
        from src.package_manager.agent_loader import AgentLoader

        print(f"[Execute] Running agent '{agent_name}' with task: {task[:50]}...")

        # 1. Load agent config
        loader = AgentLoader()
        try:
            config = loader.load_agent(agent_name)
        except Exception:
            # If no config, create default
            config = AgentConfig(
                name=agent_name,
                mode=AgentMode.PRIMARY,
            )

        # 2. Create YoungAgent instance
        agent = YoungAgent(config)

        # 3. Execute task
        result = await agent.run(task)

        # 4. Return result
        return result

    def _validate_import(
        self, agent_name: str, structure: dict[str, Any], config_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate import result - quality gate"""
        validation = {
            "passed": True,
            "score": 1.0,
            "warnings": [],
            "errors": [],
        }

        # Check project structure - 0.2 deduction per missing item
        if not structure.get("languages"):
            validation["warnings"].append("No programming languages detected")
            validation["score"] -= 0.2

        if not structure.get("has_claude_md"):
            validation["warnings"].append("No CLAUDE.md found - agent behavior may not be optimal")
            validation["score"] -= 0.2

        # Check for SubAgents (from any source)
        subagents = structure.get("subagent_prompts", [])
        if not subagents:
            validation["warnings"].append("No sub-agents found from roles/, agents/, or AGENTS.md")
            validation["score"] -= 0.1

        # Check config files - 0.15 deduction if missing
        if not config_result.get("skills") and not config_result.get("mcps"):
            validation["warnings"].append("No skills or MCPs configured")
            validation["score"] -= 0.15

        # Ensure score doesn't go below 0
        validation["score"] = max(0, validation["score"])

        # Quality threshold check
        if validation["score"] < 0.6:
            validation["passed"] = False
            validation["errors"].append(
                f"Quality score {validation['score']:.2f} below threshold 0.6"
            )

        # Add quality report
        validation["report"] = {
            "languages": structure.get("languages", []),
            "has_claude_md": structure.get("has_claude_md", False),
            "has_agents_md": structure.get("has_agents_md", False),
            "skills_count": len(config_result.get("skills", [])),
            "mcps_count": len(config_result.get("mcps", [])),
        }

        return validation

    async def _run_llm_analysis(
        self,
        project_structure: dict[str, Any],
        config_result: dict[str, Any],
        repo_metadata: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Run LLM deep analysis"""
        try:
            analyzer = ImportAnalyzer()
            analysis = await analyzer.analyze_import(
                project_structure,
                config_result,
                repo_metadata,
            )

            # Convert to dict for return
            return {
                "quality_score": analysis.quality_score,
                "missing_elements": analysis.missing_elements,
                "recommendations": analysis.recommendations,
                "compatibility_issues": analysis.compatibility_issues,
                "skill_analysis": analysis.skill_analysis,
                "mcp_analysis": analysis.mcp_analysis,
                "subagent_analysis": analysis.subagent_analysis,
                "risk_level": analysis.risk_level,
            }
        except Exception as e:
            return {"error": str(e), "quality_score": 0.5}


def import_github_enhanced(
    github_url: str,
    packages_dir: str = "packages",
    subagents_dir: str = "subagents",
    use_git_clone: bool = True,
    analyze_with_agent: bool = True,
) -> dict[str, Any]:
    """Import from GitHub (enhanced CLI entry)"""
    importer = EnhancedGitHubImporter(packages_dir, subagents_dir)
    return asyncio.run(
        importer.import_from_url(
            github_url, use_git_clone=use_git_clone, analyze_with_agent=analyze_with_agent
        )
    )
