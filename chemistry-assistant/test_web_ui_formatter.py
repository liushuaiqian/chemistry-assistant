#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web UI格式化器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.web_ui_formatter import (
    clean_and_format_output,
    format_comparison_output,
    format_chain_result,
    format_error_message,
    format_status_message
)

def test_web_ui_formatter():
    """
    测试Web UI格式化器的各种功能
    """
    print("=== 测试Web UI格式化器功能 ===")
    
    # 测试1: 基本输出格式化
    print("\n1. 测试基本输出格式化:")
    raw_output = {
        "answer": "水的分子式是H2O，反应方程式为：2H2 + O2 → 2H2O\n\n反应热：ΔH = -285.8 kJ/mol",
        "confidence": 0.95
    }
    
    formatted = clean_and_format_output(raw_output)
    print("原始输出:")
    print(raw_output)
    print("\n格式化后:")
    print(formatted)
    
    # 测试2: JSON字符串输入
    print("\n\n2. 测试JSON字符串输入:")
    json_input = '{"integrated_answer": "氢气燃烧：2H2 + O2 → 2H2O\\n这是一个放热反应。", "model_count": 3}'
    
    formatted_json = clean_and_format_output(json_input)
    print("JSON输入:")
    print(json_input)
    print("\n格式化后:")
    print(formatted_json)
    
    # 测试3: 比较输出格式化
    print("\n\n3. 测试比较输出格式化:")
    comparison_data = {
        "model_a": "模型A认为反应是放热的",
        "model_b": "模型B认为反应是吸热的",
        "similarity": 0.3
    }
    
    formatted_comparison = format_comparison_output(comparison_data)
    print("比较数据:")
    print(comparison_data)
    print("\n格式化后:")
    print(formatted_comparison)
    
    # 测试4: 链式结果格式化
    print("\n\n4. 测试链式结果格式化:")
    chain_data = {
        "reasoning_content": "根据化学原理分析...",
        "final_answer": "Fe2O3 + 3CO → 2Fe + 3CO2",
        "steps": ["步骤1", "步骤2", "步骤3"]
    }
    
    formatted_chain = format_chain_result(chain_data)
    print("链式数据:")
    print(chain_data)
    print("\n格式化后:")
    print(formatted_chain)
    
    # 测试5: 错误消息格式化
    print("\n\n5. 测试错误消息格式化:")
    try:
        raise ValueError("模拟的处理错误")
    except Exception as e:
        error_formatted = format_error_message(e, "化学方程式处理")
        print("错误消息格式化:")
        print(error_formatted)
    
    # 测试6: 状态消息格式化
    print("\n\n6. 测试状态消息格式化:")
    status_formatted = format_status_message(
        "处理完成", 
        "已成功处理3个模型的输出，融合置信度为0.92"
    )
    print("状态消息格式化:")
    print(status_formatted)
    
    # 测试7: 复杂化学内容格式化
    print("\n\n7. 测试复杂化学内容格式化:")
    complex_content = """
    化学反应分析：
    
    1. 燃烧反应：CH4 + 2O2 → CO2 + 2H2O
    2. 氧化反应：4Fe + 3O2 → 2Fe2O3
    3. 酸碱反应：HCl + NaOH → NaCl + H2O
    
    热力学数据：
    - ΔH = -890.3 kJ/mol (甲烷燃烧)
    - ΔS = 242.8 J/(mol·K)
    - ΔG = ΔH - TΔS
    
    LaTeX公式测试：
    $\\Delta H_{combustion} = -890.3 \\text{ kJ/mol}$
    
    $$\\ce{CH4 + 2O2 -> CO2 + 2H2O}$$
    """
    
    complex_formatted = clean_and_format_output(complex_content, "复杂化学分析")
    print("复杂内容:")
    print(complex_content)
    print("\n格式化后:")
    print(complex_formatted)
    
    # 测试8: 列表数据格式化
    print("\n\n8. 测试列表数据格式化:")
    list_data = [
        "反应物：H2, O2",
        "生成物：H2O",
        "反应类型：化合反应",
        "反应条件：点燃"
    ]
    
    list_formatted = clean_and_format_output(list_data)
    print("列表数据:")
    print(list_data)
    print("\n格式化后:")
    print(list_formatted)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_web_ui_formatter()