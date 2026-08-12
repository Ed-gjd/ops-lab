"""
日志归档工具 - 核心数据模型
定义工具使用的所有数据结构和类型。
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, List
import re


@dataclass
class ArchiveDate:
    """归档日期模型"""
    year: int
    month: int
    day: int
    
    @classmethod
    def from_filename(cls, filename: str, base_name: str) -> Optional['ArchiveDate']:
        """
        从归档文件名解析日期
        
        参数:
            filename: 归档文件名（如 "app-2024-01-15.log"）
            base_name: 日志文件基本名称（如 "app"）
        
        返回:
            ArchiveDate对象或None（解析失败）
        """
        # 移除扩展名
        try:
            name_without_ext = filename.rsplit('.', 1)[0]
        except (IndexError, AttributeError):
            return None
        
        # 提取日期部分
        pattern = f"{base_name}-(\\d{{4}})-(\\d{{2}})-(\\d{{2}})"
        match = re.match(pattern, name_without_ext)
        
        if not match:
            return None
        
        try:
            year, month, day = map(int, match.groups())
            # 验证日期有效性
            date(year, month, day)  # 如果日期无效会抛出ValueError
            return cls(year, month, day)
        except (ValueError, TypeError):
            return None
    
    def to_date(self) -> date:
        """转换为datetime.date对象"""
        return date(self.year, self.month, self.day)
    
    def is_before(self, days_ago: int) -> bool:
        """
        判断是否早于指定天数前
        
        参数:
            days_ago: 几天前
            
        返回:
            True表示早于指定天数前，False表示未过期
        """
        if days_ago < 0:
            raise ValueError("保留天数不能为负数")
        
        cutoff_date = date.today() - timedelta(days=days_ago)
        return self.to_date() < cutoff_date
    
    def to_string(self) -> str:
        """转换为YYYY-MM-DD格式字符串"""
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
    
    @classmethod
    def from_string(cls, date_str: str) -> Optional['ArchiveDate']:
        """
        从YYYY-MM-DD格式字符串创建ArchiveDate对象
        
        参数:
            date_str: 日期字符串（如 "2024-01-15"）
            
        返回:
            ArchiveDate对象或None（解析失败）
        """
        try:
            year, month, day = map(int, date_str.split('-'))
            # 验证日期有效性
            date(year, month, day)
            return cls(year, month, day)
        except (ValueError, AttributeError, TypeError):
            return None
    
    @classmethod
    def today(cls) -> 'ArchiveDate':
        """获取今天的归档日期"""
        today = date.today()
        return cls(today.year, today.month, today.day)


@dataclass
class ToolConfig:
    """工具配置模型"""
    log_file_path: str = "app.log"
    retention_days: int = 7
    verbose: bool = False
    dry_run: bool = False
    
    @property
    def base_name(self) -> str:
        """获取日志文件的基本名称（不含扩展名）"""
        # 去掉扩展名和路径
        import os
        filename = os.path.basename(self.log_file_path)
        if '.' in filename:
            return filename.rsplit('.', 1)[0]
        return filename
    
    @property
    def log_file_name(self) -> str:
        """获取日志文件名（含扩展名）"""
        import os
        return os.path.basename(self.log_file_path)
    
    @classmethod
    def from_namespace(cls, namespace) -> 'ToolConfig':
        """从argparse命名空间创建配置"""
        return cls(
            log_file_path=getattr(namespace, 'log_file', 'app.log'),
            retention_days=getattr(namespace, 'retention_days', 7),
            verbose=getattr(namespace, 'verbose', False),
            dry_run=getattr(namespace, 'dry_run', False)
        )


@dataclass
class ArchiveResult:
    """归档操作结果"""
    status: str  # "archived" | "skipped" | "noop" | "failed"
    message: str
    archived_file: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """判断操作是否成功（归档成功或被跳过都视为成功）"""
        return self.status in ("archived", "skipped", "noop")
    
    @property
    def was_archived(self) -> bool:
        """判断是否真正执行了归档"""
        return self.status == "archived"
    
    @classmethod
    def archived(cls, archive_file: str) -> 'ArchiveResult':
        """创建归档成功的结果"""
        return cls(
            status="archived",
            message="归档成功",
            archived_file=archive_file
        )
    
    @classmethod
    def skipped(cls, reason: str = "当天已归档") -> 'ArchiveResult':
        """创建跳过归档的结果"""
        return cls(
            status="skipped",
            message=reason
        )
    
    @classmethod
    def noop(cls, reason: str = "源文件不存在") -> 'ArchiveResult':
        """创建无操作的结果"""
        return cls(
            status="noop",
            message=reason
        )
    
    @classmethod
    def failed(cls, error_msg: str, error: Optional[Exception] = None) -> 'ArchiveResult':
        """创建归档失败的结果"""
        return cls(
            status="failed",
            message=f"归档失败: {error_msg}",
            error=str(error) if error else error_msg
        )


@dataclass
class CleanupResult:
    """清理操作结果"""
    success: bool
    message: str
    deleted_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    @property
    def total_deleted(self) -> int:
        """获取成功删除的文件数"""
        return len(self.deleted_files)
    
    @property
    def total_failed(self) -> int:
        """获取失败删除的文件数"""
        return len(self.failed_files)
    
    @classmethod
    def success_result(cls, deleted_files: List[str]) -> 'CleanupResult':
        """创建清理成功的结果"""
        if deleted_files:
            return cls(
                success=True,
                message=f"清理了 {len(deleted_files)} 个过期归档",
                deleted_files=deleted_files
            )
        else:
            return cls(
                success=True,
                message="无需清理"
            )
    
    @classmethod
    def failure_result(cls, error_msg: str, failed_files: List[str] = None) -> 'CleanupResult':
        """创建清理失败的结果"""
        return cls(
            success=False,
            message=f"清理失败: {error_msg}",
            failed_files=failed_files or [],
            error=error_msg
        )


@dataclass
class ToolResult:
    """工具运行结果"""
    exit_code: int
    archive_result: Optional[ArchiveResult] = None
    cleanup_result: Optional[CleanupResult] = None
    
    @property
    def success(self) -> bool:
        """判断工具运行是否成功"""
        return self.exit_code == 0