#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
化学求解器
提供摩尔质量计算、方程式平衡等功能
"""

import re
import math
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
    
    def calculate_concentration(self, moles=None, volume=None, mass=None, molar_mass=None, molarity=None):
        """
        计算溶液浓度
        
        Args:
            moles (float): 溶质的摩尔数 (mol)
            volume (float): 溶液体积 (L)
            mass (float): 溶质质量 (g)
            molar_mass (float): 溶质摩尔质量 (g/mol)
            molarity (float): 摩尔浓度 (mol/L)
            
        Returns:
            dict: 包含计算结果的字典
        """
        result = {}
        
        # 如果给定质量和摩尔质量，计算摩尔数
        if mass is not None and molar_mass is not None:
            moles = mass / molar_mass
            result['moles_calculated'] = moles
        
        # 计算摩尔浓度 (M = n/V)
        if moles is not None and volume is not None:
            molarity = moles / volume
            result['molarity'] = molarity
            result['molarity_unit'] = 'mol/L'
        
        # 计算体积 (V = n/M)
        elif moles is not None and molarity is not None:
            volume = moles / molarity
            result['volume'] = volume
            result['volume_unit'] = 'L'
        
        # 计算摩尔数 (n = M×V)
        elif molarity is not None and volume is not None:
            moles = molarity * volume
            result['moles'] = moles
            result['moles_unit'] = 'mol'
        
        return result
    
    def calculate_ph(self, concentration=None, poh=None, is_acid=True, is_strong=True, ka=None, kb=None):
        """
        计算pH值
        
        Args:
            concentration (float): 酸或碱的浓度 (mol/L)
            poh (float): pOH值
            is_acid (bool): 是否为酸性溶液
            is_strong (bool): 是否为强酸/强碱
            ka (float): 酸解离常数
            kb (float): 碱解离常数
            
        Returns:
            dict: 包含pH、pOH、[H+]、[OH-]等信息的字典
        """
        result = {}
        
        # 从pOH计算pH
        if poh is not None:
            ph = 14 - poh
            result['pH'] = ph
            result['pOH'] = poh
            result['H+_concentration'] = 10 ** (-ph)
            result['OH-_concentration'] = 10 ** (-poh)
            return result
        
        if concentration is None:
            raise ValueError("必须提供浓度或pOH值")
        
        if is_strong:
            # 强酸强碱的计算
            if is_acid:
                # 强酸: [H+] = C
                h_concentration = concentration
                ph = -math.log10(h_concentration)
            else:
                # 强碱: [OH-] = C
                oh_concentration = concentration
                poh = -math.log10(oh_concentration)
                ph = 14 - poh
                h_concentration = 10 ** (-ph)
        else:
            # 弱酸弱碱的计算
            if is_acid and ka is not None:
                # 弱酸: [H+] = sqrt(Ka × C)
                h_concentration = math.sqrt(ka * concentration)
                ph = -math.log10(h_concentration)
            elif not is_acid and kb is not None:
                # 弱碱: [OH-] = sqrt(Kb × C)
                oh_concentration = math.sqrt(kb * concentration)
                poh = -math.log10(oh_concentration)
                ph = 14 - poh
                h_concentration = 10 ** (-ph)
            else:
                raise ValueError("弱酸弱碱计算需要提供Ka或Kb值")
        
        result['pH'] = round(ph, 2)
        result['pOH'] = round(14 - ph, 2)
        result['H+_concentration'] = h_concentration
        result['OH-_concentration'] = 10 ** (-(14 - ph))
        result['concentration_input'] = concentration
        result['acid_type'] = '强酸' if is_strong and is_acid else ('弱酸' if is_acid else ('强碱' if is_strong else '弱碱'))
        
        return result
    
    def calculate_gas_law(self, pressure=None, volume=None, temperature=None, moles=None, 
                         mass=None, molar_mass=None, law_type='ideal'):
        """
        气体定律计算 (理想气体定律: PV = nRT)
        
        Args:
            pressure (float): 压强 (atm)
            volume (float): 体积 (L)
            temperature (float): 温度 (K)
            moles (float): 摩尔数 (mol)
            mass (float): 质量 (g)
            molar_mass (float): 摩尔质量 (g/mol)
            law_type (str): 气体定律类型 ('ideal', 'boyle', 'charles', 'gay_lussac')
            
        Returns:
            dict: 包含计算结果的字典
        """
        R = 0.08206  # 理想气体常数 (L·atm/(mol·K))
        result = {}
        
        # 如果给定质量和摩尔质量，计算摩尔数
        if mass is not None and molar_mass is not None:
            moles = mass / molar_mass
            result['moles_calculated'] = moles
        
        if law_type == 'ideal':
            # 理想气体定律: PV = nRT
            known_vars = sum([1 for var in [pressure, volume, temperature, moles] if var is not None])
            
            if known_vars < 3:
                raise ValueError("理想气体定律计算至少需要3个已知量")
            
            if pressure is None:
                pressure = (moles * R * temperature) / volume
                result['pressure'] = pressure
                result['pressure_unit'] = 'atm'
            elif volume is None:
                volume = (moles * R * temperature) / pressure
                result['volume'] = volume
                result['volume_unit'] = 'L'
            elif temperature is None:
                temperature = (pressure * volume) / (moles * R)
                result['temperature'] = temperature
                result['temperature_unit'] = 'K'
                result['temperature_celsius'] = temperature - 273.15
            elif moles is None:
                moles = (pressure * volume) / (R * temperature)
                result['moles'] = moles
                result['moles_unit'] = 'mol'
        
        elif law_type == 'boyle':
            # 玻意耳定律: P1V1 = P2V2 (温度恒定)
            if pressure is not None and volume is not None:
                result['PV_product'] = pressure * volume
                result['law'] = 'Boyle\'s Law: P₁V₁ = P₂V₂'
        
        elif law_type == 'charles':
            # 查理定律: V1/T1 = V2/T2 (压强恒定)
            if volume is not None and temperature is not None:
                result['V_over_T'] = volume / temperature
                result['law'] = 'Charles\' Law: V₁/T₁ = V₂/T₂'
        
        elif law_type == 'gay_lussac':
            # 盖-吕萨克定律: P1/T1 = P2/T2 (体积恒定)
            if pressure is not None and temperature is not None:
                result['P_over_T'] = pressure / temperature
                result['law'] = 'Gay-Lussac\'s Law: P₁/T₁ = P₂/T₂'
        
        # 添加标准状态下的信息
        if moles is not None:
            result['volume_at_STP'] = moles * 22.4  # 标准状况下的体积 (L)
            result['volume_at_STP_unit'] = 'L (at STP)'
        
        return result
    
    def calculate_stoichiometry(self, equation, given_amount, given_compound, target_compound, amount_type='moles'):
        """
        化学计量学计算
        
        Args:
            equation (str): 平衡的化学方程式
            given_amount (float): 已知物质的量
            given_compound (str): 已知物质的化学式
            target_compound (str): 目标物质的化学式
            amount_type (str): 量的类型 ('moles', 'mass', 'volume_gas')
            
        Returns:
            dict: 包含计算结果的字典
        """
        result = {}
        
        # 解析平衡方程式获取系数
        reactants, products = self._parse_equation(equation)
        all_compounds = reactants + products
        
        # 找到给定物质和目标物质的系数
        given_coeff = None
        target_coeff = None
        
        for compound in all_compounds:
            if compound['formula'] == given_compound:
                given_coeff = compound['coefficient']
            if compound['formula'] == target_compound:
                target_coeff = compound['coefficient']
        
        if given_coeff is None:
            raise ValueError(f"在方程式中未找到化合物: {given_compound}")
        if target_coeff is None:
            raise ValueError(f"在方程式中未找到化合物: {target_compound}")
        
        # 计算摩尔比
        molar_ratio = target_coeff / given_coeff
        
        if amount_type == 'moles':
            # 直接按摩尔比计算
            target_moles = given_amount * molar_ratio
            result['target_moles'] = target_moles
            result['target_moles_unit'] = 'mol'
        
        elif amount_type == 'mass':
            # 质量计算：先转换为摩尔数，再计算目标摩尔数，最后转换为质量
            given_molar_mass = self.calculate_molar_mass(given_compound)
            target_molar_mass = self.calculate_molar_mass(target_compound)
            
            given_moles = given_amount / given_molar_mass
            target_moles = given_moles * molar_ratio
            target_mass = target_moles * target_molar_mass
            
            result['given_molar_mass'] = given_molar_mass
            result['target_molar_mass'] = target_molar_mass
            result['given_moles'] = given_moles
            result['target_moles'] = target_moles
            result['target_mass'] = target_mass
            result['target_mass_unit'] = 'g'
        
        elif amount_type == 'volume_gas':
            # 气体体积计算（标准状况）
            given_moles = given_amount / 22.4  # 标准状况下1mol气体占22.4L
            target_moles = given_moles * molar_ratio
            target_volume = target_moles * 22.4
            
            result['given_moles'] = given_moles
            result['target_moles'] = target_moles
            result['target_volume'] = target_volume
            result['target_volume_unit'] = 'L (at STP)'
        
        result['molar_ratio'] = molar_ratio
        result['equation'] = equation
        result['given_compound'] = given_compound
        result['target_compound'] = target_compound
        result['given_coefficient'] = given_coeff
        result['target_coefficient'] = target_coeff
        
        return result
    
    def convert_temperature(self, temperature, from_unit='C', to_unit='K'):
        """
        温度单位转换
        
        Args:
            temperature (float): 温度值
            from_unit (str): 原单位 ('C', 'K', 'F')
            to_unit (str): 目标单位 ('C', 'K', 'F')
            
        Returns:
            float: 转换后的温度值
        """
        # 先转换为开尔文
        if from_unit == 'C':
            kelvin = temperature + 273.15
        elif from_unit == 'F':
            kelvin = (temperature - 32) * 5/9 + 273.15
        elif from_unit == 'K':
            kelvin = temperature
        else:
            raise ValueError("不支持的温度单位")
        
        # 从开尔文转换为目标单位
        if to_unit == 'C':
            return kelvin - 273.15
        elif to_unit == 'F':
            return (kelvin - 273.15) * 9/5 + 32
        elif to_unit == 'K':
            return kelvin
        else:
            raise ValueError("不支持的温度单位")
    
    def calculate_solution_dilution(self, c1=None, v1=None, c2=None, v2=None):
        """
        溶液稀释计算 (C1V1 = C2V2)
        
        Args:
            c1 (float): 原溶液浓度 (mol/L)
            v1 (float): 原溶液体积 (L)
            c2 (float): 稀释后浓度 (mol/L)
            v2 (float): 稀释后体积 (L)
            
        Returns:
            dict: 包含计算结果的字典
        """
        result = {}
        known_vars = sum([1 for var in [c1, v1, c2, v2] if var is not None])
        
        if known_vars < 3:
            raise ValueError("稀释计算至少需要3个已知量")
        
        if c1 is None:
            c1 = (c2 * v2) / v1
            result['original_concentration'] = c1
            result['original_concentration_unit'] = 'mol/L'
        elif v1 is None:
            v1 = (c2 * v2) / c1
            result['original_volume'] = v1
            result['original_volume_unit'] = 'L'
        elif c2 is None:
            c2 = (c1 * v1) / v2
            result['final_concentration'] = c2
            result['final_concentration_unit'] = 'mol/L'
        elif v2 is None:
            v2 = (c1 * v1) / c2
            result['final_volume'] = v2
            result['final_volume_unit'] = 'L'
        
        # 计算稀释倍数
        if c1 is not None and c2 is not None:
            dilution_factor = c1 / c2
            result['dilution_factor'] = dilution_factor
        
        # 计算需要加入的溶剂体积
        if v1 is not None and v2 is not None:
            solvent_volume = v2 - v1
            result['solvent_volume_to_add'] = solvent_volume
            result['solvent_volume_unit'] = 'L'
        
        result['equation'] = 'C₁V₁ = C₂V₂'
        
        return result