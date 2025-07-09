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