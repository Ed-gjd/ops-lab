"""
保留期管理器模块
负责管理归档文件的保留策略，清理过期文件。
"""

import os
import re
from datetime import date, timedelta
from typing import List, Tuple, Optional
from .models import ArchiveDate, CleanupResult
from .file_operations import FileOperations
from .logger import ToolLogger


class RetentionManager:
    """
    保留期管理器类
    负责管理归档文件的保留策略，清理过期文件
    """
    
    def __init__(self, log_file_path: str, retention_days: int = 7, 
                 logger: Optional[ToolLogger] = None):
        """
        初始化保留期管理器
        
        参数:
            log_file_path: 日志文件路径
            retention_days: 保留天数
            logger: 日志记录器实例
        """
        self.log_file_path = log_file_path
        self.retention_days = retention_days
        self.logger = logger or ToolLogger.create_default_logger()
        
        # 提取基本名称（不含扩展名）
        self.base_name = self._extract_base_name(log_file_path)
        
        # 归档文件名模式
        self.archive_pattern = f"{self.base_name}-*.log"
        
        # 缓存归档文件列表
        self._archive_files = None
    
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
    
    def _get_archive_directory(self) -> str:
        """
        获取归档文件所在的目录
        
        返回:
            目录路径
        """
        return os.path.dirname(self.log_file_path) or "."
    
    def find_archive_files(self, refresh: bool = False) -> List[str]:
        """
        查找所有归档文件
        
        参数:
            refresh: 是否刷新缓存
            
        返回:
            归档文件路径列表
        """
        if self._archive_files is not None and not refresh:
            return self._archive_files
        
        archive_dir = self._get_archive_directory()
        archive_files = FileOperations.find_files_by_pattern(archive_dir, self.archive_pattern)
        
        # 过滤出有效的归档文件（符合命名规范）
        valid_archive_files = []
        for file_path in archive_files:
            filename = os.path.basename(file_path)
            
            # 解析归档日期
            archive_date = ArchiveDate.from_filename(filename, self.base_name)
            if archive_date is not None:
                valid_archive_files.append(file_path)
            else:
                self.logger.debug(f"跳过无效归档文件: {filename}")
        
        # 按修改时间排序（最新的在前）
        valid_archive_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        self._archive_files = valid_archive_files
        return valid_archive_files
    
    def is_expired(self, archive_file_path: str) -> bool:
        """
        判断归档文件是否过期
        
        参数:
            archive_file_path: 归档文件路径
            
        返回:
            True表示过期，False表示未过期
        """
        filename = os.path.basename(archive_file_path)
        
        # 解析归档日期
        archive_date = ArchiveDate.from_filename(filename, self.base_name)
        if archive_date is None:
            # 无法解析日期，视为无效文件（不删除）
            self.logger.debug(f"无法解析归档文件日期: {filename}")
            return False
        
        # 检查是否过期
        try:
            return archive_date.is_before(self.retention_days)
        except ValueError as e:
            self.logger.error(f"日期比较错误: {e}")
            return False
    
    def get_expired_files(self) -> List[str]:
        """
        获取所有过期的归档文件
        
        返回:
            过期归档文件路径列表
        """
        archive_files = self.find_archive_files()
        expired_files = []
        
        for file_path in archive_files:
            if self.is_expired(file_path):
                expired_files.append(file_path)
        
        return expired_files
    
    def cleanup_expired(self, dry_run: bool = False) -> CleanupResult:
        """
        清理过期归档文件
        
        参数:
            dry_run: 模拟运行模式（不实际删除文件）
            
        返回:
            CleanupResult对象
        """
        self.logger.section("清理过期归档")
        
        if dry_run:
            self.logger.info("模拟运行模式 - 不会实际删除文件")
        
        # 查找所有归档文件
        archive_files = self.find_archive_files(refresh=True)
        total_archives = len(archive_files)
        
        if total_archives == 0:
            self.logger.info("没有找到归档文件")
            return CleanupResult.success_result([])
        
        self.logger.info(f"找到 {total_archives} 个归档文件")
        
        # 获取过期文件
        expired_files = self.get_expired_files()
        expired_count = len(expired_files)
        
        if expired_count == 0:
            self.logger.info(f"没有过期文件（保留 {self.retention_days} 天）")
            return CleanupResult.success_result([])
        
        self.logger.info(f"发现 {expired_count} 个过期文件")
        
        # 执行清理
        deleted_files = []
        failed_files = []
        
        for file_path in expired_files:
            filename = os.path.basename(file_path)
            
            # 解析归档日期（用于日志）
            archive_date = ArchiveDate.from_filename(filename, self.base_name)
            archive_date_str = archive_date.to_string() if archive_date else "未知日期"
            
            # 获取文件大小（用于日志）
            file_size = FileOperations.get_file_size(file_path) or 0
            
            if dry_run:
                self.logger.info(f"[模拟] 删除过期归档: {filename} ({archive_date_str}, {file_size}字节)")
                deleted_files.append(file_path)
            else:
                self.logger.progress(f"删除过期归档: {filename} ({archive_date_str}, {file_size}字节)")
                
                # 执行删除
                delete_success = FileOperations.delete_file(file_path)
                
                if delete_success:
                    self.logger.debug(f"删除成功: {filename}")
                    deleted_files.append(file_path)
                else:
                    error_msg = f"删除失败: {filename}"
                    self.logger.error(error_msg)
                    failed_files.append(file_path)
        
        # 生成结果
        if failed_files:
            error_msg = f"清理完成，但有 {len(failed_files)} 个文件删除失败"
            self.logger.error(error_msg)
            return CleanupResult.failure_result(error_msg, failed_files)
        elif deleted_files:
            self.logger.success(f"清理完成，删除了 {len(deleted_files)} 个过期归档文件")
            return CleanupResult.success_result(deleted_files)
        else:
            self.logger.info("清理完成，没有删除任何文件")
            return CleanupResult.success_result([])
    
    def get_retention_info(self) -> dict:
        """
        获取保留期信息
        
        返回:
            包含保留期信息的字典
        """
        archive_files = self.find_archive_files()
        expired_files = self.get_expired_files()
        
        # 计算最早的归档日期
        earliest_date = None
        for file_path in archive_files:
            filename = os.path.basename(file_path)
            archive_date = ArchiveDate.from_filename(filename, self.base_name)
            if archive_date:
                date_obj = archive_date.to_date()
                if earliest_date is None or date_obj < earliest_date:
                    earliest_date = date_obj
        
        # 计算最晚的归档日期
        latest_date = None
        for file_path in archive_files:
            filename = os.path.basename(file_path)
            archive_date = ArchiveDate.from_filename(filename, self.base_name)
            if archive_date:
                date_obj = archive_date.to_date()
                if latest_date is None or date_obj > latest_date:
                    latest_date = date_obj
        
        # 计算保留截止日期
        cutoff_date = date.today() - timedelta(days=self.retention_days)
        
        return {
            "log_file_path": self.log_file_path,
            "base_name": self.base_name,
            "retention_days": self.retention_days,
            "total_archives": len(archive_files),
            "expired_archives": len(expired_files),
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d"),
            "earliest_archive_date": earliest_date.strftime("%Y-%m-%d") if earliest_date else None,
            "latest_archive_date": latest_date.strftime("%Y-%m-%d") if latest_date else None
        }
    
    def print_retention_info(self, verbose: bool = False):
        """打印保留期信息"""
        info = self.get_retention_info()
        archive_files = self.find_archive_files()
        
        self.logger.section("保留期信息")
        self.logger.info(f"日志文件: {info['log_file_path']}")
        self.logger.info(f"基本名称: {info['base_name']}")
        self.logger.info(f"保留天数: {info['retention_days']} 天")
        self.logger.info(f"保留截止日期: {info['cutoff_date']} 之前")
        self.logger.info(f"归档文件总数: {info['total_archives']}")
        self.logger.info(f"过期文件数: {info['expired_archives']}")
        
        if info['earliest_archive_date']:
            self.logger.info(f"最早归档日期: {info['earliest_archive_date']}")
        
        if info['latest_archive_date']:
            self.logger.info(f"最新归档日期: {info['latest_archive_date']}")
        
        # 详细模式下显示所有归档文件
        if verbose and archive_files:
            self.logger.section("归档文件列表")
            for file_path in archive_files:
                filename = os.path.basename(file_path)
                archive_date = ArchiveDate.from_filename(filename, self.base_name)
                file_size = FileOperations.get_file_size(file_path) or 0
                is_expired = self.is_expired(file_path)
                
                date_str = archive_date.to_string() if archive_date else "无效日期"
                expired_marker = " (过期)" if is_expired else ""
                
                self.logger.info(f"  {filename} - {date_str} - {file_size}字节{expired_marker}")
    
    def cleanup_all_archives(self, dry_run: bool = False) -> CleanupResult:
        """
        清理所有归档文件（危险操作）
        
        参数:
            dry_run: 模拟运行模式
            
        返回:
            CleanupResult对象
        """
        self.logger.warning("执行危险操作：清理所有归档文件")
        
        if dry_run:
            self.logger.info("模拟运行模式 - 不会实际删除文件")
        
        archive_files = self.find_archive_files(refresh=True)
        
        if not archive_files:
            self.logger.info("没有归档文件可清理")
            return CleanupResult.success_result([])
        
        self.logger.warning(f"将清理所有 {len(archive_files)} 个归档文件")
        
        # 执行清理
        deleted_files = []
        failed_files = []
        
        for file_path in archive_files:
            filename = os.path.basename(file_path)
            file_size = FileOperations.get_file_size(file_path) or 0
            
            if dry_run:
                self.logger.info(f"[模拟] 删除归档: {filename} ({file_size}字节)")
                deleted_files.append(file_path)
            else:
                self.logger.progress(f"删除归档: {filename} ({file_size}字节)")
                
                delete_success = FileOperations.delete_file(file_path)
                
                if delete_success:
                    deleted_files.append(file_path)
                else:
                    failed_files.append(file_path)
        
        # 生成结果
        if failed_files:
            error_msg = f"清理完成，但有 {len(failed_files)} 个文件删除失败"
            self.logger.error(error_msg)
            return CleanupResult.failure_result(error_msg, failed_files)
        else:
            self.logger.success(f"清理完成，删除了 {len(deleted_files)} 个归档文件")
            return CleanupResult.success_result(deleted_files)


