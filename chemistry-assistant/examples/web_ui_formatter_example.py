#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI 格式化器使用示例
演示如何在不同场景下使用web_ui_formatter模块
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.web_ui_formatter import (
    clean_and_format_output,
    format_comparison_output,
    format_chain_result,
    format_error_message,
    format_status_message
)

def example_basic_formatting():
    """
    示例1: 基本输出格式化
    """
    print("=== 示例1: 基本输出格式化 ===")
    
    # 模拟模型输出
    model_output = {
        "answer": "氢气和氧气反应生成水：2H2 + O2 → 2H2O\n\n这是一个放热反应，反应热为-285.8 kJ/mol。",
        "confidence": 0.92,
        "source": "化学知识库"
    }
    
    formatted = clean_and_format_output(model_output, "化学反应分析")
    print(formatted)
    print("\n" + "="*50 + "\n")

def example_json_string_input():
    """
    示例2: JSON字符串输入处理
    """
    print("=== 示例2: JSON字符串输入处理 ===")
    
    # 模拟从API接收到的JSON字符串
    json_response = '''
    {
        "integrated_answer": "根据化学平衡原理，Le Chatelier原理指出：\n\n当系统处于平衡状态时，如果改变影响平衡的条件之一，平衡就会向减弱这种改变的方向移动。\n\n例如：N2 + 3H2 ⇌ 2NH3 + 热量\n\n- 增加压力：平衡向右移动（分子数减少）\n- 升高温度：平衡向左移动（吸热方向）",
        "model_count": 3,
        "fusion_confidence": 0.89
    }
    '''
    
    formatted = clean_and_format_output(json_response)
    print(formatted)
    print("\n" + "="*50 + "\n")

def example_comparison_formatting():
    """
    示例3: 模型对比结果格式化
    """
    print("=== 示例3: 模型对比结果格式化 ===")
    
    comparison_data = {
        "model_gpt4": "GPT-4认为这个反应是自发进行的，因为ΔG < 0",
        "model_claude": "Claude认为需要考虑温度条件，在高温下反应可能不自发",
        "model_tongyi": "通义千问强调了催化剂的重要性，认为催化剂可以降低活化能",
        "similarity_score": 0.73,
        "consensus": "三个模型都同意反应的热力学可行性，但对条件要求有不同观点"
    }
    
    formatted = format_comparison_output(comparison_data)
    print(formatted)
    print("\n" + "="*50 + "\n")

def example_chain_result_formatting():
    """
    示例4: 链式处理结果格式化
    """
    print("=== 示例4: 链式处理结果格式化 ===")
    
    chain_data = {
        "reasoning_content": "首先分析反应物的性质...\n然后考虑反应条件...\n最后得出结论...",
        "intermediate_steps": [
            "步骤1: 识别反应类型",
            "步骤2: 分析热力学",
            "步骤3: 考虑动力学",
            "步骤4: 得出结论"
        ],
        "final_answer": "CaCO3 + 2HCl → CaCl2 + H2O + CO2↑\n\n这是一个酸碱反应，产生的CO2气体会逸出，推动反应向右进行。",
        "confidence": 0.95
    }
    
    formatted = format_chain_result(chain_data)
    print(formatted)
    print("\n" + "="*50 + "\n")

def example_error_handling():
    """
    示例5: 错误处理和格式化
    """
    print("=== 示例5: 错误处理和格式化 ===")
    
    # 模拟不同类型的错误
    errors = [
        (ValueError("输入的化学方程式格式不正确"), "化学方程式解析"),
        (ConnectionError("无法连接到化学数据库"), "数据库查询"),
        (TimeoutError("模型响应超时"), "模型推理")
    ]
    
    for error, context in errors:
        formatted_error = format_error_message(error, context)
        print(formatted_error)
        print("-" * 30)
    
    print("\n" + "="*50 + "\n")

