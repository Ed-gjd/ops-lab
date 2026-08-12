"""
日志归档器模块
负责日志文件的归档和清空操作。
"""

import os
from datetime import date
from typing import Optional
from .models import ArchiveDate, ArchiveResult
from .file_operations import FileOperations
from .logger import ToolLogger


class LogArchiver:
    """
    日志归档器类
    负责按日期归档日志文件，处理归档逻辑
    """
    
    def __init__(self, log_file_path: str, logger: Optional[ToolLogger] = None):
        """
        初始化日志归档器
        
        参数:
            log_file_path: 日志文件路径
            logger: 日志记录器实例
        """
        self.log_file_path = log_file_path
        self.logger = logger or ToolLogger.create_default_logger()
        
        # 提取基本名称（不含扩展名）
        self.base_name = self._extract_base_name(log_file_path)
        
        # 缓存文件存在性检查结果
        self._log_file_exists = None
    
    def _extract_base_name(self, file_path: str) -> str:
        """
        从文件路径提取基本名称（不含扩展名）
        
        参数:
            file_path: 文件路径
            
        返回:
            基本名称
        """
        # 获取文件名（不含路径）
        filename = os.path.basename(file_path)
        
        # 移除扩展名
        if '.' in filename:
            return filename.rsplit('.', 1)[0]
        return filename
    
    def _get_today_archive_filename(self) -> str:
        """
        获取今天的归档文件名
        
        返回:
            归档文件名
        """
        today = date.today()
        archive_date = ArchiveDate.today()
        return f"{self.base_name}-{archive_date.to_string()}.log"
    
    def _get_archive_file_path(self, archive_filename: str) -> str:
        """
        获取归档文件的完整路径
        
        参数:
            archive_filename: 归档文件名
            
        返回:
            归档文件完整路径
        """
        # 归档文件与源文件在同一目录
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir:
            return os.path.join(log_dir, archive_filename)
        return archive_filename
    
    def _log_file_exists(self) -> bool:
        """
        检查日志文件是否存在
        
        返回:
            True表示存在，False表示不存在
        """
        # 使用缓存避免重复检查
        if self._log_file_exists is None:
            self._log_file_exists = FileOperations.file_exists(self.log_file_path)
        return self._log_file_exists
    
    def _today_archive_exists(self) -> bool:
        """
        检查今天的归档文件是否已存在
        
        返回:
            True表示已存在，False表示不存在
        """
        archive_filename = self._get_today_archive_filename()
        archive_path = self._get_archive_file_path(archive_filename)
        return FileOperations.file_exists(archive_path)
    
    def should_archive(self) -> bool:
        """
        判断是否需要归档
        
        返回:
            True表示需要归档，False表示不需要
        """
        # 如果日志文件不存在，不需要归档
        if not self._log_file_exists():
            self.logger.debug(f"日志文件不存在: {self.log_file_path}")
            return False
        
        # 如果今天的归档文件已存在，不需要归档
        if self._today_archive_exists():
            self.logger.debug(f"今天的归档文件已存在: {self._get_today_archive_filename()}")
            return False
        
        # 检查日志文件是否为空（空文件不需要归档）
        file_size = FileOperations.get_file_size(self.log_file_path)
        if file_size == 0:
            self.logger.debug(f"日志文件为空: {self.log_file_path}")
            return False
        
        return True
    
    def archive(self) -> ArchiveResult:
        """
        执行归档操作
        
        返回:
            ArchiveResult对象
        """
        self.logger.progress(f"开始归档: {self.log_file_path}")
        
        # 检查日志文件是否存在
        if not self._log_file_exists():
            self.logger.warning(f"日志文件不存在: {self.log_file_path}")
            return ArchiveResult.noop("源文件不存在")
        
        # 检查文件大小
        file_size = FileOperations.get_file_size(self.log_file_path)
        if file_size == 0:
            self.logger.info(f"日志文件为空，跳过归档: {self.log_file_path}")
            return ArchiveResult.noop("源文件为空")
        
        # 获取今天的归档文件名
        archive_filename = self._get_today_archive_filename()
        archive_path = self._get_archive_file_path(archive_filename)
        
        # 检查是否已归档
        if FileOperations.file_exists(archive_path):
            self.logger.info(f"当天已归档: {archive_filename}")
            return ArchiveResult.skipped("当天已归档")
        
        # 执行文件复制
        self.logger.debug(f"复制文件: {self.log_file_path} -> {archive_path}")
        copy_success = FileOperations.copy_file(self.log_file_path, archive_path)
        
        if not copy_success:
            error_msg = f"文件复制失败: {self.log_file_path} -> {archive_path}"
            self.logger.error(error_msg)
            return ArchiveResult.failed(error_msg)
        
        # 验证归档完整性
        if not FileOperations.files_equal(self.log_file_path, archive_path):
            error_msg = f"归档文件内容不一致: {archive_path}"
            self.logger.error(error_msg)
            
            # 清理不完整的归档文件
            FileOperations.delete_file(archive_path)
            return ArchiveResult.failed(error_msg)
        
        # 归档成功
        self.logger.success(f"归档成功: {archive_filename} ({file_size}字节)")
        return ArchiveResult.archived(archive_path)
    
    def clear_log_file(self) -> bool:
        """
        清空日志文件
        
        返回:
            True表示成功，False表示失败
        """
        self.logger.progress(f"清空日志文件: {self.log_file_path}")
        
        # 检查文件是否存在
        if not self._log_file_exists():
            self.logger.warning(f"日志文件不存在，无需清空: {self.log_file_path}")
            return True  # 文件不存在视为成功（幂等性）
        
        # 检查文件大小
        file_size = FileOperations.get_file_size(self.log_file_path)
        if file_size == 0:
            self.logger.debug(f"日志文件已为空: {self.log_file_path}")
            return True  # 文件已空视为成功（幂等性）
        
        # 执行文件清空
        truncate_success = FileOperations.truncate_file(self.log_file_path)
        
        if not truncate_success:
            error_msg = f"清空日志文件失败: {self.log_file_path}"
            self.logger.error(error_msg)
            return False
        
        # 验证清空结果
        new_size = FileOperations.get_file_size(self.log_file_path)
        if new_size != 0:
            error_msg = f"清空后文件大小不为0: {new_size}字节"
            self.logger.error(error_msg)
            return False
        
        self.logger.success(f"日志文件已清空: {self.log_file_path} ({file_size}字节 -> 0字节)")
        return True
    
    def safe_archive_and_clear(self) -> ArchiveResult:
        """
        安全执行归档和清空操作（原子操作）
        
        返回:
            ArchiveResult对象
        """
        self.logger.section("归档操作")
        
        # 执行归档
        archive_result = self.archive()
        
        # 如果归档成功，清空源文件
        if archive_result.was_archived:
            clear_success = self.clear_log_file()
            
            if not clear_success:
                # 清空失败，记录错误但保持归档结果
                error_msg = "归档成功但清空源文件失败"
                self.logger.error(error_msg)
                
                # 创建一个新的结果对象，包含归档成功但清空失败的信息
                return ArchiveResult(
                    status="archived",
                    message=f"{archive_result.message}，但{error_msg}",
                    archived_file=archive_result.archived_file,
                    error=error_msg
                )
        
        return archive_result
    
    def get_archive_info(self) -> dict:
        """
        获取归档信息
        
        返回:
            包含归档信息的字典
        """
        log_file_exists = self._log_file_exists()
        today_archive_exists = self._today_archive_exists()
        file_size = FileOperations.get_file_size(self.log_file_path) if log_file_exists else 0
        
        return {
            "log_file_path": self.log_file_path,
            "base_name": self.base_name,
            "log_file_exists": log_file_exists,
            "today_archive_exists": today_archive_exists,
            "file_size": file_size,
            "should_archive": self.should_archive() if log_file_exists else False,
            "today_archive_filename": self._get_today_archive_filename() if log_file_exists else None
        }
    
    def print_archive_info(self):
        """打印归档信息"""
        info = self.get_archive_info()
        
        self.logger.section("归档信息")
        self.logger.info(f"日志文件: {info['log_file_path']}")
        self.logger.info(f"基本名称: {info['base_name']}")
        self.logger.info(f"文件存在: {'是' if info['log_file_exists'] else '否'}")
        
        if info['log_file_exists']:
            self.logger.info(f"文件大小: {info['file_size']}字节")
            self.logger.info(f"今天归档存在: {'是' if info['today_archive_exists'] else '否'}")
            self.logger.info(f"需要归档: {'是' if info['should_archive'] else '否'}")
            
            if info['today_archive_exists']:
                self.logger.info(f"今天归档文件: {info['today_archive_filename']}")


