"""
文件操作属性测试
验证Property 1: 归档操作完整性和Property 2: 成功归档后清空源文件
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck
import pytest

from log_archiver.file_operations import FileOperations


# Property 1: 归档操作完整性
# Validates: Requirements 1.1, 1.2

@given(
    content=st.binary(min_size=1, max_size=10240),  # 最大10KB的内容
    source_filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x),
    dest_filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_1_file_copy_integrity(content, source_filename, dest_filename):
    """Property 1: 文件复制应保持内容完整性"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建源文件
        source_path = os.path.join(temp_dir, source_filename)
        dest_path = os.path.join(temp_dir, dest_filename)
        
        # 写入内容到源文件
        with open(source_path, 'wb') as f:
            f.write(content)
        
        # 执行文件复制
        result = FileOperations.copy_file(source_path, dest_path)
        
        # 验证复制成功
        assert result == True, "文件复制应该成功"
        
        # 验证目标文件存在
        assert os.path.exists(dest_path), "目标文件应该存在"
        
        # 验证文件大小一致
        source_size = os.path.getsize(source_path)
        dest_size = os.path.getsize(dest_path)
        assert source_size == dest_size, f"文件大小应该一致: 源={source_size}, 目标={dest_size}"
        
        # 验证文件内容一致
        with open(source_path, 'rb') as src, open(dest_path, 'rb') as dst:
            assert src.read() == dst.read(), "文件内容应该完全一致"
        
        # 验证FileOperations.files_equal方法
        assert FileOperations.files_equal(source_path, dest_path), "files_equal应该返回True"


