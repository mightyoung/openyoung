"""
CLI Commands Package - 模块化 CLI 命令

将 CLI 命令拆分为独立模块:
- run: 运行命令
- config: 配置命令
- agent: Agent 管理命令
- eval: 评估命令
"""

from .agent import agent_group
from .config import config_group
from .eval import eval_group
from .run import run_group

__all__ = [
    "run_group",
    "config_group",
    "agent_group",
    "eval_group",
]
