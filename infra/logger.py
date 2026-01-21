# 创建简化但完整的日志系统

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# 导入loguru库，比标准库logging更简单好用
from loguru import logger

# 导入配置
from .config import config


# ==================== 第一部分：配置类 ====================
class LogConfig:
    """
    日志配置类
    集中管理所有日志相关的设置
    为什么需要：避免配置散落在各处，便于统一修改
    """
    
    def __init__(self):
        """初始化日志配置"""
        # 从主配置读取日志级别
        self.level = config.app.log_level
        
        # 日志文件存储目录
        self.log_dir = Path("./logs")
        
        # 日志文件路径
        self.app_log = self.log_dir / "app.log"      # 应用日志
        self.error_log = self.log_dir / "error.log"  # 错误日志
        
        # 日志格式
        self.format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "  # 时间
            "<level>{level: <8}</level> | "                 # 日志级别
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "  # 位置
            "<level>{message}</level>"                      # 消息
        )
        
        # 日志轮转配置
        self.rotation = "10 MB"    # 每个日志文件最大10MB
        self.retention = "30 days" # 保留30天的日志
        
    def ensure_dirs(self):
        """确保日志目录存在"""
        self.log_dir.mkdir(parents=True, exist_ok=True)


# ==================== 第二部分：初始化函数 ====================
def setup_logging():
    """
    初始化日志系统
    为什么需要：在程序启动时调用，配置日志的输出方式和格式
    """
    # 创建配置实例
    log_config = LogConfig()
    
    # 确保日志目录存在
    log_config.ensure_dirs()
    
    # 第一步：移除loguru的默认处理器
    # 为什么：loguru默认有一个输出到控制台的处理器，我们想要自定义配置
    logger.remove()
    
    # 第二步：添加控制台处理器
    # 为什么：开发时需要看到控制台输出，方便调试
    logger.add(
        sink=sys.stderr,          # 输出到标准错误
        level=log_config.level,   # 使用配置的日志级别
        format=log_config.format, # 使用自定义格式
        colorize=True,            # 启用颜色，更易读
        backtrace=True,           # 显示完整的错误堆栈
    )
    
    # 第三步：添加普通文件日志处理器
    # 为什么：需要持久化日志，便于后续查看和分析
    logger.add(
        sink=log_config.app_log,  # 输出到文件
        level="DEBUG",            # 文件记录更详细的DEBUG信息
        format=log_config.format,
        rotation=log_config.rotation,  # 文件大小达到10MB时轮转
        retention=log_config.retention, # 保留30天
        compression="zip",        # 压缩旧日志节省空间
        encoding="utf-8",         # 使用UTF-8编码
    )
    
    # 第四步：添加错误日志专用处理器
    # 为什么：错误日志需要单独管理，便于快速定位问题
    logger.add(
        sink=log_config.error_log,
        level="ERROR",            # 只记录ERROR及以上级别
        format=log_config.format,
        rotation=log_config.rotation,
        retention=log_config.retention,
        compression="zip",
        encoding="utf-8",
    )
    
    # 第五步：配置异常自动捕获
    # 为什么：自动记录未处理的异常，避免程序静默失败
    logger.catch(
        message="捕获到未处理的异常",  # 异常消息前缀
        onerror=lambda _: logger.error("程序因未处理异常退出"),
    )
    
    # 记录日志系统初始化完成
    logger.info("日志系统初始化完成")
    logger.debug(f"日志级别: {log_config.level}")
    logger.debug(f"日志目录: {log_config.log_dir.absolute()}")


# ==================== 第三部分：便捷函数 ====================
def debug(message: str, **context):
    """
    DEBUG级别日志
    用途：记录详细的调试信息，开发时使用
    为什么需要：封装logger.debug，提供统一接口
    """
    if context:
        logger.bind(**context).debug(message)
    else:
        logger.debug(message)


def info(message: str, **context):
    """
    INFO级别日志
    用途：记录正常的程序运行信息
    为什么需要：封装logger.info，提供统一接口
    """
    if context:
        logger.bind(**context).info(message)
    else:
        logger.info(message)


def warning(message: str, **context):
    """
    WARNING级别日志
    用途：记录警告信息，表示可能有问题但不影响运行
    为什么需要：封装logger.warning，提供统一接口
    """
    if context:
        logger.bind(**context).warning(message)
    else:
        logger.warning(message)


def error(message: str, **context):
    """
    ERROR级别日志
    用途：记录错误信息，表示功能无法正常工作
    为什么需要：封装logger.error，提供统一接口
    """
    if context:
        logger.bind(**context).error(message)
    else:
        logger.error(message)


def exception(message: str, exc: Exception, **context):
    """
    异常日志
    用途：专门记录异常及其堆栈信息
    为什么需要：自动包含异常堆栈，便于调试
    """
    logger.opt(exception=exc).error(message, **context)


# ==================== 第四部分：专业日志函数 ====================
def log_request(
    method: str,
    path: str,
    client_ip: str,
    status_code: int = 200,
    duration_ms: float = 0.0,
    **extra
):
    """
    记录HTTP请求日志
    为什么需要：统一记录所有API请求，便于监控和调试
    """
    # 根据状态码决定日志级别
    level = "ERROR" if status_code >= 500 else "INFO"
    
    # 构建日志消息
    message = f"{method} {path} - {status_code} ({duration_ms:.2f}ms)"
    
    # 添加上下文信息
    context = {
        "type": "request",
        "method": method,
        "path": path,
        "client_ip": client_ip,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **extra
    }
    
    # 记录日志
    logger.bind(**context).log(level, message)


def log_performance(operation: str, duration_ms: float, **extra):
    """
    记录性能日志
    为什么需要：监控操作耗时，发现性能瓶颈
    """
    # 根据耗时决定日志级别
    if duration_ms > 1000:  # 超过1秒
        level = "WARNING"
        message = f"性能警告: {operation} 耗时 {duration_ms:.2f}ms"
    else:
        level = "DEBUG"
        message = f"{operation} 耗时 {duration_ms:.2f}ms"
    
    # 记录日志
    logger.bind(type="performance", operation=operation, duration_ms=duration_ms, **extra).log(level, message)


# ==================== 第五部分：初始化调用 ====================
# 自动初始化日志系统
# 为什么：导入这个模块时自动设置好日志系统
try:
    setup_logging()
except Exception as e:
    # 如果日志系统初始化失败，至少输出到控制台
    print(f"❌ 日志系统初始化失败: {e}")
    import traceback
    traceback.print_exc()


# ==================== 第六部分：导出接口 ====================
# 明确导出哪些函数和对象
# 为什么：控制模块的公开接口，避免内部实现被意外使用
__all__ = [
    # 便捷函数
    "debug",
    "info", 
    "warning",
    "error",
    "exception",
    
    # 专业日志函数
    "log_request",
    "log_performance",
    
    # 主logger对象（供需要高级功能的代码使用）
    "logger",
    
    # 初始化函数（如果其他地方需要重新初始化）
    "setup_logging",
]
