"""
命令行接口模块
提供日志归档工具的命令行接口。
"""

import argparse
import sys
from typing import Optional, List
from .models import ToolConfig, ToolResult
from .archiver import LogArchiver, archive_log_file
from .retention_manager import RetentionManager, cleanup_expired_archives
from .logger import ToolLogger


class CLIInterface:
    """
    命令行接口类
    处理命令行参数解析和工具执行协调
    """
    
    def __init__(self):
        """初始化命令行接口"""
        self.parser = self._create_parser()
        self.logger = None  # 在parse_arguments中初始化
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        创建参数解析器
        
        返回:
            ArgumentParser对象
        """
        parser = argparse.ArgumentParser(
            description='日志归档工具 - 按日期归档日志文件并清理过期归档',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  %(prog)s                        归档app.log并清理7天前的归档
  %(prog)s --log-file system.log  归档system.log
  %(prog)s --retention-days 30    保留30天归档
  %(prog)s --dry-run              模拟运行，不执行实际文件操作
  %(prog)s --verbose              详细输出模式
  %(prog)s --info                 仅显示信息，不执行操作
  %(prog)s --cleanup-only         仅清理过期归档，不执行归档
  %(prog)s --archive-only         仅执行归档，不清理过期归档
            """
        )
        
        # 主要参数
        parser.add_argument(
            '--log-file', '-l',
            type=str,
            default='app.log',
            help='要归档的日志文件路径（默认: app.log）'
        )
        
        parser.add_argument(
            '--retention-days', '-r',
            type=int,
            default=7,
            help='归档文件保留天数（默认: 7）'
        )
        
        # 操作模式
        parser.add_argument(
            '--archive-only',
            action='store_true',
            help='仅执行归档操作，不清理过期归档'
        )
        
        parser.add_argument(
            '--cleanup-only',
            action='store_true',
            help='仅清理过期归档，不执行归档操作'
        )
        
        parser.add_argument(
            '--info',
            action='store_true',
            help='仅显示信息，不执行任何操作'
        )
        
        # 输出控制
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='详细输出模式'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行模式，不执行实际文件操作'
        )
        
        # 特殊操作
        parser.add_argument(
            '--cleanup-all',
            action='store_true',
            help='清理所有归档文件（危险操作）'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        return parser
    
    def parse_arguments(self, args: Optional[List[str]] = None) -> ToolConfig:
        """
        解析命令行参数
        
        参数:
            args: 命令行参数列表（默认使用sys.argv[1:]）
            
        返回:
            ToolConfig对象
        """
        if args is None:
            args = sys.argv[1:]
        
        # 解析参数
        parsed_args = self.parser.parse_args(args)
        
        # 创建日志记录器
        self.logger = ToolLogger.create_default_logger(verbose=parsed_args.verbose)
        
        # 创建配置对象
        config = ToolConfig.from_namespace(parsed_args)
        
        # 记录配置信息
        if parsed_args.verbose:
            self.logger.section("配置信息")
            self.logger.info(f"日志文件: {config.log_file_path}")
            self.logger.info(f"保留天数: {config.retention_days}")
            self.logger.info(f"详细模式: {'是' if config.verbose else '否'}")
            self.logger.info(f"模拟运行: {'是' if config.dry_run else '否'}")
            
            # 操作模式
            if parsed_args.archive_only:
                self.logger.info("操作模式: 仅归档")
            elif parsed_args.cleanup_only:
                self.logger.info("操作模式: 仅清理")
            elif parsed_args.info:
                self.logger.info("操作模式: 仅显示信息")
            elif parsed_args.cleanup_all:
                self.logger.warning("操作模式: 清理所有归档（危险操作）")
            else:
                self.logger.info("操作模式: 完整归档和清理")
        
        return config
    
    def run(self, config: Optional[ToolConfig] = None) -> ToolResult:
        """
        执行主逻辑
        
        参数:
            config: 工具配置（如果为None则从命令行解析）
            
        返回:
            ToolResult对象
        """
        # 如果没有提供配置，从命令行解析
        if config is None:
            try:
                config = self.parse_arguments()
            except SystemExit:
                # argparse在--help或错误时调用sys.exit()
                return ToolResult(exit_code=1)
        
        # 确保日志记录器已初始化
        if self.logger is None:
            self.logger = ToolLogger.create_default_logger(verbose=config.verbose)
        
        # 设置日志记录器详细模式
        self.logger.set_verbose(config.verbose)
        
        # 根据操作模式执行
        args = self.parser.parse_args([])  # 获取默认参数来检查模式
        
        try:
            # 重新解析以获取实际参数
            actual_args = self.parser.parse_args()
            
            if actual_args.info:
                return self._run_info_mode(config)
            elif actual_args.cleanup_all:
                return self._run_cleanup_all_mode(config)
            elif actual_args.archive_only:
                return self._run_archive_only_mode(config)
            elif actual_args.cleanup_only:
                return self._run_cleanup_only_mode(config)
            else:
                return self._run_full_mode(config)
                
        except AttributeError:
            # 如果没有实际参数（例如在测试中），运行完整模式
            return self._run_full_mode(config)
    
    def _run_info_mode(self, config: ToolConfig) -> ToolResult:
        """运行信息显示模式"""
        self.logger.section("信息模式")
        
        try:
            # 显示归档信息
            archiver = LogArchiver(config.log_file_path, self.logger)
            archiver.print_archive_info()
            
            # 显示保留期信息
            manager = RetentionManager(config.log_file_path, config.retention_days, self.logger)
            manager.print_retention_info(verbose=config.verbose)
            
            # 打印日志统计
            self.logger.print_statistics()
            
            return ToolResult(exit_code=0)
            
        except Exception as e:
            self.logger.error(f"显示信息时出错: {e}")
            return ToolResult(exit_code=1)
    
    def _run_cleanup_all_mode(self, config: ToolConfig) -> ToolResult:
        """运行清理所有归档模式（危险操作）"""
        self.logger.section("清理所有归档模式")
        self.logger.warning("执行危险操作：清理所有归档文件")
        
        if config.dry_run:
            self.logger.info("模拟运行模式 - 不会实际删除文件")
        
        # 请求确认（在dry-run模式下跳过）
        if not config.dry_run:
            self.logger.warning("此操作将删除所有归档文件，不可恢复！")
            response = input("确认要继续吗？(yes/no): ").strip().lower()
            if response != 'yes':
                self.logger.info("操作已取消")
                return ToolResult(exit_code=0)
        
        try:
            manager = RetentionManager(config.log_file_path, config.retention_days, self.logger)
            cleanup_result = manager.cleanup_all_archives(dry_run=config.dry_run)
            
            if cleanup_result.success:
                if cleanup_result.total_deleted > 0:
                    self.logger.success(f"清理完成，删除了 {cleanup_result.total_deleted} 个归档文件")
                else:
                    self.logger.info("没有归档文件可清理")
                return ToolResult(exit_code=0, cleanup_result=cleanup_result)
            else:
                self.logger.error(f"清理失败: {cleanup_result.message}")
                if cleanup_result.error:
                    self.logger.error(f"错误详情: {cleanup_result.error}")
                return ToolResult(exit_code=1, cleanup_result=cleanup_result)
                
        except Exception as e:
            self.logger.error(f"清理所有归档时出错: {e}")
            return ToolResult(exit_code=1)
    
    def _run_archive_only_mode(self, config: ToolConfig) -> ToolResult:
        """运行仅归档模式"""
        self.logger.section("归档模式")
        
        if config.dry_run:
            self.logger.info("模拟运行模式 - 不会实际执行文件操作")
        
        try:
            archiver = LogArchiver(config.log_file_path, self.logger)
            archive_result = archiver.safe_archive_and_clear()
            
            if config.dry_run:
                self.logger.info("[模拟] 归档操作完成")
                return ToolResult(exit_code=0, archive_result=archive_result)
            
            if archive_result.success:
                if archive_result.was_archived:
                    self.logger.success(f"归档成功: {archive_result.message}")
                    if archive_result.archived_file:
                        self.logger.info(f"归档文件: {archive_result.archived_file}")
                else:
                    self.logger.info(f"归档操作: {archive_result.message}")
                return ToolResult(exit_code=0, archive_result=archive_result)
            else:
                self.logger.error(f"归档失败: {archive_result.message}")
                if archive_result.error:
                    self.logger.error(f"错误详情: {archive_result.error}")
                return ToolResult(exit_code=1, archive_result=archive_result)
                
        except Exception as e:
            self.logger.error(f"归档操作时出错: {e}")
            return ToolResult(exit_code=1)
    
    def _run_cleanup_only_mode(self, config: ToolConfig) -> ToolResult:
        """运行仅清理模式"""
        self.logger.section("清理模式")
        
        if config.dry_run:
            self.logger.info("模拟运行模式 - 不会实际删除文件")
        
        try:
            manager = RetentionManager(config.log_file_path, config.retention_days, self.logger)
            cleanup_result = manager.cleanup_expired(dry_run=config.dry_run)
            
            if cleanup_result.success:
                if cleanup_result.total_deleted > 0:
                    self.logger.success(f"清理完成: {cleanup_result.message}")
                else:
                    self.logger.info(f"清理操作: {cleanup_result.message}")
                return ToolResult(exit_code=0, cleanup_result=cleanup_result)
            else:
                self.logger.error(f"清理失败: {cleanup_result.message}")
                if cleanup_result.error:
                    self.logger.error(f"错误详情: {cleanup_result.error}")
                return ToolResult(exit_code=1, cleanup_result=cleanup_result)
                
        except Exception as e:
            self.logger.error(f"清理操作时出错: {e}")
            return ToolResult(exit_code=1)
    
    def _run_full_mode(self, config: ToolConfig) -> ToolResult:
        """运行完整模式（归档 + 清理）"""
        self.logger.section("日志归档工具")
        
        if config.dry_run:
            self.logger.info("模拟运行模式 - 不会实际执行文件操作")
        
        try:
            # 执行归档
            self.logger.progress("开始归档操作")
            archiver = LogArchiver(config.log_file_path, self.logger)
            archive_result = archiver.safe_archive_and_clear()
            
            # 执行清理
            self.logger.progress("开始清理操作")
            manager = RetentionManager(config.log_file_path, config.retention_days, self.logger)
            cleanup_result = manager.cleanup_expired(dry_run=config.dry_run)
            
            # 生成最终结果
            exit_code = 0
            
            if not archive_result.success and archive_result.status == "failed":
                self.logger.error("归档操作失败")
                exit_code = 1
            
            if not cleanup_result.success:
                self.logger.error("清理操作失败")
                exit_code = 1
            
            # 打印摘要
            self._print_summary(archive_result, cleanup_result, config.dry_run)
            
            # 打印日志统计
            if config.verbose:
                self.logger.print_statistics()
            
            return ToolResult(
                exit_code=exit_code,
                archive_result=archive_result,
                cleanup_result=cleanup_result
            )
            
        except Exception as e:
            self.logger.error(f"工具执行时出错: {e}")
            return ToolResult(exit_code=1)
    
    def _print_summary(self, archive_result, cleanup_result, dry_run: bool):
        """打印执行摘要"""
        self.logger.section("执行摘要")
        
        # 归档结果
        if archive_result.was_archived:
            self.logger.success(f"归档: 成功创建归档文件")
            if archive_result.archived_file:
                self.logger.info(f"归档文件: {archive_result.archived_file}")
        elif archive_result.status == "skipped":
            self.logger.info(f"归档: {archive_result.message}")
        elif archive_result.status == "noop":
            self.logger.info(f"归档: {archive_result.message}")
        elif archive_result.status == "failed":
            self.logger.failure(f"归档: {archive_result.message}")
        
        # 清理结果
        if cleanup_result.total_deleted > 0:
            if dry_run:
                self.logger.info(f"清理: 模拟删除 {cleanup_result.total_deleted} ��过期归档")
            else:
                self.logger.success(f"清理: 删除了 {cleanup_result.total_deleted} 个过期归档")
        else:
            self.logger.info(f"清理: {cleanup_result.message}")
        
        # 最终状态
        if dry_run:
            self.logger.info("模拟运行完成 - 未执行实际文件操作")
        else:
            if archive_result.success and cleanup_result.success:
                self.logger.success("所有操作完成成功")
            else:
                self.logger.warning("操作完成，但有警告或错误")


# 主入口点
def main():
    """命令行工具主入口点"""
    cli = CLIInterface()
    result = cli.run()
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()