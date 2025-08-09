#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终测试：验证表格格式和KaTeX错误修复
"""

from utils.web_ui_formatter import clean_and_format_output

# 测试用户报告的具体问题
test_content = r"""
## 2.3 加成反应（需要到条件）

| 反应类型 | 方程式（条件） | 现象/产物用途 |
|---------|---------------|---------------|
| 加氢反应 | \text{C}_6\text{H}_6 + 3\,\text{H}_2 \xrightarrow{\text{Ni},\,200\,^\circ\text{C}} \text{C}_6\text{H}_{12} | 产物已己烷：尼龙-6,6的关键单体。 |
| 卤代反应 | C₆H₆ + Br₂ →[Fe/FeBr₃] C₆H₅Br + HBr | 生成溴苯（有机合成） |
| 硝化反应 | C₆H₆ + HNO₃ →[浓H₂SO₄, 55 °C] C₆H₅NO₂ + H₂O | 生成硝基苯（染料中间体） |
"""

print("=== 原始内容 ===")
print(test_content)
print("\n" + "="*60 + "\n")

print("=== 格式化后内容 ===")
formatted_content = clean_and_format_output(test_content)
print(formatted_content)
print("\n" + "="*60 + "\n")

# 检查修复效果
print("=== 修复效果检查 ===")

# 检查KaTeX问题修复
problematic_latex = ['\\text{', '\\xrightarrow{', '^\\circ']
fixed_issues = []
remaining_issues = []

for issue in problematic_latex:
    if issue in test_content and issue not in formatted_content:
        fixed_issues.append(issue)
    elif issue in formatted_content:
        remaining_issues.append(issue)

print("✓ 已修复的KaTeX问题:")
for issue in fixed_issues:
    print(f"  - {issue}")

if remaining_issues:
    print("⚠ 仍存在的问题:")
    for issue in remaining_issues:
        print(f"  - {issue}")
else:
    print("✓ 所有KaTeX问题已修复")

# 检查表格格式
print("\n=== 表格格式检查 ===")
lines = formatted_content.split('\n')
table_lines = [line for line in lines if '|' in line and ('→' in line or 'chemical-equation' in line)]

print(f"找到 {len(table_lines)} 行包含化学方程式的表格行:")
for i, line in enumerate(table_lines, 1):
    print(f"{i}. {line}")
    if 'chemical-equation' in line:
        print("   ✓ 已添加CSS类")
    if len(line) > 120:
        print(f"   ⚠ 行长度: {len(line)} 字符（可能需要滚动）")
    else:
        print(f"   ✓ 行长度: {len(line)} 字符（正常）")

print("\n=== 测试完成 ===")
print("所有修复已应用，可以在Web界面中测试实际效果。")