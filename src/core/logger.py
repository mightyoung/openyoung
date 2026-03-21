"""
统一日志工具

提供标准化的日志配置，替换所有散落的 print("[Warning]")
"""

import logging
import sys

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(
    name: str,
    level: int = logging.INFO,
    format_str: str = DEFAULT_FORMAT,
) -> logging.Logger:
    """获取标准化的 Logger 实例

    Args:
        name: Logger 名称，通常使用 __name__
        level: 日志级别，默认 INFO
        format_str: 日志格式

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台 handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # 格式化
    formatter = logging.Formatter(format_str, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def configure_root_logger(
    level: int = logging.INFO,
    format_str: str = DEFAULT_FORMAT,
) -> None:
    """配置根 Logger

    Args:
        level: 日志级别
        format_str: 日志格式
    """
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt=DATE_FORMAT,
        force=True,
    )


# 预定义的日志级别常量
class LogLevel:
    """日志级别常量"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# 便捷函数：快速获取 logger
def debug(name: str, msg: str) -> None:
    """快速记录 debug 日志"""
    get_logger(name).debug(msg)


def info(name: str, msg: str) -> None:
    """快速记录 info 日志"""
    get_logger(name).info(msg)


def warning(name: str, msg: str) -> None:
    """快速记录 warning 日志

    替换原来的 print(f"[Warning] {msg}")
    """
    get_logger(name).warning(msg)


def error(name: str, msg: str, exc_info: bool = False) -> None:
    """快速记录 error 日志

    Args:
        name: Logger 名称
        msg: 日志消息
        exc_info: 是否包含异常信息
    """
    get_logger(name).error(msg, exc_info=exc_info)


def critical(name: str, msg: str) -> None:
    """快速记录 critical 日志"""
    get_logger(name).critical(msg)
