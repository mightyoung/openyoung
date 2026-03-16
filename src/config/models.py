"""
Pydantic 配置模型

参考 FastAPI 和 Pydantic 最佳实践
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class SandboxConfig(BaseModel):
    """沙箱配置"""
    max_execution_time_ms: int = Field(default=300000, description="最大执行时间(毫秒)")
    max_memory_mb: int = Field(default=512, description="最大内存(MB)")
    allow_network: bool = Field(default=False, description="是否允许网络访问")
    allowed_domains: list[str] = Field(default_factory=list, description="允许的域名列表")
    enable_prompt_detection: bool = Field(default=True, description="启用提示注入检测")
    enable_secret_detection: bool = Field(default=True, description="启用敏感信息检测")


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: Literal["openai", "anthropic", "azure"] = Field(default="openai", description="LLM 提供商")
    model: str = Field(default="gpt-4", description="模型名称")
    api_key: Optional[str] = Field(default=None, description="API Key")
    base_url: Optional[str] = Field(default=None, description="自定义 API 地址")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=4096, description="最大 token 数")
    timeout: int = Field(default=60, description="超时时间(秒)")


class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str = Field(default="young", description="Agent 名称")
    description: str = Field(default="OpenYoung Agent", description="Agent 描述")
    default_model: str = Field(default="gpt-4", description="默认模型")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟(秒)")
    enable_caching: bool = Field(default=True, description="启用缓存")
    cache_ttl: int = Field(default=3600, description="缓存 TTL(秒)")


class EvaluationConfig(BaseModel):
    """评估配置"""
    enable: bool = Field(default=True, description="启用评估")
    criteria: dict[str, float] = Field(
        default_factory=lambda: {
            "accuracy": 0.4,
            "completeness": 0.3,
            "efficiency": 0.3,
        },
        description="评估标准及权重"
    )
    timeout: int = Field(default=300, description="评估超时(秒)")
    max_iterations: int = Field(default=10, description="最大迭代次数")


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: Literal["sqlite", "postgresql", "mongodb"] = Field(default="sqlite", description="数据库类型")
    path: Optional[str] = Field(default=None, description="SQLite 路径")
    host: Optional[str] = Field(default=None, description="主机地址")
    port: Optional[int] = Field(default=None, description="端口号")
    database: Optional[str] = Field(default=None, description="数据库名")
    username: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="日志级别")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="日志格式")
    file: Optional[str] = Field(default=None, description="日志文件路径")
    max_bytes: int = Field(default=10485760, description="单个日志文件大小")
    backup_count: int = Field(default=5, description="备份文件数量")


class OpenYoungConfig(BaseSettings):
    """OpenYoung 主配置（支持分层配置）"""

    # 环境变量前缀
    model_config = {
        "env_prefix": "YOUNG_",
        "env_nested_delimiter": "__",
        "case_sensitive": False,
    }

    # 应用配置
    app_name: str = Field(default="OpenYoung", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")
    environment: Literal["development", "staging", "production"] = Field(default="development", description="环境")

    # 子配置
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig, description="沙箱配置")
    llm: LLMConfig = Field(default_factory=LLMConfig, description="LLM 配置")
    agent: AgentConfig = Field(default_factory=AgentConfig, description="Agent 配置")
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig, description="评估配置")
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="日志配置")

    # 路径配置
    data_dir: str = Field(default="./data", description="数据目录")
    cache_dir: str = Field(default="./cache", description="缓存目录")
    log_dir: str = Field(default="./logs", description="日志目录")

    def get_llm_config(self) -> LLMConfig:
        """获取 LLM 配置"""
        return self.llm

    def get_sandbox_config(self) -> SandboxConfig:
        """获取沙箱配置"""
        return self.sandbox

    def get_evaluation_config(self) -> EvaluationConfig:
        """获取评估配置"""
        return self.evaluation
