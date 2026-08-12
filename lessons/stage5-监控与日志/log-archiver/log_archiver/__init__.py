"""
日志归档工具包
提供日志文件归档、清空和过期清理功能。
"""

from .models import ArchiveDate, ToolConfig, ArchiveResult, CleanupResult, ToolResult
from .file_operations import FileOperations
from .logger import ToolLogger, log_info, log_warning, log_error, log_debug
from .archiver import LogArchiver, archive_log_file, check_archive_status
from .retention_manager import RetentionManager, cleanup_expired_archives, get_retention_status

__version__ = "1.0.0"
__all__ = [
    # 模型
    'ArchiveDate',
    'ToolConfig', 
    'ArchiveResult',
    'CleanupResult',
    'ToolResult',
    
    # 文件操作
    'FileOperations',
    
    # 日志记录
    'ToolLogger',
    'log_info',
    'log_warning', 
    'log_error',
    'log_debug',
    
    # 归档器
    'LogArchiver',
    'archive_log_file',
    'check_archive_status',
    
    # 保留期管理器
    'RetentionManager',
    'cleanup_expired_archives',
    'get_retention_status',
]