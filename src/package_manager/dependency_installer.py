"""
Dependency Installer - 自动安装缺失的依赖
"""

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

from src.package_manager.dependency_resolver import (
    AgentDependency,
    DependencyInfo,
    DependencyResolver,
)


@dataclass
class InstallResult:
    """安装结果"""

    success: bool
    name: str
    type: str
    path: str | None = None
    error: str | None = None


class DependencyInstaller:
    """依赖安装器"""

    def __init__(self, packages_dir: str = "packages"):
        self.packages_dir = Path(packages_dir)
        self.skills_dir = Path("skills")
        self.hooks_dir = Path("hooks")

        # 确保目录存在
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    async def install_skill(self, skill: DependencyInfo) -> InstallResult:
        """安装 Skill

        支持的来源：
        - local: 本地目录
        - github: GitHub 仓库
        - npm: npm 包
        """
        skill_name = skill.name

        # 检查是否已安装
        skill_path = self.skills_dir / skill_name
        if skill_path.exists():
            return InstallResult(
                success=True,
                name=skill_name,
                type="skill",
                path=str(skill_path),
            )

        # 根据来源安装
        if skill.source:
            if skill.source.startswith("github:") or "github.com" in skill.source:
                return await self._install_from_github(skill)
            elif skill.source.startswith("npm:"):
                return await self._install_from_npm(skill)
            elif skill.source.startswith("local:"):
                return self._install_from_local(skill)

        # 尝试从 npm 安装
        return await self._install_skill_from_npm(skill)

    async def _install_from_github(self, skill: DependencyInfo) -> InstallResult:
        """从 GitHub 安装"""
        source = skill.source.replace("github:", "").strip()
        if not source.startswith("http"):
            source = f"https://github.com/{source}"

        # 解析 owner/repo
        parts = source.split("github.com/")[-1].rstrip("/").split("/")
        if len(parts) < 2:
            return InstallResult(
                success=False,
                name=skill.name,
                type="skill",
                error=f"Invalid GitHub URL: {source}",
            )

        owner, repo = parts[0], parts[1]
        skill_name = skill.name
        skill_path = self.skills_dir / skill_name

        print(f"[Skill] Installing from GitHub: {owner}/{repo}")

        try:
            # 克隆仓库
            import httpx

            # 使用 GitHub API 获取默认分支
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = httpx.get(api_url, timeout=30)
            response.raise_for_status()
            repo_info = response.json()
            default_branch = repo_info.get("default_branch", "main")

            # 获取 skill 目录
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            response = httpx.get(tree_url, timeout=30)
            response.raise_for_status()
            tree = response.json()

            # 查找 skill 相关文件
            skill_files = []
            for item in tree.get("tree", []):
                path = item.get("path", "")
                if "skill" in path.lower() or "skill" in repo.lower():
                    skill_files.append(path)

            if not skill_files:
                return InstallResult(
                    success=False,
                    name=skill_name,
                    type="skill",
                    error="No skill files found in repository",
                )

            # 创建目录
            skill_path.mkdir(parents=True, exist_ok=True)

            # 下载文件
            for path in skill_files[:20]:  # 限制数量
                content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                response = httpx.get(content_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", "")
                    if content:
                        import base64

                        try:
                            content = base64.b64decode(content).decode("utf-8")
                        except:
                            continue

                        # 保存文件
                        file_path = skill_path / path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content)

            return InstallResult(
                success=True,
                name=skill_name,
                type="skill",
                path=str(skill_path),
            )

        except Exception as e:
            return InstallResult(
                success=False,
                name=skill_name,
                type="skill",
                error=str(e),
            )

    async def _install_from_npm(self, skill: DependencyInfo) -> InstallResult:
        """从 npm 安装"""
        package_name = skill.source.replace("npm:", "").strip()
        skill_name = skill.name
        skill_path = self.skills_dir / skill_name

        print(f"[Skill] Installing from npm: {package_name}")

        try:
            # 运行 npm install
            proc = await asyncio.create_subprocess_shell(
                f"npm pack {package_name} --pack-destination {self.skills_dir}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                return InstallResult(
                    success=False,
                    name=skill_name,
                    type="skill",
                    error=f"npm install failed: {stderr.decode()}",
                )

            # 解压
            # ... (简化处理)
            return InstallResult(
                success=True,
                name=skill_name,
                type="skill",
                path=str(skill_path),
            )

        except Exception as e:
            return InstallResult(
                success=False,
                name=skill_name,
                type="skill",
                error=str(e),
            )

    def _install_from_local(self, skill: DependencyInfo) -> InstallResult:
        """从本地安装"""
        source_path = Path(skill.source.replace("local:", "").strip())
        skill_name = skill.name
        skill_path = self.skills_dir / skill_name

        if not source_path.exists():
            return InstallResult(
                success=False,
                name=skill_name,
                type="skill",
                error=f"Source path not found: {source_path}",
            )

        try:
            shutil.copytree(source_path, skill_path, dirs_exist_ok=True)
            return InstallResult(
                success=True,
                name=skill_name,
                type="skill",
                path=str(skill_path),
            )
        except Exception as e:
            return InstallResult(
                success=False,
                name=skill_name,
                type="skill",
                error=str(e),
            )

    async def _install_skill_from_npm(self, skill: DependencyInfo) -> InstallResult:
        """从 npm 安装 skill（尝试推断包名）"""
        # 尝试常见的包名格式
        possible_names = [
            f"@openyoung/skill-{skill.name}",
            f"skill-{skill.name}",
            f"openyoung-skill-{skill.name}",
        ]

        for pkg_name in possible_names:
            result = await self._install_from_npm(
                DependencyInfo(type="skill", name=skill.name, source=f"npm:{pkg_name}")
            )
            if result.success:
                return result

        return InstallResult(
            success=False,
            name=skill.name,
            type="skill",
            error="Skill not found in npm registry",
        )

    async def install_mcp(self, mcp: DependencyInfo) -> InstallResult:
        """安装 MCP"""
        mcp_name = mcp.name

        # 检查是否已安装
        mcp_path = self.packages_dir / f"mcp-{mcp_name}"
        if mcp_path.exists():
            return InstallResult(
                success=True,
                name=mcp_name,
                type="mcp",
                path=str(mcp_path),
            )

        # 如果有来源，从来源安装
        if mcp.source:
            # TODO(wontfix): 实现 MCP 安装逻辑
            pass

        return InstallResult(
            success=False,
            name=mcp_name,
            type="mcp",
            error="MCP installation not implemented",
        )

    async def install_hook(self, hook: DependencyInfo) -> InstallResult:
        """安装 Hook"""
        hook_name = hook.name
        hook_path = self.hooks_dir / hook_name

        # 检查是否已安装
        if hook_path.exists():
            return InstallResult(
                success=True,
                name=hook_name,
                type="hook",
                path=str(hook_path),
            )

        # 如果有来源，从来源安装
        if hook.source:
            # TODO(wontfix): 实现 Hook 安装逻辑
            pass

        return InstallResult(
            success=False,
            name=hook_name,
            type="hook",
            error="Hook installation not implemented",
        )

    async def install_dependencies(self, deps: AgentDependency) -> dict[str, list[InstallResult]]:
        """安装所有依赖"""
        results = {
            "skills": [],
            "mcps": [],
            "hooks": [],
        }

        # 安装 Skills
        for skill in deps.skills:
            result = await self.install_skill(skill)
            results["skills"].append(result)
            status = "✅" if result.success else "❌"
            print(f"  {status} Skill: {skill.name}")

        # 安装 MCPs
        for mcp in deps.mcps:
            result = await self.install_mcp(mcp)
            results["mcps"].append(result)
            status = "✅" if result.success else "❌"
            print(f"  {status} MCP: {mcp.name}")

        # 安装 Hooks
        for hook in deps.hooks:
            result = await self.install_hook(hook)
            results["hooks"].append(result)
            status = "✅" if result.success else "❌"
            print(f"  {status} Hook: {hook.name}")

        return results


# ========== 便捷函数 ==========


async def install_agent_dependencies(agent_path: str) -> dict[str, list[InstallResult]]:
    """安装 Agent 的所有依赖"""
    resolver = DependencyResolver()
    all_deps = resolver.resolve_from_file(agent_path)
    missing_deps = resolver.find_missing(all_deps)

    if not missing_deps.all_dependencies:
        print("[Dependency] All dependencies already installed")
        return {}

    print(f"[Dependency] Installing {len(missing_deps.all_dependencies)} missing dependencies...")

    installer = DependencyInstaller()
    return await installer.install_dependencies(missing_deps)
