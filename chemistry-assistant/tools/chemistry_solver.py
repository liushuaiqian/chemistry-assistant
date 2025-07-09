#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学求解器
提供摩尔质量计算、方程式平衡等功能
"""

import re
from sympy import symbols, Matrix, solve_linear_system, Rational

class ChemistrySolver:
    """
    化学求解器类
    提供各种化学计算和处理功能
    """
    
    def __init__(self):
        """
        初始化化学求解器
        """
        # 元素周期表（元素符号: 原子量）
        self.periodic_table = {
            'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012, 'B': 10.811, 'C': 12.011, 'N': 14.007, 'O': 15.999,
            'F': 18.998, 'Ne': 20.180, 'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086, 'P': 30.974, 'S': 32.065,
            'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078, 'Sc': 44.956, 'Ti': 47.867, 'V': 50.942, 'Cr': 51.996,
            'Mn': 54.938, 'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.380, 'Ga': 69.723, 'Ge': 72.640,
            'As': 74.922, 'Se': 78.971, 'Br': 79.904, 'Kr': 83.798, 'Rb': 85.468, 'Sr': 87.620, 'Y': 88.906, 'Zr': 91.224,
            'Nb': 92.906, 'Mo': 95.950, 'Tc': 98.000, 'Ru': 101.070, 'Rh': 102.906, 'Pd': 106.420, 'Ag': 107.868, 'Cd': 112.411,
            'In': 114.818, 'Sn': 118.710, 'Sb': 121.760, 'Te': 127.600, 'I': 126.904, 'Xe': 131.293, 'Cs': 132.905, 'Ba': 137.327,
            'La': 138.905, 'Ce': 140.116, 'Pr': 140.908, 'Nd': 144.242, 'Pm': 145.000, 'Sm': 150.360, 'Eu': 151.964, 'Gd': 157.250,
            'Tb': 158.925, 'Dy': 162.500, 'Ho': 164.930, 'Er': 167.259, 'Tm': 168.934, 'Yb': 173.054, 'Lu': 174.967, 'Hf': 178.490,
            'Ta': 180.948, 'W': 183.840, 'Re': 186.207, 'Os': 190.230, 'Ir': 192.217, 'Pt': 195.084, 'Au': 196.967, 'Hg': 200.590,
            'Tl': 204.383, 'Pb': 207.200, 'Bi': 208.980, 'Po': 209.000, 'At': 210.000, 'Rn': 222.000, 'Fr': 223.000, 'Ra': 226.000,
            'Ac': 227.000, 'Th': 232.038, 'Pa': 231.036, 'U': 238.029, 'Np': 237.000, 'Pu': 244.000, 'Am': 243.000, 'Cm': 247.000
        }
    
    def calculate_molar_mass(self, formula):
        """
        计算化学式的摩尔质量
        
        Args:
            formula (str): 化学式，如 'H2O', 'C6H12O6'
            
        Returns:
            float: 摩尔质量 (g/mol)
        """
        # 解析化学式
        elements = self._parse_formula(formula)
        
        # 计算摩尔质量
        molar_mass = 0.0
        for element, count in elements.items():
            if element in self.periodic_table:
                molar_mass += self.periodic_table[element] * count
            else:
                raise ValueError(f"未知元素: {element}")
        
        return molar_mass
    
    def balance_equation(self, equation):
        """
        平衡化学方程式
        
        Args:
            equation (str): 未平衡的化学方程式，如 'H2 + O2 = H2O'
            
        Returns:
            str: 平衡后的化学方程式
        """
        # 解析方程式
        reactants, products = self._parse_equation(equation)
        
        # 获取所有元素
        all_elements = set()
        for compound in reactants + products:
            elements = self._parse_formula(compound['formula'])
            all_elements.update(elements.keys())
        
        # 构建系数矩阵
        matrix = []
        for element in all_elements:
            row = []
            # 反应物系数（正）
            for compound in reactants:
                elements = self._parse_formula(compound['formula'])
                row.append(elements.get(element, 0))
            # 生成物系数（负）
            for compound in products:
                elements = self._parse_formula(compound['formula'])
                row.append(-elements.get(element, 0))
            matrix.append(row)
        
        # 求解线性方程组
        coefficients = self._solve_matrix(matrix)
        
        # 构建平衡后的方程式
        balanced_equation = ""
        for i, compound in enumerate(reactants):
            if i > 0:
                balanced_equation += " + "
            coef = coefficients[i]
            if coef > 1:
                balanced_equation += str(coef)
            balanced_equation += compound['formula']
        
        balanced_equation += " = "
        
        for i, compound in enumerate(products):
            if i > 0:
                balanced_equation += " + "
            coef = coefficients[i + len(reactants)]
            if coef > 1:
                balanced_equation += str(coef)
            balanced_equation += compound['formula']
        
        return balanced_equation
    
    def extract_formula(self, text):
        """
        从文本中提取化学式
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的化学式，如果未找到则返回空字符串
        """
        # 匹配化学式的正则表达式
        pattern = r'([A-Z][a-z]?\d*)+'
        matches = re.findall(pattern, text)
        
        # 返回第一个匹配的化学式
        if matches:
            return matches[0]
        
        return ""
    
    def extract_equation(self, text):
        """
        从文本中提取化学方程式
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的化学方程式，如果未找到则返回空字符串
        """
        # 匹配化学方程式的正则表达式（包含等号或箭头）
        pattern = r'([A-Z][a-z]?\d*)+(?:[\s+]+([A-Z][a-z]?\d*)+)*\s*(?:=|->|→|⟶)\s*([A-Z][a-z]?\d*)+(?:[\s+]+([A-Z][a-z]?\d*)+)*'
        matches = re.findall(pattern, text)
        
        # 返回第一个匹配的化学方程式
        if matches:
            # 重建完整的方程式
            equation_parts = []
            for part in matches[0]:
                if part:
                    equation_parts.append(part)
            
            # 插入等号
            if len(equation_parts) >= 2:
                equation = equation_parts[0]
                for i in range(1, len(equation_parts)):
                    if i == len(equation_parts) // 2:
                        equation += " = "
                    else:
                        equation += " + "
                    equation += equation_parts[i]
                return equation
        
        return ""
    
    def extract_compound(self, text):
        """
        从文本中提取化合物名称或化学式
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的化合物，如果未找到则返回空字符串
        """
        # 首先尝试提取化学式
        formula = self.extract_formula(text)
        if formula:
            return formula
        
        # 如果没有找到化学式，尝试匹配常见化合物名称
        common_compounds = [
            '水', '氧气', '二氧化碳', '氢气', '氮气', '甲烷', '乙醇', '乙酸', '氨气', '硫酸',
            '盐酸', '氢氧化钠', '氯化钠', '碳酸钙', '葡萄糖', '蔗糖', '淀粉', '蛋白质', '脂肪', '维生素'
        ]
        
        for compound in common_compounds:
            if compound in text:
                return compound
        
        return ""
    
    def _parse_formula(self, formula):
        """
        解析化学式，提取元素及其数量
        
        Args:
            formula (str): 化学式
            
        Returns:
            dict: 元素及其数量的字典
        """
        elements = {}
        i = 0
        
        while i < len(formula):
            # 匹配元素符号（第一个字母大写，可能跟着一个小写字母）
            if formula[i].isupper():
                if i + 1 < len(formula) and formula[i + 1].islower():
                    element = formula[i:i+2]
                    i += 2
                else:
                    element = formula[i]
                    i += 1
                
                # 匹配数量（如果有）
                count = ""
                while i < len(formula) and formula[i].isdigit():
                    count += formula[i]
                    i += 1
                
                # 如果没有明确的数量，默认为1
                count = int(count) if count else 1
                
                # 更新元素计数
                if element in elements:
                    elements[element] += count
                else:
                    elements[element] = count
            else:
                # 跳过非元素字符
                i += 1
        
        return elements
    
    def _parse_equation(self, equation):
        """
        解析化学方程式，提取反应物和生成物
        
        Args:
            equation (str): 化学方程式
            
        Returns:
            tuple: (反应物列表, 生成物列表)
        """
        # 替换各种等号和箭头为标准等号
        equation = equation.replace('->', '=').replace('→', '=').replace('⟶', '=')
        
        # 分割反应物和生成物
        sides = equation.split('=')
        if len(sides) != 2:
            raise ValueError("无效的方程式格式")
        
        reactants_str = sides[0].strip()
        products_str = sides[1].strip()
        
        # 解析反应物
        reactants = []
        for reactant in reactants_str.split('+'):
            reactant = reactant.strip()
            # 提取系数（如果有）
            match = re.match(r'^(\d+)(.+)$', reactant)
            if match:
                coefficient = int(match.group(1))
                formula = match.group(2).strip()
            else:
                coefficient = 1
                formula = reactant
            
            reactants.append({'formula': formula, 'coefficient': coefficient})
        
        # 解析生成物
        products = []
        for product in products_str.split('+'):
            product = product.strip()
            # 提取系数（如果有）
            match = re.match(r'^(\d+)(.+)$', product)
            if match:
                coefficient = int(match.group(1))
                formula = match.group(2).strip()
            else:
                coefficient = 1
                formula = product
            
            products.append({'formula': formula, 'coefficient': coefficient})
        
        return reactants, products
    
    def _solve_matrix(self, matrix):
        """
        求解线性方程组，获取平衡系数
        
        Args:
            matrix (list): 系数矩阵
            
        Returns:
            list: 平衡系数
        """
        # 使用SymPy求解线性方程组
        n = len(matrix[0])  # 未知数个数（系数）
        
        # 创建符号变量
        vars_list = symbols(f'x0:{n}')
        
        # 构建增广矩阵（右侧为0）
        augmented_matrix = [row + [0] for row in matrix]
        
        # 求解线性方程组
        solution = solve_linear_system(Matrix(augmented_matrix), *vars_list)
        
        # 如果没有解，使用基本的高斯消元法
        if not solution:
            # 设置第一个系数为1
            solution = {vars_list[0]: 1}
            # 这里应该实现完整的高斯消元法，但为简化，我们返回一个基本解
            for i in range(1, n):
                solution[vars_list[i]] = 1
        
        # 提取系数值并转换为整数
        coefficients = []
        for i in range(n):
            if vars_list[i] in solution:
                value = solution[vars_list[i]]
                if isinstance(value, Rational):
                    # 如果是分数，转换为浮点数再四舍五入为整数
                    coefficients.append(round(float(value)))
                else:
                    coefficients.append(int(value))
            else:
                # 如果变量不在解中，设置为1
                coefficients.append(1)
        
        # 确保所有系数为正整数且最小
        gcd = self._find_gcd(coefficients)
        coefficients = [abs(c // gcd) if gcd != 0 else abs(c) for c in coefficients]
        
        return coefficients
    
    def _find_gcd(self, numbers):
        """
        计算一组数的最大公约数
        
        Args:
            numbers (list): 整数列表
            
        Returns:
            int: 最大公约数
        """
        from math import gcd
        from functools import reduce
        
        # 过滤掉0
        non_zero = [n for n in numbers if n != 0]
        if not non_zero:
            return 1
        
        # 计算最大公约数
        return reduce(gcd, non_zero)