# 便捷函数
def cleanup_expired_archives(log_file_path: str, retention_days: int = 7, 
                            verbose: bool = False, dry_run: bool = False) -> CleanupResult:
    """
    便捷函数：清理过期归档文件
    
    参数:
        log_file_path: 日志文件路径
        retention_days: 保留天数
        verbose: 是否启用详细模式
        dry_run: 模拟运行模式
        
    返回:
        CleanupResult对象
    """
    logger = ToolLogger.create_default_logger(verbose=verbose)
    manager = RetentionManager(log_file_path, retention_days, logger)
    return manager.cleanup_expired(dry_run)


def get_retention_status(log_file_path: str, retention_days: int = 7, 
                        verbose: bool = False) -> dict:
    """
    便捷函数：获取保留期状态
    
    参数:
        log_file_path: 日志文件路径
        retention_days: 保留天数
        verbose: 是否启用详细模式
        
    返回:
        包含保留期信息的字典
    """
    logger = ToolLogger.create_default_logger(verbose=verbose)
    manager = RetentionManager(log_file_path, retention_days, logger)
    return manager.get_retention_info()


if __name__ == "__main__":
    # 命令行测试入口
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="归档文件保留期管理器")
    parser.add_argument("log_file", help="日志文件路径")
    parser.add_argument("-r", "--retention-days", type=int, default=7, 
                       help="保留天数（默认: 7）")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="详细输出模式")
    parser.add_argument("--dry-run", action="store_true", 
                       help="模拟运行，不实际删除文件")
    parser.add_argument("--info", action="store_true", 
                       help="仅显示信息，不执行清理")
    parser.add_argument("--cleanup-all", action="store_true", 
                       help="清理所有归档文件（危险操作）")
    
    args = parser.parse_args()
    
    logger = ToolLogger.create_default_logger(verbose=args.verbose)
    manager = RetentionManager(args.log_file, args.retention_days, logger)
    
    if args.info:
        manager.print_retention_info(verbose=args.verbose)
        sys.exit(0)
    elif args.cleanup_all:
        result = manager.cleanup_all_archives(dry_run=args.dry_run)
    else:
        result = manager.cleanup_expired(dry_run=args.dry_run)
    
    if result.success:
        print(f"清理操作: {result.message}")
        if result.total_deleted > 0:
            print(f"删除文件数: {result.total_deleted}")
            if args.verbose:
                for file_path in result.deleted_files:
                    print(f"  {os.path.basename(file_path)}")
        sys.exit(0)
    else:
        print(f"错误: {result.message}")
        if result.error:
            print(f"详情: {result.error}")
        sys.exit(1)