@given(
    content=st.binary(min_size=0, max_size=10240),
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_1_file_equality_check(content, filename):
    """Property 1: 文件相等性检查应正确工作"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建两个相同内容的文件
        file1_path = os.path.join(temp_dir, f"file1_{filename}")
        file2_path = os.path.join(temp_dir, f"file2_{filename}")
        
        # 写入相同内容
        with open(file1_path, 'wb') as f1, open(file2_path, 'wb') as f2:
            f1.write(content)
            f2.write(content)
        
        # 验证文件相等
        assert FileOperations.files_equal(file1_path, file2_path), "相同内容的文件应该相等"
        
        # 仅大小比较模式
        assert FileOperations.files_equal(file1_path, file2_path, compare_size_only=True), \
            "大小比较模式应该通过"
        
        # 创建不同内容的第三个文件
        if content:
            file3_path = os.path.join(temp_dir, f"file3_{filename}")
            different_content = content + b"different"
            with open(file3_path, 'wb') as f3:
                f3.write(different_content)
            
            # 验证不同内容文件不相等
            assert not FileOperations.files_equal(file1_path, file3_path), "不同内容的文件不应该相等"


@given(
    content=st.binary(min_size=1, max_size=5120)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_property_1_copy_nonexistent_source(content):
    """Property 1: 复制不存在的源文件应该失败"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 不存在的源文件
        source_path = os.path.join(temp_dir, "nonexistent_source.txt")
        dest_path = os.path.join(temp_dir, "destination.txt")
        
        # 验证源文件不存在
        assert not os.path.exists(source_path)
        
        # 复制应该失败
        result = FileOperations.copy_file(source_path, dest_path)
        assert result == False, "复制不存在的源文件应该失败"
        
        # 目标文件不应该被创建
        assert not os.path.exists(dest_path), "目标文件不应该被创建"


# Property 2: 成功归档后清空源文件
# Validates: Requirements 2.1

@given(
    content=st.binary(min_size=1, max_size=10240),
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=50)
def test_property_2_file_truncation(content, filename):
    """Property 2: 文件清空操作应正确工作"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 创建有内容的文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        original_size = len(content)
        assert os.path.getsize(file_path) == original_size
        
        # 执行文件清空
        result = FileOperations.truncate_file(file_path)
        
        # 验证清空成功
        assert result == True, "文件清空应该成功"
        
        # 验证文件大小为0
        new_size = os.path.getsize(file_path)
        assert new_size == 0, f"清空后文件大小应该为0，实际为{new_size}"
        
        # 验证文件内容为空
        with open(file_path, 'rb') as f:
            assert f.read() == b'', "文件内容应该为空"


@given(
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_property_2_truncate_nonexistent_file(filename):
    """Property 2: 清空不存在的文件应该失败"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 验证文件不存在
        assert not os.path.exists(file_path)
        
        # 清空应该失败
        result = FileOperations.truncate_file(file_path)
        assert result == False, "清空不存在的文件应该失败"


@given(
    content=st.binary(min_size=0, max_size=5120),
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_property_2_repeated_truncation(content, filename):
    """Property 2: 重复清空文件应该幂等"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 创建文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        original_size = len(content)
        
        # 第一次清空
        result1 = FileOperations.truncate_file(file_path)
        assert result1 == True
        assert os.path.getsize(file_path) == 0
        
        # 第二次清空（文件已经是空的）
        result2 = FileOperations.truncate_file(file_path)
        assert result2 == True, "重复清空空文件应该成功（幂等性）"
        assert os.path.getsize(file_path) == 0


# 附加测试：文件操作的其他属性

@given(
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x),
    content=st.binary(min_size=0, max_size=1024)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_file_deletion_properties(filename, content):
    """文件删除操作的属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 创建文件
        if content:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 验证文件存在
            assert FileOperations.file_exists(file_path)
            
            # 删除文件
            result = FileOperations.delete_file(file_path)
            assert result == True, "删除存在的文件应该成功"
            assert not FileOperations.file_exists(file_path), "文件应该不存在"
        
        # 删除不存在的文件（幂等性）
        result = FileOperations.delete_file(file_path)
        assert result == True, "删除不存在的文件应该返回True（幂等性）"


@given(
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x),
    content=st.binary(min_size=1, max_size=512)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=30)
def test_file_size_properties(filename, content):
    """文件大小相关属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 创建文件
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 验证文件大小
        expected_size = len(content)
        actual_size = FileOperations.get_file_size(file_path)
        assert actual_size == expected_size, f"文件大小应该为{expected_size}，实际为{actual_size}"
        
        # 验证文件存在性
        assert FileOperations.file_exists(file_path)
        
        # 验证不存在的文件大小
        nonexistent_path = os.path.join(temp_dir, "nonexistent.txt")
        assert FileOperations.get_file_size(nonexistent_path) is None


@given(
    pattern_base=st.text(min_size=1, max_size=10).filter(lambda x: '*' not in x),
    count=st.integers(min_value=0, max_value=5)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20)
def test_file_finding_properties(pattern_base, count):
    """文件查找属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建测试文件
        created_files = []
        for i in range(count):
            filename = f"{pattern_base}_{i}.txt"
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"content_{i}")
            created_files.append(file_path)
        
        # 查找文件
        pattern = f"{pattern_base}_*.txt"
        found_files = FileOperations.find_files_by_pattern(temp_dir, pattern)
        
        # 验证找到的文件数量
        assert len(found_files) == count, f"应该找到{count}个文件，实际找到{len(found_files)}个"
        
        # 验证找到的文件路径
        found_files_sorted = sorted(found_files)
        created_files_sorted = sorted(created_files)
        assert found_files_sorted == created_files_sorted, "找到的文件应该与创建的文件一致"


@given(
    dirname=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20)
def test_directory_creation_properties(dirname):
    """目录创建属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建嵌套目录
        nested_dir = os.path.join(temp_dir, "level1", "level2", dirname)
        
        # 确保目录存在
        result = FileOperations.ensure_directory_exists(nested_dir)
        assert result == True, "目录创建应该成功"
        assert os.path.exists(nested_dir), "目录应该存在"
        assert os.path.isdir(nested_dir), "应该是目录"
        
        # 重复创建（幂等性）
        result = FileOperations.ensure_directory_exists(nested_dir)
        assert result == True, "重复创建目录应该成功（幂等性）"


@given(
    filename=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x),
    content=st.binary(min_size=1, max_size=512)
)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=20)
def test_safe_file_operation_properties(filename, content):
    """安全文件操作属性测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, filename)
        
        # 测试成功的文件操作
        def successful_operation(path):
            with open(path, 'wb') as f:
                f.write(content)
            return True
        
        success, error = FileOperations.safe_file_operation(successful_operation, file_path)
        assert success == True, "成功操作应该返回True"
        assert error is None, "成功操作不应该有错误信息"
        assert os.path.exists(file_path), "文件应该被创建"
        
        # 测试失败的文件操作
        def failing_operation(path):
            raise PermissionError("模拟权限错误")
        
        success, error = FileOperations.safe_file_operation(failing_operation, file_path)
        assert success == False, "失败操作应该返回False"
        assert error is not None, "失败操作应该有错误信息"
        assert "权限错误" in error, "错误信息应该包含权限错误"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])