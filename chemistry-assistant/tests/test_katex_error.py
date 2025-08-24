#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试KaTeX错误的化学方程式
"""

from utils.web_ui_formatter import clean_and_format_output

# 用户报告的有问题的化学方程式
test_equation = r"\text{C}_6\text{H}_6 + 3\,\text{H}_2 \xrightarrow{\text{Ni},\,200\,^\circ\text{C}} \text{C}_6\text{H}_{12}"

print("=== 原始方程式 ===")
print(test_equation)
print()

# 测试格式化
print("=== 格式化后 ===")
formatted = clean_and_format_output(test_equation)
print(formatted)
print()

# 测试包含在表格中的情况
table_content = f"""
| 反应类型 | 方程式 | 条件 |
|---------|--------|------|
| 加成反应 | {test_equation} | 高温高压 |
"""

print("=== 表格中的方程式 ===")
print(table_content)
print()

print("=== 表格格式化后 ===")
formatted_table = clean_and_format_output(table_content)
print(formatted_table)
print()

# 分析问题和修复效果
print("=== 修复效果检查 ===")
if '\\text{' in formatted:
    print("⚠ 格式化后仍包含\\text{}命令")
else:
    print("✓ \\text{}命令已被处理")
    
if '\\xrightarrow{' in formatted:
    print("⚠ 格式化后仍包含\\xrightarrow{}命令")
else:
    print("✓ \\xrightarrow{}命令已被处理")
    
if '^\\circ' in formatted:
    print("⚠ 格式化后仍包含^\\circ命令")
else:
    print("✓ ^\\circ命令已被处理")

# 测试其他可能有问题的LaTeX命令
print("\n=== 测试其他LaTeX命令 ===")
other_problematic_equations = [
    r"\ce{H2O}",  # mhchem命令
    r"\mathrm{H}_2\mathrm{O}",  # mathrm命令
    r"\text{反应条件}",  # 中文text命令
    r"A \xrightarrow[下标]{上标} B",  # 带上下标的箭头
]

for eq in other_problematic_equations:
    print(f"原始: {eq}")
    fixed = clean_and_format_output(eq)
    print(f"修复: {fixed}")
    print()