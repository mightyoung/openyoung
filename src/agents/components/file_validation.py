"""
File Validation Utilities

提取自 young_agent.py 的 validate_file_creation 函数。
验证任务执行后文件是否真实创建。
"""

import os
import re
import time
from pathlib import Path
from typing import Any


def validate_file_creation(task_description: str, agent_result: str) -> dict[str, Any]:
    """验证文件是否真实创建

    从任务描述中提取可能的文件路径，然后检查这些路径是否存在。
    如果任务描述中提到保存到文件，但文件未创建，则返回失败。

    Args:
        task_description: 任务描述
        agent_result: Agent 的执行结果

    Returns:
        验证结果: {"verified": bool, "files_found": list, "files_expected": list, "message": str}
    """
    # 从任务描述中提取可能的文件路径
    expected_files = []

    # 模式1: "保存到 xxx/yyy.py"
    patterns = [
        r"保存[到]?\s*([^\s]+\.py)",
        r"保存[到]?\s*([^\s]+\.json)",
        r"保存[到]?\s*([^\s]+\.txt)",
        r"save.*?to\s+([^\s]+\.py)",
        r"save.*?to\s+([^\s]+\.json)",
        r"保存[到]?\s*([^\s]+)",
        r"output/([^\s]+)",
        r"创建.*?([^\s]+\.py)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, task_description)
        expected_files.extend(matches)

    # 清理路径
    expected_files = [f.strip() for f in expected_files if f.strip()]

    # 检查文件是否存在
    found_files = []
    # 支持多种路径：相对路径、output/、绝对路径、/tmp/、~/
    base_dirs = [
        "",  # 当前目录
        "output/",  # output 目录
        "./output/",  # ./output 目录
        "/Users/muyi/Downloads/dev/openyoung/output/",  # 绝对路径
        "/tmp/",  # 临时目录
        os.path.expanduser("~/"),  # 家目录
    ]

    for file_path in expected_files:
        # 1. 先检查绝对路径（如果以 / 或 ~ 开头）
        if file_path.startswith("/"):
            if os.path.exists(file_path):
                found_files.append(file_path)
                continue
        elif file_path.startswith("~"):
            expanded = os.path.expanduser(file_path)
            if os.path.exists(expanded):
                found_files.append(expanded)
                continue

        # 2. 尝试不同的基准目录
        for base_dir in base_dirs:
            full_path = os.path.join(base_dir, file_path)
            if os.path.exists(full_path):
                found_files.append(full_path)
                break
            # 也检查不带扩展名的版本
            if not os.path.splitext(file_path)[1]:
                for ext in [".py", ".json", ".txt", ".md"]:
                    if os.path.exists(full_path + ext):
                        found_files.append(full_path + ext)
                        break

    # 如果没有找到任何预期的文件，检查 output 或 /tmp 目录中是否有任何新文件
    if not found_files:
        search_dirs = []
        if "output" in task_description.lower():
            search_dirs.append(Path("output"))
        # 也检查 /tmp 目录
        tmp_dir = Path("/tmp")
        if tmp_dir.exists():
            search_dirs.append(tmp_dir)

        if search_dirs:
            # 获取最近修改的文件（5分钟内）
            now = time.time()
            for search_dir in search_dirs:
                if search_dir.exists():
                    recent_files = []
                    try:
                        for f in search_dir.rglob("*"):
                            if f.is_file() and (now - f.stat().st_mtime) < 300:
                                recent_files.append(str(f))
                    except PermissionError:
                        continue
                    if recent_files:
                        found_files.extend(recent_files[:5])  # 最多5个
                        break

    # 判断验证是否通过
    verified = len(found_files) > 0 if expected_files else True

    message = ""
    if expected_files:
        if found_files:
            message = f"Found {len(found_files)}/{len(expected_files)} expected files"
        else:
            message = f"No expected files found (expected {len(expected_files)})"
    else:
        message = "No specific file paths in task description"

    return {
        "verified": verified,
        "files_found": found_files,
        "files_expected": expected_files,
        "message": message,
    }
