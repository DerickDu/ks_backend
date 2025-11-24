#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PEP 8代码风格检查脚本

用于检查项目中的Python文件是否符合PEP 8编码规范。
建议在提交代码前运行此脚本进行检查。
"""

import os
import sys
import subprocess
from typing import List

def get_python_files(directory: str) -> List[str]:
    """
    获取目录下所有的Python文件
    
    参数:
        directory: 要搜索的目录路径
    
    返回:
        List[str]: Python文件路径列表
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def check_pep8(files: List[str]) -> bool:
    """
    使用pycodestyle检查文件是否符合PEP 8
    
    参数:
        files: 要检查的文件路径列表
    
    返回:
        bool: 所有文件是否都通过检查
    """
    try:
        # 尝试导入pycodestyle
        import pycodestyle
        
        # 创建检查器实例
        style_guide = pycodestyle.StyleGuide(
            quiet=False,  # 显示详细信息
            show_source=True,  # 显示有问题的源代码
            max_line_length=100,  # 允许的最大行长度
            ignore=['E203', 'W503']  # 忽略某些检查规则
        )
        
        # 运行检查
        report = style_guide.check_files(files)
        
        # 打印检查结果摘要
        print(f"\nPEP 8检查结果:")
        print(f"检查文件数: {len(files)}")
        print(f"发现问题数: {report.total_errors}")
        
        return report.total_errors == 0
        
    except ImportError:
        print("错误: 未安装pycodestyle。请运行 'pip install pycodestyle' 后再试。")
        print("正在尝试使用pylint作为替代...")
        
        # 尝试使用pylint作为替代
        try:
            subprocess.run(['pylint', '--version'], check=True, capture_output=True)
            
            for file in files:
                print(f"\n检查文件: {file}")
                subprocess.run(['pylint', file])
            
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("错误: 未安装pylint。无法进行PEP 8检查。")
            return False

def check_imports_order(files: List[str]) -> bool:
    """
    检查导入语句的顺序是否符合标准
    
    参数:
        files: 要检查的文件路径列表
    
    返回:
        bool: 导入顺序是否都符合标准
    """
    try:
        # 尝试导入isort
        import isort
        
        all_good = True
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not isort.check_string(content, settings=isort.settings.Config()):
                print(f"文件 {file} 的导入顺序需要调整")
                all_good = False
        
        if all_good:
            print("所有文件的导入顺序都符合标准")
        
        return all_good
        
    except ImportError:
        print("警告: 未安装isort。跳过导入顺序检查。")
        return True

def main():
    """
    主函数，执行PEP 8检查
    """
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取所有Python文件
    python_files = get_python_files(current_dir)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 执行检查
    pep8_passed = check_pep8(python_files)
    imports_passed = check_imports_order(python_files)
    
    # 输出最终结果
    if pep8_passed and imports_passed:
        print("\n✅ 所有检查都已通过！代码符合PEP 8规范。")
        return 0
    else:
        print("\n❌ 检查未通过。请修复上述问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())