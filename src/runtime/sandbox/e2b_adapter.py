"""
E2B Sandbox Adapter - E2B 沙箱适配器

基于 E2B SDK 实现安全沙箱执行
参考: https://e2b.dev
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# E2B 可用性检查
E2B_AVAILABLE = False
try:
    import e2b_code_interpreter

    E2B_AVAILABLE = True
except ImportError:
    logger.warning("E2B SDK not available, using fallback")


@dataclass
class ExecutionResult:
    """执行结果"""

    output: str
    error: str
    exit_code: int
    duration_ms: int
    artifacts: list = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []


class E2BSandbox:
    """
    E2B 沙箱后端

    特点:
    - 150ms 冷启动
    - microVM 隔离
    - 支持 Python, JavaScript, Bash
    """

    def __init__(
        self,
        template: str = "python3",
        timeout: int = 300,
    ):
        """
        初始化 E2B 沙箱

        Args:
            template: 沙箱模板 (python3, nodejs, etc.)
            timeout: 超时时间(秒)
        """
        self._template = template
        self._timeout = timeout
        self._sandbox = None

    def _get_sandbox(self):
        """获取或创建沙箱实例"""
        if not E2B_AVAILABLE:
            raise RuntimeError("E2B SDK not installed. Run: pip install e2b-code-interpreter")

        if self._sandbox is None:
            self._sandbox = e2b_code_interpreter.Sandbox(
                template=self._template,
                timeout=self._timeout,
            )
        return self._sandbox

    async def execute(self, code: str, language: str = "python") -> ExecutionResult:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的代码
            language: 语言 (python, javascript)

        Returns:
            ExecutionResult: 执行结果
        """
        import time

        start_time = time.time()

        try:
            sandbox = self._get_sandbox()

            # 根据语言执行
            if language.lower() in ("python", "py"):
                results = sandbox.run_code(code)
            elif language.lower() in ("javascript", "js"):
                results = sandbox.run_code(code)
            else:
                # 使用bash执行
                results = sandbox.commands.run(code)

            # 解析结果
            output = ""
            error = ""
            artifacts = []

            if results.logs:
                output = "\n".join([str(log) for log in results.logs.stdout])
                error = "\n".join([str(log) for log in results.logs.stderr])

            # 检查错误
            exit_code = 0
            if results.error or error:
                exit_code = 1

            # 提取artifacts (生成的文件)
            if results.files:
                artifacts = [{"name": f.name, "content": f.content} for f in results.files]

            duration_ms = int((time.time() - start_time) * 1000)

            return ExecutionResult(
                output=output,
                error=error,
                exit_code=exit_code,
                duration_ms=duration_ms,
                artifacts=artifacts,
            )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"E2B execution error: {e}")
            return ExecutionResult(
                output="",
                error=str(e),
                exit_code=1,
                duration_ms=duration_ms,
            )

    async def install(self, packages: list[str]) -> bool:
        """
        安装依赖包

        Args:
            packages: 包列表

        Returns:
            bool: 是否成功
        """
        try:
            sandbox = self._get_sandbox()

            for pkg in packages:
                sandbox.commands.run(f"pip install {pkg}")

            return True
        except Exception as e:
            logger.error(f"Package install error: {e}")
            return False

    def destroy(self):
        """销毁沙箱实例"""
        if self._sandbox:
            self._sandbox.kill()
            self._sandbox = None


class E2BFallback:
    """
    E2B 后备实现 (当E2B不可用时使用)
    """

    def __init__(self, timeout: int = 300):
        self._timeout = timeout

    async def execute(self, code: str, language: str = "python") -> ExecutionResult:
        """后备执行 - 简单返回错误"""
        return ExecutionResult(
            output="",
            error="E2B not available. Install with: pip install e2b-code-interpreter",
            exit_code=1,
            duration_ms=0,
        )

    async def install(self, packages: list[str]) -> bool:
        return False

    def destroy(self):
        pass


def create_e2b_sandbox(
    template: str = "python3",
    timeout: int = 300,
    fallback: bool = True,
) -> Optional[E2BSandbox]:
    """
    创建 E2B 沙箱实例

    Args:
        template: 沙箱模板
        timeout: 超时时间
        fallback: 是否允许后备实现

    Returns:
        E2BSandbox 或 None
    """
    if E2B_AVAILABLE:
        return E2BSandbox(template=template, timeout=timeout)

    if fallback:
        return E2BFallback(timeout=timeout)

    return None
