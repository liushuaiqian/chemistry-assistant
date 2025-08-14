#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试修复后的化学计算功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'chemistry-assistant'))

from tools.chemistry_solver import ChemistrySolver

def test_formula_parsing():
    """测试化学式解析功能（支持括号和晶水）"""
    print("=== 测试化学式解析功能 ===")
    solver = ChemistrySolver()
    
    test_cases = [
        'Ca(OH)2',
        'Al2(SO4)3', 
        'CuSO4·5H2O',
        'CuSO4•5H2O',
        'CuSO4.5H2O',
        'Mg(NO3)2·6H2O',
        'Ca(ClO)2',
        'NH4NO3'
    ]
    
    for formula in test_cases:
        try:
            elements = solver._parse_formula(formula)
            molar_mass = solver.calculate_molar_mass(formula)
            print(f"{formula:15} -> {elements} -> {molar_mass:.1f} g/mol")
        except Exception as e:
            print(f"{formula:15} -> 错误: {e}")
    print()

def test_equation_balancing():
    """测试方程式配平功能"""
    print("=== 测试方程式配平功能 ===")
    solver = ChemistrySolver()
    
    test_equations = [
        'H2 + O2 = H2O',
        'Fe + O2 = Fe2O3',
        'Al + HCl = AlCl3 + H2',
        'C2H6 + O2 = CO2 + H2O',
        'NH3 + O2 = NO + H2O'
    ]
    
    for equation in test_equations:
        try:
            balanced = solver.balance_equation(equation)
            print(f"原方程式: {equation}")
            print(f"配平后:   {balanced}")
            print()
        except Exception as e:
            print(f"配平失败: {equation} -> 错误: {e}")
            print()

def test_text_extraction():
    """测试文本提取功能"""
    print("=== 测试文本提取功能 ===")
    solver = ChemistrySolver()
    
    test_texts = [
        "计算Ca(OH)2的摩尔质量",
        "Al2(SO4)3与NaOH反应", 
        "CuSO4·5H2O晶体的组成",
        "反应方程式：H2 + O2 = H2O",
        "配平方程式：Fe + O2 = Fe2O3",
        "化学式C6H12O6代表葡萄糖"
    ]
    
    for text in test_texts:
        formula = solver.extract_formula(text)
        equation = solver.extract_equation(text)
        compound = solver.extract_compound(text)
        
        print(f"文本: {text}")
        print(f"  化学式: {formula}")
        print(f"  方程式: {equation}")
        print(f"  化合物: {compound}")
        print()

def test_comprehensive():
    """综合测试"""
    print("=== 综合测试 ===")
    solver = ChemistrySolver()
    
    # 测试复杂化学式的摩尔质量计算
    complex_formulas = ['Ca(OH)2', 'Al2(SO4)3', 'CuSO4·5H2O']
    
    for formula in complex_formulas:
        try:
            molar_mass = solver.calculate_molar_mass(formula)
            print(f"{formula} 的摩尔质量: {molar_mass:.2f} g/mol")
        except Exception as e:
            print(f"{formula} 计算失败: {e}")
    
    print()
    
    # 测试方程式配平的稳定性
    equations = ['H2 + O2 = H2O', 'Fe + O2 = Fe2O3']
    
    for eq in equations:
        try:
            balanced = solver.balance_equation(eq)
            print(f"配平成功: {eq} -> {balanced}")
        except Exception as e:
            print(f"配平失败: {eq} -> {e}")

if __name__ == "__main__":
    test_formula_parsing()
    test_equation_balancing()
    test_text_extraction()
    test_comprehensive()
    print("测试完成！")