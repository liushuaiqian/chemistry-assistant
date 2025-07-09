#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务路由器
负责问题类型识别和调度路由
"""

import re
from models.local_chat_model import LocalChatModel

class TaskRouter:
    """
    任务路由器类
    负责识别查询类型并路由到相应的处理流程
    """
    
    def __init__(self):
        """
        初始化任务路由器
        """
        # 初始化本地模型用于任务分类
        self.model = LocalChatModel()
        
        # 定义任务类型关键词模式
        self.patterns = {
            'calculation': r'(计算|求|算出|摩尔|质量|浓度|平衡|方程式|化学式|元素|分子量)',
            'knowledge_question': r'(概念|定义|解释|什么是|如何|为什么|原理|理论|规则|法则)',
        }
    
    def identify_task(self, query):
        """
        识别查询的任务类型
        
        Args:
            query (str): 用户查询
            
        Returns:
            tuple: (任务类型, 任务信息字典)
        """
        # 初始化任务信息
        task_info = {
            'original_query': query,
            'detected_entities': [],
            'confidence': 0.0
        }
        
        # 1. 使用规则匹配进行初步分类
        task_type = self._rule_based_classification(query)
        task_info['rule_based_type'] = task_type
        
        # 2. 使用模型进行更精确的分类
        model_task_type, confidence = self._model_based_classification(query)
        task_info['model_based_type'] = model_task_type
        task_info['confidence'] = confidence
        
        # 3. 提取查询中的关键实体
        entities = self._extract_entities(query)
        task_info['detected_entities'] = entities
        
        # 4. 确定最终任务类型（优先使用模型分类结果，置信度高的情况下）
        final_task_type = model_task_type if confidence > 0.7 else task_type
        
        # 如果无法确定类型，默认为一般问题
        if not final_task_type:
            final_task_type = 'general_question'
        
        return final_task_type, task_info
    
    def _rule_based_classification(self, query):
        """
        基于规则的任务分类
        
        Args:
            query (str): 用户查询
            
        Returns:
            str: 任务类型
        """
        # 检查是否匹配计算类问题
        if re.search(self.patterns['calculation'], query):
            return 'calculation'
        
        # 检查是否匹配知识类问题
        if re.search(self.patterns['knowledge_question'], query):
            return 'knowledge_question'
        
        # 如果包含多种模式，可能是复杂问题
        pattern_matches = sum(1 for p in self.patterns.values() if re.search(p, query))
        if pattern_matches > 1:
            return 'complex'
        
        # 默认为一般问题
        return 'general_question'
    
    def _model_based_classification(self, query):
        """
        基于模型的任务分类
        
        Args:
            query (str): 用户查询
            
        Returns:
            tuple: (任务类型, 置信度)
        """
        # 构建分类提示
        prompt = f"""请将以下化学问题分类为以下类型之一：
        1. general_question: 一般性问题
        2. knowledge_question: 化学知识问题
        3. calculation: 化学计算问题
        4. complex: 复杂问题（涉及多个方面）
        
        问题: {query}
        
        分类结果（只返回类型名称和置信度，格式为'类型:置信度'）："""
        
        # 调用模型进行分类
        try:
            response = self.model.generate(prompt)
            # 解析响应获取类型和置信度
            parts = response.strip().split(':')
            if len(parts) >= 2:
                task_type = parts[0].strip()
                confidence = float(parts[1].strip())
                return task_type, confidence
        except Exception as e:
            print(f"模型分类出错: {e}")
        
        # 默认返回
        return 'general_question', 0.5
    
    def _extract_entities(self, query):
        """
        从查询中提取关键实体
        
        Args:
            query (str): 用户查询
            
        Returns:
            list: 提取的实体列表
        """
        entities = []
        
        # 提取化学元素和化合物
        element_pattern = r'([A-Z][a-z]?\d*)+'
        compound_matches = re.findall(element_pattern, query)
        if compound_matches:
            entities.extend([{'type': 'compound', 'value': match} for match in compound_matches])
        
        # 提取数值（可能与计算相关）
        number_pattern = r'\d+(\.\d+)?'
        number_matches = re.findall(number_pattern, query)
        if number_matches:
            entities.extend([{'type': 'number', 'value': match} for match in number_matches])
        
        return entities