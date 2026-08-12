"""
日志记录器模块
提供分级日志记录功能，支持verbose模式控制。
"""

import sys
from enum import Enum
from typing import Optional
import logging
import datetime


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ToolLogger:
    """
    日志记录器类
    提供分级日志记录，支持verbose模式控制详细输出
    """
    
    def __init__(self, verbose: bool = False, log_to_file: bool = False, 
                 log_file_path: Optional[str] = None):
        """
        初始化日志记录器
        
        参数:
            verbose: 是否启用详细模式
            log_to_file: 是否记录到文件
            log_file_path: 日志文件路径（如果log_to_file为True）
        """
        self.verbose = verbose
        self.log_to_file = log_to_file
        self.log_file_path = log_file_path
        
        # 设置基础日志格式
        self.log_format = "%(asctime)s - %(levelname)s - %(message)s"
        self.date_format = "%Y-%m-%d %H:%M:%S"
        
        # 初始化Python logging（用于文件日志）
        if log_to_file and log_file_path:
            self._setup_file_logging()
        
        # 消息计数器
        self.message_counts = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 0,
            LogLevel.WARNING: 0,
            LogLevel.ERROR: 0
        }
    
    def _setup_file_logging(self):
        """设置文件日志记录"""
        try:
            # 确保日志目录存在
            import os
            log_dir = os.path.dirname(self.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 配置文件处理器
            file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG if self.verbose else logging.INFO)
            file_handler.setFormatter(logging.Formatter(self.log_format))
            
            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.DEBUG)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # 文件日志设置失败，回退到控制台日志
            print(f"警告: 无法设置文件日志记录: {e}", file=sys.stderr)
            self.log_to_file = False
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """
        格式化日志消息
        
        参数:
            level: 日志级别
            message: 原始消息
            
        返回:
            格式化后的消息
        """
        timestamp = datetime.datetime.now().strftime(self.date_format)
        return f"{timestamp} - {level.value} - {message}"
    
    def _log_to_console(self, level: LogLevel, formatted_message: str):
        """
        记录到控制台
        
        参数:
            level: 日志级别
            formatted_message: 格式化后的消息
        """
        if level == LogLevel.ERROR:
            print(formatted_message, file=sys.stderr)
        else:
            print(formatted_message)
    
    def _log_to_file(self, level: LogLevel, message: str):
        """
        记录到文件（使用Python logging模块）
        
        参数:
            level: 日志级别
            message: 原始消息
        """
        if not self.log_to_file:
            return
        
        try:
            logger = logging.getLogger()
            
            if level == LogLevel.DEBUG:
                logger.debug(message)
            elif level == LogLevel.INFO:
                logger.info(message)
            elif level == LogLevel.WARNING:
                logger.warning(message)
            elif level == LogLevel.ERROR:
                logger.error(message)
                
        except Exception as e:
            # 文件记录失败，输出到控制台
            self._log_to_console(LogLevel.ERROR, f"文件日志记录失败: {e}")
    
    def _should_log(self, level: LogLevel) -> bool:
        """
        判断是否应该记录指定级别的日志
        
        参数:
            level: 日志级别
            
        返回:
            True表示应该记录，False表示跳过
        """
        # 在详细模式下记录所有级别
        if self.verbose:
            return True
        
        # 非详细模式下跳过DEBUG级别
        if level == LogLevel.DEBUG:
            return False
        
        return True
    
    def _log(self, level: LogLevel, message: str):
        """
        内部日志记录方法
        
        参数:
            level: 日志级别
            message: 日志消息
        """
        if not self._should_log(level):
            return
        
        # 更新计数器
        self.message_counts[level] += 1
        
        # 格式化消息
        formatted_message = self._format_message(level, message)
        
        # 记录到控制台
        self._log_to_console(level, formatted_message)
        
        # 记录到文件（如果启用）
        if self.log_to_file:
            self._log_to_file(level, message)
    
    def info(self, message: str):
        """
        记录信息性消息
        
        参数:
            message: 信息消息
        """
        self._log(LogLevel.INFO, message)
    
    def warning(self, message: str):
        """
        记录警告消息
        
        参数:
            message: 警告消息
        """
        self._log(LogLevel.WARNING, message)
    
    def error(self, message: str):
        """
        记录错误消息
        
        参数:
            message: 错误消息
        """
        self._log(LogLevel.ERROR, message)
    
    def debug(self, message: str):
        """
        记录调试消息（仅在详细模式下输出）
        
        参数:
            message: 调试消息
        """
        self._log(LogLevel.DEBUG, message)
    
    def success(self, message: str):
        """
        记录成功消息（INFO级别，带成功标记）
        
        参数:
            message: 成功消息
        """
        self.info(f"✓ {message}")
    
    def failure(self, message: str):
        """
        记录失败消息（ERROR级别，带失败标记）
        
        参数:
            message: 失败消息
        """
        self.error(f"✗ {message}")
    
    def section(self, title: str):
        """
        记录章节标题
        
        参数:
            title: 章节标题
        """
        separator = "=" * 60
        self.info(f"\n{separator}")
        self.info(f"{title}")
        self.info(f"{separator}")
    
    def progress(self, message: str):
        """
        记录进度消息（INFO级别，带进度标记）
        
        参数:
            message: 进度消息
        """
        self.info(f"→ {message}")
    
    def get_statistics(self) -> dict:
        """
        获取日志统计信息
        
        返回:
            包含各级别日志数量的字典
        """
        return {
            "total": sum(self.message_counts.values()),
            "debug": self.message_counts[LogLevel.DEBUG],
            "info": self.message_counts[LogLevel.INFO],
            "warning": self.message_counts[LogLevel.WARNING],
            "error": self.message_counts[LogLevel.ERROR]
        }
    
    def print_statistics(self):
        """打印日志统计信息"""
        stats = self.get_statistics()
        
        if stats["total"] == 0:
            self.info("没有记录任何日志")
            return
        
        self.section("日志统计")
        self.info(f"总日志数: {stats['total']}")
        
        if self.verbose:
            self.info(f"调试日志: {stats['debug']}")
        
        self.info(f"信息日志: {stats['info']}")
        self.info(f"警告日志: {stats['warning']}")
        self.info(f"错误日志: {stats['error']}")
    
    def set_verbose(self, verbose: bool):
        """
        设置详细模式
        
        参数:
            verbose: 是否启用详细模式
        """
        self.verbose = verbose
        if verbose:
            self.info("已启用详细日志模式")
    
    @classmethod
    def create_default_logger(cls, verbose: bool = False) -> 'ToolLogger':
        """
        创建默认日志记录器（仅控制台输出）
        
        参数:
            verbose: 是否启用详细模式
            
        返回:
            配置好的ToolLogger实例
        """
        return cls(verbose=verbose, log_to_file=False)
    
    @classmethod
    def create_file_logger(cls, log_file_path: str, verbose: bool = False) -> 'ToolLogger':
        """
        创建文件日志记录器
        
        参数:
            log_file_path: 日志文件路径
            verbose: 是否启用详细模式
            
        返回:
            配置好的ToolLogger实例
        """
        return cls(verbose=verbose, log_to_file=True, log_file_path=log_file_path)


# 全局默认日志记录器实例
_default_logger = None


def get_default_logger() -> ToolLogger:
    """
    获取全局默认日志记录器
    
    返回:
        全局ToolLogger实例
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = ToolLogger.create_default_logger()
    return _default_logger


def set_default_logger(logger: ToolLogger):
    """
    设置全局默认日志记录器
    
    参数:
        logger: 要设置的日志记录器
    """
    global _default_logger
    _default_logger = logger


# 便捷函数
def log_info(message: str):
    """记录信息性消息（使用全局记录器）"""
    get_default_logger().info(message)


def log_warning(message: str):
    """记录警告消息（使用全局记录器）"""
    get_default_logger().warning(message)


def log_error(message: str):
    """记录错误消息（使用全局记录器）"""
    get_default_logger().error(message)


def log_debug(message: str):
    """记录调试消息（使用全局记录器）"""
    get_default_logger().debug(message)