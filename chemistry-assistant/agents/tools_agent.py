#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具Agent
负责化学计算类工具调用
"""

from tools.chemistry_solver import ChemistrySolver
from tools.knowledge_api import KnowledgeAPI

class ToolsAgent:
    """
    工具Agent类
    负责调用各种化学计算工具和知识API
    """
    
    def __init__(self):
        """
        初始化工具Agent
        """
        self.chemistry_solver = ChemistrySolver()
        self.knowledge_api = KnowledgeAPI()
        self.name = "工具Agent"
    
    def process(self, query, task_info, context=None):
        """
        处理用户查询
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            context (dict, optional): 上下文信息，包含其他Agent的处理结果
            
        Returns:
            str: 处理结果
        """
        # 分析查询，确定需要使用的工具
        tool_type = self._determine_tool_type(query, task_info)
        
        # 根据工具类型调用相应的处理函数
        if tool_type == 'molar_mass':
            result = self._calculate_molar_mass(query, task_info)
        elif tool_type == 'balance_equation':
            result = self._balance_equation(query, task_info)
        elif tool_type == 'compound_info':
            result = self._get_compound_info(query, task_info)
        elif tool_type == 'concentration':
            result = self._calculate_concentration(query, task_info)
        elif tool_type == 'ph':
            result = self._calculate_ph(query, task_info)
        elif tool_type == 'gas_law':
            result = self._calculate_gas_law(query, task_info)
        elif tool_type == 'stoichiometry':
            result = self._calculate_stoichiometry(query, task_info)
        elif tool_type == 'temperature':
            result = self._convert_temperature(query, task_info)
        elif tool_type == 'dilution':
            result = self._calculate_dilution(query, task_info)
        else:
            result = "无法确定需要使用的工具类型"
        
        return result
    
    def _determine_tool_type(self, query, task_info):
        """
        确定需要使用的工具类型
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 工具类型
        """
        # 检查是否包含摩尔质量计算相关关键词
        if any(keyword in query for keyword in ['摩尔质量', '分子量', '原子量', '质量']):
            return 'molar_mass'
        
        # 检查是否包含方程式平衡相关关键词
        if any(keyword in query for keyword in ['方程式', '平衡', '化学反应', '反应方程式']):
            return 'balance_equation'
        
        # 检查是否包含化合物信息查询相关关键词
        if any(keyword in query for keyword in ['化合物', '性质', '结构', '信息']):
            return 'compound_info'
        
        # 检查是否包含浓度计算相关关键词
        if any(keyword in query for keyword in ['浓度', '摩尔浓度', '质量浓度', 'mol/L', 'g/L', '溶液']):
            return 'concentration'
        
        # 检查是否包含pH计算相关关键词
        if any(keyword in query for keyword in ['pH', 'ph', 'pOH', '酸碱', '氢离子', '氢氧根']):
            return 'ph'
        
        # 检查是否包含气体定律相关关键词
        if any(keyword in query for keyword in ['气体定律', '理想气体', '波义耳', '查理', '盖吕萨克', '压强', '体积', '温度']):
            return 'gas_law'
        
        # 检查是否包含化学计量学相关关键词
        if any(keyword in query for keyword in ['化学计量', '反应量', '产物量', '理论产量', '实际产量']):
            return 'stoichiometry'
        
        # 检查是否包含温度转换相关关键词
        if any(keyword in query for keyword in ['温度转换', '摄氏度', '华氏度', '开尔文', '°C', '°F', 'K']):
            return 'temperature'
        
        # 检查是否包含稀释计算相关关键词
        if any(keyword in query for keyword in ['稀释', '稀释液', '浓缩', '稀释倍数']):
            return 'dilution'
        
        # 检查是否有检测到的化合物实体
        if 'detected_entities' in task_info:
            for entity in task_info['detected_entities']:
                if entity['type'] == 'compound':
                    return 'compound_info'
        
        # 默认返回空
        return ''
    
    def _calculate_molar_mass(self, query, task_info):
        """
        计算摩尔质量
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        # 从查询或任务信息中提取化学式
        formula = self._extract_formula(query, task_info)
        
        if not formula:
            return "未能识别化学式，请明确指定要计算摩尔质量的化合物"
        
        # 调用化学求解器计算摩尔质量
        try:
            molar_mass = self.chemistry_solver.calculate_molar_mass(formula)
            return f"{formula}的摩尔质量为: {molar_mass:.4f} g/mol"
        except Exception as e:
            return f"计算摩尔质量时出错: {str(e)}"
    
    def _balance_equation(self, query, task_info):
        """
        平衡化学方程式
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 平衡后的方程式
        """
        # 从查询中提取未平衡的方程式
        equation = self._extract_equation(query)
        
        if not equation:
            return "未能识别化学方程式，请明确指定要平衡的方程式"
        
        # 调用化学求解器平衡方程式
        try:
            balanced_equation = self.chemistry_solver.balance_equation(equation)
            return f"平衡后的方程式: {balanced_equation}"
        except Exception as e:
            return f"平衡方程式时出错: {str(e)}"
    
    def _get_compound_info(self, query, task_info):
        """
        获取化合物信息
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 化合物信息
        """
        # 从查询或任务信息中提取化合物名称或化学式
        compound = self._extract_compound(query, task_info)
        
        if not compound:
            return "未能识别化合物，请明确指定要查询的化合物"
        
        # 调用知识API获取化合物信息
        try:
            compound_info = self.knowledge_api.get_compound_info(compound)
            
            # 格式化输出
            result = f"化合物信息: {compound}\n\n"
            result += f"分子式: {compound_info.get('molecular_formula', '未知')}\n"
            result += f"摩尔质量: {compound_info.get('molar_mass', '未知')} g/mol\n"
            result += f"密度: {compound_info.get('density', '未知')} g/cm³\n"
            result += f"熔点: {compound_info.get('melting_point', '未知')} °C\n"
            result += f"沸点: {compound_info.get('boiling_point', '未知')} °C\n"
            result += f"溶解性: {compound_info.get('solubility', '未知')}\n"
            result += f"危险性: {compound_info.get('hazards', '未知')}\n"
            
            return result
        except Exception as e:
            return f"获取化合物信息时出错: {str(e)}"
    
    def _extract_formula(self, query, task_info):
        """
        从查询或任务信息中提取化学式
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 提取的化学式
        """
        # 从任务信息中提取化合物实体
        if 'detected_entities' in task_info:
            for entity in task_info['detected_entities']:
                if entity['type'] == 'compound':
                    return entity['value']
        
        # 使用化学求解器的方法从查询中提取化学式
        return self.chemistry_solver.extract_formula(query)
    
    def _extract_equation(self, query):
        """
        从查询中提取化学方程式
        
        Args:
            query (str): 用户查询
            
        Returns:
            str: 提取的化学方程式
        """
        # 使用化学求解器的方法从查询中提取方程式
        return self.chemistry_solver.extract_equation(query)
    
    def _extract_compound(self, query, task_info):
        """
        从查询或任务信息中提取化合物名称或化学式
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 提取的化合物
        """
        # 从任务信息中提取化合物实体
        if 'detected_entities' in task_info:
            for entity in task_info['detected_entities']:
                if entity['type'] == 'compound':
                    return entity['value']
        
        # 使用化学求解器的方法从查询中提取化合物
        return self.chemistry_solver.extract_compound(query)
    
    def _calculate_concentration(self, query, task_info):
        """
        计算溶液浓度
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_concentration_params(query)
            result = self.chemistry_solver.calculate_concentration(**params)
            return f"浓度计算结果: {result}"
        except Exception as e:
            return f"计算浓度时出错: {str(e)}"
    
    def _calculate_ph(self, query, task_info):
        """
        计算pH值
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_ph_params(query)
            result = self.chemistry_solver.calculate_ph(**params)
            return f"pH计算结果: {result}"
        except Exception as e:
            return f"计算pH时出错: {str(e)}"
    
    def _calculate_gas_law(self, query, task_info):
        """
        计算气体定律
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_gas_law_params(query)
            result = self.chemistry_solver.calculate_gas_law(**params)
            return f"气体定律计算结果: {result}"
        except Exception as e:
            return f"计算气体定律时出错: {str(e)}"
    
    def _calculate_stoichiometry(self, query, task_info):
        """
        计算化学计量学
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_stoichiometry_params(query)
            result = self.chemistry_solver.calculate_stoichiometry(**params)
            return f"化学计量学计算结果: {result}"
        except Exception as e:
            return f"计算化学计量学时出错: {str(e)}"
    
    def _convert_temperature(self, query, task_info):
        """
        转换温度单位
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 转换结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_temperature_params(query)
            result = self.chemistry_solver.convert_temperature(**params)
            return f"温度转换结果: {result}"
        except Exception as e:
            return f"转换温度时出错: {str(e)}"
    
    def _calculate_dilution(self, query, task_info):
        """
        计算溶液稀释
        
        Args:
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 计算结果
        """
        try:
            # 从查询中提取参数
            params = self._extract_dilution_params(query)
            result = self.chemistry_solver.calculate_solution_dilution(**params)
            return f"稀释计算结果: {result}"
        except Exception as e:
            return f"计算稀释时出错: {str(e)}"
    
    def _extract_concentration_params(self, query):
        """
        从查询中提取浓度计算参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        import re
        
        # 简单的参数提取逻辑，实际应用中可能需要更复杂的NLP处理
        params = {}
        
        # 提取摩尔数
        moles_match = re.search(r'(\d+\.?\d*)\s*mol', query)
        if moles_match:
            params['moles'] = float(moles_match.group(1))
        
        # 提取体积
        volume_match = re.search(r'(\d+\.?\d*)\s*[Ll]', query)
        if volume_match:
            params['volume'] = float(volume_match.group(1))
        
        # 提取质量
        mass_match = re.search(r'(\d+\.?\d*)\s*[gG]', query)
        if mass_match:
            params['mass'] = float(mass_match.group(1))
        
        return params
    
    def _extract_ph_params(self, query):
        """
        从查询中提取pH计算参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        import re
        
        params = {}
        
        # 提取浓度
        concentration_match = re.search(r'(\d+\.?\d*)\s*[Mm]', query)
        if concentration_match:
            params['concentration'] = float(concentration_match.group(1))
        
        # 判断酸碱类型
        if any(keyword in query for keyword in ['强酸', 'HCl', 'HNO3', 'H2SO4']):
            params['acid_type'] = 'strong'
        elif any(keyword in query for keyword in ['弱酸', 'CH3COOH', 'HCOOH']):
            params['acid_type'] = 'weak'
        elif any(keyword in query for keyword in ['强碱', 'NaOH', 'KOH']):
            params['base_type'] = 'strong'
        elif any(keyword in query for keyword in ['弱碱', 'NH3']):
            params['base_type'] = 'weak'
        
        return params
    
    def _extract_gas_law_params(self, query):
        """
        从查询中提取气体定律参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        import re
        
        params = {}
        
        # 提取压强
        pressure_match = re.search(r'(\d+\.?\d*)\s*(?:atm|Pa|kPa|mmHg)', query)
        if pressure_match:
            params['pressure'] = float(pressure_match.group(1))
        
        # 提取体积
        volume_match = re.search(r'(\d+\.?\d*)\s*[Ll]', query)
        if volume_match:
            params['volume'] = float(volume_match.group(1))
        
        # 提取温度
        temp_match = re.search(r'(\d+\.?\d*)\s*[KkCc°]', query)
        if temp_match:
            params['temperature'] = float(temp_match.group(1))
        
        # 提取摩尔数
        moles_match = re.search(r'(\d+\.?\d*)\s*mol', query)
        if moles_match:
            params['moles'] = float(moles_match.group(1))
        
        return params
    
    def _extract_stoichiometry_params(self, query):
        """
        从查询中提取化学计量学参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        params = {}
        
        # 提取化学方程式
        equation = self._extract_equation(query)
        if equation:
            params['equation'] = equation
        
        # 提取反应物量
        import re
        amount_match = re.search(r'(\d+\.?\d*)\s*(?:mol|g)', query)
        if amount_match:
            params['reactant_amount'] = float(amount_match.group(1))
        
        return params
    
    def _extract_temperature_params(self, query):
        """
        从查询中提取温度转换参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        import re
        
        params = {}
        
        # 提取温度值
        temp_match = re.search(r'(\d+\.?\d*)', query)
        if temp_match:
            params['temperature'] = float(temp_match.group(1))
        
        # 判断源单位和目标单位
        if '°C' in query or '摄氏' in query:
            params['from_unit'] = 'C'
        elif '°F' in query or '华氏' in query:
            params['from_unit'] = 'F'
        elif 'K' in query or '开尔文' in query:
            params['from_unit'] = 'K'
        
        if '转' in query:
            if '华氏' in query.split('转')[1] or '°F' in query.split('转')[1]:
                params['to_unit'] = 'F'
            elif '开尔文' in query.split('转')[1] or 'K' in query.split('转')[1]:
                params['to_unit'] = 'K'
            else:
                params['to_unit'] = 'C'
        
        return params
    
    def _extract_dilution_params(self, query):
        """
        从查询中提取稀释计算参数
        
        Args:
            query (str): 用户查询
            
        Returns:
            dict: 参数字典
        """
        import re
        
        params = {}
        
        # 提取初始浓度
        c1_match = re.search(r'(\d+\.?\d*)\s*[Mm]', query)
        if c1_match:
            params['c1'] = float(c1_match.group(1))
        
        # 提取体积
        volumes = re.findall(r'(\d+\.?\d*)\s*[Ll]', query)
        if len(volumes) >= 2:
            params['v1'] = float(volumes[0])
            params['v2'] = float(volumes[1])
        elif len(volumes) == 1:
            params['v1'] = float(volumes[0])
        
        return params