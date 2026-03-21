"""
GitHub Fetcher - Repository metadata and file fetching

Handles API calls to GitHub, GitLab, Gitee for repository metadata.
"""

import os
from pathlib import Path
from typing import Any

import httpx


class GitHubFetcher:
    """GitHub/GitLab/Gitee repository metadata fetcher"""

    def __init__(self):
        self.temp_dir = Path("/tmp") / "openyoung_imports"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def fetch_repo_metadata(self, host: str, owner: str, repo: str) -> dict[str, Any] | None:
        """Fetch repository metadata via API (fast)"""
        try:
            if host == "github.com":
                return self._fetch_github_metadata(owner, repo)
            elif host == "gitlab.com":
                return self._fetch_gitlab_metadata(owner, repo)
            elif host == "gitee.com":
                return self._fetch_gitee_metadata(owner, repo)
        except Exception as e:
            print(f"[Metadata] Failed to fetch: {e}")
        return None

    def _fetch_github_metadata(self, owner: str, repo: str) -> dict[str, Any] | None:
        """Fetch GitHub repository metadata"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        response = httpx.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count", 0),
                "language": data.get("language"),
                "default_branch": data.get("default_branch"),
                "url": data.get("html_url"),
            }
        return None

    def _fetch_gitlab_metadata(self, owner: str, repo: str) -> dict[str, Any] | None:
        """Fetch GitLab repository metadata"""
        import urllib.parse

        encoded = urllib.parse.quote(f"{owner}/{repo}")
        url = f"https://gitlab.com/api/v4/projects/{encoded}"
        response = httpx.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "stars": data.get("star_count", 0),
                "language": data.get("language"),
                "default_branch": data.get("default_branch"),
                "url": data.get("web_url"),
            }
        return None

    def _fetch_gitee_metadata(self, owner: str, repo: str) -> dict[str, Any] | None:
        """Fetch Gitee repository metadata"""
        url = f"https://gitee.com/api/v5/repos/{owner}/{repo}"
        response = httpx.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data.get("name"),
                "description": data.get("description"),
                "stars": data.get("stargazers_count", 0),
                "language": data.get("language"),
                "default_branch": data.get("default_branch"),
                "url": data.get("html_url"),
            }
        return None

    def fetch_repo_files(self, host: str, owner: str, repo: str) -> Path | None:
        """Fetch repository files via API (fallback)"""
        return None

    def git_clone(self, owner: str, repo: str) -> Path | None:
        """Git clone repository to local"""
        import shutil
        import subprocess

        repo_url = f"https://github.com/{owner}/{repo}.git"
        local_path = self.temp_dir / f"{owner}_{repo}"

        # If exists, remove first
        if local_path.exists():
            shutil.rmtree(local_path)

        try:
            result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(local_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                print(f"[GitHub] Cloned to {local_path}")
                return local_path
            else:
                print(f"[Error] Git clone failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"[Error] Git clone error: {e}")
            return None

    def parse_github_url(self, url: str) -> tuple:
        """Parse GitHub URL"""
        url = url.strip().rstrip("/")

        if "github.com" in url:
            parts = url.split("github.com/")[-1].split("/")
        else:
            parts = url.split("/")

        if len(parts) >= 2:
            return parts[0], parts[1]
        return None, None