def example_status_messages():
    """
    示例6: 状态消息格式化
    """
    print("=== 示例6: 状态消息格式化 ===")
    
    # 不同的状态消息
    status_messages = [
        ("处理开始", "正在初始化3个AI模型..."),
        ("数据检索完成", "已从化学数据库检索到15条相关记录"),
        ("模型推理完成", "GPT-4: 0.92, Claude: 0.89, 通义千问: 0.87"),
        ("结果融合完成", "最终置信度: 0.91, 一致性评分: 0.85")
    ]
    
    for status, details in status_messages:
        formatted_status = format_status_message(status, details)
        print(formatted_status)
        print("-" * 30)
    
    print("\n" + "="*50 + "\n")

def example_complex_chemistry_content():
    """
    示例7: 复杂化学内容格式化
    """
    print("=== 示例7: 复杂化学内容格式化 ===")
    
    complex_content = """
    # 有机化学反应机理分析
    
    ## 1. 亲核取代反应 (SN2)
    
    反应方程式：CH3CH2Br + OH- → CH3CH2OH + Br-
    
    **机理特点：**
    - 一步反应，协同进行
    - 构型发生翻转
    - 反应速率 ∝ [RX][Nu-]
    
    ## 2. 热力学数据
    
    | 参数 | 数值 |
    |------|------|
    | ΔH | -45.2 kJ/mol |
    | ΔS | +12.8 J/(mol·K) |
    | ΔG | -48.0 kJ/mol |
    
    ## 3. 反应条件优化
    
    ```
    温度: 25-60°C
    溶剂: 极性非质子溶剂 (DMSO, DMF)
    浓度: 0.1-0.5 M
    ```
    
    ## 4. 数学表达式
    
    反应速率常数的温度依赖性：
    $$k = A \\exp\\left(-\\frac{E_a}{RT}\\right)$$
    
    其中：
    - k: 反应速率常数
    - A: 指前因子
    - Ea: 活化能
    - R: 气体常数
    - T: 绝对温度
    """
    
    formatted = clean_and_format_output(complex_content, "有机化学反应分析")
    print(formatted)
    print("\n" + "="*50 + "\n")

def example_gradio_integration():
    """
    示例8: Gradio集成示例
    """
    print("=== 示例8: Gradio集成示例 ===")
    
    # 模拟Gradio处理函数
    def process_chemistry_question(question, image=None):
        """
        模拟的化学问题处理函数
        """
        try:
            # 模拟处理逻辑
            if "反应" in question:
                answer = {
                    "answer": f"关于'{question}'的分析：\n\n这是一个典型的化学反应问题。",
                    "reaction_type": "化合反应",
                    "products": ["H2O", "CO2"]
                }
                comparison = {
                    "model_agreement": 0.89,
                    "key_differences": "模型在反应条件上有轻微分歧"
                }
                chain_result = {
                    "reasoning": "基于化学原理进行分析...",
                    "conclusion": "反应在标准条件下可以进行"
                }
            else:
                answer = "请提供更具体的化学问题。"
                comparison = None
                chain_result = None
            
            # 使用格式化器处理输出
            formatted_answer = clean_and_format_output(answer)
            formatted_comparison = format_comparison_output(comparison) if comparison else ""
            formatted_chain = format_chain_result(chain_result) if chain_result else ""
            
            return formatted_answer, formatted_comparison, formatted_chain
            
        except Exception as e:
            error_msg = format_error_message(e, "化学问题处理")
            return error_msg, "", ""
    
    # 测试不同的问题
    test_questions = [
        "氢气和氧气的反应机理是什么？",
        "请解释一下",  # 模糊问题
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n--- 测试问题 {i}: {question} ---")
        answer, comparison, chain = process_chemistry_question(question)
        
        print("\n【主要回答】")
        print(answer)
        
        if comparison:
            print("\n【模型对比】")
            print(comparison)
        
        if chain:
            print("\n【推理过程】")
            print(chain)
        
        print("\n" + "-"*50)
    
    print("\n" + "="*50 + "\n")

def main():
    """
    运行所有示例
    """
    print("🧪 Web UI 格式化器使用示例\n")
    
    examples = [
        example_basic_formatting,
        example_json_string_input,
        example_comparison_formatting,
        example_chain_result_formatting,
        example_error_handling,
        example_status_messages,
        example_complex_chemistry_content,
        example_gradio_integration
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"❌ 示例执行出错: {e}\n")
    
    print("✅ 所有示例执行完成！")

if __name__ == "__main__":
    main()