#!/usr/bin/env python3
"""
日志归档工具 - 主入口点
按日期归档日志文件并清理过期归档。
"""

import sys
import os

# 添加当前目录到Python路径，以便导入log_archiver模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_archiver.cli import main


if __name__ == "__main__":
    main()