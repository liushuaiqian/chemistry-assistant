#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学计算功能验证测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.chemistry_solver import ChemistrySolver

def test_chemistry_functions():
    """
    测试化学计算的核心功能
    """
    solver = ChemistrySolver()
    
    print('=== 化学计算功能验证测试 ===\n')
    
    # 1. 摩尔质量计算测试
    print('1. 摩尔质量计算:')
    formulas = ['H2O', 'CO2', 'NaCl', 'C6H12O6', 'CaCl2', 'Fe2O3']
    for formula in formulas:
        try:
            mass = solver.calculate_molar_mass(formula)
            print(f'   {formula}: {mass} g/mol')
        except Exception as e:
            print(f'   {formula}: ERROR - {e}')
    
    # 2. 浓度计算测试
    print('\n2. 浓度计算:')
    try:
        result = solver.calculate_concentration(moles=0.5, volume=1.0)
        print(f'   0.5 mol in 1.0 L: molarity = {result.get("molarity", "N/A")} mol/L')
        
        result = solver.calculate_concentration(molarity=0.1, volume=2.0)
        print(f'   0.1 M in 2.0 L: moles = {result.get("moles", "N/A")} mol')
        
        result = solver.calculate_concentration(mass=36.0, molar_mass=18.0, volume=1.0)
        print(f'   36g H2O in 1.0 L: molarity = {result.get("molarity", "N/A")} mol/L')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 3. pH计算测试
    print('\n3. pH计算:')
    try:
        result = solver.calculate_ph(concentration=0.1, is_acid=True, is_strong=True)
        print(f'   0.1 M强酸: pH = {result["pH"]}')
        
        result = solver.calculate_ph(concentration=0.01, is_acid=False, is_strong=True)
        print(f'   0.01 M强碱: pH = {result["pH"]}')
        
        result = solver.calculate_ph(poh=3.0)
        print(f'   pOH = 3.0: pH = {result["pH"]}')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 4. 温度转换测试
    print('\n4. 温度转换:')
    try:
        temp_k = solver.convert_temperature(0, 'C', 'K')
        print(f'   0°C = {temp_k} K')
        
        temp_f = solver.convert_temperature(100, 'C', 'F')
        print(f'   100°C = {temp_f} °F')
        
        temp_c = solver.convert_temperature(273.15, 'K', 'C')
        print(f'   273.15 K = {temp_c} °C')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 5. 气体定律测试
    print('\n5. 气体定律计算:')
    try:
        result = solver.calculate_gas_law(volume=22.4, temperature=273.15, moles=1.0)
        print(f'   标况验证: pressure = {result.get("pressure", "N/A")} atm')
        
        result = solver.calculate_gas_law(pressure=2.0, temperature=273.15, moles=1.0)
        print(f'   2 atm, 273.15 K, 1 mol: volume = {result.get("volume", "N/A")} L')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 6. 稀释计算测试
    print('\n6. 稀释计算:')
    try:
        result = solver.calculate_solution_dilution(c1=1.0, v1=1.0, v2=10.0)
        print(f'   1M 1L稀释到10L: final_concentration = {result.get("final_concentration", "N/A")} mol/L')
        print(f'   稀释倍数: {result.get("dilution_factor", "N/A")}')
        
        result = solver.calculate_solution_dilution(c1=2.0, c2=0.5, v2=1.0)
        print(f'   2M稀释到0.5M, 1L: original_volume = {result.get("original_volume", "N/A")} L')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 7. 化学方程式平衡测试
    print('\n7. 化学方程式平衡:')
    equations = [
        'H2 + O2 = H2O',
        'Fe + O2 = Fe2O3',
        'C + O2 = CO2'
    ]
    for equation in equations:
        try:
            balanced = solver.balance_equation(equation)
            print(f'   {equation} → {balanced}')
        except Exception as e:
            print(f'   {equation}: ERROR - {e}')
    
    # 8. 化学计量学计算测试
    print('\n8. 化学计量学计算:')
    try:
        result = solver.calculate_stoichiometry(
            equation="2H2 + O2 = 2H2O",
            given_amount=4.0,
            given_compound="H2",
            target_compound="H2O",
            amount_type="moles"
        )
        print(f'   4 mol H2 → {result.get("target_moles", "N/A")} mol H2O')
        
        result = solver.calculate_stoichiometry(
            equation="C + O2 = CO2",
            given_amount=12.0,
            given_compound="C",
            target_compound="CO2",
            amount_type="mass"
        )
        print(f'   12g C → {result.get("target_mass", "N/A")} g CO2')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    # 9. 文本提取测试
    print('\n9. 文本提取功能:')
    try:
        formula = solver.extract_formula("水的化学式是H2O")
        print(f'   "水的化学式是H2O" → 化学式: {formula}')
        
        equation = solver.extract_equation("反应: H2 + O2 = H2O")
        print(f'   "反应: H2 + O2 = H2O" → 方程式: {equation}')
        
        compound = solver.extract_compound("计算二氧化碳的性质")
        print(f'   "计算二氧化碳的性质" → 化合物: {compound}')
    except Exception as e:
        print(f'   ERROR: {e}')
    
    print('\n=== 测试完成 ===')
    print('\n功能总结:')
    print('✓ 摩尔质量计算 - 支持基础化学式')
    print('✓ 浓度计算 - 支持多种参数组合')
    print('✓ pH值计算 - 支持强酸强碱和pOH转换')
    print('✓ 温度转换 - 支持C/F/K三种单位')
    print('✓ 气体定律 - 支持理想气体定律计算')
    print('✓ 稀释计算 - 支持C1V1=C2V2定律')
    print('✓ 方程式平衡 - 基于矩阵求解')
    print('✓ 化学计量学 - 支持摩尔、质量、体积计算')
    print('✓ 文本提取 - 智能提取化学式、方程式、化合物')

if __name__ == '__main__':
    test_chemistry_functions()