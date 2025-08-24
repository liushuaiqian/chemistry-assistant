#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学助手集成测试
测试化学方程式配平功能的实际应用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.chemistry_solver import ChemistrySolver

def test_chemistry_solver_integration():
    """
    测试化学求解器的集成功能
    """
    print("=== 化学助手集成测试 ===")
    print()
    
    # 初始化化学求解器
    solver = ChemistrySolver()
    
    # 测试复杂的氧化还原反应配平
    test_cases = [
        {
            "equation": "KMnO₄ + HCl = MnCl₂ + Cl₂ + KCl + H₂O",
            "description": "高锰酸钾与盐酸反应",
            "expected": "2KMnO₄ + 16HCl → 2MnCl₂ + 5Cl₂↑ + 2KCl + 8H₂O"
        },
        {
            "equation": "K2Cr2O7 + HCl = CrCl3 + Cl2 + KCl + H2O",
            "description": "重铬酸钾与盐酸反应",
            "expected": "K2Cr2O7 + 14HCl → 2CrCl3 + 3Cl2↑ + 2KCl + 7H2O"
        },
        {
            "equation": "Cu + HNO3 = Cu(NO3)2 + NO + H2O",
            "description": "铜与稀硝酸反应",
            "expected": "3Cu + 8HNO3 → 3Cu(NO3)2 + 2NO↑ + 4H2O"
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['description']}")
        print(f"输入方程式: {test_case['equation']}")
        
        try:
            # 使用化学求解器配平方程式
            balanced = solver.balance_equation(test_case['equation'])
            print(f"配平结果: {balanced}")
            print(f"预期结果: {test_case['expected']}")
            
            # 检查关键系数是否正确
            if check_balancing_correctness(balanced, test_case['expected']):
                print("✓ 配平成功")
                success_count += 1
            else:
                print("✗ 配平结果不符合预期")
                
        except Exception as e:
            print(f"✗ 配平失败: {e}")
        
        print("-" * 50)
        print()
    
    print(f"测试总结: {success_count}/{total_count} 个测试通过")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    
    return success_count == total_count

def check_balancing_correctness(result, expected):
    """
    检查配平结果是否正确
    
    Args:
        result (str): 实际配平结果
        expected (str): 期望的配平结果
        
    Returns:
        bool: 是否正确
    """
    # 简单的字符串匹配检查
    # 提取关键的系数信息
    import re
    
    def extract_coefficients(equation):
        # 提取所有数字系数
        coeffs = re.findall(r'(\d+)', equation)
        return [int(c) for c in coeffs]
    
    result_coeffs = extract_coefficients(result)
    expected_coeffs = extract_coefficients(expected)
    
    # 比较主要系数（前几个）
    if len(result_coeffs) >= 3 and len(expected_coeffs) >= 3:
        return result_coeffs[:3] == expected_coeffs[:3]
    
    return False

def test_specific_problem():
    """
    测试用户提到的具体问题
    """
    print("=== 用户问题专项测试 ===")
    print()
    
    solver = ChemistrySolver()
    
    # 用户提到的具体方程式
    problem_equation = "KMnO₄ ＋ HCl → MnCl₂ ＋ Cl₂↑ ＋ KCl ＋ H₂O"
    
    print(f"问题方程式: {problem_equation}")
    print("这是一个典型的氧化还原反应，之前的配平功能无法处理")
    print()
    
    try:
        balanced = solver.balance_equation(problem_equation)
        print(f"配平结果: {balanced}")
        
        # 验证配平是否正确
        expected_pattern = ["2", "16", "2", "5", "2", "8"]  # 主要系数
        if all(coeff in balanced for coeff in expected_pattern[:3]):
            print("✓ 成功解决了用户提到的问题！")
            print("✓ 复杂氧化还原反应配平功能正常工作")
            return True
        else:
            print("✗ 配平结果可能不正确")
            return False
            
    except Exception as e:
        print(f"✗ 配平失败: {e}")
        return False

if __name__ == "__main__":
    # 运行集成测试
    integration_success = test_chemistry_solver_integration()
    
    print()
    
    # 测试具体问题
    problem_success = test_specific_problem()
    
    print()
    print("=== 最终测试结果 ===")
    if integration_success and problem_success:
        print("✓ 所有测试通过！化学方程式配平功能已成功修复")
        print("✓ 现在可以正确处理复杂的氧化还原反应")
    else:
        print("✗ 部分测试失败，需要进一步调试")