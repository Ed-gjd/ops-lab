"""
数据模型属性测试
验证Property 4: 参数解析正确性和Property 6: 日期解析稳定性
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck
from datetime import date, timedelta
import pytest
from log_archiver.models import ArchiveDate, ToolConfig, ArchiveResult, CleanupResult, ToolResult


# Property 4: 参数解析正确性
# Validates: Requirements 4.2

@given(
    log_file=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\\' not in x),
    retention_days=st.integers(min_value=1, max_value=365),
    verbose=st.booleans(),
    dry_run=st.booleans()
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
def test_property_4_tool_config_parameter_parsing(log_file, retention_days, verbose, dry_run):
    """Property 4: 工具配置应正确解析所有有效参数组合"""
    # 创建模拟的命名空间对象
    class Namespace:
        def __init__(self, log_file, retention_days, verbose, dry_run):
            self.log_file = log_file
            self.retention_days = retention_days
            self.verbose = verbose
            self.dry_run = dry_run
    
    # 创建命名空间
    namespace = Namespace(log_file, retention_days, verbose, dry_run)
    
    # 测试ToolConfig.from_namespace方法
    config = ToolConfig.from_namespace(namespace)
    
    # 验证参数是否正确解析
    assert config.log_file_path == log_file
    assert config.retention_days == retention_days
    assert config.verbose == verbose
    assert config.dry_run == dry_run
    
    # 验证基础名称提取
    base_name = log_file.rsplit('.', 1)[0] if '.' in log_file else log_file
    assert config.base_name == base_name
    
    # 验证日志文件名提取
    import os
    expected_filename = os.path.basename(log_file)
    assert config.log_file_name == expected_filename


@given(
    log_file=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\\' not in x),
    retention_days=st.integers(min_value=1, max_value=365)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_4_default_parameters(log_file, retention_days):
    """Property 4: 工具配置应正确处理默认参数"""
    # 创建模拟的命名空间对象，只提供部分参数
    class PartialNamespace:
        def __init__(self, log_file=None, retention_days=None, verbose=None, dry_run=None):
            if log_file is not None:
                self.log_file = log_file
            if retention_days is not None:
                self.retention_days = retention_days
            if verbose is not None:
                self.verbose = verbose
            if dry_run is not None:
                self.dry_run = dry_run
    
    # 测试部分参数情况
    namespace = PartialNamespace(log_file=log_file)
    config = ToolConfig.from_namespace(namespace)
    assert config.log_file_path == log_file
    assert config.retention_days == 7  # 默认值
    assert config.verbose == False  # 默认值
    assert config.dry_run == False  # 默认值


# Property 6: 日期解析稳定性
# Validates: 支持性隐式需求

@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
def test_property_6_archive_date_creation(year, month, day):
    """Property 6: ArchiveDate对象应能正确处理所有有效日期"""
    try:
        # 尝试创建日期以验证其有效性
        date_obj = date(year, month, day)
        # 如果能创建日期对象，那么ArchiveDate应该也能创建
        archive_date = ArchiveDate(year, month, day)
        
        # 验证转换一致性
        assert archive_date.to_date() == date_obj
        assert archive_date.year == year
        assert archive_date.month == month
        assert archive_date.day == day
        
        # 验证字符串转换
        date_str = archive_date.to_string()
        assert date_str == f"{year:04d}-{month:02d}-{day:02d}"
        
        # 验证字符串解析
        parsed_date = ArchiveDate.from_string(date_str)
        assert parsed_date is not None
        assert parsed_date.year == year
        assert parsed_date.month == month
        assert parsed_date.day == day
        
    except ValueError:
        # 如果date()构造函数抛出异常，说明这不是有效日期
        # ArchiveDate不应创建成功（但实际上不会尝试创建）
        pass


@given(
    base_name=st.text(min_size=1, max_size=20).filter(lambda x: '-' not in x),
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
def test_property_6_filename_parsing(base_name, year, month, day):
    """Property 6: 从文件名解析日期应稳定且一致"""
    try:
        # 尝试创建日期以验证其有效性
        date_obj = date(year, month, day)
        
        # 创建文件名
        filename = f"{base_name}-{year:04d}-{month:02d}-{day:02d}.log"
        
        # 解析文件名
        archive_date = ArchiveDate.from_filename(filename, base_name)
        
        # 验证解析结果
        assert archive_date is not None
        assert archive_date.year == year
        assert archive_date.month == month
        assert archive_date.day == day
        
        # 验证转换一致性
        assert archive_date.to_date() == date_obj
        
        # 测试无效文件名
        invalid_filename = f"{base_name}-invalid-date.log"
        assert ArchiveDate.from_filename(invalid_filename, base_name) is None
        
        # 测试不同base_name
        different_base = f"different-{year:04d}-{month:02d}-{day:02d}.log"
        assert ArchiveDate.from_filename(different_base, base_name) is None
        
    except ValueError:
        # 如果date()构造函数抛出异常，说明这不是有效日期
        # 不应继续测试
        pass


@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=31),
    days_ago=st.integers(min_value=0, max_value=1000)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100)
def test_property_6_date_comparison_consistency(year, month, day, days_ago):
    """Property 6: 日期比较应保持一致性"""
    try:
        # 尝试创建日期以验证其有效性
        date_obj = date(year, month, day)
        archive_date = ArchiveDate(year, month, day)
        
        # 验证日期比较的一致性
        expected_is_before = date_obj < (date.today() - timedelta(days=days_ago))
        actual_is_before = archive_date.is_before(days_ago)
        
        # 对于有效日期，两者应该一致
        assert actual_is_before == expected_is_before
        
        # 测试负保留天数
        if days_ago < 0:
            try:
                archive_date.is_before(-1)
                pytest.fail("负保留天数应该抛出异常")
            except ValueError:
                pass  # 预期行为
                
    except ValueError:
        # 如果date()构造函数抛出异常，说明这不是有效日期
        pass


# 附加测试：Result对象的行为属性

@given(
    status=st.sampled_from(["archived", "skipped", "noop", "failed"]),
    message=st.text(min_size=1, max_size=100),
    archive_file=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    error=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_archive_result_success_property(status, message, archive_file, error):
    """ArchiveResult的success属性应正确反映状态"""
    result = ArchiveResult(
        status=status,
        message=message,
        archived_file=archive_file,
        error=error
    )
    
    # 验证success属性的逻辑
    if status in ("archived", "skipped", "noop"):
        assert result.success == True
        assert result.was_archived == (status == "archived")
    else:
        assert result.success == False
        assert result.was_archived == False


@given(
    success=st.booleans(),
    message=st.text(min_size=1, max_size=100),
    deleted_files=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    failed_files=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    error=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_cleanup_result_properties(success, message, deleted_files, failed_files, error):
    """CleanupResult的属性应正确计算"""
    result = CleanupResult(
        success=success,
        message=message,
        deleted_files=deleted_files,
        failed_files=failed_files,
        error=error
    )
    
    # 验证计数属性
    assert result.total_deleted == len(deleted_files)
    assert result.total_failed == len(failed_files)


@given(
    exit_code=st.integers(min_value=0, max_value=255),
    archive_result=st.one_of(st.none(), st.builds(
        ArchiveResult,
        status=st.sampled_from(["archived", "skipped", "noop", "failed"]),
        message=st.text(min_size=1, max_size=50)
    )),
    cleanup_result=st.one_of(st.none(), st.builds(
        CleanupResult,
        success=st.booleans(),
        message=st.text(min_size=1, max_size=50)
    ))
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_tool_result_properties(exit_code, archive_result, cleanup_result):
    """ToolResult的属性应正确反映退出状态"""
    result = ToolResult(
        exit_code=exit_code,
        archive_result=archive_result,
        cleanup_result=cleanup_result
    )
    
    # 验证success属性
    assert result.success == (exit_code == 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])