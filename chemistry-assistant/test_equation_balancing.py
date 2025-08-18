#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学方程式配平功能测试
测试新的矩阵求解配平算法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.chemistry_solver import ChemistrySolver

def test_equation_balancing():
    """
    测试化学方程式配平功能
    """
    solver = ChemistrySolver()
    
    # 测试用例
    test_equations = [
        # 简单方程式
        "H2 + O2 = H2O",
        "Fe + O2 = Fe2O3",
        "Al + HCl = AlCl3 + H2",
        
        # 复杂氧化还原反应
        "KMnO₄ + HCl = MnCl₂ + Cl₂ + KCl + H₂O",
        "KMnO4 + HCl = MnCl2 + Cl2 + KCl + H2O",
        "K2Cr2O7 + HCl = CrCl3 + Cl2 + KCl + H2O",
        "Cu + HNO3 = Cu(NO3)2 + NO + H2O",
        
        # 其他复杂反应
        "C2H6 + O2 = CO2 + H2O",
        "NH3 + O2 = NO + H2O",
        "Ca + H2O = Ca(OH)2 + H2"
    ]
    
    print("=== 化学方程式配平测试 ===")
    print()
    
    for i, equation in enumerate(test_equations, 1):
        print(f"测试 {i}: {equation}")
        try:
            balanced = solver.balance_equation(equation)
            print(f"配平结果: {balanced}")
            
            # 验证配平是否正确
            if verify_balance(balanced, solver):
                print("✓ 配平正确")
            else:
                print("✗ 配平可能有误")
                
        except Exception as e:
            print(f"✗ 配平失败: {e}")
        
        print("-" * 50)
        print()

def verify_balance(equation, solver):
    """
    验证方程式是否平衡（简单验证）
    
    Args:
        equation (str): 平衡后的方程式
        solver (ChemistrySolver): 化学求解器实例
        
    Returns:
        bool: 是否平衡
    """
    try:
        # 解析方程式
        reactants, products = solver._parse_equation(equation)
        
        # 统计各元素的原子数
        reactant_elements = {}
        product_elements = {}
        
        # 统计反应物中的元素
        for reactant in reactants:
            formula = solver._clean_formula(reactant['formula'])
            coefficient = reactant.get('coefficient', 1)
            
            # 从配平后的方程式中提取系数
            if equation.count(reactant['formula']) > 0:
                # 查找系数
                import re
                pattern = r'(\d+)?' + re.escape(reactant['formula'])
                match = re.search(pattern, equation)
                if match and match.group(1):
                    coefficient = int(match.group(1))
            
            composition = solver._parse_formula(formula)
            for element, count in composition.items():
                reactant_elements[element] = reactant_elements.get(element, 0) + count * coefficient
        
        # 统计生成物中的元素
        for product in products:
            formula = solver._clean_formula(product['formula'])
            coefficient = product.get('coefficient', 1)
            
            # 从配平后的方程式中提取系数
            if equation.count(product['formula']) > 0:
                # 查找系数
                import re
                pattern = r'(\d+)?' + re.escape(product['formula'])
                match = re.search(pattern, equation.split('→')[1] if '→' in equation else equation.split('=')[1])
                if match and match.group(1):
                    coefficient = int(match.group(1))
            
            composition = solver._parse_formula(formula)
            for element, count in composition.items():
                product_elements[element] = product_elements.get(element, 0) + count * coefficient
        
        # 比较元素数量
        all_elements = set(reactant_elements.keys()) | set(product_elements.keys())
        for element in all_elements:
            if reactant_elements.get(element, 0) != product_elements.get(element, 0):
                return False
        
        return True
        
    except Exception as e:
        print(f"验证过程出错: {e}")
        return False

def test_specific_kmno4_reaction():
    """
    专门测试KMnO₄ + HCl反应
    """
    solver = ChemistrySolver()
    
    print("=== KMnO₄ + HCl 反应专项测试 ===")
    print()
    
    # 测试不同的输入格式
    test_cases = [
        "KMnO₄ + HCl = MnCl₂ + Cl₂ + KCl + H₂O",
        "KMnO4 + HCl = MnCl2 + Cl2 + KCl + H2O",
        "KMnO₄ ＋ HCl ＝ MnCl₂ ＋ Cl₂↑ ＋ KCl ＋ H₂O",
        "KMnO4 + HCl → MnCl2 + Cl2↑ + KCl + H2O"
    ]
    
    for i, equation in enumerate(test_cases, 1):
        print(f"测试格式 {i}: {equation}")
        try:
            balanced = solver.balance_equation(equation)
            print(f"配平结果: {balanced}")
            print(f"预期结果: 2KMnO₄ + 16HCl → 2MnCl₂ + 5Cl₂↑ + 2KCl + 8H₂O")
            
            # 检查是否包含正确的系数
            if "2KMnO" in balanced and "16HCl" in balanced and "5Cl₂" in balanced:
                print("✓ 配平系数正确")
            else:
                print("✗ 配平系数可能有误")
                
        except Exception as e:
            print(f"✗ 配平失败: {e}")
        
        print("-" * 40)
        print()

if __name__ == "__main__":
    test_equation_balancing()
    print()
    test_specific_kmno4_reaction()