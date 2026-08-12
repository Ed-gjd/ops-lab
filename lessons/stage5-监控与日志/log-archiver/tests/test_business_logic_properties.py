"""
业务逻辑属性测试
验证Property 3: 过期文件识别和Property 7: 文件操作幂等性
"""

import sys
import os
import tempfile
import shutil
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck
import pytest

from log_archiver.models import ArchiveDate
from log_archiver.archiver import LogArchiver
from log_archiver.retention_manager import RetentionManager
from log_archiver.logger import ToolLogger


# Property 3: 过期文件识别
# Validates: Requirements 3.1

@given(
    base_name=st.text(min_size=1, max_size=10).filter(lambda x: '-' not in x),
    year=st.integers(min_value=2000, max_value=2025),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # 避免2月29日等特殊日期
    retention_days=st.integers(min_value=1, max_value=365)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
def test_property_3_expired_file_detection(base_name, year, month, day, retention_days):
    """Property 3: 过期文件识别应正确工作"""
    try:
        # 创建有效的日期对象
        archive_date = date(year, month, day)
        today = date.today()
        
        # 计算归档日期与今天的天数差
        days_difference = (today - archive_date).days
        
        # 预期是否过期
        expected_expired = days_difference >= retention_days
        
        # 创建ArchiveDate对象
        archive_date_obj = ArchiveDate(year, month, day)
        
        # 使用is_before方法检查是否过期
        actual_expired = archive_date_obj.is_before(retention_days)
        
        # 验证结果一致性
        assert actual_expired == expected_expired, \
            f"过期检测不一致: 归档日期={archive_date}, " \
            f"保留天数={retention_days}, 预期={expected_expired}, 实际={actual_expired}"
        
        # 对于非过期文件，减少保留天数应该使其过期
        if not expected_expired and retention_days > 1:
            smaller_retention = max(1, retention_days - 1)
            # 在某些边界情况下可能不会过期，所以只检查如果确实过期的情况
            if days_difference >= smaller_retention:
                assert archive_date_obj.is_before(smaller_retention), \
                    f"减少保留天数应使文件过期: {archive_date} 在 {smaller_retention} 天前"
        
    except ValueError:
        # 如果date()构造函数抛出异常，说明不是有效日期，跳过测试
        pass


@given(
    base_name=st.text(min_size=1, max_size=10).filter(lambda x: '-' not in x),
    days_old=st.integers(min_value=0, max_value=400)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_3_retention_manager_expiry(base_name, days_old):
    """Property 3: RetentionManager应正确识别过期文件"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建模拟的日志文件
        log_file = os.path.join(temp_dir, f"{base_name}.log")
        with open(log_file, 'w') as f:
            f.write("test content")
        
        # 计算归档日期
        archive_date = date.today() - timedelta(days=days_old)
        
        # 创建归档文件
        archive_filename = f"{base_name}-{archive_date.strftime('%Y-%m-%d')}.log"
        archive_path = os.path.join(temp_dir, archive_filename)
        with open(archive_path, 'w') as f:
            f.write(f"archive content from {archive_date}")
        
        # 测试不同的保留天数
        for retention_days in [1, 7, 30, 100]:
            # 预期是否过期
            expected_expired = days_old >= retention_days
            
            # 创建RetentionManager
            manager = RetentionManager(log_file, retention_days)
            
            # 由于manager使用文件系统路径，我们需要模拟查找文件
            # 这里直接测试is_expired方法
            is_expired = manager.is_expired(archive_path)
            
            # 验证过期检测
            assert is_expired == expected_expired, \
                f"过期检测错误: 文件{days_old}天前, " \
                f"保留{retention_days}天, 预期={expected_expired}, 实际={is_expired}"


# Property 7: 文件操作幂等性
# Validates: Requirements 1.3, 2.2

@given(
    log_content=st.binary(min_size=0, max_size=1024),
    filename=st.text(min_size=1, max_size=15).filter(lambda x: '.' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_7_archive_idempotence(log_content, filename):
    """Property 7: 归档操作应具有幂等性"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建日志文件
        log_file = os.path.join(temp_dir, f"{filename}.log")
        
        if log_content:
            with open(log_file, 'wb') as f:
                f.write(log_content)
        
        # 创建LogArchiver（静默日志）
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)  # 减少日志输出
        logger = ToolLogger(verbose=False)
        archiver = LogArchiver(log_file, logger)
        
        # 第一次归档
        result1 = archiver.archive()
        
        # 检查归档状态信息
        info1 = archiver.get_archive_info()
        
        # 第二次归档（应具有幂等性）
        result2 = archiver.archive()
        info2 = archiver.get_archive_info()
        
        # 验证幂等性属性
        if info1['log_file_exists'] and info1['should_archive']:
            # 第一次应该归档成功
            assert result1.was_archived or result1.success, "第一次归档应成功"
            
            # 第二次应该跳过（当天已归档）
            assert result2.status == "skipped" or not result2.was_archived, \
                "第二次归档应跳过（幂等性）"
            
            # 归档信息应该一致
            assert info1['today_archive_exists'] == info2['today_archive_exists'], \
                "归档存在状态应一致"
        else:
            # 如果第一次不需要归档，第二次也应该不需要
            assert result1.status in ("noop", "skipped"), "第一次应无操作或跳过"
            assert result2.status in ("noop", "skipped"), "第二次应无操作或跳过（幂等性）"


@given(
    log_content=st.binary(min_size=0, max_size=512)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_property_7_clear_log_idempotence(log_content):
    """Property 7: 清空日志操作应具有幂等性"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建日志文件
        log_file = os.path.join(temp_dir, "test.log")
        
        # 写入内容
        with open(log_file, 'wb') as f:
            f.write(log_content)
        
        original_size = len(log_content)
        
        # 创建LogArchiver
        logger = ToolLogger(verbose=False)
        archiver = LogArchiver(log_file, logger)
        
        # 第一次清空
        success1 = archiver.clear_log_file()
        
        # 检查文件大小
        size1 = os.path.getsize(log_file)
        
        # 第二次清空（幂等性）
        success2 = archiver.clear_log_file()
        size2 = os.path.getsize(log_file)
        
        # 验证幂等性
        assert success1 == True, "第一次清空应成功"
        assert success2 == True, "第二次清空应成功（幂等性）"
        assert size1 == 0, "第一次清空后文件大小应为0"
        assert size2 == 0, "第二次清空后文件大小应为0（幂等性）"
        
        # 如果原始内容为空，清空操作应该仍然成功（幂等性）
        if original_size == 0:
            assert success1 == True, "清空空文件应成功（幂等性）"


@given(
    base_name=st.text(min_size=1, max_size=10).filter(lambda x: '-' not in x),
    file_count=st.integers(min_value=0, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_property_7_cleanup_idempotence(base_name, file_count):
    """Property 7: 清理操作应具有幂等性"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建日志文件
        log_file = os.path.join(temp_dir, f"{base_name}.log")
        with open(log_file, 'w') as f:
            f.write("test log")
        
        # 创建一些归档文件（部分可能过期）
        created_files = []
        for i in range(file_count):
            # 创建不同日期的归档文件
            days_ago = i * 10  # 0, 10, 20, 30, 40天前
            archive_date = date.today() - timedelta(days=days_ago)
            archive_filename = f"{base_name}-{archive_date.strftime('%Y-%m-%d')}.log"
            archive_path = os.path.join(temp_dir, archive_filename)
            
            with open(archive_path, 'w') as f:
                f.write(f"archive {i}")
            created_files.append(archive_path)
        
        # 创建RetentionManager（保留7天）
        logger = ToolLogger(verbose=False)
        manager = RetentionManager(log_file, retention_days=7, logger=logger)
        
        # 第一次清理
        result1 = manager.cleanup_expired(dry_run=True)  # 使用dry-run测试幂等性
        
        # 记录清理结果
        deleted_count1 = result1.total_deleted
        
        # 第二次清理（幂等性测试 - dry-run模式）
        result2 = manager.cleanup_expired(dry_run=True)
        deleted_count2 = result2.total_deleted
        
        # 验证幂等性：两次dry-run应该报告相同数量的待删除文件
        assert deleted_count1 == deleted_count2, \
            f"清理操作应幂等: 第一次{deleted_count1}个, 第二次{deleted_count2}个"
        
        # 验证find_archive_files方法的幂等性
        files1 = manager.find_archive_files()
        files2 = manager.find_archive_files(refresh=False)  # 使用缓存
        files3 = manager.find_archive_files(refresh=True)   # 刷新缓存
        
        assert sorted(files1) == sorted(files2), "缓存查找应一致（幂等性）"
        assert sorted(files1) == sorted(files3), "刷新后查找应一致"


# 附加测试：归档和清理的集成属性

@given(
    log_content=st.binary(min_size=1, max_size=1024),
    retention_days=st.integers(min_value=1, max_value=30)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_archive_and_cleanup_integration(log_content, retention_days):
    """归档和清理的集成属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建日志文件
        log_file = os.path.join(temp_dir, "app.log")
        with open(log_file, 'wb') as f:
            f.write(log_content)
        
        original_size = len(log_content)
        
        # 创建工具组件
        logger = ToolLogger(verbose=False)
        archiver = LogArchiver(log_file, logger)
        manager = RetentionManager(log_file, retention_days, logger)
        
        # 归档前状态
        archive_info_before = archiver.get_archive_info()
        retention_info_before = manager.get_retention_info()
        
        # 执行归档
        archive_result = archiver.safe_archive_and_clear()
        
        # 归档后状态
        archive_info_after = archiver.get_archive_info()
        
        # 验证归档结果
        if original_size > 0:
            assert archive_result.success, "归档应成功"
            
            if archive_result.was_archived:
                # 验证源文件被清空
                assert os.path.getsize(log_file) == 0, "归档后源文件应被清空"
                
                # 验证归档文件存在
                assert archive_info_after['today_archive_exists'], "归档文件应存在"
                
                # 执行清理（应没有过期文件，因为刚刚创建）
                cleanup_result = manager.cleanup_expired(dry_run=True)
                assert cleanup_result.success, "清理应成功"
                assert cleanup_result.total_deleted == 0, "新归档不应被清理"
        
        # 验证信息一致性
        assert archive_info_before['log_file_path'] == archive_info_after['log_file_path']
        assert retention_info_before['log_file_path'] == log_file


@given(
    filenames=st.lists(
        st.text(min_size=1, max_size=20).filter(lambda x: '.' not in x and '-' not in x),
        min_size=1, max_size=5
    ),
    content_size=st.integers(min_value=0, max_value=512)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20)
def test_file_operations_in_archiver(filenames, content_size):
    """LogArchiver中文件操作的属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        for base_name in filenames:
            # 创建日志文件
            log_file = os.path.join(temp_dir, f"{base_name}.log")
            content = b"x" * content_size
            with open(log_file, 'wb') as f:
                f.write(content)
            
            # 创建LogArchiver
            archiver = LogArchiver(log_file)
            
            # 测试should_archive
            should_archive = archiver.should_archive()
            
            # 根据条件验证结果
            if content_size == 0:
                assert not should_archive, "空文件不应归档"
            else:
                # 对于非空文件，第一次应该需要归档
                # 但我们需要考虑当天是否已归档
                archive_info = archiver.get_archive_info()
                
                if archive_info['today_archive_exists']:
                    assert not should_archive, "当天已归档不应再次归档"
                else:
                    assert should_archive, "非空文件且未归档时应归档"
            
            # 测试get_archive_info一致性
            info = archiver.get_archive_info()
            assert info['log_file_path'] == log_file
            assert info['base_name'] == base_name
            assert info['log_file_exists'] == True
            assert info['file_size'] == content_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])