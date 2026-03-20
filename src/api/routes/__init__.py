"""
API Routes - 统一API路由管理

这个模块统一导出所有API路由，便于在server.py中集中注册
"""

from fastapi import APIRouter

# 导入各个模块的router
# 注意: session_api 同时支持 router模式和app模式

# 导出 router 用于直接注册
__all__ = [
    "router",
]


def get_all_routers():
    """
    获取所有需要注册的routers

    返回格式: [(router, prefix, tags), ...]
    """
    routers = []

    # 添加 evaluation_api routers
    try:
        from src.evaluation_api.routers import (
            evaluations,
            executions,
            exports,
            stream,
        )

        routers.append((executions.router, "/api/v1", ["Executions"]))
        routers.append((evaluations.router, "/api/v1", ["Evaluations"]))
        routers.append((exports.router, "/api/v1", ["Exports"]))
        routers.append((stream.router, "/api/v1", ["Stream"]))
    except ImportError:
        pass

    return routers
