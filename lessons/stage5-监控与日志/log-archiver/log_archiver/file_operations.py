"""
文件操作模块
封装所有文件系统操作，提供统一的错误处理。
"""

import os
import shutil
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FileOperations:
    """文件操作工具类"""
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str) -> bool:
        """
        复制文件
        
        参数:
            source_path: 源文件路径
            destination_path: 目标文件路径
            
        返回:
            True表示成功，False表示失败
        """
        try:
            # 检查源文件是否存在
            if not os.path.exists(source_path):
                logger.error(f"源文件不存在: {source_path}")
                return False
            
            # 检查源文件是否可读
            if not os.access(source_path, os.R_OK):
                logger.error(f"源文件不可读: {source_path}")
                return False
            
            # 确保目标目录存在
            dest_dir = os.path.dirname(destination_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, destination_path)
            
            # 验证复制是否成功
            if os.path.exists(destination_path):
                source_size = os.path.getsize(source_path)
                dest_size = os.path.getsize(destination_path)
                
                if source_size == dest_size:
                    logger.debug(f"文件复制成功: {source_path} -> {destination_path}")
                    return True
                else:
                    logger.error(f"文件大小不一致: 源={source_size}字节, 目标={dest_size}字节")
                    # 清理不完整的复制
                    try:
                        os.remove(destination_path)
                    except OSError:
                        pass
                    return False
            else:
                logger.error(f"目标文件未创建: {destination_path}")
                return False
                
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            return False
        except OSError as e:
            logger.error(f"操作系统错误: {e}")
            return False
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return False
    
    @staticmethod
    def truncate_file(file_path: str) -> bool:
        """
        清空文件内容
        
        参数:
            file_path: 文件路径
            
        返回:
            True表示成功，False表示失败
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 检查文件是否可写
            if not os.access(file_path, os.W_OK):
                logger.error(f"文件不可写: {file_path}")
                return False
            
            # 备份原始大小（用于日志）
            original_size = os.path.getsize(file_path)
            
            # 清空文件
            with open(file_path, 'w') as f:
                f.write('')  # 写入空内容
            
            # 验证清空是否成功
            new_size = os.path.getsize(file_path)
            
            if new_size == 0:
                logger.debug(f"文件清空成功: {file_path} ({original_size}字节 -> 0字节)")
                return True
            else:
                logger.error(f"文件清空失败: 新大小={new_size}字节")
                return False
                
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            return False
        except OSError as e:
            logger.error(f"操作系统错误: {e}")
            return False
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件
        
        参数:
            file_path: 文件路径
            
        返回:
            True表示成功，False表示失败
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.debug(f"文件不存在（无需删除）: {file_path}")
                return True  # 文件不存在被视为"成功"（幂等性）
            
            # 检查文件是否可删除
            if not os.access(file_path, os.W_OK):
                logger.error(f"文件不可删除: {file_path}")
                return False
            
            # 记录文件大小（用于日志）
            file_size = os.path.getsize(file_path)
            
            # 删除文件
            os.remove(file_path)
            
            # 验证删除是否成功
            if not os.path.exists(file_path):
                logger.debug(f"文件删除成功: {file_path} ({file_size}字节)")
                return True
            else:
                logger.error(f"文件删除失败: {file_path}")
                return False
                
        except PermissionError as e:
            logger.error(f"权限错误: {e}")
            return False
        except OSError as e:
            logger.error(f"操作系统错误: {e}")
            return False
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        检查文件是否存在
        
        参数:
            file_path: 文件路径
            
        返回:
            True表示存在，False表示不存在
        """
        try:
            return os.path.exists(file_path) and os.path.isfile(file_path)
        except Exception as e:
            logger.error(f"检查文件存在性时出错: {e}")
            return False
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        获取文件大小
        
        参数:
            file_path: 文件路径
            
        返回:
            文件大小（字节），如果文件不存在或出错则返回None
        """
        try:
            if FileOperations.file_exists(file_path):
                return os.path.getsize(file_path)
            return None
        except Exception as e:
            logger.error(f"获取文件大小时出错: {e}")
            return None
    
    @staticmethod
    def files_equal(file1_path: str, file2_path: str, compare_size_only: bool = False) -> bool:
        """
        比较两个文件是否相同
        
        参数:
            file1_path: 第一个文件路径
            file2_path: 第二个文件路径
            compare_size_only: 是否仅比较文件大小
            
        返回:
            True表示文件相同，False表示不同
        """
        try:
            # 检查两个文件都存在
            if not (FileOperations.file_exists(file1_path) and 
                    FileOperations.file_exists(file2_path)):
                return False
            
            # 比较文件大小
            size1 = FileOperations.get_file_size(file1_path)
            size2 = FileOperations.get_file_size(file2_path)
            
            if size1 != size2:
                return False
            
            # 如果仅比较大小，则到此为止
            if compare_size_only:
                return True
            
            # 比较文件内容
            with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
                # 逐块比较，避免大文件内存问题
                chunk_size = 8192  # 8KB块
                while True:
                    chunk1 = f1.read(chunk_size)
                    chunk2 = f2.read(chunk_size)
                    
                    if chunk1 != chunk2:
                        return False
                    
                    if not chunk1:  # 两个文件都已读取完毕
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"比较文件时出错: {e}")
            return False
    
    @staticmethod
    def find_files_by_pattern(directory: str, pattern: str) -> list:
        """
        根据模式查找文件
        
        参数:
            directory: 目录路径
            pattern: 文件名模式（支持*通配符）
            
        返回:
            匹配的文件路径列表
        """
        import glob
        
        try:
            search_path = os.path.join(directory, pattern)
            return glob.glob(search_path)
        except Exception as e:
            logger.error(f"查找文件时出错: {e}")
            return []
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        确保目录存在（如果不存在则创建）
        
        参数:
            directory_path: 目录路径
            
        返回:
            True表示成功，False表示失败
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录时出错: {e}")
            return False
    
    @staticmethod
    def get_file_modification_time(file_path: str) -> Optional[float]:
        """
        获取文件修改时间
        
        参数:
            file_path: 文件路径
            
        返回:
            修改时间（UNIX时间戳），如果文件不存在或出错则返回None
        """
        try:
            if FileOperations.file_exists(file_path):
                return os.path.getmtime(file_path)
            return None
        except Exception as e:
            logger.error(f"获取文件修改时间时出错: {e}")
            return None
    
    @staticmethod
    def safe_file_operation(operation_func, *args, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        安全执行文件操作
        
        参数:
            operation_func: 要执行的文件操作函数
            *args, **kwargs: 操作函数的参数
            
        返回:
            (成功标志, 错误信息)
        """
        try:
            result = operation_func(*args, **kwargs)
            return (result, None if result else "操作失败")
        except PermissionError as e:
            return (False, f"权限错误: {e}")
        except OSError as e:
            return (False, f"操作系统错误: {e}")
        except Exception as e:
            return (False, f"未知错误: {e}")