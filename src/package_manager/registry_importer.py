"""
Registry Importer - Import from package registries
"""

import os
from typing import Any


class RegistryImporter:
    """包注册表导入器

    支持从以下来源导入:
    - PyPI
    - npm
    - GitHub Releases
    """

    def __init__(self, registry_type: str = "pypi"):
        self.registry_type = registry_type
        self.registry_urls = {
            "pypi": "https://pypi.org/pypi/{package}/json",
            "npm": "https://registry.npmjs.org/{package}",
        }

    async def fetch_package_info(
        self, package_name: str, version: str = None
    ) -> dict[str, Any]:
        """获取包信息"""
        if self.registry_type == "pypi":
            return await self._fetch_pypi(package_name, version)
        elif self.registry_type == "npm":
            return await self._fetch_npm(package_name, version)
        else:
            raise ValueError(f"Unknown registry type: {self.registry_type}")

    async def _fetch_pypi(
        self, package_name: str, version: str = None
    ) -> dict[str, Any]:
        """从 PyPI 获取包信息"""
        import httpx

        url = self.registry_urls["pypi"].format(package=package_name)
        if version:
            url += f"/{version}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def _fetch_npm(
        self, package_name: str, version: str = None
    ) -> dict[str, Any]:
        """从 npm 获取包信息"""
        import httpx

        url = self.registry_urls["npm"].format(package=package_name)
        if version:
            url += f"/{version}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def download_and_extract(
        self, package_name: str, target_dir: str, version: str = None
    ) -> dict[str, Any]:
        """下载并解压包到目标目录"""
        # 获取包信息
        info = await self.fetch_package_info(package_name, version)

        if self.registry_type == "pypi":
            return await self._extract_pypi(info, target_dir)
        elif self.registry_type == "npm":
            return await self._extract_npm(info, target_dir)

    async def _extract_pypi(
        self, info: dict[str, Any], target_dir: str
    ) -> dict[str, Any]:
        """提取 PyPI 包"""
        # PyPI 包通常是 wheel 或 tar.gz
        urls = info.get("urls", [])
        for url_info in urls:
            if url_info["packagetype"] == "wheel":
                # 下载 wheel 文件
                import httpx

                wheel_url = url_info["url"]
                async with httpx.AsyncClient() as client:
                    response = await client.get(wheel_url)
                    response.raise_for_status()

                wheel_path = os.path.join(target_dir, url_info["filename"])
                with open(wheel_path, "wb") as f:
                    f.write(response.content)

                return {
                    "success": True,
                    "file": wheel_path,
                    "type": "wheel",
                }

        return {"success": False, "error": "No wheel found"}

    async def _extract_npm(
        self, info: dict[str, Any], target_dir: str
    ) -> dict[str, Any]:
        """提取 npm 包"""
        # npm 包是 tarball
        dist = info.get("dist", {})
        tarball = dist.get("tarball")

        if tarball:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(tarball)
                response.raise_for_status()

                tarball_path = os.path.join(target_dir, "package.tgz")
                with open(tarball_path, "wb") as f:
                    f.write(response.content)

                return {
                    "success": True,
                    "file": tarball_path,
                    "type": "tarball",
                }

        return {"success": False, "error": "No tarball found"}

    def parse_package_spec(self, spec: str) -> dict[str, str]:
        """解析包规格字符串

        支持格式:
        - package
        - package@1.0.0
        - github:owner/repo
        - path:./local/path
        """
        # npm-style version
        if "@" in spec and not spec.startswith("@"):
            name, version = spec.split("@", 1)
            return {"name": name, "version": version, "source": "registry"}

        # GitHub
        if spec.startswith("github:"):
            repo = spec[7:]
            return {"name": repo, "source": "github"}

        # Local path
        if spec.startswith("path:"):
            path = spec[5:]
            return {"name": path, "source": "local"}

        # Default: registry package
        return {"name": spec, "version": None, "source": "registry"}
