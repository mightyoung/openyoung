"""
Evaluation API - Phase 1 评估平台后端服务

提供 FastAPI REST API 用于:
- 执行记录查询
- 评估记录管理
- 数据导出
- 实时流推送
"""

from .main import create_app

__all__ = ["create_app"]