# 便捷函数
def archive_log_file(log_file_path: str, verbose: bool = False) -> ArchiveResult:
    """
    便捷函数：归档单个日志文件
    
    参数:
        log_file_path: 日志文件路径
        verbose: 是否启用详细模式
        
    返回:
        ArchiveResult对象
    """
    logger = ToolLogger.create_default_logger(verbose=verbose)
    archiver = LogArchiver(log_file_path, logger)
    return archiver.safe_archive_and_clear()


def check_archive_status(log_file_path: str, verbose: bool = False) -> dict:
    """
    便捷函数：检查归档状态
    
    参数:
        log_file_path: 日志文件路径
        verbose: 是否启用详细模式
        
    返回:
        包含归档信息的字典
    """
    logger = ToolLogger.create_default_logger(verbose=verbose)
    archiver = LogArchiver(log_file_path, logger)
    return archiver.get_archive_info()


if __name__ == "__main__":
    # 命令行测试入口
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python -m log_archiver.archiver <日志文件路径> [--verbose]")
        sys.exit(1)
    
    log_file = sys.argv[1]
    verbose = "--verbose" in sys.argv
    
    result = archive_log_file(log_file, verbose)
    
    if result.success:
        print(f"归档操作: {result.message}")
        if result.archived_file:
            print(f"归档文件: {result.archived_file}")
        sys.exit(0)
    else:
        print(f"错误: {result.message}")
        if result.error:
            print(f"详情: {result.error}")
        sys.exit(1)