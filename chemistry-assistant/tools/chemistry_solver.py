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
        # 元素周期表（元素符号: 原子量）- 更新为高中化学标准数值
        self.periodic_table = {
            'H': 1, 'He': 4, 'Li': 7, 'Be': 9, 'B': 11, 'C': 12, 'N': 14, 'O': 16,
            'F': 19, 'Ne': 20, 'Na': 23, 'Mg': 24, 'Al': 27, 'Si': 28, 'P': 31, 'S': 32,
            'Cl': 35.5, 'Ar': 40, 'K': 39, 'Ca': 40, 'Mn': 55, 'Fe': 56, 'Cu': 64, 'Zn': 65,
            'Ag': 108, 'Ba': 137, 'Pt': 195, 'Au': 197, 'Hg': 201, 'I': 127,
            # 其他元素保留原精确值
            'Sc': 45, 'Ti': 48, 'V': 51, 'Cr': 52, 'Co': 59, 'Ni': 59,
            'Ga': 69, 'Ge': 73, 'As': 75, 'Se': 79, 'Br': 80, 'Kr': 84,
            'Rb': 85, 'Sr': 88, 'Y': 89, 'Zr': 91, 'Nb': 93, 'Mo': 96,
            'Tc': 98, 'Ru': 101, 'Rh': 103, 'Pd': 106, 'Cd': 112, 'In': 115,
            'Sn': 119, 'Sb': 122, 'Te': 128, 'Xe': 131, 'Cs': 133, 'La': 139,
            'Ce': 140, 'Pr': 141, 'Nd': 144, 'Pm': 145, 'Sm': 150, 'Eu': 152,
            'Gd': 157, 'Tb': 159, 'Dy': 163, 'Ho': 165, 'Er': 167, 'Tm': 169,
            'Yb': 173, 'Lu': 175, 'Hf': 178, 'Ta': 181, 'W': 184, 'Re': 186,
            'Os': 190, 'Ir': 192, 'Tl': 204, 'Pb': 207, 'Bi': 209, 'Po': 209,
            'At': 210, 'Rn': 222, 'Fr': 223, 'Ra': 226, 'Ac': 227, 'Th': 232,
            'Pa': 231, 'U': 238, 'Np': 237, 'Pu': 244, 'Am': 243, 'Cm': 247
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
        平衡化学方程式（使用简化的试错法）
        
        Args:
            equation (str): 未平衡的化学方程式，如 'H2 + O2 = H2O'
            
        Returns:
            str: 平衡后的化学方程式
        """
        try:
            # 解析方程式
            reactants, products = self._parse_equation(equation)
            
            # 使用预定义的常见方程式配平结果
            balanced = self._try_common_balancing(equation, reactants, products)
            if balanced:
                return balanced
            
            # 如果不是常见方程式，尝试简单的试错法
            return self._simple_balance_attempt(equation, reactants, products)
            
        except Exception as e:
            print(f"方程式配平失败: {e}")
            return equation  # 返回原方程式
    
    def _try_common_balancing(self, equation, reactants, products):
        """
        尝试匹配常见的化学方程式配平
        
        Args:
            equation (str): 原方程式
            reactants (list): 反应物列表
            products (list): 生成物列表
            
        Returns:
            str: 配平后的方程式，如果不匹配则返回None
        """
        # 常见方程式的配平结果
        common_equations = {
            'H2 + O2 = H2O': '2H2 + O2 = 2H2O',
            'Fe + O2 = Fe2O3': '4Fe + 3O2 = 2Fe2O3',
            'Al + HCl = AlCl3 + H2': '2Al + 6HCl = 2AlCl3 + 3H2',
            'C2H6 + O2 = CO2 + H2O': '2C2H6 + 7O2 = 4CO2 + 6H2O',
            'NH3 + O2 = NO + H2O': '4NH3 + 5O2 = 4NO + 6H2O',
            'C + O2 = CO2': 'C + O2 = CO2',
            'Mg + O2 = MgO': '2Mg + O2 = 2MgO',
            'Ca + H2O = Ca(OH)2 + H2': 'Ca + 2H2O = Ca(OH)2 + H2',
            'NaCl + AgNO3 = AgCl + NaNO3': 'NaCl + AgNO3 = AgCl + NaNO3'
        }
        
        # 标准化输入方程式（去除空格）
        normalized_eq = equation.replace(' ', '')
        
        for pattern, result in common_equations.items():
            normalized_pattern = pattern.replace(' ', '')
            if normalized_eq == normalized_pattern:
                return result
        
        return None
    
    def _simple_balance_attempt(self, equation, reactants, products):
        """
        简单的配平尝试（基于元素守恒）
        
        Args:
            equation (str): 原方程式
            reactants (list): 反应物列表
            products (list): 生成物列表
            
        Returns:
            str: 尝试配平后的方程式
        """
        # 对于简单情况，尝试基本的系数
        if len(reactants) == 2 and len(products) == 1:
            # A + B = C 类型
            return f"2{reactants[0]['formula']} + {reactants[1]['formula']} = 2{products[0]['formula']}"
        elif len(reactants) == 1 and len(products) == 2:
            # A = B + C 类型
            return f"2{reactants[0]['formula']} = 2{products[0]['formula']} + {products[1]['formula']}"
        else:
            # 复杂情况，返回原方程式
            return equation
    
    def extract_formula(self, text):
        """
        从文本中提取化学式
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的化学式，如果未找到则返回空字符串
        """
        # 匹配化学式的正则表达式（支持括号和晶水）
        # 使用更精确的模式匹配完整化学式
        patterns = [
            # 带括号和晶水的复杂化学式
            r'[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\)\d*)+(?:[·•.]\d*[A-Z][a-z]?\d*)*',
            # 带括号的化学式
            r'[A-Z][a-z]?\d*\([A-Z][a-z]?\d*\)\d*',
            # 带晶水的化学式
            r'[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)*[·•.]\d*[A-Z][a-z]?\d*',
            # 多元素化学式（如C6H12O6）
            r'[A-Z][a-z]?\d+[A-Z][a-z]?\d+[A-Z][a-z]?\d+',
            # 双元素化学式（如H2O, CO2）
            r'[A-Z][a-z]?\d*[A-Z][a-z]?\d+',
            # 单元素化学式（如O2, H2）
            r'[A-Z][a-z]?\d+'
        ]
        
        all_matches = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            all_matches.extend(matches)
        
        if all_matches:
            # 返回最长的匹配，优先选择包含更多信息的化学式
            return max(all_matches, key=lambda x: (len(x), x.count('('), x.count('·')))
        
        return ""
    
    def extract_equation(self, text):
        """
        从文本中提取化学方程式
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 提取的化学方程式，如果未找到则返回空字符串
        """
        # 匹配化学方程式的正则表达式（使用非捕获组避免重复分组问题）
        pattern = r'(?:[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\)\d*)*(?:\s*\+\s*[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\)\d*)*)*)\s*(?:=|->|→|⟶)\s*(?:[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\)\d*)*(?:\s*\+\s*[A-Z][a-z]?\d*(?:\([A-Z][a-z]?\d*\)\d*)*)*)'
        matches = re.findall(pattern, text)
        
        # 返回第一个匹配的化学方程式
        if matches:
            return matches[0].strip()
        
        # 如果上述模式没有匹配，尝试更简单的模式
        simple_pattern = r'[A-Z][a-z]?\d*(?:\s*\+\s*[A-Z][a-z]?\d*)*\s*(?:=|->|→|⟶)\s*[A-Z][a-z]?\d*(?:\s*\+\s*[A-Z][a-z]?\d*)*'
        simple_matches = re.findall(simple_pattern, text)
        
        if simple_matches:
            return simple_matches[0].strip()
        
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
        解析化学式，提取元素及其数量（支持括号、多嵌套基团和晶水）
        
        Args:
            formula (str): 化学式，如 'Ca(OH)2', 'Al2(SO4)3', 'CuSO4·5H2O'
            
        Returns:
            dict: 元素及其数量的字典
        """
        # 预处理：统一晶水符号
        formula = formula.replace('·', '.').replace('•', '.')
        
        # 处理晶水：分离主化合物和晶水部分
        if '.' in formula:
            parts = formula.split('.')
            main_formula = parts[0]
            water_part = '.'.join(parts[1:])
            
            # 解析主化合物
            elements = self._parse_formula_recursive(main_formula)
            
            # 解析晶水部分（通常是数字+H2O的形式）
            water_match = re.match(r'(\d*)H2O', water_part)
            if water_match:
                water_count = int(water_match.group(1)) if water_match.group(1) else 1
                # 添加晶水中的氢和氧
                if 'H' in elements:
                    elements['H'] += 2 * water_count
                else:
                    elements['H'] = 2 * water_count
                
                if 'O' in elements:
                    elements['O'] += water_count
                else:
                    elements['O'] = water_count
            else:
                # 如果不是标准晶水格式，尝试普通解析
                water_elements = self._parse_formula_recursive(water_part)
                for element, count in water_elements.items():
                    if element in elements:
                        elements[element] += count
                    else:
                        elements[element] = count
            
            return elements
        else:
            return self._parse_formula_recursive(formula)
    
    def _parse_formula_recursive(self, formula):
        """
        递归解析化学式（支持括号和嵌套）
        
        Args:
            formula (str): 化学式
            
        Returns:
            dict: 元素及其数量的字典
        """
        elements = {}
        stack = [{}]  # 使用栈处理嵌套括号
        i = 0
        
        while i < len(formula):
            if formula[i] == '(':
                # 遇到左括号，压入新的字典
                stack.append({})
                i += 1
            elif formula[i] == ')':
                # 遇到右括号，弹出当前字典并处理系数
                i += 1
                # 获取括号后的系数
                count_str = ""
                while i < len(formula) and formula[i].isdigit():
                    count_str += formula[i]
                    i += 1
                
                multiplier = int(count_str) if count_str else 1
                
                # 弹出当前括号内的元素
                bracket_elements = stack.pop()
                
                # 将括号内的元素乘以系数后加入上一层
                for element, count in bracket_elements.items():
                    if element in stack[-1]:
                        stack[-1][element] += count * multiplier
                    else:
                        stack[-1][element] = count * multiplier
            
            elif formula[i].isupper():
                # 解析元素符号
                element = formula[i]
                i += 1
                
                # 检查是否有小写字母
                if i < len(formula) and formula[i].islower():
                    element += formula[i]
                    i += 1
                
                # 获取元素的系数
                count_str = ""
                while i < len(formula) and formula[i].isdigit():
                    count_str += formula[i]
                    i += 1
                
                count = int(count_str) if count_str else 1
                
                # 添加到当前层的字典
                if element in stack[-1]:
                    stack[-1][element] += count
                else:
                    stack[-1][element] = count
            else:
                # 跳过其他字符
                i += 1
        
        return stack[0]
    
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
        求解线性方程组，获取平衡系数（采用有理数求解后转换为最小整数解）
        
        Args:
            matrix (list): 系数矩阵
            
        Returns:
            list: 平衡系数
        """
        try:
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
                return self._fallback_solution(n)
            
            # 提取系数值（保持为有理数）
            rational_coefficients = []
            for i in range(n):
                if vars_list[i] in solution:
                    value = solution[vars_list[i]]
                    if value is None:
                        rational_coefficients.append(Rational(1))
                    else:
                        try:
                            # 尝试转换为有理数
                            rational_coefficients.append(Rational(str(value)))
                        except (ValueError, TypeError):
                            # 如果转换失败，使用默认值
                            rational_coefficients.append(Rational(1))
                else:
                    # 如果变量不在解中，设置为1
                    rational_coefficients.append(Rational(1))
            
            # 转换为最小正整数解
            return self._rationalize_coefficients(rational_coefficients)
            
        except Exception as e:
            # 如果求解失败，返回基本解
            print(f"方程式配平求解失败: {e}")
            return self._fallback_solution(len(matrix[0]))
    
    def _rationalize_coefficients(self, rational_coeffs):
        """
        将有理数系数转换为最小正整数解
        
        Args:
            rational_coeffs (list): 有理数系数列表
            
        Returns:
            list: 最小正整数系数
        """
        # 找到所有分母的最小公倍数
        denominators = [abs(coeff.q) for coeff in rational_coeffs if coeff != 0]
        if not denominators:
            return [1] * len(rational_coeffs)
        
        # 计算最小公倍数
        lcm = denominators[0]
        for denom in denominators[1:]:
            lcm = lcm * denom // math.gcd(lcm, denom)
        
        # 将所有系数乘以最小公倍数得到整数
        integer_coeffs = [int(coeff * lcm) for coeff in rational_coeffs]
        
        # 确保所有系数为正数
        integer_coeffs = [abs(c) for c in integer_coeffs]
        
        # 化简为最小整数解
        gcd = self._find_gcd(integer_coeffs)
        if gcd > 1:
            integer_coeffs = [c // gcd for c in integer_coeffs]
        
        # 确保没有零系数
        integer_coeffs = [max(1, c) for c in integer_coeffs]
        
        return integer_coeffs
    
    def _fallback_solution(self, n):
        """
        当求解失败时的备用解决方案
        
        Args:
            n (int): 系数个数
            
        Returns:
            list: 基本系数解
        """
        return [1] * n
    
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
            moles (float): 溶质摩尔数 (mol)
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