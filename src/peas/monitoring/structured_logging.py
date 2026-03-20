"""
Structured JSON logging for PEAS
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        # 添加额外字段
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)


class PEASLogger:
    """PEAS结构化日志器"""

    def __init__(self, name: str = "peas"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        # 添加JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def log(self, level: str, message: str, **kwargs) -> None:
        """记录结构化日志"""
        extra = {"extra": kwargs} if kwargs else {}
        getattr(self.logger, level.lower())(message, extra=extra)

    def info(self, message: str, **kwargs) -> None:
        self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self.log("ERROR", message, **kwargs)
