"""
Configuration Models - 使用 Pydantic 的配置模型

提供类型安全的配置定义和验证。
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class LLMConfig(BaseModel):
    """LLM 配置"""

    provider: str = "deepseek"
    model: str = "deepseek-chat"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)
    api_key: Optional[str] = None

    @field_validator("model")
    @classmethod
    def model_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Model cannot be empty")
        return v.strip()


class ExecutionConfig(BaseModel):
    """执行配置"""

    timeout: int = Field(default=300, ge=1, le=3600)
    max_tool_calls: int = Field(default=10, ge=1, le=100)
    checkpoint_enabled: bool = True
    max_retries: int = Field(default=3, ge=0, le=10)


class PermissionRuleModel(BaseModel):
    """权限规则模型"""

    tool: str = "*"
    action: str = "ask"
    description: Optional[str] = None


class PermissionConfigModel(BaseModel):
    """权限配置模型"""

    _global: str = "ask"
    rules: list[PermissionRuleModel] = Field(default_factory=list)
    confirm_message: str = "确认执行此操作?"

    @model_validator(mode="before")
    @classmethod
    def validate_global_action(cls, data):
        if isinstance(data, dict):
            # 确保 _global 字段有效
            if "_global" in data:
                valid_actions = {"ask", "auto", "deny", "confirm"}
                if data["_global"] not in valid_actions:
                    data["_global"] = "ask"
        return data


class AgentConfigModel(BaseModel):
    """Agent 配置模型"""

    name: str = "default"
    mode: str = "primary"
    model: str = "deepseek-chat"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    tools: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    always_skills: list[str] = Field(default_factory=list)
    system_prompt: str = "你是一个有帮助的AI助手。"
    execution: Optional[ExecutionConfig] = None
    permission: Optional[PermissionConfigModel] = None


class AppConfig(BaseModel):
    """应用配置模型"""

    version: str = "0.1.0"
    default_agent: str = "default"
    default_llm: Optional[str] = None
    debug: bool = False
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            return "INFO"
        return v_upper


# 导出配置模型
__all__ = [
    "LLMConfig",
    "ExecutionConfig",
    "PermissionRuleModel",
    "PermissionConfigModel",
    "AgentConfigModel",
    "AppConfig",
]
