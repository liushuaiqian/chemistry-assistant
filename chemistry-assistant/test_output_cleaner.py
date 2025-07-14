#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试输出清理功能
"""

from utils.output_cleaner import clean_output, clean_model_output, clean_parallel_output

def test_output_cleaner():
    """
    测试输出清理功能
    """
    print("=== 测试输出清理功能 ===")
    
    # 测试原始乱码文本
    test_text = """### 问题分析和解题思路

要从铁生成三氧化二铁\(\ce{ 
 $$ 
 }\)可以通过铁与氧气在特定条件下反应来实现这个过程通常涉及到铁的氧化即铁失去电子给氧分子从而形成氧化物根据条件的不同如温度氧气浓度等可以得到不同形式的铁氧化物但本题特别指出了是三氧化二铁\(\ce{$Fe{2} 
 O_{3}$}\)

### 详细的解答步骤

**步骤一确定反应物**
- 反应物为纯铁 \(\ce{ 
 $$}\) 和氧气 \(\ce{$\ce{$O_{2}Extra close brace or missing open brace 
 }\)

**步骤二写出化学方程式**
- 铁与氧气反应生成三氧化二铁的基本化学方程式为
 \[
 4\ce{$\ce{Fe}$} + 3\ce{$\ce{$O_{2}Extra close brace or missing open brace 
 } 
  2\ce{$Fe_{2} 
 O_{3}$}
 \]"""
    
    print("原始文本:")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    # 清理文本
    cleaned_text = clean_output(test_text)
    print("清理后文本:")
    print(cleaned_text)
    print("\n" + "="*50 + "\n")
    
    # 测试模型输出清理
    model_response = {
        'answer': test_text,
        'model_name': 'test_model',
        'success': True
    }
    
    cleaned_model_output = clean_model_output(model_response)
    print("清理后模型输出:")
    print(cleaned_model_output)
    print("\n" + "="*50 + "\n")
    
    # 测试并行结果清理
    parallel_results = {
        'tongyi': {
            'answer': test_text,
            'model_name': 'tongyi',
            'success': True
        },
        'deepseek': {
            'answer': test_text,
            'model_name': 'deepseek', 
            'success': True
        }
    }
    
    cleaned_parallel = clean_parallel_output(parallel_results)
    print("清理后并行结果:")
    for model_name, result in cleaned_parallel.items():
        print(f"\n{model_name}:")
        print(result['answer'][:200] + "...")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_output_cleaner()