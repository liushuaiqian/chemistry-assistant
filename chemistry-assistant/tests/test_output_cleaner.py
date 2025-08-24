#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试输出清理器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.output_cleaner import output_cleaner

def test_output_cleaner():
    """
    测试输出清理器的各种功能
    """
    print("=== 测试输出清理器功能 ===")
    
    # 测试1: 基本Markdown清理
    print("\n1. 测试基本Markdown清理:")
    raw_text = """
    这是一个化学反应：H2 + O2 → H2O
    
    化学公式：$H_2SO_4$
    
    代码块：
    ```python
    print("hello")
    
    数学公式：$$\\Delta H = -285.8 \\text{ kJ/mol}$$
    
    特殊字符：<script>alert('test')</script>
    """
    
    cleaned = output_cleaner.clean_model_response(raw_text)
    print("原始文本:")
    print(repr(raw_text))
    print("\n清理后:")
    print(cleaned)
    
    # 测试2: 化学公式标准化
    print("\n\n2. 测试化学公式标准化:")
    chemical_text = """
    水的分子式是H2O，硫酸是H2SO4
    反应：2H2 + O2 → 2H2O
    温度变化：ΔH = -285.8 kJ/mol
    """
    
    normalized = output_cleaner._normalize_chemical_formulas(chemical_text)
    print("原始文本:")
    print(chemical_text)
    print("\n标准化后:")
    print(normalized)
    
    # 测试3: 融合输出清理
    print("\n\n3. 测试融合输出清理:")
    model_output = """
    ## 模型A的回答
    
    这个化学反应的方程式是：
    $H_2 + Cl_2 \\rightarrow 2HCl$
    
    反应热为：$\\Delta H = -184.6 \\text{ kJ/mol}$
    """
    
    fusion_cleaned = output_cleaner.sanitize_model_output_for_fusion(model_output, "测试模型")
    print("原始模型输出:")
    print(model_output)
    print("\n融合清理后:")
    print(fusion_cleaned)
    
    # 测试4: 最终格式化输出
    print("\n\n4. 测试最终格式化输出:")
    final_text = """
    根据化学反应原理，氢气和氯气反应生成氯化氢：
    
    $H_2 + Cl_2 \\rightarrow 2HCl$
    
    这是一个放热反应，反应热为 $\\Delta H = -184.6 \\text{ kJ/mol}$
    
    反应条件：常温常压下即可进行。
    """
    
    formatted = output_cleaner.format_final_output(final_text, "化学反应分析")
    print("原始文本:")
    print(final_text)
    print("\n最终格式化后:")
    print(formatted)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_output_cleaner()