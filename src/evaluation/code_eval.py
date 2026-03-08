"""
CodeEval - 代码正确性评估器
基于 SWE-bench 风格的评估
"""

import asyncio
import tempfile
from dataclasses import dataclass
from typing import Any


@dataclass
class CodeExecutionResult:
    """代码执行结果"""

    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float


class CodeEval:
    """代码正确性评估器

    功能:
    - 代码语法检查
    - 代码执行验证
    - 单元测试通过率
    - 代码修复能力评估 (SWE-bench 风格)
    """

    def __init__(self):
        self.name = "code_eval"
        self.description = "代码正确性评估器"

    async def evaluate(
        self,
        code: str,
        expected_output: str | None = None,
        test_cases: list | None = None,
        language: str = "python",
    ) -> dict[str, Any]:
        """评估代码正确性

        Args:
            code: 待评估的代码
            expected_output: 期望的输出
            test_cases: 测试用例列表
            language: 编程语言

        Returns:
            评估结果字典
        """
        results = {
            "syntax_valid": False,
            "execution_success": False,
            "output_match": False,
            "test_pass_rate": 0.0,
            "overall_score": 0.0,
        }

        # 1. 语法检查
        syntax_result = await self._check_syntax(code, language)
        results["syntax_valid"] = syntax_result["valid"]

        if not syntax_result["valid"]:
            results["syntax_error"] = syntax_result.get("error")
            return results

        # 2. 执行验证
        if expected_output:
            exec_result = await self._execute_code(code, language)
            results["execution_success"] = exec_result.success
            results["output"] = exec_result.stdout
            results["execution_time"] = exec_result.execution_time

            # 输出匹配检查
            if exec_result.success:
                actual = exec_result.stdout.strip()
                expected = expected_output.strip()
                results["output_match"] = actual == expected

        # 3. 测试用例评估
        if test_cases:
            test_results = await self._run_tests(code, test_cases, language)
            results["test_pass_rate"] = test_results["pass_rate"]
            results["test_results"] = test_results["details"]

        # 4. 计算综合评分
        results["overall_score"] = self._calculate_score(results)

        return results

    async def _check_syntax(self, code: str, language: str) -> dict[str, Any]:
        """检查代码语法"""
        if language == "python":
            try:
                compile(code, "<string>", "exec")
                return {"valid": True}
            except SyntaxError as e:
                return {"valid": False, "error": str(e)}

        # 其他语言暂不实现
        return {"valid": True}

    async def _execute_code(
        self,
        code: str,
        language: str,
        timeout: int = 30,
    ) -> CodeExecutionResult:
        """执行代码"""
        if language == "python":
            return await self._execute_python(code, timeout)

        return CodeExecutionResult(
            success=False,
            stdout="",
            stderr=f"Unsupported language: {language}",
            return_code=-1,
            execution_time=0.0,
        )

    async def _execute_python(
        self,
        code: str,
        timeout: int = 30,
    ) -> CodeExecutionResult:
        """执行 Python 代码"""
        import time

        start_time = time.time()

        try:
            # 创建临时文件执行
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
            ) as f:
                f.write(code)
                temp_file = f.name

            # 执行代码
            process = await asyncio.create_subprocess_exec(
                "python3",
                temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return CodeExecutionResult(
                    success=False,
                    stdout="",
                    stderr="Execution timeout",
                    return_code=-1,
                    execution_time=timeout,
                )

            execution_time = time.time() - start_time

            return CodeExecutionResult(
                success=(process.returncode == 0),
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                return_code=process.returncode or 0,
                execution_time=execution_time,
            )

        except Exception as e:
            return CodeExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=time.time() - start_time,
            )

    async def _run_tests(
        self,
        code: str,
        test_cases: list,
        language: str,
    ) -> dict[str, Any]:
        """运行测试用例"""
        if language != "python":
            return {"pass_rate": 0.0, "details": []}

        passed = 0
        details = []

        for i, test_case in enumerate(test_cases):
            # 构建测试代码
            input_data = test_case.get("input")
            expected = test_case.get("expected")

            test_code = f"""
{code}

# Test case {i + 1}
input_data = {repr(input_data)}
expected = {repr(expected)}
"""

            exec_result = await self._execute_python(test_code, timeout=10)

            if exec_result.success and expected in exec_result.stdout:
                passed += 1
                status = "PASS"
            else:
                status = "FAIL"

            details.append(
                {
                    "case": i + 1,
                    "status": status,
                    "output": exec_result.stdout[:100],
                }
            )

        pass_rate = passed / len(test_cases) if test_cases else 0.0

        return {
            "pass_rate": pass_rate,
            "passed": passed,
            "total": len(test_cases),
            "details": details,
        }

    def _calculate_score(self, results: dict[str, Any]) -> float:
        """计算综合评分"""
        score = 0.0
        weights = {
            "syntax_valid": 0.2,
            "execution_success": 0.2,
            "output_match": 0.3,
            "test_pass_rate": 0.3,
        }

        if results.get("syntax_valid", False):
            score += weights["syntax_valid"]

        if results.get("execution_success", False):
            score += weights["execution_success"]

        if results.get("output_match", False):
            score += weights["output_match"]

        score += results.get("test_pass_rate", 0.0) * weights["test_pass_rate"]

        return score


# 便捷函数
def create_code_eval() -> CodeEval:
    """创建 CodeEval 实例"""
    return CodeEval()
