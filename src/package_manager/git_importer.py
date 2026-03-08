"""
Git Importer - 通用 Git 仓库导入器接口
支持 GitHub、GitLab、Gitee 等 git 仓库
"""

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path


class GitImporter(ABC):
    """通用 Git 仓库导入器抽象基类"""

    # 支持的仓库类型
    SUPPORTED_HOSTS = ["github", "gitlab", "gitee", "bitbucket"]

    def __init__(self, temp_dir: str = "/tmp/openyoung_imports"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_host_name(self) -> str:
        """获取仓库主机名"""
        pass

    @abstractmethod
    def parse_url(self, url: str) -> tuple[str, str, str] | None:
        """解析仓库 URL

        Returns:
            Tuple[host, owner, repo] 或 None
        """
        pass

    @abstractmethod
    def get_clone_url(self, owner: str, repo: str) -> str:
        """获取克隆 URL"""
        pass

    @abstractmethod
    def get_api_url(self, owner: str, repo: str) -> str:
        """获取 API URL"""
        pass

    def clone(self, owner: str, repo: str, branch: str = "main") -> Path | None:
        """克隆仓库到本地"""
        clone_url = self.get_clone_url(owner, repo)
        local_path = self.temp_dir / f"{self.get_host_name()}_{owner}_{repo}"

        # 如果已存在，先删除
        if local_path.exists():
            shutil.rmtree(local_path)

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, clone_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return local_path
            else:
                print(f"[GitImporter] Clone failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"[GitImporter] Clone error: {e}")
            return None

    def get_file_content(self, local_path: Path, file_path: str) -> str | None:
        """从本地克隆获取文件内容"""
        full_path = local_path / file_path
        if full_path.exists():
            try:
                return full_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[GitImporter] Read file error: {e}")
                return None
        return None

    def list_files(self, local_path: Path, pattern: str = "**/*") -> list:
        """列出仓库中的文件"""
        if not local_path.exists():
            return []
        return [str(p.relative_to(local_path)) for p in local_path.rglob(pattern)]


class GitHubImporter(GitImporter):
    """GitHub 仓库导入器"""

    def __init__(self, temp_dir: str = "/tmp/openyoung_imports"):
        super().__init__(temp_dir)
        self.host = "github.com"

    def get_host_name(self) -> str:
        return "github"

    def parse_url(self, url: str) -> tuple[str, str, str] | None:
        """解析 GitHub URL"""
        url = url.strip().rstrip("/")

        # 支持多种格式
        # https://github.com/owner/repo
        # http://github.com/owner/repo
        # github.com/owner/repo
        # owner/repo

        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            # 去除 .git 后缀
            if repo.endswith(".git"):
                repo = repo[:-4]
            return self.host, owner, repo

        return None

    def get_clone_url(self, owner: str, repo: str) -> str:
        return f"https://github.com/{owner}/{repo}.git"

    def get_api_url(self, owner: str, repo: str) -> str:
        return f"https://api.github.com/repos/{owner}/{repo}"


class GitLabImporter(GitImporter):
    """GitLab 仓库导入器"""

    def __init__(self, temp_dir: str = "/tmp/openyoung_imports"):
        super().__init__(temp_dir)
        self.host = "gitlab.com"

    def get_host_name(self) -> str:
        return "gitlab"

    def parse_url(self, url: str) -> tuple[str, str, str] | None:
        """解析 GitLab URL"""
        url = url.strip().rstrip("/")

        if "gitlab.com" in url:
            parts = url.split("gitlab.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            return self.host, owner, repo

        return None

    def get_clone_url(self, owner: str, repo: str) -> str:
        return f"https://gitlab.com/{owner}/{repo}.git"

    def get_api_url(self, owner: str, repo: str) -> str:
        # URL 编码 owner/repo
        import urllib.parse
        encoded = urllib.parse.quote(f"{owner}/{repo}")
        return f"https://gitlab.com/api/v4/projects/{encoded}"


class GiteeImporter(GitImporter):
    """Gitee 仓库导入器"""

    def __init__(self, temp_dir: str = "/tmp/openyoung_imports"):
        super().__init__(temp_dir)
        self.host = "gitee.com"

    def get_host_name(self) -> str:
        return "gitee"

    def parse_url(self, url: str) -> tuple[str, str, str] | None:
        """解析 Gitee URL"""
        url = url.strip().rstrip("/")

        if "gitee.com" in url:
            parts = url.split("gitee.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            if repo.endswith(".git"):
                repo = repo[:-4]
            return self.host, owner, repo

        return None

    def get_clone_url(self, owner: str, repo: str) -> str:
        return f"https://gitee.com/{owner}/{repo}.git"

    def get_api_url(self, owner: str, repo: str) -> str:
        return f"https://gitee.com/api/v5/repos/{owner}/{repo}"


# 导入器工厂
class GitImporterFactory:
    """Git 导入器工厂"""

    _importers = {
        "github": GitHubImporter,
        "gitlab": GitLabImporter,
        "gitee": GiteeImporter,
    }

    @classmethod
    def create(cls, host: str, temp_dir: str = "/tmp/openyoung_imports") -> GitImporter | None:
        """根据主机名创建导入器"""
        importer_class = cls._importers.get(host.lower())
        if importer_class:
            return importer_class(temp_dir)
        return None

    @classmethod
    def from_url(cls, url: str, temp_dir: str = "/tmp/openyoung_imports") -> tuple[GitImporter, str, str, str] | None:
        """从 URL 自动识别并创建导入器

        Returns:
            Tuple[importer, host, owner, repo] 或 None
        """
        url = url.lower()

        # 尝试每个支持的导入器
        for host in cls._importers.keys():
            if host in url:
                importer = cls.create(host, temp_dir)
                if importer:
                    parsed = importer.parse_url(url)
                    if parsed:
                        h, owner, repo = parsed
                        return importer, h, owner, repo

        return None


# 兼容性别名
GitImporterBase = GitImporter
