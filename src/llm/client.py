"""
LLM Client - 适配器模式

此文件已弃用，请使用 src.llm.client_adapter.LLMClient
保留此文件仅为向后兼容
"""

# R1-2: 使用适配器模式，保持向后兼容
from src.llm.client_adapter import LLMClient

__all__ = ["LLMClient"]
