#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agent管理器
负责Agent管理和协作逻辑
"""

from agents.local_model_agent import LocalModelAgent
from agents.external_agent import ExternalAgent
from agents.retriever_agent import RetrieverAgent
from agents.tools_agent import ToolsAgent

class AgentManager:
    """
    Agent管理器类
    负责创建、管理和协调各种Agent
    """
    
    def __init__(self):
        """
        初始化Agent管理器
        """
        # 初始化各种Agent
        self.agents = {
            'local_model': LocalModelAgent(),
            'openai': ExternalAgent(provider='openai'),
            'zhipu': ExternalAgent(provider='zhipu'),
            'claude': ExternalAgent(provider='claude'),
            'tongyi': ExternalAgent(provider='tongyi'),
            'retriever': RetrieverAgent(),
            'tools': ToolsAgent()
        }
    
    def select_agents(self, task_type, task_info):
        """
        根据任务类型选择合适的Agent
        
        Args:
            task_type (str): 任务类型
            task_info (dict): 任务相关信息
            
        Returns:
            list: 选中的Agent列表
        """
        selected_agents = []
        
        # 获取首选外部模型（如果指定）
        preferred_model = task_info.get('preferred_model', 'local_model')
        external_model = self.agents.get(preferred_model, self.agents['local_model'])
        
        # 根据任务类型选择合适的Agent
        if task_type == 'general_question':
            # 一般问题使用本地模型或指定的外部模型
            selected_agents.append(external_model)
        
        elif task_type == 'knowledge_question':
            # 知识问题使用检索Agent和模型Agent
            selected_agents.append(self.agents['retriever'])
            selected_agents.append(external_model)
        
        elif task_type == 'calculation':
            # 计算问题使用工具Agent
            selected_agents.append(self.agents['tools'])
        
        elif task_type == 'complex':
            # 复杂问题使用多个Agent协作
            selected_agents.append(self.agents['retriever'])
            selected_agents.append(self.agents['tools'])
            selected_agents.append(external_model)
        
        # 如果没有匹配的任务类型，默认使用本地模型
        if not selected_agents:
            selected_agents.append(self.agents['local_model'])
        
        return selected_agents
    
    def execute_task(self, agents, query, task_info):
        """
        协调多个Agent执行任务
        
        Args:
            agents (list): Agent列表
            query (str): 用户查询
            task_info (dict): 任务相关信息
            
        Returns:
            str: 处理结果
        """
        # 如果只有一个Agent，直接使用该Agent处理
        if len(agents) == 1:
            return agents[0].process(query, task_info)
        
        # 多个Agent协作处理
        intermediate_results = {}
        final_result = ""
        
        # 按顺序执行每个Agent
        for i, agent in enumerate(agents):
            # 将前面Agent的结果作为上下文传递给当前Agent
            agent_result = agent.process(query, task_info, intermediate_results)
            
            # 保存中间结果
            intermediate_results[f'agent_{i}'] = agent_result
            
            # 更新最终结果
            final_result = agent_result
        
        return final_result
    
    def get_available_agents(self):
        """
        获取所有可用的Agent列表
        
        Returns:
            list: Agent名称列表
        """
        return list(self.agents.keys())